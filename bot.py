import logging


from telegram import Update,User, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, PicklePersistence, CallbackQueryHandler
from keyboa.keyboard import Keyboa

from openweather_api import *
from datetime import time, timedelta


import os
import pytz


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)



async def start(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user in context.bot_data["sub_list"]:
        await update.message.reply_text("Я тебя уже видел, хватит прикидываться")
    else:
        await update.message.reply_text("Привет, я бот, который буду присылать вас прогнозы погоды.\nЧтобы выбрать город, наберите команду /change\nЧтобы получить список команд, наберите команду /help")
        context.bot_data['sub_list'].add(update.effective_user)
        context.bot_data['sub_dict'][update.effective_user] = None
        context.bot_data['forecasts'][update.effective_user] = None


async def init_data(application: Application):
    if 'sub_list' not in application.bot_data:
        application.bot_data["sub_list"] = set()
    if 'sub_dict' not in application.bot_data:
        application.bot_data["sub_dict"] = dict()
    if 'forecasts' not in application.bot_data:
        application.bot_data["forecasts"] = dict()


async def choose_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите название вашего города")
    return 1


async def user_entered_place(update: Update, context: ContextTypes.DEFAULT_TYPE)->int:
    place = update.message.text
    if get_forecast(place):
        context.bot_data["sub_dict"][update.effective_user] = place
        context.bot_data["forecasts"][update.effective_user] = get_forecast(place)
        context.bot_data["forecasts"][update.effective_user].weathers = context.bot_data["forecasts"][update.effective_user].weathers[1::] 
        await update.message.reply_text("Город успешно выбран!")
        await get_closest_forecast(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Возникла ошибка :(\nВведите название города ещё раз")
        return 1


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отмена!")
    return ConversationHandler.END


async def update_forecast(context: ContextTypes.DEFAULT_TYPE):
    subs = context.bot_data["sub_list"]
    for sub in subs:
        context.bot_data["forecasts"][sub] = get_forecast(context.bot_data["sub_dict"][sub])

SUPERUSER = int(os.getenv("superuser"))


async def send_bot_data(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(SUPERUSER, f"Количество пользователей:{len(context.bot_data['sub_list'])}")


async def get_closest_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE)->int:
    if context.bot_data["sub_dict"][update.effective_user]:
        weather = context.bot_data["forecasts"][update.effective_user].weathers[0]
        res = "Прогноз на данный момент\n"
        res += "Местность: " + context.bot_data["sub_dict"][update.effective_user] + "\n"
        res += "Общее состояние: " + weather.status + "\nПодробное состояние: " + weather.detailed_status+"\n"
        res += "Температура (°C): " + str(weather.temperature("celsius")["temp"]) + ", по ощущениям: " + str(weather.temperature("celsius")["feels_like"]) + "\n"
        res += "Температура (°F): " + str(weather.temperature("fahrenheit")["temp"]) + ", по ощущениям: " + str(weather.temperature("fahrenheit")["feels_like"])+"\n"
        res += "Скорость ветра (м/с): " + str(weather.wind()["speed"]) + "\n"
        res += "Атмосферное давление (мм рт. ст.): " + str(weather.barometric_pressure()["press"]//1.33) + "\n"
        await update.message.reply_text(res)
    else:
        await update.message.reply_text("Вы не выбрали город. Введите команду /change")

async def send_3h_forecast(context: ContextTypes.DEFAULT_TYPE)->int:
    subs = context.bot_data["sub_list"]
    for sub in subs:
        if context.bot_data["forecasts"][sub]:
            weather = context.bot_data["forecasts"][sub].weathers[0]
            res = "Прогноз на ближайшее время\n"
            res += "Местность: " + context.bot_data["sub_dict"][sub] + "\n"
            res += "Общее состояние: " + weather.status + "\nПодробное состояние: " + weather.detailed_status+"\n"
            res += "Температура (°C): " + str(weather.temperature("celsius")["temp"]) + ", по ощущениям: " + str(weather.temperature("celsius")["feels_like"]) + "\n"
            res += "Температура (°F): " + str(weather.temperature("fahrenheit")["temp"]) + ", по ощущениям: " + str(weather.temperature("fahrenheit")["feels_like"])+"\n"
            res += "Скорость ветра (м/с): " + str(weather.wind()["speed"]) + "\n"
            res += "Атмосферное давление (мм рт. ст.): " + str(weather.barometric_pressure()["press"]//1.33) + "\n"
            context.bot_data["forecasts"][sub].weathers = context.bot_data["forecasts"][sub].weathers[1::] 
            await sub.send_message(res)
        else:
            await sub.send_message("Вы не выбрали город. Введите команду /change")


async def about(update:Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Данный бот был создан после неудачного попадания его создателя под дождь.\nНа основе данных с OpenWeather каждые 3 часа присылает прогноз погоды в выбранном городе.\nНадеюсь, что всё работает правильно\n\n\n2023 г."
    await update.message.reply_text(msg)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    A simple list of command
    '''
    commands = [
        '/help - команды',
        '/change - поменять город',
        '/closest - прогноз на ближайшее время',
        "/about - о боте и создателе"
    ]
    await update.message.reply_text('\n'.join(commands))



def main() -> None:
    token = os.getenv("BOT_TOKEN")
    my_persistence = PicklePersistence(filepath="data.bin")
    application = Application.builder().token(token).persistence(persistence=my_persistence).post_init(init_data).build()


    input_handler = ConversationHandler(
        entry_points=[CommandHandler("change", choose_place)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_entered_place)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )



    application.job_queue.run_daily(send_bot_data, time = time(13, 0, 0, tzinfo=pytz.timezone("Europe/Moscow")), name = "send_bot_data")
    application.job_queue.run_daily(update_forecast, time=time(0,0,0,tzinfo=pytz.timezone("Europe/Moscow")), name = "update_forecasts")
    for i in range(0, 24, 3):
        application.job_queue.run_daily(send_3h_forecast, time = time(i,0,0, tzinfo=pytz.timezone("Europe/Moscow")), name ="send_3h_forecast")
    application.add_handler(input_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("closest", get_closest_forecast))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("about", about))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()