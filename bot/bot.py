import os
from dotenv import load_dotenv
import telebot
from telebot import types
from parsebase import (
    brows,
    lashes,
    clarification,
    nails,
    extra_services,
    add_to_cart,
    calculate_total,
    delete_from_cart,
    get_cart_items,
)

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

current_category = {}

def main_menu(show_delete=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Брови"),
        types.KeyboardButton("Ресницы"),
        types.KeyboardButton("Маникюр"),
        types.KeyboardButton("Педикюр"),
        types.KeyboardButton("Посмотреть корзину"),
        types.KeyboardButton("Назад")
    )
    if show_delete:
        markup.add(types.KeyboardButton("Выбрать услугу для удаления"))
    return markup

@bot.message_handler(commands=['start'])
def greeting(message):
    welcome_message = (
        "Привет! Я бот, который сможет сориентировать вас по "
        "итоговой стоимости вашего посещения салона МАМА МИА. "
        "Для начала сбора услуги выберите категорию:"
    )
    markup = main_menu()
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.startswith("Удалить "))
def handle_deletion(message):
    
    service_name = message.text.replace("Удалить ", "").strip()
    user_id = message.from_user.id
    deleted_service = delete_from_cart(user_id, service_name)
    if deleted_service:
        bot.send_message(message.chat.id, f"Услуга '{service_name}' удалена из корзины.", reply_markup=main_menu(show_delete=True))
        show_cart(message)
    else:
        bot.send_message(message.chat.id, "Ошибка: услуга не найдена в корзине или уже удалена.", reply_markup=main_menu(show_delete=True))

@bot.message_handler(content_types=['text'])
def handle_category(message):
    global current_category
    if message.text == 'Брови':
        current_category = {'context': 'brows'}
        send_services(message, brows(), 0)
    elif message.text == 'Ресницы':
        current_category = {'context': 'lashes'}
        send_services(message, lashes(), 0)
    elif message.text == 'Маникюр':
        current_category = {'context': 'hand'}
        process_clarification(message, 'hand', nails, 1)
    elif message.text == 'Педикюр':
        current_category = {'context': 'leg'}
        process_clarification(message, 'leg', nails, 1)
    elif message.text == 'Посмотреть корзину':
        show_cart(message)  
    elif message.text == 'Выбрать услугу для удаления':
        show_deletion_options(message)  
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, "Выберите категорию", reply_markup=main_menu())
    else:
        process_service_selection(message)

def show_cart(message):
    
    user_id = message.from_user.id
    total = calculate_total(user_id)
    bot.send_message(message.chat.id, f"{total}", reply_markup=main_menu(show_delete=True))

def show_deletion_options(message):
    
    user_id = message.from_user.id
    cart_items = get_cart_items(user_id)  

    if not cart_items:
        bot.send_message(message.chat.id, "В вашей корзине нет услуг.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    for item in cart_items:
        service_name = item['service_name']
        markup.add(types.KeyboardButton(f"Удалить {service_name}"))

    markup.add(types.KeyboardButton("Назад"))  
    bot.send_message(message.chat.id, "Выберите услугу для удаления:", reply_markup=markup)

def send_services(message, services, step):
    if not services:
        bot.send_message(message.chat.id, "Услуги не найдены.")
        return

    services_text = "Доступные услуги:\n"
    for service in services:
        services_text += f"- {service['name']}:\n"
        services_text += f"  • Цена мастера квалификации 1: {service['master1_price']}₽\n"
        services_text += f"  • Цена мастера квалификации 2: {service['master2_price']}₽\n"
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    for service in services:
        for master in [1, 2]:
            btn_text = f"{service['name']} (Мастер {master}) - {service[f'master{master}_price']}₽"
            markup.add(types.KeyboardButton(btn_text))
    markup.add(types.KeyboardButton("Назад"))
    markup.add(types.KeyboardButton("Посмотреть корзину"))
    if step == 1:
        markup.add(types.KeyboardButton("Далее"))
    if step == 2:
        markup.add(types.KeyboardButton("Допы"))
    
    bot.send_message(message.chat.id, services_text.strip(), reply_markup=markup)

def process_clarification(message, context, next_step, step):
    if step == 1:
        bot.send_message(
            message.chat.id,
            "Будем собирать услугу поэтапно: 1 - снятие прошлого покрытия 2 - выбор нового покрытия 3 - дополнительные опции. Добавьте услуги из предложенных выше или продолжите. Для продолжения выберите 'Далее'."
        )
        clarification_services = clarification(context)
        send_services(message, clarification_services, 1) 
    elif step == 2:
        bot.send_message(
            message.chat.id,
            "Добавьте услуги из предложенных выше или продолжите. Для продолжения выберите 'Допы'."
        )
        clarification_services = nails(context)
        send_services(message, clarification_services, 2) 
    current_category['next_step'] = next_step

def process_service_selection(message):
    try:
        service, price = message.text.rsplit(' - ', 1)
        service = service.strip()
        price = price.replace('₽', '').strip()
        if add_to_cart(message.from_user.id ,service, price):
            bot.send_message(message.chat.id, "Услуга добавлена в корзину.")
            return 1
        else:
            bot.send_message(message.chat.id, "Ошибка добавления в корзину. Попробуйте снова")
    except ValueError:
        if message.text == 'Далее' and 'next_step' in current_category:
            process_clarification(message, 'hand', extra_services, 2)
        elif message.text == 'Допы' and 'next_step' in current_category: 
            send_services(message, current_category['next_step'](), 0)
            return 1
        else:
            bot.send_message(message.chat.id, "Выберите услугу из предложенного списка.")

bot.polling(none_stop=True)
