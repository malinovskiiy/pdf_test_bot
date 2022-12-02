# Импорт библиотек ========================================
# -*- coding: utf-8 -*-
import json
import uuid
import requests
import telebot
import os
import sys
import time
import sqlite3


from telebot.types import InlineKeyboardButton
from telegram_bot_pagination import InlineKeyboardPaginator
from math import ceil
from datetime import datetime, date
from dateutil import relativedelta


# Импорт компонентов бота ================================

from markups import main_bot_markup, ip_bot_markup, markup, ip_back_markup, full_fin_report_markup, back_to_fin_report_start_markup, fin_analysis_markup, main_menu_markup, reputation_markup, fin_risk_markup, one_day_markup  # Маркапы все
from API_KEYS import *  # Ключи API


def restart():
    print("bot crashed, restart now!!!")
    os.execv(sys.executable, ['python'] + sys.argv)

# Бот ==============================================

bot = telebot.TeleBot(telegram_api_key)

# === ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ===

connect = sqlite3.connect('users.db', check_same_thread=False)

cursor = connect.cursor()


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!

def clean_message(call):
    bot.delete_message(call.message.chat.id, call.message.id)


# Обработчик стартовой команды ====================================
@bot.message_handler(commands=['start'])
def start(message):

    msg_greet_main = f'Мур-мур, {message.from_user.first_name}!\n\n😻Я - МурLOOK - персональный кото-ассистент для проверки контрагентов.\n\nЯ могу в режиме реального времени:\n\n✅ Выполнить полную проверку надежности контрагента\n❌ Выявить его негативные факторы.\n\n❗️Для проверки просто введи ИНН компании или ИП, или же название компании (также можно указать город) и нажми "отправить сообщение".\n\n❓Возникли вопросы? Напиши нам @support_tgbots_test156.'

    
    cursor.execute('CREATE TABLE IF NOT EXISTS login_id(id INTEGER, query TEXT, bot_main_msg TEXT, company_name TEXT, inn TEXT, date_registered TEXT, kpp TEXT, ogrn TEXT, ogrn_date TEXT, work_type_code TEXT,work_type_info TEXT, company_status TEXT, company_address TEXT, fund TEXT, zakupki_date_start TEXT, zakupki_date_end TEXT, contracts_date_start TEXT, contracts_date_end TEXT, user_search_results TEXT, director_change TEXT, address_change TEXT, founders_change TEXT)')

    connect.commit()

    people_id = message.chat.id

    cursor.execute(f"SELECT id FROM login_id WHERE id = {people_id}")

    connect.commit()

    data = cursor.fetchone()

    if data is None:
        user_info = [message.chat.id, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

        cursor.execute("INSERT INTO login_id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", user_info)

        connect.commit()
    
    
    bot.send_message(message.chat.id, msg_greet_main, parse_mode='html')

# Обработчик стартовой команды ====================================


@bot.message_handler(commands=['main_menu'])
def main_menu(message):
    msg_greet_main = f'Мур-мур, {message.from_user.first_name}!\n\n😻Я - МурLOOK - персональный кото-ассистент для проверки контрагентов.\n\nЯ могу в режиме реального времени:\n\n✅ Выполнить полную проверку надежности контрагента;\n❌ Выявить его негативные факторы.\n\n❗️ Для проверки просто введи ИНН компании или ИП, или же название компании (также можно указать город) и нажми "отправить сообщение".\n\n❓ Возникли вопросы? Напиши нам @support_tgbots_test156.'

    bot.send_message(message.chat.id, msg_greet_main, parse_mode='html')


@bot.message_handler(commands=['ul_name_search'])
def ul_name_search(message):
    bot.send_message(
        message.chat.id, 'Введите название организации', parse_mode='html')


@bot.message_handler(commands=['fio_name_search'])
def ul_name_search(message):
    bot.send_message(
        message.chat.id, 'Введите ФИО руководителя ИП или юр.лица', parse_mode='html')


# Обработчик ИНН запроса ==========================================
@bot.message_handler(content_types=['text'])
def message_handler(message):
    global search_result_pages

    cursor.execute("UPDATE login_id SET query = (?) WHERE id = (?)", (message.text, message.chat.id))

    connect.commit()

    cursor.execute(f"SELECT query FROM login_id WHERE id = {message.chat.id}")

    connect.commit()

    user_query = cursor.fetchone()[0]

    # БД ЧЕК✅ ЮРИДИЧЕСКОЕ ЛИЦО (10 цифр инн) (цифра либо команда из 11 цифр со слешем)
    if len(user_query) == 10 and user_query.isdigit() or (len(user_query) == 11 and user_query[1:].isdigit() and user_query.startswith('/')):
        # try:
        if user_query.startswith('/'):
            message_text = user_query[1:]
        else:
            message_text = user_query

        info_dict = {}

        arb_msg1 = bot.send_message(message.chat.id, 'Ищу информацию по запросу...')

        response = requests.get(
            f'https://api-fns.ru/api/egr?req={message_text}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.delete_message(message.chat.id, arb_msg1.id)
        
        # Первая информация о ЮРИДИЧЕСКОМ ЛИЦЕ(название, инн, дата рег., кпп, огрн)====

        try:
            info_dict['company_name'] = json_object['items'][0]['ЮЛ']['НаимСокрЮЛ']
        except KeyError:
            info_dict['company_name'] = '❌ Не найдено'

        
        cursor.execute("UPDATE login_id SET company_name = (?) WHERE id = (?)", (info_dict['company_name'], message.chat.id))

        connect.commit()

        info_dict['inn'] = json_object['items'][0]['ЮЛ']['ИНН']

        cursor.execute("UPDATE login_id SET inn = (?) WHERE id = (?)", (info_dict['inn'], message.chat.id))

        connect.commit()

        
        printed_year = json_object['items'][0]['ЮЛ']['ДатаРег'][:4]
        printed_month = json_object['items'][0]['ЮЛ']['ДатаРег'][5:7]
        printed_day = json_object['items'][0]['ЮЛ']['ДатаРег'][8:10]

        info_dict['date_registered'] = f'{printed_day}.{printed_month}.{printed_year}'
        
        today = datetime.today()

        ul_date_registered = datetime.strptime(info_dict['date_registered'], "%d.%m.%Y")

        delta = relativedelta.relativedelta(today, ul_date_registered)

        age = datetime.today().year - ul_date_registered.year

        yrs = {'1':'год', '234':'года', '567890':'лет'}

        year_suffix = next(v for k, v in yrs.items() if str(age%10) in k)
        
        if age > 10 and str(age)[-2] == '1': year_suffix = 'лет'

        month_suffix = ("месяц" if 11 <= delta.months <= 19 or delta.months % 10 == 1 else
                        "месяца" if 2 <= delta.months % 10 <= 4 else
                        "месяцев")

        info_dict['date_registered'] += f', ведет деятельность уже {delta.years} {year_suffix} и {delta.months} {month_suffix}'

        cursor.execute("UPDATE login_id SET date_registered = (?) WHERE id = (?)", (info_dict['date_registered'], message.chat.id))
        connect.commit()
        

        info_dict['kpp'] = json_object['items'][0]['ЮЛ']['КПП']
        cursor.execute("UPDATE login_id SET kpp = (?) WHERE id = (?)", (info_dict['kpp'], message.chat.id))
        connect.commit()

        info_dict['ogrn'] = json_object['items'][0]['ЮЛ']['ОГРН']
        cursor.execute("UPDATE login_id SET ogrn = (?) WHERE id = (?)", (info_dict['ogrn'], message.chat.id))
        connect.commit()

        info_dict['ogrn_date'] = datetime.strptime(json_object['items'][0]['ЮЛ']['ДатаОГРН'], "%Y-%m-%d").strftime("%d.%m.%Y")

        cursor.execute("UPDATE login_id SET ogrn_date = (?) WHERE id = (?)", (info_dict['ogrn_date'], message.chat.id))
        connect.commit()

        # Основной вид деятельности=================================

        try:
            info_dict['work_type_code'] = json_object['items'][0]['ЮЛ']['ОснВидДеят']['Код']
            info_dict['work_type_info'] = json_object['items'][0]['ЮЛ']['ОснВидДеят']['Текст']
        except KeyError:
            info_dict['work_type_code'] = '❌ Код не найден,'
            info_dict['work_type_info'] = 'название не найдено'

        cursor.execute("UPDATE login_id SET work_type_code = (?) WHERE id = (?)", (info_dict['work_type_code'], message.chat.id))
        connect.commit()

        cursor.execute("UPDATE login_id SET work_type_info = (?) WHERE id = (?)", (info_dict['work_type_info'], message.chat.id))
        connect.commit()

        # Статус юр лица=========================================

        if json_object['items'][0]['ЮЛ']['Статус'] == "Действующее":
            info_dict['company_status'] = f"✅ Действующее"
        else:
            info_dict['company_status'] = f"❌ {json_object['items'][0]['ЮЛ']['Статус']} с {json_object['items'][0]['ЮЛ']['СтатусДата']}"

        cursor.execute("UPDATE login_id SET company_status = (?) WHERE id = (?)", (info_dict['company_status'], message.chat.id))
        connect.commit()

        # Адрес, данные о руководителе ================================

        info_dict['company_address'] = json_object['items'][0]['ЮЛ']['Адрес']['АдресПолн']
        cursor.execute("UPDATE login_id SET `company_address` = (?) WHERE id = (?)", (info_dict['company_address'], message.chat.id))
        connect.commit()


        try:
            info_dict['director_name'] = '✅ ' + \
                json_object['items'][0]['ЮЛ']['Руководитель']['ФИОПолн']
            info_dict['director_date_start'] = datetime.strptime(json_object['items'][0]['ЮЛ']['Руководитель']['Дата'], "%Y-%m-%d").strftime("%d.%m.%Y")
        except KeyError:
            info_dict['director_name'] = '❌ Не найдено'
            info_dict['director_date_start'] = 'дата не найдена'

        try:
            info_dict['workers_count'] = f"{json_object['items'][0]['ЮЛ']['ОткрСведения']['КолРаб']} на {datetime.strptime(json_object['items'][0]['ЮЛ']['ОткрСведения']['Дата'], '%Y-%m-%d').strftime('%d.%m.%Y')}"
        except:
            info_dict['workers_count'] = '❌ Не найдено'

        # Учредители и уставной капитал ====================================================

        try:
            info_dict['fund_type'] = json_object['items'][0]['ЮЛ']['Капитал']['ВидКап'] + ":"
            info_dict['fund'] = '{0:,}'.format(int(json_object['items'][0]['ЮЛ']['Капитал']['СумКап'])).replace(
                ',', ' ') + ' руб.'  # Сумма уставного капитала
        except:
            info_dict['fund_type'] = '❌ Не найдено'
            info_dict['fund'] = ''
        
        cursor.execute("UPDATE login_id SET fund = (?) WHERE id = (?)", (info_dict['fund'], message.chat.id))

        connect.commit()

        info_dict['founders'] = ''

        info_dict['founders_list'] = []

        # Если нет учредителей, пишем не найдено
        if not json_object['items'][0]['ЮЛ']['Учредители']:
            info_dict['founders'] = '❌ Не найдено\n\n'
        else:
            info_dict['founders'] += 'Учредители физ.лица:\n'

            founder_fl_count = 0
            
            for founder in json_object['items'][0]['ЮЛ']['Учредители']:
                # Если учредитель не физ.лицо, меняем поля на юр.лицо
                try:
                    if founder['УчрФЛ']:
                        founder_fl_count += 1
                        
                        founder_info = []

                        founder_name = founder['УчрФЛ']['ФИОПолн']
                        founder_inn = founder['УчрФЛ']['ИННФЛ']
                        founder_percent = founder['Процент']
                        founder_sum = '{0:,}'.format(int(founder['СуммаУК'])).replace(',', ' ') + ' руб.'

                        founder_info.append(founder_name)
                        founder_info.append(founder_sum)

                        info_dict['founders_list'].append(founder_info)

                        info_dict['founders'] += f'👨‍💼 {founder_name}\n├ <b>Доля в уставном капитале:</b> {founder_percent}%\n├ <b>Сумма уставного капитала:</b> {founder_sum}\n└ <b>ИНН:</b> {founder_inn}\n\n'
                except:
                    continue

            if founder_fl_count == 0:
                info_dict['founders'] += 'Учредителей физ. лиц не найдено\n\n'

            info_dict['founders'] += 'Учредители юр.лица:\n'

            founder_ul_count = 0

            for founder in json_object['items'][0]['ЮЛ']['Учредители']:
                try:
                    if founder['УчрЮЛ']:

                        founder_info = []

                        founder_ul_count += 1
                        founder_name = founder['УчрЮЛ']['НаимСокрЮЛ']
                        founder_sum = '{0:,}'.format(int(founder['СуммаУК'])).replace(',', ' ') + ' руб.'
                        founder_inn = founder['УчрЮЛ']['ИНН']
                        founder_ogrn = founder['УчрЮЛ']['ОГРН']

                        founder_info.append(founder_name)
                        founder_info.append(founder_sum)

                        info_dict['founders_list'].append(founder_info)

                        info_dict['founders'] += f'🏢 {founder_name}\n├ <b>Доля в уставном капитале:</b> {founder_sum}\n├ <b>ИНН:</b> {founder_inn}\n└ <b>ОГРН:</b> {founder_ogrn}\n\n'
                except:
                    continue
            
            if founder_ul_count == 0:
                info_dict['founders'] += 'Учредителей юр. лиц не найдено\n\n'


        # Собираем структуру отчета ===============================================

        short_description = f'<b>Краткий отчёт по {info_dict["company_name"]}</b> ({info_dict["inn"]})\n\n<b>Дата регистрации:</b>\n{info_dict["date_registered"]}\n\n📑 <b>Данные по юр. лицу</b>\n├ <b>ИНН:</b> {info_dict["inn"]}\n├ <b>КПП</b>: {info_dict["kpp"]}\n└ <b>ОГРН:</b> {info_dict["ogrn"]} от {info_dict["ogrn_date"]}\n\n<b>Основной вид деятельности:</b>\n{info_dict["work_type_code"]} {info_dict["work_type_info"]}\n\n<b>Статус юр. лица:</b>\n{info_dict["company_status"]}\n\n<b>Юридический адрес:</b>\n✅ {info_dict["company_address"]}\n\n<b>Директор:</b>\n{info_dict["director_name"]} с {info_dict["director_date_start"]} \n\n<b>Учредители:</b>\n{info_dict["founders"]}<b>Капитал:</b>\n{info_dict["fund_type"]} {info_dict["fund"]}\n\n<b>Среднесписочная численность сотрудников:</b>\n{info_dict["workers_count"]}'

        cursor.execute("UPDATE login_id SET bot_main_msg = (?) WHERE id = (?)", (short_description, message.chat.id))
        connect.commit()

        cursor.execute(f"SELECT bot_main_msg FROM login_id WHERE id = {message.chat.id}")

        connect.commit()

        # Сохраняем отчет в переменную, чтобы после обращаться к нему без повторного запроса
        bot_main_msg = cursor.fetchone()[0]

    
        try:        
            if json_object['items'][0]['ЮЛ']['История']['Адрес']:
                
                info_dict['address_change'] = ''

                for key, value in json_object['items'][0]['ЮЛ']['История']['Адрес'].items():
                    info_dict['address_change'] += f'│\n├ Период предыдущего адреса: {key}\n├ Предыдущий адрес: {value["АдресПолн"]}\n'

                cursor.execute("UPDATE login_id SET address_change = (?) WHERE id = (?)", (info_dict['address_change'], message.chat.id))
                connect.commit()
        except:
            info_dict['address_change'] = 'Не было\n'

            cursor.execute("UPDATE login_id SET address_change = (?) WHERE id = (?)", (info_dict['address_change'], message.chat.id))
            connect.commit()


        try:
            if json_object['items'][0]['ЮЛ']['История']['Руководитель']:
                
                info_dict['director_change'] = ''

                for key, value in json_object['items'][0]['ЮЛ']['История']['Руководитель'].items():
                    info_dict['director_change'] += f'│\n├ Период работы предыдущего руководителя: {key}\n├ Предыдущий руководитель: {value["ФИОПолн"]}\n'

                cursor.execute("UPDATE login_id SET director_change = (?) WHERE id = (?)", (info_dict['director_change'], message.chat.id))
                connect.commit()
        except:
            info_dict['director_change'] = 'Не было\n'

            cursor.execute("UPDATE login_id SET director_change = (?) WHERE id = (?)", (info_dict['director_change'], message.chat.id))
            connect.commit()


        try:
            if json_object['items'][0]['ЮЛ']['История']['Учредители']:
                info_dict['founders_change'] = 'Была'

                cursor.execute("UPDATE login_id SET founders_change = (?) WHERE id = (?)", (info_dict['founders_change'], message.chat.id))
                connect.commit()
        except:
            info_dict['founders_change'] = 'Не было\n'
            
            cursor.execute("UPDATE login_id SET founders_change = (?) WHERE id = (?)", (info_dict['founders_change'], message.chat.id))
            connect.commit()


        bot.send_message(message.chat.id, bot_main_msg, reply_markup=main_bot_markup, parse_mode='html')
        # except:
        #     bot.send_message(message.chat.id, 'По вашему запросу информация не найдена', reply_markup=main_menu_markup, parse_mode='html')

    # ИНФОРМАЦИЯ ОБ ИП (12 цифр инн) (цифра либо команда из 13 цифр со слешем)
    elif len(user_query) == 12 and user_query.isdigit() or (len(user_query) == 13 and user_query[1:].isdigit() and user_query.startswith('/')):
        try:
            if user_query.startswith('/'):
                message_text = user_query[1:]
            else:
                message_text = user_query

            info_dict = {}

            arb_msg1 = bot.send_message(message.chat.id, 'Ищу информацию по запросу...')

            response = requests.get(
                f'https://api-fns.ru/api/egr?req={message_text}&key={fns_api_key}').text

            json_object = json.loads(response)

            bot.delete_message(message.chat.id, arb_msg1.id)

            try:
                info_dict['company_name'] = json_object['items'][0]['ИП']['ФИОПолн']
            except KeyError:
                info_dict['company_name'] = '❌ Не найдено'

            cursor.execute("UPDATE login_id SET company_name = (?) WHERE id = (?)", (info_dict['company_name'], message.chat.id))

            connect.commit()

            

            info_dict['inn'] = json_object['items'][0]['ИП']['ИННФЛ']

            cursor.execute("UPDATE login_id SET inn = (?) WHERE id = (?)", (info_dict['inn'], message.chat.id))

            connect.commit()


            info_dict['ip_ogrn'] = json_object['items'][0]['ИП']['ОГРНИП']
            info_dict['ip_ogrn_date'] = json_object['items'][0]['ИП']['ДатаОГРН']
            info_dict['ip_address'] = f"{json_object['items'][0]['ИП']['Адрес']['Индекс']}, {json_object['items'][0]['ИП']['Адрес']['АдресПолн']}"


            printed_year = json_object['items'][0]['ИП']['ДатаРег'][:4]
            printed_month = json_object['items'][0]['ИП']['ДатаРег'][5:7]
            printed_day = json_object['items'][0]['ИП']['ДатаРег'][8:10]

            info_dict['ip_date_registered'] = f'{printed_day}.{printed_month}.{printed_year}'
        

            # Доп текст к дате регистрации ========================
            today = datetime.today()
            ip_date_registered = datetime.strptime(
                info_dict["ip_date_registered"], "%Y-%m-%d")

            try:
                delta = relativedelta.relativedelta(today, datetime.strptime(
                    json_object['items'][0]['ИП']['ДатаПрекр'], "%Y-%m-%d"))
            except:
                delta = relativedelta.relativedelta(today, ip_date_registered)

            year_suffix = ("год" if 11 <= delta.years <= 19 or delta.years % 10 == 1 else
                           "года" if 2 <= delta.years % 10 <= 4 else
                           "лет")

            month_suffix = ("месяц" if 11 <= delta.months <= 19 or delta.months % 10 == 1 else
                            "месяца" if 2 <= delta.months % 10 <= 4 else
                            "месяцев")

            # ==========================================

            info_dict['ip_type'] = json_object['items'][0]['ИП']['ВидИП']
            info_dict['ip_citizenship'] = json_object['items'][0]['ИП']['ВидГражд']

            try:
                info_dict['ip_work_type_code'] = json_object['items'][0]['ИП']['ОснВидДеят']['Код']
                info_dict['ip_work_type_info'] = json_object['items'][0]['ИП']['ОснВидДеят']['Текст']
            except KeyError:
                info_dict['ip_work_type_code'] = '❌ Код не найден,'
                info_dict['ip_work_type_info'] = 'название не найдено'

            info_dict['ip_extra_work_types'] = ''

            try:
                for item in json_object['items'][0]['ИП']['ДопВидДеят'][:-1]:

                    info_dict['ip_extra_work_types'] += f'├ {item["Код"]} {item["Текст"]}\n'
                info_dict['ip_extra_work_types'] += f'└ {json_object["items"][0]["ИП"]["ДопВидДеят"][-1]["Код"]} {json_object["items"][0]["ИП"]["ДопВидДеят"][-1]["Текст"]}'
            except:
                info_dict['ip_extra_work_types'] = 'Дополнительные виды деятельности не найдены'

            if json_object['items'][0]['ИП']['Статус'] == 'Действующее':
                info_dict['ip_status'] = "✅ Действующее"
            else:
                info_dict[
                    'ip_status'] = f"❌ {json_object['items'][0]['ИП']['Статус']} с {json_object['items'][0]['ИП']['СтатусДата'].replace('-','.')}"

            if info_dict['ip_status'] != "✅ Действующее":
                info_dict['ip_date_registered'] += f', не ведет деятельность уже {delta.years} {year_suffix} и {delta.months} {month_suffix}'
            else:
                info_dict['ip_date_registered'] += f', ведет деятельность уже {delta.years} {year_suffix} и {delta.months} {month_suffix}'

            short_description = f'<b>Краткий отчет по ИП "{info_dict["company_name"]}" ({info_dict["inn"]})</b>\n\n<b>Дата регистрации:</b> {info_dict["ip_date_registered"].replace("-", ".")}\n\n<b>Статус ИП:</b>\n {info_dict["ip_status"]}\n\n📑 <b>Данные по ИП</b>\n├ <b>ИНН:</b> {info_dict["inn"]}\n├ <b>ОГРН:</b> {info_dict["ip_ogrn"]} от {info_dict["ip_ogrn_date"].replace("-", ".")}\n├ <b>Адрес:</b> {info_dict["ip_address"]}\n├ <b>Вид ИП:</b> {info_dict["ip_type"]}\n└ <b>Вид гражданства:</b> {info_dict["ip_citizenship"]}\n\n🏛 <b>Основной вид деятельности:</b>\n{info_dict["ip_work_type_code"]} {info_dict["ip_work_type_info"]}\n\n🏛 <b>Дополнительные виды деятельности:</b>\n{info_dict["ip_extra_work_types"]}\n'

            cursor.execute("UPDATE login_id SET bot_main_msg = (?) WHERE id = (?)", (short_description, message.chat.id))
            connect.commit()

            cursor.execute(f"SELECT bot_main_msg FROM login_id WHERE id = {message.chat.id}")

            connect.commit()

            # Сохраняем отчет в переменную, чтобы после обращаться к нему без повторного запроса
            bot_main_msg = cursor.fetchone()[0]

            bot.send_message(message.chat.id, short_description,
                             reply_markup=ip_bot_markup, parse_mode='html')
        except:
            bot.send_message(message.chat.id, 'По запросу информация не найдена',
                             reply_markup=main_menu_markup, parse_mode='html')

    # БД ЧЕК✅ ЕСЛИ ПОЛЬЗОВАТЕЛЬ ВВОДИТ НЕ ЦИФРЫ ТО АВТОМАТИЧЕСКИ ПРОХОДИТ РАСШИРЕННЫЙ ПОИСК
    else:
        search_result_pages = []

        arb_msg1 = bot.send_message(message.chat.id, 'Ищу информацию по запросу...')

        search_response = requests.get(
            f'https://api-fns.ru/api/search?q={user_query}&key={fns_api_key}').text

        search_json_object = json.loads(search_response)

        search_items_count = search_json_object['Count']

        search_results = f"Найдено результатов по запросу: {search_items_count}\n\n"

        bot.delete_message(message.chat.id, arb_msg1.id)

        for item in search_json_object['items']:

            try:
                search_inn = item['ЮЛ']['ИНН']
                search_name = item['ЮЛ']['НаимСокрЮЛ']
                search_status = item['ЮЛ']['Статус']
                search_address = item['ЮЛ']['АдресПолн']

                search_results += f'🏛 {search_name}\n├ <b>ИНН:</b> /{search_inn}\n├ <b>Адрес:</b> {search_address}\n└ <b>Статус:</b> {search_status}\n\n'
            except:
                try:
                    search_inn = item['ИП']['ИНН']
                    search_name = item['ИП']['ФИОПолн']
                    search_status = item['ИП']['Статус']
                    search_address = item['ИП']['АдресПолн']

                    search_results += f'👨‍💼 {search_name}\n├ <b>ИНН:</b> /{search_inn}\n├ <b>Адрес:</b> {search_address}\n└ <b>Статус:</b> {search_status}\n\n'
                except:
                    search_address += ''

        cursor.execute("UPDATE login_id SET user_search_results = (?) WHERE id = (?)", (search_results, message.chat.id))

        connect.commit()

        bot.send_message(message.chat.id, f'🔎 Найдено результатов по запросу: {search_items_count}\n\n')
        bot.send_message(message.chat.id, 'Чтобы начать проверку нажми на ИНН')

        if search_items_count > 0:
            send_character_page(message)

# Код пагинации для расширенного поиска


@bot.callback_query_handler(func=lambda call: call.data.split('#')[0] == 'character')
def characters_page_callback(call):
    page = int(call.data.split('#')[1])
    bot.delete_message(
        call.message.chat.id,
        call.message.message_id
    )
    send_character_page(call.message, page)

def send_character_page(message, page=1):

    search_result_pages = []

    cursor.execute(f"SELECT user_search_results FROM login_id WHERE id = {message.chat.id}")

    connect.commit()

    final_search_results = cursor.fetchone()[0]

    search_results_array = final_search_results.split('\n\n')[1:]

    for i in range(ceil(len(search_results_array) / 10)):
        search_result_page = '\n\n'
        search_result_page = search_result_page.join(
            search_results_array[:10])

        search_result_pages.append(search_result_page)

        del search_results_array[:10]

    paginator = InlineKeyboardPaginator(
        len(search_result_pages),
        current_page=page,
        data_pattern='character#{page}'
    )

    paginator.add_after(InlineKeyboardButton(
        '⬅️ В главное меню', callback_data='main_menu'))

    bot.send_message(
        message.chat.id,
        search_result_pages[page-1],
        reply_markup=paginator.markup,
        parse_mode='html'
    )

# Обработчики кнопок ==============================================

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global markup, ip_bot_markup, full_fin_report_markup, fin_analysis_markup, back_to_fin_report_start_markup, main_menu_markup, reputation_markup, fin_risk_markup, one_day_markup

    '''
        0. БД ЧЕК✅ Главное меню
    '''
    if call.data == 'main_menu':

        clean_message(call)

        msg_greet_main = f'😻Я - МурLOOK - персональный кото-ассистент для проверки контрагентов.\n\nЯ могу в режиме реального времени:\n\n✅ Выполнить полную проверку надежности контрагента;\n❌ Выявить его негативные факторы.\n\n❗️Для проверки просто введи ИНН компании или ИП, или же название компании (также можно указать город) и нажми "отправить сообщение".\n\n❓Возникли вопросы? Напиши нам @support_tgbots_test156.'

        bot.send_message(call.message.chat.id, msg_greet_main, parse_mode='html')
    

    """
        4.2 Исполнительные производства
    """
    if call.data == 'isp_report':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        response = requests.get(f'https://api.damia.ru/fssp/isps?inn={user_info[0]}&key={damia_fssp_key}').text

        json_object = json.loads(response)

        isp_text = f"<h1>Информация об исполнительных производствах {user_info[1]}:</h1>\n\n<hr>\n\n"

        try:
            for number, data in json_object[user_info[0]].items():
                
                isp_date_start = data['Дата']

                isp_doc_type = data['ВидИсп']
                isp_doc_date = data['ДатаИсп']
                isp_doc_number = data['НомерИсп']

                isp_subject = data['Предмет']

                isp_debtor_name = data['Должник']['НаимФССП']
                isp_debtor_address = data['Должник']['АдресФССП']

                isp_debt_sum = data['Сумма']
                isp_debt_remains = data['Остаток']

                isp_status = data['Статус']

                if isp_status  == 'Не завершено':
                    status_info = ''
                else:
                    
                    status_reason = data["ПричЗаверш"]

                    if status_reason != '':
                        status_info = f'\n├ <b>Дата завершения:</b> {data["ДатаЗаверш"]}\n├ <b>Причина завершения:</b> {data["ПричЗаверш"]}'
                    else:
                        status_info = f'\n├ <b>Дата завершения:</b> {data["ДатаЗаверш"]}'



                isp_text += f"📔 <b>{number}:</b>\n├ <b>Дата возбуждения:</b> {isp_date_start}\n├ <b>Исполнительный документ:</b> {isp_doc_type} {isp_doc_number} от {isp_doc_date}\n├ <b>Предмет:</b> {isp_subject}\n└ 👨‍💼 <b>Должник:</b>\n\t\t\t\t\t\t├ <b>Наименование:</b> {isp_debtor_name}\n\t\t\t\t\t\t└ <b>Адрес:</b> {isp_debtor_address}\n├ <b>Сумма задолженности:</b> {isp_debt_sum}\n├ <b>Остаток задолженности:</b> {isp_debt_remains}\n├ <b>Статус:</b> {isp_status}{status_info}\n\n<hr>\n\n"

        
        
                # Генерация уникального имени файла для последующего удаления
                filename = r"Исполнительные_производства_" + str(uuid.uuid4())
                                                                                                                                                                        
                with open(f'{filename}.html', "wb") as f:

                    ready_text  = "<html><head><meta charset='utf-8'/><style>.html {box-sizing: border-box;} * {margin: 0;font-family: Helvetica, sans-serif; box-sizing: border-box;} body {margin: 0; min-width: 320px; padding: 20px}</style><title>Output Data in an HTML file\n \
                </title>\n</head> <body>"  + isp_text + "</body></html>"

                    f.write(ready_text.replace("\n", "<br>").replace("\t", "&nbsp;").encode("UTF-8"))

                doc_file = open(f'{filename}.html', 'r', encoding="utf-8")

                bot.send_document(call.message.chat.id, doc_file, reply_markup=markup)

                doc_file.close()

                os.remove(f'{filename}.html')
        except:
            bot.send_message(call.message.chat.id, "Информация об исполнительных производствах  не найдена!", reply_markup=markup)


    '''
        5.1 БД ЧЕК✅ Госзакупки
    '''

    if call.data == 'purchases':

        date_begin = bot.send_message(call.message.chat.id, 'Укажите дату начала поиска в формате <b>День-Месяц-Год</b>, например, 14-01-2018', parse_mode='html')

        bot.register_next_step_handler(date_begin, zakupki_date_end)

    '''
        5.2 БД ЧЕК✅ Госконтракты
    '''
    if call.data == 'contracts':

        date_begin = bot.send_message(
            call.message.chat.id, 'Укажите дату начала поиска в формате <b>День-Месяц-Год</b>, например, 14-01-2018', parse_mode='html')

        bot.register_next_step_handler(date_begin, contract_date_end)

    '''
        1.1 БД ЧЕК✅ Блокировки счетов
    '''
    if call.data == 'block':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        response = requests.get(
            f'https://api-fns.ru/api/nalogbi?inn={user_info[0]}&bik=&key={fns_api_key}').text

        json_object = json.loads(response)

        block_text = f'<b>Проверка блокировки счетов {user_info[1]}:</b>\n\n'

        try:
            negative = json_object['items'][0]['ЮЛ']['Негатив']['Текст']

            block_text += f'{negative}\n\n<b>Подробная информация по блокировкам:</b>\n\n======\n\n'

            for item in json_object['items'][0]['ЮЛ']['Негатив']['БлокСчетаИнфо']:

                bik = item['БИК']
                bank = item['Банк']
                sol_number = item['НомерРеш']
                sol_date = item['ДатаРеш']
                taxes_org = item['КодНО']
                serv_date = item['ВремяИнф']

                if item['КодОснов'] == None:
                    sol_code = 'Не найдено'
                else:
                    sol_code = item['КодОснов']

                block_text += f'БИК: {bik}\nБанк: {bank}\nНомер решения: {sol_number}\nДата решения: {sol_date}\nКод налогового органа: {taxes_org}\nДата и время размещения информации в сервисе: {serv_date}\nКод основания для вынесения решения: {sol_code}\n\n======\n\n'
        except:
            block_text += '✅ Блокировок не найдено'

        bot.send_message(call.message.chat.id, block_text,
                         parse_mode='html', reply_markup=markup)

    '''
        7. Негативные факторы
    '''
    if call.data == 'check_agent':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name, fund, company_status FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию о негативных факторах [0%]')

        # Запрос api по арбитражным делам ======================================================
        response_arb = requests.get(
            f'https://api.damia.ru/arb/dela?q={user_info[0]}&key={damia_arb_api_key}').text

        json_object_arb = json.loads(response_arb)


        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об арбитражных делах [10%]')

        # Запрос api по проверке контрагента ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/check?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Проверяю бух. отчетность [40%]')

        # Запрос api по бух. отчетности ======================================================
        response_fin_report = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object_fin_report = json.loads(response_fin_report)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Проверяю данные из ЕГРЮЛ [70%]')

        # Запрос api по проверке контрагента egr ======================================================
        response_egr = requests.get(
            f'https://api-fns.ru/api/egr?req={user_info[0]}&key={fns_api_key}').text

        json_object_egr = json.loads(response_egr)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Составляю отчет [100%]')
        
        bot.delete_message(call.message.chat.id, arb_msg1.id)

        negative_text = ''

        # Доп текст к дате регистрации
        today = datetime.today()
        ul_date_registered = datetime.strptime(json_object_egr['items'][0]['ЮЛ']['ДатаРег'], "%Y-%m-%d")

        delta = relativedelta.relativedelta(today, ul_date_registered)

        
        # ✅ Если контрагент ведёт деятельность менее 3 лет
        if delta.years < 3:
            negative_text += '❗️ <b>Создан менее 3 лет назад</b>\n\n'

        # ✅ Если статус организации или ИП любой кроме Действующее
        if user_info[3] != '✅ Действующее':
            negative_text += f'❗️ <b>Статус:</b> {user_info[3]}\n\n'

        # ✅ Если у контрагента минимальный размер уставного капитала
        if user_info[2].replace(" ", "") == '10000руб.':
            negative_text += '❗️ <b>Минимальный размер уставного капитала</b>\n\n'

        # ✅ Если ИНН контрагента есть в Спецреестре ФНС (Имеющие задолженность по уплате налогов)
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['ЗадолжНалог']:
                negative_text += '❗️ <b>Контрагент имеет превышающую 1000 рублей задолженность по уплате налогов, которая направлялась на взыскание судебному приставу-исполнителю</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если в ЕГРЮЛ есть отметка о недостоверности данных об адресе организации 
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['НедостоверАдрес']:
                negative_text += '❗️ <b>Недостоверный адрес</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если руководитель найден в Реестре массовых руководителей
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['РеестрМассРук']:
                negative_text += '❗️ <b>Массовый руководитель</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если в ЕГРЮЛ есть отметка о недостоверности данных о руководителе
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['НедостоверРук']:
                negative_text += '❗️ <b>Недостоверность данных о руководителе</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если хотя бы один из учредителей найден в Реестре массовых учредителей
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['РеестрМассУчр']:
                negative_text += '❗️ <b>Массовый учредитель</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если ИНН контрагента есть в Спецреестре ФНС (Не представляющие налоговую отчетность более года) 
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['НеПредостОтч']:
                negative_text += '❗️ <b>Контрагент не предоставляет налоговую отчетность более года</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если есть сведения по ИНН контрагента в Сведения о суммах недоимки и задолженности по пеням и штрафам
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['НедоимкаНалог']:
                negative_text += '❗️ <b>Найдены сведения о суммах недоимки и задолженности по пеням и штрафам</b>\n\n'
        except:
            negative_text += ''

        # ✅  Если не найдена отчётность за последний год 
        try:
            if int(list(json_object_fin_report[user_info[0]].keys())[-1]) != int(today.year - 1):
                negative_text += '❗️ <b>Организация не представила финансовую отчётность за последний год</b>\n\n'
        except:
            negative_text += ''

        # ✅  Если руководитель найден в Реестре дисквалифицированных лиц
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['ДисквРук'] or json_object['items'][0]['ЮЛ']['Негатив']['ДисквРукДр'] or json_object['items'][0]['ЮЛ']['Негатив']['ДисквРукДрБезИНН']:
                negative_text += '❗️ <b>Руководитель числится в Реестре дисквалифицированных лиц</b>\n\n'
        except:
            negative_text += ''

        try:
            # Отчет за последний год
            last_year_dict = json_object_fin_report[user_info[0]][list(json_object_fin_report[user_info[0]].keys())[-1]]

            # Отчет за предпоследний год
            prev_year_dict = json_object_fin_report[user_info[0]][list(json_object_fin_report[user_info[0]].keys())[-2]]
        except:
            last_year_dict = {}
            prev_year_dict = {}

        def calculate_difference(first, second):
    
            percentage = round(
                (abs(int(first) - int(second)) / int(second)) * 100.0, 2)

            if first > second:
                return f"⬆️ {percentage}%"
            elif first < second:
                return f"⬇️ {percentage}%"
            else:
                return "-"

        # ✅ Если Валовая прибыль ⬇️
        try:
            val_income = calculate_difference(prev_year_dict["2100"], last_year_dict["2100"])
            
            if val_income.startswith('⬇️'):
                negative_text += '❗️ <b>Снижение валовой прибыли:</b>\n└ Снижение уровня рентабельности производства, падение уровня эффективности труда или применение неправильной логистики\n\n'
        except:
            negative_text += ''

        # ✅ Чистая прибыль (нераспределенная прибыль (непокрытый убыток) ⬇️
        try:
            pure_income = calculate_difference(prev_year_dict["2400"], last_year_dict["2400"])
            
            if pure_income.startswith('⬇️'):
                negative_text += '❗️ <b>Снижение чистой прибыли:</b>\n└ Уменьшение объёма продаж, рост себестоимости продукции, возможное завышении цены продукта, из-за чего снизились показатели реализации\n\n'
        except:
            negative_text += ''

        # ✅ Если Основные средства ⬇️
        try:
            fixed_assets = calculate_difference(prev_year_dict["1600"], last_year_dict["1600"])
            
            if fixed_assets.startswith('⬇️'):
                negative_text += '❗️ <b>Снижение стоимости основных средств:</b>\n└ Сокращение хозяйственного оборота и может быть следствием износа ОС, или результатом снижения платёжеспособного спроса на товары, работы и услуги\n\n'
        except:
            negative_text += ''

        # ✅ Если Доходы (выручка)  ⬇️
        try:
            income = calculate_difference(prev_year_dict["2110"], last_year_dict["2110"])
            
            if income.startswith('⬇️'):
                negative_text += '❗️ <b>Снижение выручки:</b>\n└ Снижение объёма, реализованной продукции/уменьшение уровня реализованных цен/ снижение ассортимента (структура) реализованной продукции\n\n'
        except:
            negative_text += ''

        # ✅ Если Дебиторская задолженность ⬆️
        try:
            accounts_receivable = calculate_difference(prev_year_dict["1230"], last_year_dict["1230"])
            
            if accounts_receivable.startswith('⬆️'):
                negative_text += '❗️ <b>Рост количества реализуемых контрагентом услуг или товаров с отсрочкой платежа</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если Кредиторская задолженность  ⬆️
        try:
            accounts_payable = calculate_difference(prev_year_dict["1520"], last_year_dict["1520"])
            
            if accounts_payable.startswith('⬆️'):
                negative_text += '❗️ <b>Увеличение зависимости предприятия от заёмных средств</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент финансовой устойчивости < 0,7
        try:
            absolute_liquidity_ratio = round(
                (int(last_year_dict['1250']) + int(last_year_dict['1240'])) / int(last_year_dict['1500']), 2)

            if absolute_liquidity_ratio < 0.7:
                negative_text += '❗️ <b>Риск хронической неплатёжеспособности, а также попадания в финансовую зависимость от кредиторов</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент финансовой устойчивости > 0,95
        try:
            current_liquidity_ratio = round(
                int(last_year_dict['1200']) / int(last_year_dict['1500']), 2)

            if current_liquidity_ratio < 0.95:
                negative_text += '❗️ <b>Контрагент не использует все доступные возможности для расширения бизнеса, которые могут быть предоставлены за счёт «быстрых» источников финансирования</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент автономии < 0,4
        try:
            autonomy_ratio = round(
                int(last_year_dict['1300']) / int(last_year_dict['1600']), 2)

            if autonomy_ratio < 0.4:
                negative_text += '❗️ <b>Контрагент имеет низкую финансовую устойчивость и плохую долгосрочную платёжеспособность. Возможен прирост активов, приобретённых в долг</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент обеспеченности собственными оборотными средствами <= 0,1
        try:
            working_capital_ratio = round((int(last_year_dict['1300']) - int(last_year_dict['1100'])) / int(last_year_dict['1200']), 2)

            if working_capital_ratio <= 0.1:
                negative_text += '❗️ <b>Вероятность признания контрагента неплатёжеспособным в текущем периоде</b>\n\n'
        except:
            negative_text += ''


        # ✅ Если отношение дебиторской задолженности к активам > 0,7
        try:
            receivables_to_assets_ratio = round(
                int(last_year_dict['1230']) / int(last_year_dict['1600']), 2)

            if receivables_to_assets_ratio > 0.7:
                negative_text += '❗️ <b>Неэффективная работа с дебиторами</b>\n\n'
        except:
            negative_text += ''   

        # ✅ Если коэффициент соотношения заёмного и собственного капитала > 1
        try:
            debt_to_equity_ratio = round(
                (int(last_year_dict['1410']) + int(last_year_dict['1510'])) / int(last_year_dict['1300']), 2)

            if debt_to_equity_ratio > 1:
                negative_text += '❗️ <b>Признак наличия риска банкротства</b>\n\n'
        except:
            negative_text += '' 

        # ✅ Если коэффициент капитализации > 1
        try:
            capitalization_ratio = round(
                (int(last_year_dict['1400']) + int(last_year_dict['1500'])) / int(last_year_dict['1300']), 2)

            if capitalization_ratio > 1:
                negative_text += '❗️ <b>Низкая привлекательность для инвесторов</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент абсолютной ликвидности > 0,5
        try:
            absolute_liquidity_ratio = round(
                (int(last_year_dict['1250']) + int(last_year_dict['1240'])) / int(last_year_dict['1500']), 2)

            if absolute_liquidity_ratio > 0.5:
                negative_text += '❗️ <b>Нерациональная структура капитала:</b>\n└ Слишком высокая доля неработающих активов в виде наличных денег и средств на счетах. Требуется дополнительный анализ использования капитала\n\n'
        except:
            negative_text += ''
        
        # ✅ Если коэффициент абсолютной ликвидности < 0,2 
        try:
            absolute_liquidity_ratio = round(
                (int(last_year_dict['1250']) + int(last_year_dict['1240'])) / int(last_year_dict['1500']), 2)

            if absolute_liquidity_ratio < 0.2:
                negative_text += '❗️ <b>Контрагент не в состоянии оплатить немедленно обязательства за счёт ДС всех видов, а также средств, полученных от реализации ценных бумаг. Требуется дополнительный анализ платёжеспособности</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент текущей ликвидности  > 3
        try:
            current_liquidity_ratio = round(
                int(last_year_dict['1200']) / int(last_year_dict['1500']), 2)

            if current_liquidity_ratio > 3:
                negative_text += '❗️ <b>Неэффективное использование прибыли и рост нераспределенного капитала</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент текущей ликвидности < 1
        try:
            current_liquidity_ratio = round(
                int(last_year_dict['1200']) / int(last_year_dict['1500']), 2)

            if current_liquidity_ratio < 1:
                negative_text += '❗️ <b>Финансовый риск, - бизнес не в состоянии стабильно оплачивать текущие счета</b>\n\n'
        except:
            negative_text += ''
        
        # ✅ Если коэффициент быстрой ликвидности < 0,7
        try:
            quick_liquidity_ratio = round((int(last_year_dict['1230']) or 0 + int(last_year_dict['1240']) or 0 + int(
                last_year_dict['1250']) or 0) / (int(last_year_dict['1510']) or 0 + int(last_year_dict['1520']) or 0 + int(last_year_dict['1550']) or 0), 2)

            if quick_liquidity_ratio < 0.7:
                negative_text += '❗️ <b>Кредиты будут выданы под больший процент, увеличится размер залогового имущества, либо возможен отказ в кредитовании. Вероятен риск потери потенциальных инвесторов</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если коэффициент обеспеченности обязательств активами > 0,85
        try:
            liabilities_with_assets_ratio = round((int(last_year_dict['1600']) or 0 - int(last_year_dict['1200']) or 0) / (int(
                last_year_dict['1520']) or 0 + int(last_year_dict['1510']) or 0 + int(last_year_dict['1550']) or 0 + int(last_year_dict['1400']) or 0), 2)

            if liabilities_with_assets_ratio < 0.7:
                negative_text += '❗️ <b>Плохая способность субъекта хозяйствования рассчитываться по своим обязательствам</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если степень платежёспособности по текущим обязательствам > 6
        try:
            current_liabilities_ratio = round((int(last_year_dict['1510']) or 0 + int(
                last_year_dict['1520']) or 0 + int(last_year_dict['1550']) or 0) / (int(last_year_dict['2120']) or 0 / 12), 2)

            if current_liabilities_ratio > 6:
                negative_text += '❗️ <b>Контрагенту нужно много времени (больше 6 мес.) чтобы расплатиться, закрыть долги</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если рентабельность по чистой прибыли < 0
        try:
            net_profit_margin = round((int(last_year_dict['2400']) / int(last_year_dict['2110'])) * 100, 2)

            if net_profit_margin < 0:
                negative_text += '❗️ <b>Бизнес не приносит прибыли, убыточен</b>\n\n'
        except:
            negative_text += ''

        #  ✅ Если рентабельность затрат < 0
        try:
            cost_effectiveness = round((int(last_year_dict['2400']) / (int(last_year_dict['2120']) + int(
                last_year_dict['2210']) + int(last_year_dict['2220']))) * 100, 2)

            if cost_effectiveness < 0:
                negative_text += '❗️ <b>Неэффективное использование ресурсов и неокупаемость расходов</b>\n\n'
        except:
            negative_text += ''

        #  ✅ Если рентабельность активов < 0
        try:
            return_on_assets = round(
                (int(last_year_dict['2400']) / int(last_year_dict['1600'])) * 100, 2)

            if return_on_assets < 0:
                negative_text += '❗️ <b>Активы используются неэффективно</b>\n\n'
        except:
            negative_text += ''

        # ✅  Если рентабельность собственного капитала < 0
        try:
            return_on_equity = round(
                (int(last_year_dict['2400']) / int(last_year_dict['1300'])) * 100, 2)

            if return_on_equity < 0:
                negative_text += '❗️ <b>Инвестированные средства не приносят доходность</b>\n\n'
        except:
            negative_text += ''

        #  ✅ Если общая рентабельность продаж < 0
        try:
            return_on_sales = round(
                (int(last_year_dict['2100']) / int(last_year_dict['2110'])) * 100, 2)

            if return_on_sales < 0:
                negative_text += '❗️ <b>Контрагент не способен организовать и контролировать текущую деятельность</b>\n\n'
        except:
            negative_text += ''

        # ✅ Если проверка руководителя контрагента по ИНН Реестре банкротств выдает результаты о наличии процедуры банкротства 
        try:
            if json_object['items'][0]['ЮЛ']['Негатив']['БанкротНамерение']:
                negative_text += '❗️ <b>В отношении руководителя контрагента найдены сведения о процедуре банкротства</b>\n\n'
        except:
            negative_text += ''
        
        arb_defendant_count = 0
        arb_plaintiff_count = 0
        arb_third_count = 0

        arb_active_defendant_count = 0
        arb_active_plaintiff_count = 0
        arb_active_third_count = 0

        arb_finished_defendant_count = 0
        arb_finished_plaintiff_count = 0
        arb_finished_third_count = 0

        arb_defendant_active_sum = 0
        arb_plaitiff_active_sum = 0

        # Собираем статистику по арбитражным делам в качестве ответчика
        try:
            
            for number, list_item in json_object_arb['result']['Ответчик'].items():

                arb_defendant_count += 1

                if list_item['Статус'] == "Рассмотрение дела завершено":
                    arb_finished_defendant_count += 1
                else:
                    arb_active_defendant_count += 1
                    arb_defendant_active_sum += list_item['Сумма']
        except:
            pass
        
        # Собираем статистику по арбитражным делам в качестве истца
        try:
            for number, list_item in json_object_arb['result']['Истец'].items():
                
                arb_plaintiff_count += 1

                if list_item['Статус'] == "Рассмотрение дела завершено":
                    arb_finished_plaintiff_count += 1
                else:
                    arb_active_plaintiff_count += 1
                    arb_plaitiff_active_sum += list_item['Сумма']
        except:
            pass
        
        # Собираем статистику по арбитражным делам в качестве третьего лица
        try:
            for number, list_item in json_object_arb['result']['ТретьеЛицо'].items():
                
                arb_third_count += 1

                if list_item['Статус'] == "Рассмотрение дела завершено":
                    arb_finished_third_count += 1
                else:
                    arb_active_third_count += 1
        except:
            pass
        

        # ✅ Если выступает в арбитражных делах преимущественно в роли ответчика 
        if arb_defendant_count > arb_plaintiff_count:
            negative_text += '❗️ <b>Выступает в арбитражных делах преимущественно в роли ответчика</b>\n\n'

        # ✅ Если в прошлом контрагент проходил в качестве ответчика в судебном разбирательстве(-ах)
        if arb_finished_defendant_count > 0:
            negative_text += '❗️ <b>Завершённые судебные дела в качестве ответчика</b>\n\n'

        # ✅ Если на данный момент контрагент проходит в качестве ответчика в судебном разбирательстве(-ах)
        if arb_active_defendant_count > 0:
            negative_text += '❗️ <b>Активные судебные дела в качестве ответчика</b>\n\n'

        # ✅ Если в прошлом контрагент проходил в качестве третьего лица в судебном разбирательстве(-ах)
        if arb_finished_third_count > 0:
            negative_text += '❗️ <b>Завершённые судебные дела в качестве третьего лица</b>\n\n'

        # ✅ Если на данный момент контрагент проходит в качестве третьего лица в судебном разбирательстве(-ах) 
        if arb_active_third_count > 0:
            negative_text += '❗️ <b>Активные судебные дела в качестве третьего лица</b>\n\n'

        # ✅ Если сумма активных дел, в которых контрагент проходит как ответчик больше суммы активных дел, по которым контрагент проходит как истец на 30%
        if arb_plaitiff_active_sum != 0 and arb_defendant_active_sum > arb_plaitiff_active_sum and round((abs(int(arb_defendant_active_sum) - int(arb_plaitiff_active_sum)) / int(arb_plaitiff_active_sum)) * 100.0, 2):
            negative_text += '❗️ <b>Сумма предъявленных компании исков значительно превышает сумму предъявляемых ею исков</b>\n\n'

        # =======================================================================

        agent_text_msg = f'<b>Выявленные в результате проверки негативные факторы {user_info[1]}:</b>\n\n{negative_text}'

        bot.send_message(call.message.chat.id, agent_text_msg, reply_markup=markup, parse_mode='html')

    '''
        1. БД ЧЕК ✅ Проверка наличия признаков фирмы-однодневки и фиктивной деятельности
    '''
    if call.data == 'one_day':
        
        clean_message(call)

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию в Спецреестрах ФНС [0%]')

        time.sleep(1)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Ищу информацию о фиктивной деятельности [50%]')

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        # Запрос api по проверке контрагента =====================================
        response_check = requests.get(
            f'https://api-fns.ru/api/check?req={user_info[0]}&key={fns_api_key}').text

        json_object_check = json.loads(response_check)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Составляю отчет [100%]')

        time.sleep(1)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        one_day_text = f'<b>Проверка наличия признаков фирмы-однодневки и фиктивной деятельности {user_info[1]}</b>\n\n'

        # ✅ Реестр массовых руководителей
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['РеестрМассРук']:
                one_day_text += '1️⃣ <b>Реестр массовых руководителей:</b>\n└ Руководитель состоит в реестре\n\n'
        except:
            one_day_text += '1️⃣ <b>Реестр массовых руководителей:</b>\n└ Руководитель в реестре не состоит\n\n'

        # ✅ Недостоверность данных о Руководителе
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['НедостоверРук']:
                one_day_text += '2️⃣ <b>Недостоверность данных о руководителе:</b>\n└ Состоит в реестре\n\n'
        except:
            one_day_text += '2️⃣ <b>Недостоверность данных о руководителе:</b>\n└ В реестре не числится\n\n'

        # ✅ Недостоверный адрес
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['НедостоверАдрес']:
                one_day_text += '3️⃣ <b>Недостоверность данных об адресе организации:</b>\n└ Состоит в реестре\n\n'
        except:
            one_day_text += '3️⃣ <b>Недостоверность данных об адресе организации:</b>\n└ В реестре не числится\n\n'

        # ✅ Реестр массовых учредителей
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['РеестрМассУчр']:
                one_day_text += '4️⃣ <b>Реестр массовых учредителей:</b>\n└ Учредитель(-и) организации состоит(-ят) в реестре\n\n'
        except:
            one_day_text += '4️⃣ <b>Реестр массовых учредителей:</b>\n└ Учредитель(-и) организации в реестре не состоит(-ят)\n\n'

        # ✅ Дисквалифицированные лица (Руководитель)
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['ДисквРук'] or json_object_check['items'][0]['ЮЛ']['Негатив']['ДисквРукДр']:
                one_day_text += '5️⃣ <b>Дисквалифицированные лица (руководитель):</b>\n└ Найден\n\n'
        except:
            one_day_text += '5️⃣ <b>Дисквалифицированные лица (руководитель):</b>\n└ Не найден\n\n'

        # ✅ Спецреестр ФНС (Имеющие задолженность по уплате налогов)
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['ЗадолжНалог']:
                one_day_text += '6️⃣ <b>Спецреестр ФНС (имеющие задолженность по уплате налогов):</b>\n└ Числится в реестре\n\n'
        except:
            one_day_text += '6️⃣ <b>Спецреестр ФНС (имеющие задолженность по уплате налогов):</b>\n└ В реестре не числится \n\n'

        # Спецреестр ФНС (Не представляющие налоговую отчетность более года)
        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['НеПредостОтч']:
                one_day_text += '7️⃣ <b>Спецреестр ФНС (Не представляющие налоговую отчетность более года):</b>\n└ Числится в реестре\n\n'
        except:
            one_day_text += '7️⃣ <b>Спецреестр ФНС (Не представляющие налоговую отчетность более года):</b>\n└ В реестре не числится \n\n'

        bot.send_message(call.message.chat.id, one_day_text, parse_mode='html', reply_markup=one_day_markup)
        
    '''
        2. БД ЧЕК ✅ Проверка платёжеспособности по данным последней доступной бухгалтерской отчетности
    '''
    if call.data == 'fin_report':

        clean_message(call)

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу бух.отчетность [0%]')


        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Ищу информацию по платёжеспособности [50%]')


        # Запрос api по бух. отчетности ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Составляю отчет [100%]')

        time.sleep(1)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        report_text = f'<b>Проверка платёжеспособности {user_info[1]} по данным последней доступной бухгалтерской отчётности</b>\n\n'

        try:

            # Отчет за последний год
            last_year_dict = json_object[user_info[0]][list(json_object[user_info[0]].keys())[-1]]

            # Отчет за предпоследний год
            prev_year_dict = json_object[user_info[0]][list(json_object[user_info[0]].keys())[-2]]
        except:
            last_year_dict = {}
            prev_year_dict = {}

        def calculate_difference(first, second):

            percentage = round((abs(int(first) - int(second)) / int(second)) * 100.0, 2)

            if first > second:
                return f"⬆️ {percentage}%"
            elif first < second:
                return f"⬇️ {percentage}%"
            else:
                return "-"

        try:
            if int(list(json_object_fin_report[user_info[0]].keys())[-1]) != int(today.year - 1):
                report_text += '📝 <b>Наличие отчётности за последний отчетный период:</b>\n└ Нет ❗️\n\n'
        except:
            report_text += '📝 <b>Наличие отчётности за последний отчетный период:</b>\n└ Есть ✅\n\n'

        # ✅ Баланс
        try:
            if calculate_difference(prev_year_dict["1600"], last_year_dict["1600"]).startswith("⬆️"):
                report_text += f'🟢 <b>Баланс:</b>\n└ {last_year_dict["1600"]} тыс. руб. {calculate_difference(prev_year_dict["1600"], last_year_dict["1600"])}\n\n'
            elif calculate_difference(prev_year_dict["1600"], last_year_dict["1600"]).startswith("⬇️"):
                report_text += f'🔻 <b>Баланс:</b>\n└ {last_year_dict["1600"]} тыс. руб. {calculate_difference(prev_year_dict["1600"], last_year_dict["1600"])}\n\n'
            else:
                report_text += f'• <b>Баланс:</b>\n└ {last_year_dict["1600"]} тыс. руб. {calculate_difference(prev_year_dict["1600"], last_year_dict["1600"])}\n\n'
        except:
            report_text += '<b>❌ Баланс:</b>\n└ Не найдено\n\n'

        # ✅ Валовая прибыль
        try:
            if calculate_difference(prev_year_dict["2100"], last_year_dict["2100"]).startswith("⬆️"):
                report_text += f'🟢 <b>Валовая прибыль:</b>\n└ {last_year_dict["2100"]} тыс. руб. {calculate_difference(prev_year_dict["2100"], last_year_dict["2100"])}\n\n'
            elif calculate_difference(prev_year_dict["2100"], last_year_dict["2100"]).startswith("⬇️"):
                report_text += f'🔻 <b>Валовая прибыль:</b>\n└ {last_year_dict["2100"]} тыс. руб. {calculate_difference(prev_year_dict["2100"], last_year_dict["2100"])}\n\n'
            else:
                report_text += f'• <b>Валовая прибыль:</b>\n└ {last_year_dict["2100"]} тыс. руб. {calculate_difference(prev_year_dict["2100"], last_year_dict["2100"])}\n\n'
        except:
            report_text += '<b>❌ Валовая прибыль:</b>\n└ Не найдено\n\n'
        
        # ✅ Чистая прибыль
        try:   
            if calculate_difference(prev_year_dict["2400"], last_year_dict["2400"]).startswith("⬆️"):
                report_text += f'🟢 <b>Чистая прибыль:</b>\n└ {last_year_dict["2400"]} тыс. руб. {calculate_difference(prev_year_dict["2400"], last_year_dict["2400"])}\n\n'
            elif calculate_difference(prev_year_dict["2400"], last_year_dict["2400"]).startswith("⬇️"):
                report_text += f'🔻 <b>Чистая прибыль:</b>\n└ {last_year_dict["2400"]} тыс. руб. {calculate_difference(prev_year_dict["2400"], last_year_dict["2400"])}\n\n'
            else:
                report_text += f'• <b>Чистая прибыль:</b>\n└ {last_year_dict["2400"]} тыс. руб. {calculate_difference(prev_year_dict["2400"], last_year_dict["2400"])}\n\n'

        except:
            report_text += '❌ <b> Чистая прибыль:</b>\n└ Не найдено\n\n'

        # ✅ Основные средства
        try:
            if calculate_difference(prev_year_dict["1150"], last_year_dict["1150"]).startswith("⬆️"):
                report_text += f'🟢 <b>Основные средства:</b>\n└ {last_year_dict["1150"]} тыс. руб. {calculate_difference(prev_year_dict["1150"], last_year_dict["1150"])}\n\n'
            elif calculate_difference(prev_year_dict["1150"], last_year_dict["1150"]).startswith("⬇️"):
                report_text += f'🔻 <b>Основные средства:</b>\n└ {last_year_dict["1150"]} тыс. руб. {calculate_difference(prev_year_dict["1150"], last_year_dict["1150"])}\n\n'
            else:
                report_text += f'• <b> Основные средства:</b>\n└ {last_year_dict["1150"]} тыс. руб. {calculate_difference(prev_year_dict["1150"], last_year_dict["1150"])}\n\n'
        except:
            report_text += '❌ <b>Основные средства:</b>\n└ Не найдено\n\n'

        # ✅ Доходы(выручка)
        try:
            if calculate_difference(prev_year_dict["2110"], last_year_dict["2110"]).startswith("⬆️"):
                report_text += f'🟢 <b>Доходы (выручка):</b>\n└ {last_year_dict["2110"]} тыс. руб. {calculate_difference(prev_year_dict["2110"], last_year_dict["2110"])}\n\n'
            elif calculate_difference(prev_year_dict["2110"], last_year_dict["2110"]).startswith("⬇️"):
                report_text += f'🔻 <b>Доходы (выручка):</b>\n└ {last_year_dict["2110"]} тыс. руб. {calculate_difference(prev_year_dict["2110"], last_year_dict["2110"])}\n\n'
            else:
                report_text += f'• <b>Доходы (выручка):</b>\n└ {last_year_dict["2110"]} тыс. руб. {calculate_difference(prev_year_dict["2110"], last_year_dict["2110"])}\n\n'
        except:
            report_text += '❌ <b>Доходы (выручка):</b>\n└\n└ Не найдено\n\n'

        # ✅ Дебиторская задолженность
        try:
            if calculate_difference(prev_year_dict["1230"], last_year_dict["1230"]).startswith("⬇️"):
                report_text += f'🟢 <b>Дебиторская задолженность:</b>\n└ {last_year_dict["1230"]} тыс. руб. {calculate_difference(prev_year_dict["1230"], last_year_dict["1230"])}\n\n'
            elif calculate_difference(prev_year_dict["1230"], last_year_dict["1230"]).startswith("⬆️"):
                report_text += f'🔻 <b>Дебиторская задолженность:</b>\n└ {last_year_dict["1230"]} тыс. руб. {calculate_difference(prev_year_dict["1230"], last_year_dict["1230"])}\n\n'
            else:
                report_text += f'• <b>Дебиторская задолженность:</b>\n└ {last_year_dict["1230"]} тыс. руб. {calculate_difference(prev_year_dict["1230"], last_year_dict["1230"])}\n\n'
        except:
            report_text += '<b>❌ Дебиторская задолженность:</b>\n└\n└ Не найдено\n\n'

        # ✅ Кредиторская задолженность
        try:
            if calculate_difference(prev_year_dict["1520"], last_year_dict["1520"]).startswith("⬇️"):
                report_text += f'🟢 <b>Кредиторская задолженность:</b>\n└ {last_year_dict["1520"]} тыс. руб. {calculate_difference(prev_year_dict["1520"], last_year_dict["1520"])}\n'
            elif calculate_difference(prev_year_dict["1520"], last_year_dict["1520"]).startswith("⬆️"):
                report_text += f'🔻 <b>Кредиторская задолженность:</b>\n└ {last_year_dict["1520"]} тыс. руб. {calculate_difference(prev_year_dict["1520"], last_year_dict["1520"])}\n'
            else:
                report_text += f'• <b>Кредиторская задолженность:</b>\n└ {last_year_dict["1520"]} тыс. руб. {calculate_difference(prev_year_dict["1520"], last_year_dict["1520"])}\n'
        except:
            report_text += '❌ <b>Кредиторская задолженность:</b>\n└ Не найдено\n\n'

        bot.send_message(call.message.chat.id, report_text,
                         parse_mode='html', reply_markup=full_fin_report_markup)

    '''
        2.1 БД ЧЕК ✅ Полная бух отчетность по году
    '''
    if call.data == 'full_fin_report':

        cursor.execute(f"SELECT inn FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        # Запрос api по бух. отчетности ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        try:
            available_report_years = ', '
            available_report_years = available_report_years.join(
                list(json_object[user_info[0]].keys()))

            report_date = bot.send_message(
                call.message.chat.id, f'Укажите год, например, 2018.\nДоступные года: {available_report_years}.')
            
            bot.register_next_step_handler(report_date, show_full_fin_report)
        except:
            bot.send_message(call.message.chat.id, 'Данных по отчетности нет', reply_markup=markup)
        
    '''
        3. БД ЧЕК ✅ ВСЕ ПУНКТЫ РАБОТАЮТ ✅ Финансовый анализ
    '''
    if call.data == 'fin_analysis':

        clean_message(call)

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Загружается модуль финансового анализа...')

        time.sleep(0.5)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        bot.send_message(call.message.chat.id, 'Выбери, что бы ты хотел проанализировать',
                         reply_markup=fin_analysis_markup)

    if call.data == 'financial_stability':
        
        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Запрашиваю данные о финансовой устойчивости...')

        # Запрос api по бух. отчетности ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        try:
            last_year_dict = json_object[user_info[0]][list(json_object[user_info[0]].keys())[-1]]
        except:
            last_year_dict = {}
        # Финансовая устойчивость

        # ✅ Коэффициент финансовой устойчивости
        try:
            financial_stability_ratio = round(
                (int(last_year_dict['1300']) + int(last_year_dict['1400'])) / int(last_year_dict['1700']), 2)

            if financial_stability_ratio > 0.9:
                financial_stability_ratio_text = f"<b>1️⃣  Коэффициент финансовой устойчивости:</b> \n├  {financial_stability_ratio} 🔥\n└ Компания почти не привлекает краткосрочные источники финансирования, что, однако, не всегда экономически правильно"
            elif financial_stability_ratio > 0.8 and financial_stability_ratio < 0.9:
                financial_stability_ratio_text = f"<b>1️⃣ Коэффициент финансовой устойчивости:</b> \n├ {financial_stability_ratio} 👍\n└ Активы компании профинансированы за счёт надёжных и долгосрочных источников"
            elif financial_stability_ratio > 0.7 and financial_stability_ratio < 0.8:
                financial_stability_ratio_text = f"<b>1️⃣ Коэффициент финансовой устойчивости:</b> \n├ {financial_stability_ratio} ❗\n└ Сомнительная финансовая независимость компании"
            else:
                financial_stability_ratio_text = f"<b>1️⃣ Коэффициент финансовой устойчивости:</b> \n├ {financial_stability_ratio} 👎\n└ Не стабильное положение компании, поскольку доля долговременных источников финансирования меньше, чем краткосрочных"
        except:
            financial_stability_ratio_text = "<b>1️⃣ Коэффициент финансовой устойчивости:</b> 0"

        # ✅ Коэффициент автономии
        try:
            autonomy_ratio = round(
                int(last_year_dict['1300']) / int(last_year_dict['1600']), 2)

            if autonomy_ratio > 0.8:
                autonomy_ratio_text = f"<b>2️⃣ Коэффициент автономии:</b> \n├ {autonomy_ratio} 🔥\n└ Организация независима от кредиторов"
            elif autonomy_ratio > 0.6 and autonomy_ratio < 0.8:
                autonomy_ratio_text = f"<b>2️⃣ Коэффициент автономии:</b> \n├ {autonomy_ratio} 👍\n└ Организация в приемлемой степени зависима от кредиторов"
            elif autonomy_ratio > 0.4 and autonomy_ratio < 0.6:
                autonomy_ratio_text = f"<b>2️⃣ Коэффициент автономии:</b> \n├ {autonomy_ratio} ❗\n└ Сомнительная финансовая независимость компании"
            else:
                autonomy_ratio_text = f"<b>2️⃣ Коэффициент автономии:</b> \n├ {autonomy_ratio} 👎\n└ Организация зависима от заёмных источников финансирования"
        except:
            autonomy_ratio_text = "<b>2️⃣ Коэффициент автономии:</b> 0"

        # ✅ Коэффицент обеспеченности собственными оборотными средствами
        try:
            working_capital_ratio = round((int(last_year_dict['1300']) - int(last_year_dict['1100'])) / int(last_year_dict['1200']), 2)

            if working_capital_ratio > 0.1:
                working_capital_ratio_text = f"<b>3️⃣ Коэффицент обеспеченности собственными оборотными средствами:</b> \n├ {working_capital_ratio} 👍\n└ Удовлетворительная структура баланса"
            elif working_capital_ratio > 0 and working_capital_ratio < 0.1:
                working_capital_ratio_text = f"<b>3️⃣ Коэффицент обеспеченности собственными оборотными средствами:</b> \n├ {working_capital_ratio} ❗\n└ Неудовлетворительная структура баланса"
            else:
                working_capital_ratio_text = f"<b>3️⃣ Коэффицент обеспеченности собственными оборотными средствами:</b> \n├ {working_capital_ratio} 👎\n└ Все оборотные, а также часть внеоборотных активов созданы за счёт кредитов и различных займов"
        except:
            working_capital_ratio_text = "<b>3️⃣ Коэффицент обеспеченности собственными оборотными средствами:</b> 0"

        # ✅ Отношение дебиторской задолженности к активам
        try:
            receivables_to_assets_ratio = round(
                int(last_year_dict['1230']) / int(last_year_dict['1600']), 2)

            if receivables_to_assets_ratio < 0.4:
                receivables_to_assets_ratio_text = f"<b>4️⃣ Отношение дебиторской задолженности к активам:</b> \n├ {receivables_to_assets_ratio} 👍\n└ Нормальная доля ожидаемых платежей"
            elif receivables_to_assets_ratio > 0.4 and receivables_to_assets_ratio < 0.7:
                receivables_to_assets_ratio_text = f"<b>4️⃣ Отношение дебиторской задолженности к активам:</b> \n├ {receivables_to_assets_ratio} ❗\n└ Нежелательная доля дебиторской задолженности"
            else:
                receivables_to_assets_ratio_text = f"<b>4️⃣ Отношение дебиторской задолженности к активам:</b> \n├ {receivables_to_assets_ratio} 👎\n└ Сильное влияние объёма дебиторской задолженности на общую картину финансовой состоятельности"
        except:
            receivables_to_assets_ratio_text = "<b>4️⃣ Отношение дебиторской задолженности к активам:</b> 0"

        # ✅ Коэффициент соотношения заёмного и собственного капитала
        try:
            debt_to_equity_ratio = round(
                (int(last_year_dict['1410']) + int(last_year_dict['1510'])) / int(last_year_dict['1300']), 2)

            if debt_to_equity_ratio < 0.5:
                debt_to_equity_ratio_text = f"<b>5️⃣ Коэффициент соотношения заёмного и собственного капитала:</b> \n├ {debt_to_equity_ratio} 🔥\n└ Устойчивое финансовое положение, одновременно указывает на неэффективность работы предприятия"
            elif debt_to_equity_ratio > 0.5 and debt_to_equity_ratio < 0.7:
                debt_to_equity_ratio_text = f"<b>5️⃣ Коэффициент соотношения заёмного и собственного капитала:</b> \n├ {debt_to_equity_ratio} 👍\n└ Оптимальное соотношение собственного и заёмного капитала"
            elif debt_to_equity_ratio > 0.7 and debt_to_equity_ratio < 1:
                debt_to_equity_ratio_text = f"<b>5️⃣ Коэффициент соотношения заёмного и собственного капитала:</b> \n├ {debt_to_equity_ratio} ❗\n└ Неустойчивость финансового положения и существование признаков неплатёжеспособности"
            else:
                debt_to_equity_ratio_text = f"<b>5️⃣ Коэффициент соотношения заёмного и собственного капитала:</b> \n├ {debt_to_equity_ratio} 👎\n└ Преобладание заёмных средств над собственными"
        except:
            debt_to_equity_ratio_text = "<b>5️⃣ Коэффициент соотношения заёмного и собственного капитала:</b> 0"

        # ✅ Коэффициент капитализации
        try:
            capitalization_ratio = round(
                (int(last_year_dict['1400']) + int(last_year_dict['1500'])) / int(last_year_dict['1300']), 2)

            if capitalization_ratio <= 1:
                capitalization_ratio_text = f"<b>6️⃣ Коэффициент капитализации:</b> \n├ {capitalization_ratio} 👍\n└ В распоряжении остаётся большая величина чистой прибыли, финансирование деятельности происходит в большей степени из собственных средств"
            else:
                capitalization_ratio_text = f"<b>6️⃣ Коэффициент капитализации:</b> \n├ {capitalization_ratio} 👎\n└ Высокий предпринимательский риск контрагента"
        except:
            capitalization_ratio_text = "<b>6️⃣ Коэффициент капитализации:</b> 0"

        financial_stability_report = f'<b>Данные о финансовой устойчивости {user_info[1]}:</b>\n\n{financial_stability_ratio_text}\n\n{autonomy_ratio_text}\n\n{working_capital_ratio_text}\n\n{receivables_to_assets_ratio_text}\n\n{debt_to_equity_ratio_text}\n\n{capitalization_ratio_text}'

        bot.send_message(call.message.chat.id, financial_stability_report,
                         reply_markup=back_to_fin_report_start_markup, parse_mode='html')

    if call.data == 'solvency':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Запрашиваю данные по платёжеспособности...')

        # Запрос api по бух. отчетности ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        try:
            last_year_dict = json_object[user_info[0]][list(json_object[user_info[0]].keys())[-1]]
        except:
            last_year_dict = {}

        # Платежеспособность

        # ✅ Коэффициент абсолютной ликвидности
        try:
            absolute_liquidity_ratio = round(
                (int(last_year_dict['1250']) + int(last_year_dict['1240'])) / int(last_year_dict['1500']), 2)

            if absolute_liquidity_ratio > 0.5:
                absolute_liquidity_ratio_text = f"<b>1️⃣ Коэффициент абсолютной ликвидности:</b> \n├ {absolute_liquidity_ratio} ❗\n└ Неоправданно высокие объёмы свободных денежных средств, которые можно было бы использовать для развития бизнеса"
            elif absolute_liquidity_ratio > 0.2 and absolute_liquidity_ratio < 0.5:
                absolute_liquidity_ratio_text = f"<b>1️⃣ Коэффициент абсолютной ликвидности:</b> \n├ {absolute_liquidity_ratio} 👍\n└ Достаточность наиболее ликвидных активов для быстрого расчета по текущим обязательствам"
            else:
                absolute_liquidity_ratio_text = f"<b>1️⃣ Коэффициент абсолютной ликвидности:</b> \n├ {absolute_liquidity_ratio} 👎\n└ Низкая готовность бизнеса к моментальному покрытию краткосрочных обязательств"
        except:
            absolute_liquidity_ratio_text = "<b>1️⃣ Коэффициент абсолютной ликвидности:</b> 0"

        # ✅ Коэффициент текущей ликвидности
        try:
            current_liquidity_ratio = round(
                int(last_year_dict['1200']) / int(last_year_dict['1500']), 2)

            if current_liquidity_ratio > 3:
                current_liquidity_ratio_text = f"<b>2️⃣ Коэффициент текущей ликвидности:</b> \n├ {current_liquidity_ratio} ⚠️\n└ Нерациональная структура капитала"
            elif current_liquidity_ratio > 2 and current_liquidity_ratio < 3:
                current_liquidity_ratio_text = f"<b>2️⃣ Коэффициент текущей ликвидности:</b> \n├ {current_liquidity_ratio} 🔥\n└ У контрагента есть деньги, и он успешно справляется с текущими обязательствами"
            elif current_liquidity_ratio > 1.5 and current_liquidity_ratio < 2:
                current_liquidity_ratio_text = f"<b>2️⃣ Коэффициент текущей ликвидности:</b> \n├ {current_liquidity_ratio} 👍\n└ Бизнес закрывает основные актуальные потребности из текущих активов"
            elif current_liquidity_ratio > 1 and current_liquidity_ratio < 1.5:
                current_liquidity_ratio_text = f"<b>2️⃣ Коэффициент текущей ликвидности:</b> \n├ {current_liquidity_ratio} ❗\n└ У контрагента больше финансовых обязательств, чем он может потянуть"
            else:
                current_liquidity_ratio_text = f"<b>2️⃣ Коэффициент текущей ликвидности:</b> \n├ {current_liquidity_ratio} 👎\n└ Вероятные трудности в погашении своих текущих обязательств"
        except:
            current_liquidity_ratio_text = "<b>2️⃣ Коэффициент текущей ликвидности:</b> 0"

        # ✅ Коэффициент быстрой ликвидности
        try:

            quick_liquidity_ratio = round((int(last_year_dict['1230']) or 0 + int(last_year_dict['1240']) or 0 + int(
                last_year_dict['1250']) or 0) / (int(last_year_dict['1510']) or 0 + int(last_year_dict['1520']) or 0 + int(last_year_dict['1550']) or 0), 2)

            if quick_liquidity_ratio > 1:
                quick_liquidity_ratio_text = f"<b>3️⃣ Коэффициент быстрой ликвидности:</b> \n├ {quick_liquidity_ratio} 👍\n└ Контрагент в состоянии обеспечить быстрое полное погашение имеющейся текущей задолженности за счёт собственных средств"
            elif quick_liquidity_ratio > 0.7 and quick_liquidity_ratio < 1:
                quick_liquidity_ratio_text = f"<b>3️⃣ Коэффициент быстрой ликвидности:</b> \n├ {quick_liquidity_ratio} ❗\n└ Допустимо, обычной практикой является ведение бизнеса с наличием долгов"
            else:
                quick_liquidity_ratio_text = f"<b>3️⃣ Коэффициент быстрой ликвидности:</b> \n├ {quick_liquidity_ratio} 👎\n└ Ликвидные активы не покрывают краткосрочные обязательства"
        except:
            quick_liquidity_ratio_text = "<b>3️⃣ Коэффициент быстрой ликвидности:</b> 0"

        # ✅ Коэффициент обеспеченности обязательств активами
        try:
            liabilities_with_assets_ratio = round((int(last_year_dict['1600']) or 0 - int(last_year_dict['1200']) or 0) / (int(
                last_year_dict['1520']) or 0 + int(last_year_dict['1510']) or 0 + int(last_year_dict['1550']) or 0 + int(last_year_dict['1400']) or 0), 2)

            if liabilities_with_assets_ratio > 0.85:
                liabilities_with_assets_ratio_text = f"<b>4️⃣ Коэффициент обеспеченности обязательств активами:</b> \n├ {liabilities_with_assets_ratio} 👎\n└ Угрожает банкротство"
            elif liabilities_with_assets_ratio > 0.5 and liabilities_with_assets_ratio < 0.85:
                liabilities_with_assets_ratio_text = f"<b>4️⃣ Коэффициент обеспеченности обязательств активами:</b> \n├ {liabilities_with_assets_ratio} ❗\n└ Сомнительная величина активов должника, приходящихся на единицу долга"
            elif liabilities_with_assets_ratio > 0.2 and liabilities_with_assets_ratio < 0.5:
                liabilities_with_assets_ratio_text = f"<b>4️⃣ Коэффициент обеспеченности обязательств активами:</b> \n├ {liabilities_with_assets_ratio} 👍\n└ Приемлемая величина активов должника, приходящихся на единицу долга"
            else:
                liabilities_with_assets_ratio_text = f"<b>4️⃣ Коэффициент обеспеченности обязательств активами:</b> \n├ {liabilities_with_assets_ratio} 👎\n└ Ликвидные активы не покрывают краткосрочные обязательства"
        except:
            liabilities_with_assets_ratio_text = "<b>4️⃣ Коэффициент обеспеченности обязательств активами:</b> 0"

        # ✅ Степень платёжеспособности по текущим обязательствам
        try:
            current_liabilities_ratio = round((int(last_year_dict['1510']) or 0 + int(
                last_year_dict['1520']) or 0 + int(last_year_dict['1550']) or 0) / (int(last_year_dict['2120']) or 0 / 12), 2)

            if current_liabilities_ratio > 6:
                current_liabilities_ratio_text = f"<b>5️⃣ Степень платёжеспособности по текущим обязательствам:</b> \n├ {current_liabilities_ratio} 👎\n└ Период, в течение которого контрагент может погасить за счёт выручки текущую задолженность перед кредиторами"
            elif current_liabilities_ratio > 4 and current_liabilities_ratio < 6:
                current_liabilities_ratio_text = f"<b>5️⃣ Степень платёжеспособности по текущим обязательствам:</b> \n├ {current_liabilities_ratio} ❗\n└ Период, в течение которого контрагент может погасить за счёт выручки текущую задолженность перед кредиторами"
            elif current_liabilities_ratio > 2 and current_liabilities_ratio < 4:
                current_liabilities_ratio_text = f"<b>5️⃣ Степень платёжеспособности по текущим обязательствам:</b> \n├ {current_liabilities_ratio} 👍\n└ Период, в течение которого контрагент может погасить за счёт выручки текущую задолженность перед кредиторами"
            else:
                current_liabilities_ratio_text = f"<b>5️⃣ Степень платёжеспособности по текущим обязательствам:</b> \n├ {current_liabilities_ratio} 🔥\n└ Период, в течение которого контрагент может погасить за счёт выручки текущую задолженность перед кредиторами"
        except:
            current_liabilities_ratio_text = "<b>5️⃣ Степень платёжеспособности по текущим обязательствам:</b> 0"

        solvency_report = f'<b>Данные о платёжеспособности {user_info[1]}:</b>\n\n{absolute_liquidity_ratio_text}\n\n{current_liquidity_ratio_text}\n\n{quick_liquidity_ratio_text}\n\n{liabilities_with_assets_ratio_text}\n\n{current_liabilities_ratio_text}'

        bot.send_message(call.message.chat.id, solvency_report,
                         reply_markup=back_to_fin_report_start_markup, parse_mode='html')

    if call.data == 'efficiency':
        
        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Запрашиваю данные по эффективности...')

        # Запрос api по бух. отчетности ======================================================
        response = requests.get(
            f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

        json_object = json.loads(response)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        try:
            last_year_dict = json_object[user_info[0]][list(json_object[user_info[0]].keys())[-1]]
        except:
            last_year_dict = {}

        # Эффективность

        # ✅ Рентабельность по чистой прибыли
        try:
            net_profit_margin = round(
                (int(last_year_dict['2400']) / int(last_year_dict['2110'])) * 100, 2)

            if net_profit_margin > 30:
                net_profit_margin_text = f"<b>1️⃣ Рентабельность по чистой прибыли:</b> \n├ {net_profit_margin}% 🔥\n└ Показатель чистой прибыли (убытка) на рубль выручки. Чем он выше, тем более высокая доходность и эффективность у конкретного бизнеса"
            elif net_profit_margin > 15 and net_profit_margin < 30:
                net_profit_margin_text = f"<b>1️⃣ Рентабельность по чистой прибыли:</b> \n├ {net_profit_margin}% 👍\n└ Показатель чистой прибыли (убытка) на рубль выручки. Чем он выше, тем более высокая доходность и эффективность у конкретного бизнеса"
            elif net_profit_margin > 0 and net_profit_margin < 15:
                net_profit_margin_text = f"<b>1️⃣ Рентабельность по чистой прибыли:</b> \n├ {net_profit_margin}% ❗\n└ Показатель чистой прибыли (убытка) на рубль выручки. Чем он выше, тем более высокая доходность и эффективность у конкретного бизнеса"
            else:
                net_profit_margin_text = f"<b>1️⃣ Рентабельность по чистой прибыли:</b> \n├ {net_profit_margin}% 👎\n└ Показатель чистой прибыли (убытка) на рубль выручки. Чем он выше, тем более высокая доходность и эффективность у конкретного бизнеса"
        except:
            net_profit_margin_text = "<b>1️⃣ Рентабельность по чистой прибыли:</b> 0"

        # ✅ Рентабельность затрат
        try:
            cost_effectiveness = round((int(last_year_dict['2400']) / (int(last_year_dict['2120']) + int(
                last_year_dict['2210']) + int(last_year_dict['2220']))) * 100, 2)

            if cost_effectiveness > 30:
                cost_effectiveness_text = f"<b>2️⃣ Рентабельность затрат:</b> \n├ {cost_effectiveness}% 🔥\n└ Показатель, отражающий уровень прибыли на 1 рубль затраченных средств"
            elif cost_effectiveness > 15 and cost_effectiveness < 30:
                cost_effectiveness_text = f"<b>2️⃣ Рентабельность затрат:</b> \n├ {cost_effectiveness}% 👍\n└ Показатель, отражающий уровень прибыли на 1 рубль затраченных средств"
            elif cost_effectiveness > 0 and cost_effectiveness < 15:
                cost_effectiveness_text = f"<b>2️⃣ Рентабельность затрат:</b> \n├ {cost_effectiveness}% ❗\n└ Показатель, отражающий уровень прибыли на 1 рубль затраченных средств"
            else:
                cost_effectiveness_text = f"<b>2️⃣ Рентабельность затрат:</b> \n├ {cost_effectiveness}% 👎\n└ Показатель, отражающий уровень прибыли на 1 рубль затраченных средств"
        except:
            cost_effectiveness_text = "<b>2️⃣ Рентабельность затрат:</b> 0"

        # ✅ Рентабельность активов
        try:
            return_on_assets = round(
                (int(last_year_dict['2400']) / int(last_year_dict['1600'])) * 100, 2)

            if return_on_assets > 30:
                return_on_assets_text = f"<b>3️⃣ Рентабельность активов:</b> \n├ {return_on_assets}% 🔥\n└ Объем прибыли в рублях, который приносит 1 рубль активов контрагента"
            elif return_on_assets > 15 and return_on_assets < 30:
                return_on_assets_text = f"<b>3️⃣ Рентабельность активов:</b> \n├ {return_on_assets}% 👍\n└ Объем прибыли в рублях, который приносит 1 рубль активов контрагента"
            elif return_on_assets > 0 and return_on_assets < 15:
                return_on_assets_text = f"<b>3️⃣ Рентабельность активов:</b> \n├ {return_on_assets}% ❗\n└ Объем прибыли в рублях, который приносит 1 рубль активов контрагента"
            else:
                return_on_assets_text = f"<b>3️⃣ Рентабельность активов:</b> \n├ {return_on_assets}% 👎\n└ Объем прибыли в рублях, который приносит 1 рубль активов контрагента"
        except:
            return_on_assets_text = "<b>3️⃣ Рентабельность активов:</b> 0"

        # ✅ Рентабельность собственного капитала
        try:
            return_on_equity = round(
                (int(last_year_dict['2400']) / int(last_year_dict['1300'])) * 100, 2)

            if return_on_equity > 30:
                return_on_equity_text = f"<b>4️⃣ Рентабельность собственного капитала:</b> \n├ {return_on_equity}% 🔥\n└ Сколько копеек прибыли приносит контрагенту каждый рубль его собственного капитала"
            elif return_on_equity > 15 and return_on_equity < 30:
                return_on_equity_text = f"<b>4️⃣ Рентабельность собственного капитала:</b> \n├ {return_on_equity}% 👍\n└ Сколько копеек прибыли приносит контрагенту каждый рубль его собственного капитала"
            elif return_on_equity > 0 and return_on_equity < 15:
                return_on_equity_text = f"<b>4️⃣ Рентабельность собственного капитала:</b> \n├ {return_on_equity}% ❗\n└ Сколько копеек прибыли приносит контрагенту каждый рубль его собственного капитала"
            else:
                return_on_equity_text = f"<b>4️⃣ Рентабельность собственного капитала:</b> \n├ {return_on_equity}% 👎\n└ Сколько копеек прибыли приносит контрагенту каждый рубль его собственного капитала"
        except:
            return_on_equity_text = "<b>4️⃣ Рентабельность собственного капитала:</b> 0"

        # ✅ Общая рентабельность продаж
        try:
            return_on_sales = round(
                (int(last_year_dict['2100']) / int(last_year_dict['2110'])) * 100, 2)

            if return_on_sales > 20:
                return_on_sales_text = f"<b>5️⃣ Общая рентабельность продаж:</b> \n├ {return_on_sales}% 🔥\n└ Доля валовой прибыли в каждом заработанном рубле. Иными словами, сколько средств остается у предприятия после покрытия себестоимости продукции"
            elif return_on_sales > 5 and return_on_sales < 20:
                return_on_sales_text = f"<b>5️⃣ Общая рентабельность продаж:</b> \n├ {return_on_sales}% 👍\n└ Доля валовой прибыли в каждом заработанном рубле. Иными словами, сколько средств остается у предприятия после покрытия себестоимости продукции"
            elif return_on_sales > 0 and return_on_sales < 5:
                return_on_sales_text = f"<b>5️⃣ Общая рентабельность продаж:</b> \n├ {return_on_sales}% ❗\n└ Доля валовой прибыли в каждом заработанном рубле. Иными словами, сколько средств остается у предприятия после покрытия себестоимости продукции"
            else:
                return_on_sales_text = f"<b>5️⃣ Общая рентабельность продаж:</b> \n├ {return_on_sales}% 👎\n└ Доля валовой прибыли в каждом заработанном рубле. Иными словами, сколько средств остается у предприятия после покрытия себестоимости продукции"
        except:
            return_on_sales_text = "<b>5️⃣ Общая рентабельность продаж не найдена</b>"

        # ✅ Оборачиваемость дебиторской задолженности
        try:
            accounts_receivable_turnover = round(
                int(last_year_dict['2110']) / int(last_year_dict['1230']), 2)

            accounts_receivable_turnover_text = f"<b>6️⃣ Оборачиваемость дебиторской задолженности:</b> \n├ {accounts_receivable_turnover}\n└ Насколько быстро организация получает оплату за проданные товары (работы, услуги) от своих покупателей"
        except:
            accounts_receivable_turnover_text = "<b>6️⃣ Оборачиваемость дебиторской задолженности:</b> 0"

        # Оборачиваемость кредиторской задолженности
        try:
            accounts_payable_turnover = ceil(
                int(last_year_dict['2110']) / int(last_year_dict['1520']))

            accounts_payable_turnover_text = f"<b>6️⃣ Оборачиваемость кредиторской задолженности:</b> \n├ {accounts_payable_turnover}\n└ Сколько раз за год фирма погасила среднюю величину своей кредиторской задолженности"
        except:
            accounts_payable_turnover_text = "<b>6️⃣ Оборачиваемость кредиторской задолженности:</b> 0"

        efficiency_report = f'<b>Данные о финансовой эффективности {user_info[1]}:</b>\n\n{net_profit_margin_text}\n\n{cost_effectiveness_text}\n\n{return_on_assets_text}\n\n{return_on_sales_text}\n\n{return_on_equity_text}\n\n{accounts_receivable_turnover_text}\n\n{accounts_payable_turnover_text}\n\n'

 

        bot.send_message(call.message.chat.id, efficiency_report,
                         reply_markup=back_to_fin_report_start_markup, parse_mode='html')
    
    # конец 3 пункта

    '''
        4. БД ЧЕК ✅ Оценка финансовых рисков и рисков неисполнения обязательств
    '''
    if call.data == 'fin_risk':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию об арбитражных делах [0%]')

        time.sleep(1)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об арбитражных делах [50%]')

        # Запрос api по арбитражным делам ==============================
        response_arb = requests.get(f'https://api.damia.ru/arb/dela?q={user_info[0]}&key={damia_arb_api_key}').text

        json_object_arb = json.loads(response_arb)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Проверяю информацию о контрагенте [75%]')

        # Запрос api по проверке контрагента =====================================
        response_check = requests.get(f'https://api-fns.ru/api/check?req={user_info[0]}&key={fns_api_key}').text

        json_object_check = json.loads(response_check)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Составляю отчет [100%]')
        
        time.sleep(1)

        bot.delete_message(call.message.chat.id, arb_msg1.id)
        
        risk_text = f'<b>Оценка финансовых рисков {user_info[1]}</b>\n\n'

        try:
            if json_object_check['items'][0]['ЮЛ']['Негатив']['БанкротНамерение']:
                risk_text += '1️⃣ <b>Реестр банкротств:</b>\n└ Числится в реестре ❗️\n\n'
        except:
            risk_text += '1️⃣ <b>Реестр банкротств:</b>\n└ В реестре не числится ✅\n\n'

        arb_count = 0
        arb_active_count = 0
        arb_active_sum = 0
        arb_full_sum = 0
        
        
        try:
            for role, case_list in json_object_arb['result'].items():
                for number, list_item in case_list.items():
                    arb_count += 1

                    arb_full_sum += list_item['Сумма']

                    if list_item['Статус'] != "Рассмотрение дела завершено":
                        arb_active_count += 1
                        arb_active_sum += list_item['Сумма']
        except:
            pass
    

        risk_text += f'2️⃣ <b>Арбитражные дела:</b>\n├ Всего найдено: {arb_count} дел на сумму {round(arb_full_sum, 2)} руб.\n└ Рассматривается сейчас: {arb_active_count} на сумму {arb_active_sum} руб.\n\n'

        
        arb_active_defendant_count = 0
        arb_active_plaintiff_count = 0
        
        arb_finished_defendant_count = 0
        arb_finished_plaintiff_count = 0
        
        arb_defendant_active_sum = 0
        arb_plaitiff_active_sum = 0

        arb_defendant_finished_sum = 0
        arb_plaitiff_finished_sum = 0

        # Собираем статистику по арбитражным делам в качестве ответчика
        try:
            for number, list_item in json_object_arb['result']['Ответчик'].items():
                if list_item['Статус'] == "Рассмотрение дела завершено":
                    arb_finished_defendant_count += 1
                    arb_defendant_finished_sum += list_item['Сумма']
                else:
                    arb_active_defendant_count += 1
                    arb_defendant_active_sum += list_item['Сумма']

            
            risk_text += f'3️⃣ <b>Наличие арбитражных дел в качестве Ответчика:</b>\n├  Завершено: {arb_finished_defendant_count} на сумму {round(arb_defendant_finished_sum, 2)}  руб.\n└ Рассматривается сейчас: {arb_active_defendant_count} на сумму {round(arb_defendant_active_sum, 2)} руб.\n\n'
            
        except:
            pass
        
        # Собираем статистику по арбитражным делам в качестве истца
        try:
            for number, list_item in json_object_arb['result']['Истец'].items():
                if list_item['Статус'] == "Рассмотрение дела завершено":
                    arb_finished_plaintiff_count += 1
                    arb_plaitiff_finished_sum += list_item['Сумма']
                else:
                    arb_active_plaintiff_count += 1
                    arb_plaitiff_active_sum += list_item['Сумма']

            risk_text += f'4️⃣ <b>Наличие арбитражных дел в качестве Истца:</b>\n├  Завершено: {arb_finished_plaintiff_count} на сумму {round(arb_plaitiff_finished_sum, 2)}  руб.\n└ Рассматривается сейчас: {arb_active_plaintiff_count} на сумму {round(arb_plaitiff_active_sum, 2)} руб.\n\n'
        except:
            pass

        bot.send_message(call.message.chat.id, risk_text, parse_mode='html', reply_markup=fin_risk_markup)

    '''
        5. БД ЧЕК ✅ Анализ репутации
    '''
    if call.data == 'reputation':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию о репутации компании [0%]')

        time.sleep(1)

        today_date = datetime.today().strftime("%Y-%m-%d")
        date_start = f'{datetime.today().year - 5}-{datetime.today().month}-{datetime.today().day}'


        # Запрос api по проверке контрагента ======================================================
        response_check = requests.get(
            f'https://api-fns.ru/api/check?req={user_info[0]}&key={fns_api_key}').text

        json_object_check = json.loads(response_check)

        try:
            msp_check = f"Состоит с {json_object_check['items'][0]['ЮЛ']['Позитив']['РеестрМСП']['ДатаВклМСП'].replace('-', '.')}"
        except:
            msp_check = 'Не состоит'

        response_egr = requests.get(f'https://api-fns.ru/api/egr?req={user_info[0]}&key={fns_api_key}').text

        json_object_egr = json.loads(response_egr)

        try:
            license_count = len(json_object_egr['items'][0]['ЮЛ']['Лицензии'])
        except:
            license_count = 'Не найдены'
        
        try:
            branch_count = len(json_object_egr['items'][0]['ЮЛ']['Филиалы'])
        except:
            branch_count = 'Не найдены'

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Ищу информацию о лицензиях компании [25%]')

        # Запрос api по госконтрактам ======================================================
        response_contract = requests.get(f'https://api.damia.ru/zakupki/contracts?inn={user_info[0]}&fz=44&format=2&from_date={date_start}&to_date={today_date}&key={damia_contracts_api_key}').text

        json_object_contract = json.loads(response_contract)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Ищу информацию о госконтрактах компании [50%]')

        # Запрос api по госзакупкам ======================================================
        response_purchase = requests.get(f'https://api.damia.ru/zakupki/zakupki?inn={user_info[0]}&fz=44&format=2&from_date={date_start}&to_date={today_date}&key={damia_zakupki_api_key}').text

        json_object_purchase = json.loads(response_purchase)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id, text='Ищу информацию о госзакупках компании [100%]')

        time.sleep(0.5)

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        contract_count = len(json_object_contract[user_info[0]])
        purchase_count = len(json_object_purchase[user_info[0]])

        reputation_text = f'<b>Данные о репутации {user_info[1]}</b>\n\n1️⃣ <b>Лицензии:</b> {license_count}\n\n2️⃣ <b>Реестр МСП:</b> {msp_check}\n\n3️⃣ <b>Участие в госзакупках (кол-во за 5 лет):</b> {purchase_count}\n\n4️⃣ <b>Участие в госконтрактах (кол-во за 5 лет):</b> {contract_count}\n\n5️⃣ <b>Филиалы и представительства:</b> {branch_count}\n\n'

        bot.send_message(call.message.chat.id, reputation_text, parse_mode='html', reply_markup=reputation_markup)

    '''
        6. БД ЧЕК ✅ Проверка изменений
    '''
    if call.data == 'check_changes':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name, address_change, director_change, founders_change FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию об изменениях [0%]')

        time.sleep(1)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об изменениях [50%]')

        response = requests.get(
            f'https://api.damia.ru/arb/dela?q={user_info[0]}&key={damia_arb_api_key}').text

        json_object = json.loads(response)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об изменениях [100%]')

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        changes_report = f'<b>Информация об изменениях в {user_info[1]}</b>\n\n<b>🏚 Изменения адреса:</b>\n{user_info[2]}\n<b>👨🏼‍💼 Смена руководителя:</b>\n{user_info[3]}\n<b>👥 Смена учредителей:</b>\n{user_info[4]}\n'

        arb_counter = 0

        try:
            for role, case_list in json_object['result'].items():
                
                current_year = datetime.today().year

                for number, list_item in case_list.items():
                    if f'{current_year}' in str(number):
                        arb_counter += 1
        except:
            arb_counter = 0

        changes_report += f'<b>🧑🏼‍⚖️ Судебные дела за последний год:</b>\nНайдено судебных дел: {arb_counter}'

        bot.send_message(call.message.chat.id, changes_report, reply_markup=markup, parse_mode='html')

    '''
        4.1 БД ЧЕК ✅ Информация об арбитражных делах
    '''
    if call.data == 'arb':

        clean_message(call)

        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        arb_msg1 = bot.send_message(
            call.message.chat.id, 'Ищу информацию об арбитражных делах [0%]')

        time.sleep(1)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об арбитражных делах [50%]')

        # Запрос api по арбитражным делам ======================================================
        response = requests.get(
            f'https://api.damia.ru/arb/dela?q={user_info[0]}&key={damia_arb_api_key}').text

        json_object = json.loads(response)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=arb_msg1.id,
                              text='Ищу информацию об арбитражных делах [100%]')

        bot.delete_message(call.message.chat.id, arb_msg1.id)

        arb_text = f'<b>Информация об арбитражных делах {user_info[1]}:</b>\n\n'

        # Сейчас сложная конструкция читать внимательно !!!!!!!!!
        #
        # Сначала мы проходимся по списку дел(по ролям) из result
        try:
            for role, case_list in json_object['result'].items():
                
                arb_last_year_type_count = 0
                arb_last_year_type_sum = 0

                current_year = datetime.today().year

                for number, list_item in case_list.items():
                    if f'{current_year}' in str(number):
                        arb_last_year_type_count += 1
                        arb_last_year_type_sum += list_item['Сумма']

               
                arb_text += f'<hr>\n\n📒 Кол-во дел в роли <b>{role}</b> за последний год: {arb_last_year_type_count}\n'

                arb_text += f'💵 Сумма по делам в роли <b>{role}</b> за последний год:\n└ {round(arb_last_year_type_sum)} руб.\n\n'

                # У каждой роли есть еще словарь дел который мы раскрываем на номер дела и информацию про него(list item это словарь информации об отдельном деле)
                for number, list_item in case_list.items():
                    
                    # Собираем информацию об отдельном деле и добавляем в отчет
                    arb_number = number
                    arb_type = list_item['Тип']
                    arb_date = list_item['Дата']
                    arb_url = list_item['Url']
                    arb_sum = round(list_item['Сумма'], 2)
                    arb_status = list_item['Статус']
                    arb_status_date = list_item['СтатусДата']

                    arb_text += f"📑 <b>Дело №{arb_number} от {arb_date}</b>\n├ Тип дела: {arb_type}\n├ URL дела: {arb_url}\n├ Сумма дела: {arb_sum} руб.\n└ Статус дела: {arb_status} с {arb_status_date}\n\n"
                    
                    
            # Генерация уникального имени файла для последующего удаления
            filename = r"Арбитражные_дела_" + str(uuid.uuid4())
                                                                                                                                                                    
            with open(f'{filename}.html', "wb") as f:

                ready_text  = "<html><head><meta charset='utf-8'/><style>.html {box-sizing: border-box;} * {margin: 0;font-family: Helvetica, sans-serif; box-sizing: border-box;} body {margin: 0; min-width: 320px; padding: 20px}</style><title>Output Data in an HTML file\n \
            </title>\n</head> <body>"  + arb_text + "</body></html>"

                f.write(ready_text.replace("\n", "<br>").replace("\t", "&nbsp;").encode("UTF-8"))

            doc_file = open(f'{filename}.html', 'r', encoding="utf-8")

            bot.send_document(call.message.chat.id, doc_file, reply_markup=markup)

            doc_file.close()

            os.remove(f'{filename}.html')
        except:
            bot.send_message(call.message.chat.id, 'Информация об арбитражных делах не найдена!', parse_mode='html', reply_markup=markup)

    '''
        8. ❌ Не работает на линуксе ❌ Выписка из ЕГРЮЛ или ЕГРИП
    '''
    if call.data == 'pdf' or call.data == 'ip_pdf':

        clean_message(call)
        # Сообщение о статусе выписки
        vyp_msg = bot.send_message(call.message.chat.id, 'Ваша выписка готовится...')

        cursor.execute(f"SELECT inn FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        try:
            # Запрос в базу для получения выписки

            if call.data == 'pdf':
                pdf_type = 'ЕГРЮЛ'
                url = f'https://api-fns.ru/api/vyp?req={user_info[0]}&key={pdf_api_key}'
            else:
                pdf_type = 'ЕГРИП'
                url = f'https://api-fns.ru/api/vyp?req={user_info[0]}&key={pdf_api_key}'

            r = requests.get(url)

            # Генерация уникального имени файла для последующего удаления
            filename = f"Выписка_{pdf_type}_" + str(uuid.uuid4())

            # Запись в файл и его генерация
            with open(f'{filename}.pdf', 'wb') as f:
                f.write(r.content)

            # Открываем поток файла для чтения и передачи в сообщение
            doc_file = open(f'{filename}.pdf', 'rb')

            # Отправляем файл
            if call.data == 'pdf':
                bot.send_document(call.message.chat.id,
                                    doc_file, reply_markup=markup)
            else:
                bot.send_document(call.message.chat.id,
                                    doc_file, reply_markup=ip_back_markup)
            
            bot.delete_message(call.message.chat.id, vyp_msg.id)

            # Закрываем поток файла чтобы удалить его
            doc_file.close()

            #Удаляем файл для очистки места на диске
            os.remove(f'{filename}.pdf')

        except:
            bot.send_message(call.message.chat.id, '❌ Не удалось получить выписку', reply_markup=markup)

    '''
        БД ЧЕК ✅ Универсальный запрос для ЮЛ возвращающий на главное сообщение с главными кнопками
    '''
    if call.data == 'ul_back':
        clean_message(call)

        back_to_short_report_msg = bot.send_message(call.message.chat.id, 'Возвращаемся обратно к отчёту...', parse_mode='html')

        time.sleep(1)

        bot.delete_message(call.message.chat.id, back_to_short_report_msg.id)

        cursor.execute(f"SELECT bot_main_msg FROM login_id WHERE id = {call.message.chat.id}")

        connect.commit()

        # Сохраняем отчет в переменную, чтобы после обращаться к нему без повторного запроса
        bot_main_msg = cursor.fetchone()[0]

        bot.send_message(call.message.chat.id, bot_main_msg,
                         reply_markup=main_bot_markup, parse_mode='html')

    '''
        БД ЧЕК ✅ Универсальный запрос для ИП возвращающий на главное сообщение с главными кнопками
    '''
    if call.data == 'ip_back':
        clean_message(call)

        cursor.execute(f"SELECT bot_main_msg FROM login_id WHERE id = {call.message.chat.id}")

        connect.commit()

        # Сохраняем отчет в переменную, чтобы после обращаться к нему без повторного запроса
        bot_main_msg = cursor.fetchone()[0]

        bot.send_message(call.message.chat.id, bot_main_msg,
                         reply_markup=ip_bot_markup, parse_mode='html')
    
    '''
        9. Полный отчет
    '''
    if call.data == 'full_report' or call.data == 'ip_full_report':

        clean_message(call)

        # Сообщение о статусе отчета
        vyp_msg = bot.send_message(call.message.chat.id, 'Ваш отчет составляется, пожалуйста подождите...')
        
        cursor.execute(f"SELECT inn, company_name FROM login_id WHERE id = {call.message.chat.id}")
        connect.commit()

        user_info = cursor.fetchone()

        url = f'https://api.damia.ru/spk/report?req={user_info[0]}&key={damia_report_key}'

        r = requests.get(url)

        # Генерация уникального имени файла для последующего удаления
        filename = f"Отчет_" + str(uuid.uuid4())

        # Запись в файл и его генерация
        with open(f'{filename}.docx', 'wb') as f:
            f.write(r.content)

        # Открываем поток файла для чтения и передачи в сообщение
        doc_file = open(f'{filename}.docx', 'rb')
        
         # Отправляем файл
        if call.data == 'full_report':
            bot.send_document(call.message.chat.id,
                                doc_file, reply_markup=markup)
        else:
            bot.send_document(call.message.chat.id,
                                doc_file, reply_markup=ip_back_markup)      

        doc_file.close()

        os.remove(f'{filename}.docx')


#  ======= Продолжение госконтрактов, госзакупок и бух отчетности ==========

# Обработчик даты конца поиска госзакупок
# БД ЧЕК ✅
def zakupki_date_end(message):
    date_end = bot.send_message(
        message.chat.id, 'Укажите дату конца поиска в формате <b>День-Месяц-Год</b>, например, 14-01-2019', parse_mode='html')

    cursor.execute("UPDATE login_id SET zakupki_date_start = (?) WHERE id = (?)", (message.text, message.chat.id))

    connect.commit()

    bot.register_next_step_handler(date_end, goszakupki)

# После двух введенных дат показывать госконтракты в данном диапозоне
# БД ЧЕК ✅
def goszakupki(message):

    cursor.execute("UPDATE login_id SET zakupki_date_end = (?) WHERE id = (?)", (message.text, message.chat.id))

    connect.commit()
    
    cursor.execute(f"SELECT zakupki_date_start, zakupki_date_end, inn, company_name FROM login_id WHERE id = {message.chat.id}")
    connect.commit()

    user_info = cursor.fetchone()

    date_start = datetime.strptime(user_info[0], "%d-%m-%Y").strftime("%Y-%m-%d")

    date_end = datetime.strptime(user_info[1], "%d-%m-%Y").strftime("%Y-%m-%d")

    print(date_start)
    print(date_end)
    
    # Запрос api по госзакупкам ======================================================
    response = requests.get(
        f'https://api.damia.ru/zakupki/zakupki?inn={user_info[2]}&fz=44&format=2&from_date={date_start}&to_date={date_end}&key={damia_zakupki_api_key}').text

    json_object = json.loads(response)

    # Сборка отчета о госзакупках ====================================================
    purchase_list = f'<h1>Участие {user_info[3]} в госзакупках c {date_start} до {date_end}:</h1>\n\n<hr>\n\n'
    
    try:
        for number, purchase_data in json_object[user_info[2]].items():
    
            purchase_number = number
            purchase_date = purchase_data['ДатаПубл'].replace("-", ".")
            purchase_customer_inn = purchase_data['ЗаказчикИНН']
            purchase_amount = f'{purchase_data["НачЦена"]["Сумма"]} {purchase_data["НачЦена"]["ВалютаКод"]}'
            purchase_product = f'{purchase_data["Продукт"]["ОКПД"]} {purchase_data["Продукт"]["Название"]}'
            purchase_status = f'{purchase_data["Статус"]["Статус"]} {purchase_data["Статус"]["Дата"].replace("-", ".")}'

            purchase_list += f'💳 <b>Госзакупка №{purchase_number}</b>\n├ <b>Дата:</b> {purchase_date}\n├ <b>ИНН Заказчика:</b> {purchase_customer_inn}\n├ <b>Сумма:</b> {purchase_amount}\n├ <b>Продукт:</b> {purchase_product}\n└ <b>Статус:</b> {purchase_status}\n\n<hr>\n\n'

        # Генерация уникального имени файла для последующего удаления
        filename = r"Госзакупки_" + str(uuid.uuid4())    

        with open(f'{filename}.html', "wb") as f:

            ready_text  = "<html><head><meta charset='utf-8'/><style>.html {box-sizing: border-box;} * {margin: 0;font-family: Helvetica, sans-serif; box-sizing: border-box;} body {margin: 0; min-width: 320px; padding: 20px}</style><title>Output Data in an HTML file\n \
        </title>\n</head> <body>"  + purchase_list + "</body></html>"

            f.write(ready_text.replace("\n", "<br>").replace("\t", "&nbsp;").encode("UTF-8"))

        doc_file = open(f'{filename}.html', 'r', encoding="utf-8")

        bot.send_document(message.chat.id, doc_file, reply_markup=markup)

        doc_file.close()

        os.remove(f'{filename}.html')

    except:
        bot.send_message(message.chat.id, "Информация о госзакупках не найдена!", reply_markup=markup)
    

# Обработчик даты конца поиска госконтрактов
# БД ЧЕК ✅
def contract_date_end(message):
    date_end = bot.send_message(
        message.chat.id, 'Укажите дату конца поиска в формате <b>День-Месяц-Год</b>, например, 14-01-2019', parse_mode='html')

    cursor.execute("UPDATE login_id SET contracts_date_start = (?) WHERE id = (?)", (message.text, message.chat.id))

    connect.commit()

    bot.register_next_step_handler(date_end, goscontracts)

# После двух введенных дат показывать госконтракты в данном диапозоне
# БД ЧЕК ✅
def goscontracts(message):

    cursor.execute("UPDATE login_id SET contracts_date_end = (?) WHERE id = (?)", (message.text, message.chat.id))

    connect.commit()
    
    cursor.execute(f"SELECT contracts_date_start, contracts_date_end, inn, company_name FROM login_id WHERE id = {message.chat.id}")
    connect.commit()

    user_info = cursor.fetchone()

    date_start = datetime.strptime(user_info[0], "%d-%m-%Y").strftime("%Y-%m-%d")
    
    date_end = datetime.strptime(user_info[1], "%d-%m-%Y").strftime("%Y-%m-%d")

    # Запрос api по госконтрактам ======================================================
    response = requests.get(
        f'https://api.damia.ru/zakupki/contracts?inn={user_info[2]}&fz=44&format=2&from_date={date_start}&to_date={date_end}&key={damia_contracts_api_key}').text

    contracts_list = f'<h1>Информация о участии {user_info[3]} в госконтрактах c {date_start} до {date_end}:</h1>\n\n<hr>\n\n'

    json_object = json.loads(response)

    # Если нет контрактов или неверная дата вывести что не найдено
    try:
        for number, contract in json_object[user_info[2]].items():

            contract_number = number
            contract_date_pub = contract['ДатаПубл']
            contract_customer_inn = contract['ЗаказчикИНН']
            contract_sum = f'{contract["Цена"]["Сумма"]} {contract["Цена"]["ВалютаКод"]}'
            contract_product = f'ОКПД: {contract["Продукт"]["ОКПД"]}\n{contract["Продукт"]["Название"]}'
            if contract['Статус']['Статус'] == 'Исполнение завершено':
                contract_status = ' Исполнение завершено'
            else:
                contract_status = ' Исполнение прекращено'
            contract_status_date = contract['Статус']['Дата']

            contracts_list += f'📃 <b>Госконтракт №{contract_number}</b>\n├ <b>Дата публикации контракта:</b> {contract_date_pub}\n├ <b>ИНН Заказчика:</b> {contract_customer_inn}\n├ <b>Сумма контракта:</b> {contract_sum}\n├ <b>Продукт:</b> {contract_product}\n├ <b>Статус контракта:</b> {contract_status}\n└ <b>Дата статуса контракта:</b> {contract_status_date}\n\n<hr>\n\n'

    
        # Генерация уникального имени файла для последующего удаления
        filename = r"Госконтракты_" + str(uuid.uuid4())

        with open(f'{filename}.html', "wb") as f:

            ready_text  = "<html><head><meta charset='utf-8'/><style>.html {box-sizing: border-box;} * {margin: 0;font-family: Helvetica, sans-serif; box-sizing: border-box;} body {margin: 0; min-width: 320px; padding: 20px}</style><title>Output Data in an HTML file\n \
        </title>\n</head> <body>"  + contracts_list + "</body></html>"

            f.write(ready_text.replace("\n", "<br>").replace("\t", "&nbsp;").encode("UTF-8"))

        doc_file = open(f'{filename}.html', 'r', encoding="utf-8")

        bot.send_document(message.chat.id, doc_file, reply_markup=markup)

        doc_file.close()

        os.remove(f'{filename}.html')

    except:
        bot.send_message(message.chat.id, "Информация о госконтрактах не найдена!", reply_markup=markup)



# Продолжение бух отчетности =======================
# БД ЧЕК ✅
def show_full_fin_report(message):
    
    cursor.execute(f"SELECT inn FROM login_id WHERE id = {message.chat.id}")
    connect.commit()

    user_info = cursor.fetchone()

    response = requests.get(
        f'https://api-fns.ru/api/bo?req={user_info[0]}&key={fns_api_key}').text

    json_object = json.loads(response)

    report_text = f'<b>Бухгалтерская отчётность по кодам и значениям за {message.text} год\nЕдиницы измерения: тыс. руб.</b>\n\n'

    try:
        for code, value in json_object[user_info[0]][message.text].items():
            report_text += f"{code} : {value}\n"

    except:
        report_text += 'Данные не найдены'

    # Отправлять несколько сообщений если оно слишком большое
    if len(report_text) > 4096:
        for x in range(0, len(report_text), 4096):
            bot.send_message(
                message.chat.id, report_text[x:x+4096], parse_mode='html')
    else:
        bot.send_message(message.chat.id, report_text, parse_mode='html')

    excel_file = open('account_codes.xls', 'rb')

    bot.send_document(message.chat.id, excel_file, reply_markup=markup)

    excel_file.close()

# try:
bot.polling(none_stop=True)
# except:
#     restart()
