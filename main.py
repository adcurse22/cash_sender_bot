import telebot
from telebot import types
import easyocr
from decouple import config

# Инициализация бота
telegram_token = config('TELEGRAM_TOKEN')
bot = telebot.TeleBot(telegram_token)


def text_recognize(file_path):
    reader = easyocr.Reader(["ru"])
    result = reader.readtext(file_path, detail=0, allowlist='1,2,3,4,5,6,7,8,9,0,А,Б,В,Г,Е,З,И,К,Л,М,Н,О,П,С,Т,Х,Ч,Ь,Э,Я,а,б,в,г,е,з,и,к,л,м,н,о,п,с,т,х,ч,ь,э,я')

    if len(result) >= 5:
        combined_result = ''.join(result[:5])
        if result[1] != result[2]:
            # Проверяем на наличие последовательности из трех нулей
            index = combined_result.find('000')
            if index != -1:
                # Удаляем все символы до последовательности из трех нулей включительно
                combined_result = combined_result[index + 20:]
            return combined_result
    return None


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def hello(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    with open('photo5.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo,
                       caption=f'Привет {message.from_user.first_name}! Пожалуйста, предоставьте четкое изображение банкноты номиналом  расположенной горизонтаьно. Изображение должно быть высокого качества для корректной обработки. Фото должно выглядеть примерно так: ',
                       reply_markup=markup)
# Обработчик для получения фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохраняем фото локально
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

    # Распознавание текста на фото
    bill_number = text_recognize("image.jpg")

    if bill_number:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте свой геотег.")
        bot.register_next_step_handler(message, ask_for_location, bill_number)
    else:
        bot.send_message(message.chat.id, "Невозможно распознать номер купюры или это не купюра.")


def ask_for_location(message, bill_number):
    if message.location:
        bot.send_message(message.chat.id, "На что будут потрачены деньги?")
        bot.register_next_step_handler(message, final_step, bill_number, message.location)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте геотег.")


def final_step(message, bill_number, location):
    expense_purpose = message.text
    text = f"Номер купюры: {bill_number}\nГеотег: {location.latitude}, {location.longitude}\nПотрачено на: {expense_purpose}"
    send_text(text)


# Отправка текста в канал
def send_text(text):
    bot.send_message(get_channel_id(), text)


# Функция для получения ID канала
def get_channel_id():
    return config('CHANNEL_ID')


bot.polling(none_stop=True)