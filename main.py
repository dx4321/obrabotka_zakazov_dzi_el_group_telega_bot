# -*- coding: utf-8 -*-
import asyncio
import sqlite3
import time
from datetime import datetime
from peewee import Model, SqliteDatabase, CharField, TextField, DateTimeField
from aiogram import Bot, types

from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import yaml

# База данных
# Настройка базы данных SQLite
db = SqliteDatabase('orders.db')


# Модель данных для пользователей
class User(Model):
    user_id = CharField(unique=True)
    phone_number = CharField()
    full_name = CharField()
    role = CharField(default='client')  # Добавим поле для роли пользователя

    class Meta:
        database = db


# Модель данных для заказов
class Order(Model):
    user_id = CharField()
    product_type = CharField()
    quantity = CharField()
    status = CharField()
    timestamp = DateTimeField()

    class Meta:
        database = db


# Модель данных для обращений
class Inquiry(Model):
    user_id = CharField()
    topic = TextField()
    message = TextField()
    status = CharField()
    timestamp = DateTimeField()

    class Meta:
        database = db


# Добавим новый класс состояний для создания обращения
class InquiryCreation(StatesGroup):
    Topic = State()
    Message = State()


# Создание таблиц в базе данных (если их нет)
db.create_tables([Order, Inquiry, User])


# Загрузка списка администраторов из config.yaml
def load_admins():
    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            return config.get('admins', [])
    except FileNotFoundError:
        return []


def load_telegram_token():
    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            return config.get('telegram_token')
    except FileNotFoundError:
        return []


# Проверка, является ли пользователь администратором
def is_admin(user_id):
    admins = load_admins()
    return int(user_id) in admins


# Инициализация бота и диспетчера
# https://t.me/dgi_el_group_bot
bot = Bot(token=load_telegram_token())
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


# Состояния
# Определение стейт-машины для взаимодействия с пользователем
class UserAuthorization(StatesGroup):
    PhoneNumber = State()
    FullName = State()


# State машина для управления заказами
class OrderCreation(StatesGroup):
    ProductName = State()
    Quantity = State()
    Address = State()


# Клавиатура для администратора
admin_menu_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Клиентские заказы"), KeyboardButton(text="Тикеты")],
        [KeyboardButton(text="Поддержка")],
    ],
    resize_keyboard=True,
)


# Клавиатура для клиента
def main_menu_markup():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Мои заказы",
        "Обращения",
        "Техническая поддержка",
    ]
    keyboard.add(*buttons)
    return keyboard


# Авторизация
# Обработка команды / start
@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    # Проверяем, есть ли пользователь в базе данных
    user_exists = User.select().where(User.user_id == message.chat.id).exists()

    if not user_exists:
        # Если пользователя нет, запрашиваем номер телефона
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        button = KeyboardButton("Скинуть свой номер", request_contact=True)
        keyboard.add(button)

        await message.reply("Добро пожаловать! Для начала, поделитесь своим контактным номером телефона.",
                            reply_markup=keyboard)
        await UserAuthorization.PhoneNumber.set()
    else:
        # Если пользователь есть, проверяем его роль
        user = User.get(User.user_id == message.chat.id)
        if is_admin(user.user_id):
            await message.reply("Добрый день, администратор!", reply_markup=admin_menu_markup)
        else:
            await message.reply(f"Добрый день, {user.full_name}!", reply_markup=main_menu_markup())


# Обработка контактного номера телефона
@dp.message_handler(state=UserAuthorization.PhoneNumber, content_types=types.ContentType.CONTACT)
async def process_contact(message: Message, state: FSMContext):
    contact_phone_number = message.contact.phone_number
    print(contact_phone_number)
    await state.update_data(phone_number=contact_phone_number)
    await message.reply("Отлично! Теперь укажите Ваше ФИО.", reply_markup=types.ReplyKeyboardRemove())
    await UserAuthorization.next()


