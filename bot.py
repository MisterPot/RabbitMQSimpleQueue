import json
import signal
import asyncio
import os
import logging

import aiogram.types
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv
import pika

from cons import connection_params


load_dotenv()


dispatcher = Dispatcher()
token = os.environ.get('BOT_KEY')
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue='0')


@dispatcher.message(CommandStart())
async def start(message: aiogram.types.Message) -> None:
    await message.answer("""
        Hello !
        Here few commands :
        /print
        /send
    """)


@dispatcher.message(Command('print'))
async def commit_print(message: aiogram.types.Message) -> None:
    channel.basic_publish(
        exchange='',
        routing_key='0',
        body=json.dumps({
            "command": 'print',
            "data": {"message": message.text}
        })
    )
    await message.answer('Command `print` committed !')


@dispatcher.message(Command('send'))
async def commit_send(message: aiogram.types.Message) -> None:
    channel.basic_publish(
        exchange='',
        routing_key='0',
        body=json.dumps({
            "command": 'send',
            'data': message.model_dump(mode='json')
        })
    )
    await message.answer('Command `send` committed !')


async def start_bot() -> None:
    bot = Bot(parse_mode=ParseMode.HTML, token=token)

    def stop_bot(*_) -> None:
        task = asyncio.create_task(
            coro=dispatcher.stop_polling()
        )
        connection.close()
        task.add_done_callback(lambda _: print('Bot stopped !'))

    signal.signal(signal.SIGINT, stop_bot)
    signal.signal(signal.SIGILL, stop_bot)

    print('Bot ready !')

    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(start_bot())