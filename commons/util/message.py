from typing import List

import telegram

from telegram import TelegramError
from telegram.ext import Updater, CommandHandler


def send_telegram_message(messages: List, token: str):
    bot = telegram.Bot(token)

    try:
        updates = bot.get_updates()
        if len(updates) == 0:
            raise RuntimeError('Telegram chat is not started.')

        chat_id = updates[-1].message.chat_id
        bot.send_message(chat_id=chat_id, text='\n\n'.join(messages))
        # bot.close()
    except (AttributeError, TelegramError, IndexError) as err:
        raise RuntimeError(err)


# updater = Updater(token="1703653403:AAEkKXwP2ovlW2rBmrApsHtW5lT49RNkuZI", use_context=True)
# dispatcher = updater.dispatcher
#
#
# def start(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="I am a bot, please talk to me.")
#
#
# start_handler = CommandHandler('start', start)
# dispatcher.add_handler(start_handler)
#
# updater.start_polling()

#
# if "__main__" == __name__:
#     send_telegram_message(["hello", "world"], token="1703653403:AAEkKXwP2ovlW2rBmrApsHtW5lT49RNkuZI")