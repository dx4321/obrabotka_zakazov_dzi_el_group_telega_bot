# Описание проекта
Здесь выложил код дипломной работы

Бот доступен по ссылке https://t.me/dgi_el_group_bot

## Название проекта

Сервис обработки заказов для Telegram-бота

## Цель проекта

Создать Telegram-бота, который будет обрабатывать заказы на покупку сухих бульонов и ингредиентов.

## Используемые технологии

* Python 3.8
* Peewee
* Aiogram

## Входные и оперативные документы, файлы и экранные формы

### Входные документы

* Заявки на покупку продуктов
    * Формат: Текстовый документ
    * Описание: Клиенты могут отправлять заявки на покупку сухих бульонов и ингредиентов через Telegram-бота. Заявка содержит информацию о выбранных продуктах и их количестве.

### Оперативные документы

* Статус заказов
    * Формат: Экранные формы в Telegram-боте
    * Описание: Клиенты могут отслеживать статус своих заказов в режиме реального времени. Информация о текущем статусе (в обработке, доставлен и т.д.) предоставляется на экранных формах.

### Входные файлы

* Контакт клиента
    * Формат: Текстовый файл
    * Описание: при старте бота выводится сообщение "Поделитесь своим контактом", и клиент должен отправить свой контакт. Этот файл используется для идентификации клиента и связи с его заказами и обращениями.

### Оперативные файлы

* Диалоги с операторами
    * Формат: Экранные формы в Telegram-боте
    * Описание: Пользователь может общаться с технической поддержкой через чат с оператором. Диалоги сохраняются в виде текстовых файлов и используются для отслеживания и анализа вопросов клиентов.

### Экранные формы

* Главное меню
    * Описание: после предоставления контакта клиента, на экране появляется главное меню с кнопками "Мои заказы", "Мои заявки", "Обратиться в чат" и "Вопрос боту". Пользователь может выбирать необходимый раздел.
* Экран отслеживания заказа
    * Описание: Пользователь видит текущий статус своего заказа (в обработке, доставлен и т.д.) на этом экране.
* Чат с оператором
    * Описание: Экранные формы, где клиент может общаться с операторами технической поддержки. Интерфейс позволяет отправлять текстовые сообщения и прикреплять файлы.
* Форма для оставления заявки
    * Описание: Пользователь может оставить заявку на покупку продуктов, указав тип продукта и его количество.

## Результатные документы, файлы и экранные формы

### Результатные документы

* Квитанция о заказе
    * Формат: Экранные формы в Telegram-боте
    * Описание: Клиент получает квитанцию оформленного заказа после успешного завершения процесса покупки. Включает в себя детали заказа, общую стоимость и информацию о доставке.

* Электронный чек
    * Формат: PDF или изображение
    * Описание: после доставки продуктов клиент получает электронный чек в виде файла. Включает в себя детали заказа и оплаты.

* Экран подтверждения заказа
    * Описание: после завершения оформления заказа клиент видит экран с подтверждением заказа, содержащим основные детали заказа и дату доставки.
* Экран обращения к технической поддержке
    * Описание: после завершения чата с оператором, клиент видит экран с подтверждением обращения, который также сохраняется в виде файла.

### Примечания

* Все оперативные данные, такие как статус заказов и диалоги с операторами, хранятся в базе данных SQLite для обеспечения постоянного доступа и анализа.
* Результатные документы и файлы предоставляются клиенту в цифровой форме для удобства хранения и последующего доступа.

## Описание работы бота

При запуске бота пользователь должен предоставить свой контактный номер телефона и ФИО. После этого ему будет предоставлено главное меню с кнопками "Мои заказы", "Мои заявки", "Обратиться в чат" и "Вопрос боту".

### Нажатие на кнопку "Мои заказы" открывает экран отслеживания заказов. Здесь пользователь может увидеть текущий статус своих заказов.

### Нажатие на кнопку "Мои заявки" открывает экран для оставления заявки на покупку продуктов. Пользователь должен указать тип продукта и его количество.

### Нажатие на кнопку "Обратиться в чат" открывает чат с оператором технической поддержки. Пользователь может общаться с оператором в текстовом формате и прикреплять файлы.

### Нажатие на кнопку "Вопрос боту" позволяет пользователю задать вопрос боту. Бот будет пытаться ответить на вопрос на основе своих знаний.

## Примеры использования бота

* **Пользователь хочет сделать заказ на 1 кг куриного бульона и 2 кг томат