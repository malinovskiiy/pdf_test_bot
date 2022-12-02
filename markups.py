from telebot import types

# Кнопки для меню "назад" ===================================

markup = types.InlineKeyboardMarkup()
button_ul_back = types.InlineKeyboardButton("⬅️ Назад", callback_data='ul_back')
markup.add(button_ul_back)

ip_back_markup = types.InlineKeyboardMarkup()
button_ip_back = types.InlineKeyboardButton("⬅️ Назад", callback_data='ip_back')

ip_back_markup.add(button_ip_back)


# ====================================================================


# 7 кнопок для запросов в api для ЮЛ ===========================

main_bot_markup = types.InlineKeyboardMarkup()

button_block = types.InlineKeyboardButton("🔒 Блокировки счетов", callback_data='block')

button_one_day = types.InlineKeyboardButton("1️⃣ Проверка наличия признаков фирмы-однодневки", callback_data='one_day')

button_fin_report = types.InlineKeyboardButton("2️⃣ Проверка платёжеспособности", callback_data='fin_report')

button_fin_analysis = types.InlineKeyboardButton("3️⃣ Финансовый анализ", callback_data='fin_analysis')

button_pdf = types.InlineKeyboardButton("8️⃣ Выписка из ЕГРЮЛ", callback_data='pdf')

button_check_agent = types.InlineKeyboardButton("7️⃣ Негативные факторы контрагента", callback_data='check_agent')


button_fin_risk = types.InlineKeyboardButton("4️⃣ Оценка финансовых рисков", callback_data='fin_risk')

button_reputation = types.InlineKeyboardButton("5️⃣ Оценка репутации", callback_data='reputation')

button_check_changes = types.InlineKeyboardButton("6️⃣ Проверить изменения", callback_data='check_changes')

button_full_report = types.InlineKeyboardButton("9️⃣ Полный отчет", callback_data='full_report')




main_bot_markup.add(button_one_day)
main_bot_markup.add(button_fin_report)
main_bot_markup.add(button_fin_analysis)
main_bot_markup.add(button_fin_risk)
main_bot_markup.add(button_reputation)
main_bot_markup.add(button_check_changes)
main_bot_markup.add(button_check_agent)
main_bot_markup.add(button_pdf)
main_bot_markup.add(button_full_report)


# 7 кнопок для запросов в api для ИП ===========================

ip_bot_markup = types.InlineKeyboardMarkup()

ip_button_pdf = types.InlineKeyboardButton("Выписка из ЕГРИП", callback_data='ip_pdf')

ip_bot_markup.add(ip_button_pdf)

# Полная бух отчетность======================


full_fin_report_markup = types.InlineKeyboardMarkup()

button_full_fin_report = types.InlineKeyboardButton("📝 Посмотреть бухгалтерскую отчётность", callback_data='full_fin_report')

full_fin_report_markup.add(button_full_fin_report)
full_fin_report_markup.add(button_ul_back)



# Финансовый анализ (3 кнопки анализа)======================

fin_analysis_markup = types.InlineKeyboardMarkup()

financial_stability_button = types.InlineKeyboardButton("1️⃣ Финансовая устойчивость", callback_data='financial_stability')

solvency_button = types.InlineKeyboardButton("2️⃣ Платёжеспособность", callback_data='solvency')

efficiency_button = types.InlineKeyboardButton("3️⃣ Эффективность", callback_data='efficiency')

fin_analysis_markup.add(financial_stability_button)
fin_analysis_markup.add(solvency_button)
fin_analysis_markup.add(efficiency_button)
fin_analysis_markup.add(button_ul_back)

# Вернуться к выбору фин анализа =====================================

back_to_fin_report_start_markup = types.InlineKeyboardMarkup()
back_to_fin_report_start_button = types.InlineKeyboardButton("Назад к выбору анализа", callback_data='fin_analysis')
back_to_fin_report_start_markup.add(back_to_fin_report_start_button)

main_menu_markup = types.InlineKeyboardMarkup()
main_menu_button = types.InlineKeyboardButton("⬅️ В главное меню", callback_data='main_menu')
main_menu_markup.add(main_menu_button)


# Оценка репутации =====================================

reputation_markup = types.InlineKeyboardMarkup()

button_purchases = types.InlineKeyboardButton("💳 Проверить госзакупки", callback_data='purchases')

button_contracts = types.InlineKeyboardButton("📃 Проверить госконтракты", callback_data='contracts')

reputation_markup.add(button_purchases, button_contracts)
reputation_markup.add(button_ul_back)


# Финансовые риски =====================================

fin_risk_markup = types.InlineKeyboardMarkup()

button_arb = types.InlineKeyboardButton("👨‍⚖️ Арбитражные дела", callback_data='arb')
button_isp_report = types.InlineKeyboardButton("🧑‍⚖️ Исполнительные производства", callback_data='isp_report')

fin_risk_markup.add(button_arb)
fin_risk_markup.add(button_isp_report)
fin_risk_markup.add(button_ul_back)

# Однодневка =====================================

one_day_markup = types.InlineKeyboardMarkup()

one_day_markup.add(button_block)
one_day_markup.add(button_ul_back)