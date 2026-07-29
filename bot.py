from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

conversation_manager = None


def set_conversation_manager(manager):

    global conversation_manager

    conversation_manager = manager


@dp.message(CommandStart())
async def start(message: Message):

    print(
        f"CHAT ID = {message.chat.id}, TYPE = {message.chat.type}"
    )

    if conversation_manager is None:
        return

    await conversation_manager.process_telegram_message(
        telegram_id=message.from_user.id,
        text="/start"
    )

@dp.message(F.text == "/groupid")
async def group_id(message: Message):

    await message.answer(
        f"ID этой группы:\n\n{message.chat.id}"
    )


@dp.message(F.text)
async def any_message(message: Message):

    if conversation_manager is None:
        return

    await conversation_manager.process_telegram_message(
        telegram_id=message.from_user.id,
        text=message.text
    )


@dp.callback_query()
async def any_callback(callback: CallbackQuery):

    if conversation_manager is None:
        await callback.answer()
        return

    await conversation_manager.process_callback(
        telegram_id=callback.from_user.id,
        data=callback.data
    )

    await callback.answer()


async def send_text(chat_id: int, text: str):

    await bot.send_message(
        chat_id=chat_id,
        text=text
    )


async def send_message(chat_id: int, text: str, reply_markup=None):

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )


async def run_bot():

    print()
    print("===============================")
    print("Telegram Bot Started")
    print("===============================")
    print()

    await dp.start_polling(bot)