# Обработка ФИО
@dp.message_handler(state=UserAuthorization.FullName)
async def process_fullname(message: Message, state: FSMContext):
    user_fullname = message.text
    user_data = await state.get_data()
    user_phone_number = user_data.get("phone_number")

    # Проверяем, есть ли пользователь в базе данных
    user_exists = User.select().where(User.user_id == message.chat.id).exists()

    if not user_exists:
        # Если пользователя нет, сохраняем его в базе данных
        User.create(user_id=message.chat.id, phone_number=user_phone_number, full_name=user_fullname)

    await state.finish()
    await message.reply(f"Спасибо, {user_fullname}! Вы успешно авторизованы.", reply_markup=main_menu_markup())


# Обработка кнопок главного меню
@dp.message_handler(lambda message: message.text in ["Мои заказы", "Обращения", "Техническая поддержка"])
async def process_main_menu(message: Message):
    if message.text == "Мои заказы":
        await show_order_options(message.chat.id)
    elif message.text == "Обращения":
        await show_inquiry_options(message.chat.id)
    elif message.text == "Техническая поддержка":
        await bot.send_message(message.chat.id, "Начат поиск оператора для технической поддержки.")


# Заказы
# Функция для отображения опций заказов
async def show_order_options(chat_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("Создать заказ", callback_data='create_order'),
        InlineKeyboardButton("Просмотреть мои заказы", callback_data='view_orders'),
    ]
    keyboard.add(*buttons)
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


# Обработка нажатия на кнопку "Просмотреть мои заказы"
@dp.callback_query_handler(lambda c: c.data == 'view_orders')
async def view_orders_callback(query: CallbackQuery):
    user_id = query.from_user.id

    # Получаем заказы пользователя из базы данных
    user_orders = Order.select().where(Order.user_id == str(user_id))

    if user_orders:
        # Если есть заказы, формируем сообщение с списком заказов
        orders_text = "Список ваших заказов:\n"
        for order in user_orders:
            orders_text += f"Заказ #{order.id}: {order.product_type}, Количество: {order.quantity}, Статус: {order.status}\n"

        await bot.send_message(user_id, orders_text)
    else:
        # Если заказов нет, отправляем сообщение об этом
        await bot.send_message(user_id, "Вы еще не сделали заказов. Чтобы сделать заказ, выберите 'Создать заказ'.")

    # Завершаем обработку коллбэка
    await query.answer()


# Добавим новый обработчик для создания заказа
@dp.callback_query_handler(lambda query: query.data == 'create_order')
async def create_order(query: CallbackQuery):
    await query.answer()
    await bot.send_message(query.from_user.id, "Введите название товара:")
    await OrderCreation.ProductName.set()


# Обработка ввода названия товара
@dp.message_handler(state=OrderCreation.ProductName)
async def process_order_product_name(message: Message, state: FSMContext):
    product_name = message.text
    await state.update_data(order_product_name=product_name)
    await OrderCreation.next()
    await bot.send_message(message.chat.id, "Введите количество товара:")


# Обработка ввода количества товара
@dp.message_handler(state=OrderCreation.Quantity)
async def process_order_quantity(message: Message, state: FSMContext):
    quantity = message.text
    await state.update_data(order_quantity=quantity)
    await OrderCreation.next()
    await bot.send_message(message.chat.id, "Введите адрес доставки:")


# Обработка ввода адреса доставки
@dp.message_handler(state=OrderCreation.Address)
async def process_order_address(message: Message, state: FSMContext):
    address = message.text
    user_data = await state.get_data()
    product_name = user_data.get("order_product_name")
    quantity = user_data.get("order_quantity")

    # Создание заказа в базе данных
    Order.create(user_id=message.chat.id, product_type=product_name, quantity=quantity, status="в обработке",
                 timestamp=datetime.now())

    await state.finish()
    await bot.send_message(message.chat.id, "Ваш заказ успешно создан!", reply_markup=main_menu_markup())


