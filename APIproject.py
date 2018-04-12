from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
import requests
import math


# Функция приветствования пользователя
def start(bot, update):
    update.message.reply_text(
        "Здравствуйте, я бот-экскурсовод. Найду объекты необходимые Вам. Напишите адрес, по которому Вы сейчас находитесь.")
    return 1


# Функция, в которой бот узнает адресс пользователя
def address(bot, update, user_data):
    user_data['address'] = update.message.text
    update.message.reply_text(
        "Адрес успешно принят.Введите название организации, которую вам надо найти.(если хотите изменить свой адрес напишите комманду /city 'новый адрес')")
    return 2


# Функция, в которой бот узнает организацию необходую пользователю
def organization(bot, update, user_data):
    user_data['org'] = update.message.text
    update.message.reply_text(
        "Организация успешно принята. Чтобы сменить организацию введите комманду /org 'название организации'")
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "3c4a592e-c4c0-4949-85d1-97291c87825c"
    address_ll = coords(user_data['address'])
    search_params = {
        "apikey": api_key,
        "text": user_data['org'],
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz",
    }
    response = requests.get(search_api_server, params=search_params)
    if not response:
        # ...
        pass
    json_response = response.json()
    if len(json_response['features']) == 0:
        update.message.reply_text('По Вашему запросу ничего не найдено, введите, новую организацию:')
        return 2
    else:
        user_data['features'] = json_response['features']
        update.message.reply_text('Чтобы выбрать организацию введите цифру:')

        for i in range(len(user_data['features'])):
            update.message.reply_text(user_data['features'][i]['properties']['id'] + ': ' +
                                      user_data['features'][i]['properties']['CompanyMetaData']['name'])
        return 3


# Функция, в которой пользователь выберет понравившуюся организацию
def choose(bot, update, user_data):
    text = update.message.text
    update.message.reply_text('Число введено')
    if int(text) > len(user_data['features']):
        update.message.reply_text('Ошибка ввода. Повторите ввод.')
        return 3
    else:
        id = int(text) - 1
        response = user_data['features'][id]
        coordinates = response['geometry']['coordinates']
        organization = response["properties"]["CompanyMetaData"]
        # # Название организации.
        org_name = organization["name"]
        update.message.reply_text("Название: " + org_name)
        # # Адрес организации.
        org_address = organization["address"]
        update.message.reply_text("Адрес: " + org_address)

        update.message.reply_text('Расстояние до вашего объекта: ' + diss(user_data['address'],
                                                                          str(coordinates[0]) + ',' + str(
                                                                              coordinates[1])) + ' метров')

        update.message.reply_text(response["properties"]["CompanyMetaData"]['Hours']['text'])
        ll, spn = str(coordinates[0]) + ',' + str(coordinates[1]), "0.001,0.001"
        # Можно воспользоваться готовой фукнцией,
        # которую предлагалось сделать на уроках, посвященных HTTP-геокодеру.

        static_api_request = "http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map".format(**locals())

        bot.sendPhoto(
            update.message.chat.id,  # Идентификатор чата. Куда посылать картинку.
            # Ссылка на static API по сути является ссылкой на картинку.
            static_api_request
        )
        update.message.reply_text('Если Вы хотите найти что-то еще - напишите адрес, по которому Вы находитесь.')
        return 1


# Нахождение координат
def coords(place):
    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode=" + place + ", 1&format=json"
    try:
        response = requests.get(geocoder_request)
        if response:
            json_response = response.json()
            return json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]['Point']['pos']
        else:
            print("Ошибка выполнения запроса:")
            print(geocoder_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
    except:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")


# Перевыбор города
def city(bot, update, args, user_data):
    user_data['address'] = (', ').join(args)
    update.message.reply_text(
        'Введите название организации или измените свой адрес, написав комманду /city "новый адрес":')


# Перевыбор организации
def org(bot, update, args, user_data):
    user_data['org'] = (', ').join(args)
    update.message.reply_text(
        "Организация успешно принята. Чтобы сменить организацию введите комманду /org 'название организации'")
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "3c4a592e-c4c0-4949-85d1-97291c87825c"
    address_ll = coords(user_data['address'])
    search_params = {
        "apikey": api_key,
        "text": user_data['org'],
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz",
    }
    response = requests.get(search_api_server, params=search_params)

    json_response = response.json()
    if len(json_response['features']) == 0:
        update.message.reply_text('По Вашему запросу ничего не найдено, введите, новую организацию:')
        return 2
    else:
        user_data['features'] = json_response['features']
        update.message.reply_text('Чтобы выбрать организацию введите цифру:')

        for i in range(len(user_data['features'])):
            update.message.reply_text(user_data['features'][i]['properties']['id'] + ': ' +
                                      user_data['features'][i]['properties']['CompanyMetaData']['name'])
        return 3


# Рассчёт расстояния
def diss(name, till):
    try:
        geocoder_request = 'http://geocode-maps.yandex.ru/1.x/?geocode=' + name + '&format=json'
        geocoder_request2 = 'http://geocode-maps.yandex.ru/1.x/?geocode=' + till + '&format=json'
        response = requests.get(geocoder_request)
        response2 = requests.get(geocoder_request2)
        if response:
            json_response = response.json()
            json_response2 = response2.json()
            a = json_response["response"]["GeoObjectCollection"]["featureMember"][0]['GeoObject']['Point']['pos']
            b = json_response2["response"]["GeoObjectCollection"]["featureMember"][0]['GeoObject']['Point']['pos']
            a = a.split()
            b = b.split()
            a_lon, a_lat = float(a[0]), float(a[1])
            b_lon, b_lat = float(b[0]), float(b[1])
            degree_to_meters_factor = 111 * 1000
            radians_lattitude = math.radians((a_lat + b_lat) / 2.)
            lat_lon_factor = math.cos(radians_lattitude)
            dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
            dy = abs(a_lat - b_lat) * degree_to_meters_factor
            distance = math.sqrt(dx * dx + dy * dy)
            return str(int(distance))
        else:
            print("Ошибка выполнения запроса:")
            print(geocoder_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
    except:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")


# Прощание ;(
def stop(bot, update):
    update.message.reply_text('До свидания!')
    return ConversationHandler.END


# Главная функция
def main():
    updater = Updater("507140989:AAH2XfsU-TGf7NJv_oNgegj9Wegb89y5zvg")
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text, address, pass_user_data=True)],
            2: [MessageHandler(Filters.text, organization, pass_user_data=True),
                CommandHandler("city", city, pass_args=True, pass_user_data=True)],
            3: [MessageHandler(Filters.text, choose, pass_user_data=True),
                CommandHandler("org", org, pass_args=True, pass_user_data=True)]},
        fallbacks=[CommandHandler('stop', stop)])
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


# Вызов главной функции
if __name__ == '__main__':
    main()  # 507140989:AAH2XfsU-TGf7NJv_oNgegj9Wegb89y5zvg