# Обращения
# Функция для отображения опций обращений
async def show_inquiry_options(chat_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("Создать обращение", callback_data='create_inquiry'),
        InlineKeyboardButton("Просмотреть обращения", callback_data='view_inquiries'),
    ]
    keyboard.add(*buttons)
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


# Добавим новый обработчик для просмотра обращений
@dp.callback_query_handler(lambda query: query.data == 'view_inquiries')
async def view_inquiries(query: CallbackQuery):
    await query.answer()

    inquiries = Inquiry.select().where(Inquiry.user_id == query.from_user.id)

    if not inquiries.exists():
        await bot.send_message(query.from_user.id, "У вас пока нет обращений.")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(f"{inquiry.topic} - {inquiry.status}", callback_data=f'view_inquiry_{inquiry.id}')
        for inquiry in inquiries
    ]
    keyboard.add(*buttons)

    await bot.send_message(query.from_user.id, "Выберите обращение для просмотра:", reply_markup=keyboard)


# Обработчик для просмотра конкретного обращения
@dp.callback_query_handler(lambda query: query.data.startswith('view_inquiry'))
async def view_inquiry(query: CallbackQuery):
    await query.answer()

    inquiry_id = int(query.data.split('_')[2])
    inquiry = Inquiry.get(Inquiry.id == inquiry_id)

    await bot.send_message(query.from_user.id,
                           f"Тема: {inquiry.topic}\nСтатус: {inquiry.status}\nСообщение: {inquiry.message}")


# Обработчик для создания обращения
@dp.callback_query_handler(lambda query: query.data == 'create_inquiry')
async def create_inquiry(query: CallbackQuery):
    await query.answer()
    await bot.send_message(query.from_user.id, "Введите тему вашего обращения:")
    await InquiryCreation.Topic.set()


# Обработчик для получения темы обращения
@dp.message_handler(state=InquiryCreation.Topic)
async def process_inquiry_topic(message: Message, state: FSMContext):
    inquiry_topic = message.text
    await state.update_data(topic=inquiry_topic)
    await bot.send_message(message.chat.id, "Тема обращения сохранена. Теперь введите текст вашего обращения:")
    await InquiryCreation.next()


# Обработчик для получения текста обращения и сохранения в базу данных
@dp.message_handler(state=InquiryCreation.Message)
async def process_inquiry_message(message: Message, state: FSMContext):
    inquiry_message = message.text
    user_data = await state.get_data()
    inquiry_topic = user_data.get("topic")

    # Сохраняем обращение в базу данных
    Inquiry.create(user_id=message.chat.id, topic=inquiry_topic, message=inquiry_message, status="В обработке",
                   timestamp=datetime.now())

    await state.finish()
    await bot.send_message(message.chat.id, "Обращение успешно создано!")


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- Часть администратора +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Обработчик для кнопки "Заказы"
@dp.message_handler(lambda message: message.text == "Клиентские заказы")
async def admin_orders(message: Message):
    # Получаем все заказы из базы данных
    orders = Order.select()

    # Выводим информацию о заказах администратору
    orders_text = "Список заказов:\n"
    for order in orders:
        orders_text += f"Заказ #{order.id}: {order.product_type}, Количество: {order.quantity}, Статус: {order.status}\n"

    await message.reply(orders_text)


# Обработчик для кнопки "Тикеты"
@dp.message_handler(lambda message: message.text == "Тикеты")
async def admin_inquiries(message: Message):
    # Получаем все обращения из базы данных
    inquiries = Inquiry.select()

    # Выводим информацию об обращениях администратору
    inquiries_text = "Список обращений:\n"
    for inquiry in inquiries:
        inquiries_text += f"Обращение #{inquiry.id}: Тема: {inquiry.topic}, Статус: {inquiry.status}\n"

    await message.reply(inquiries_text)


# Обработчик для кнопки "Поддержка"
@dp.message_handler(lambda message: message.text == "Поддержка")
async def tech_support(message: Message):
    # Добавьте здесь логику технической поддержки
    pass


# ... (обработка других сценариев)

# Запуск бота
if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
