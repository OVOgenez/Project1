import asyncio

from aiogram import F, html, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart, CommandObject

import app.scrapper as scrapper
import app.table as table

router = Router()
semaphore = asyncio.Semaphore()

# PROCESSES: dict[tuple[int, int, int]: asyncio.Task] = {}

STATES = {}
TASKS = {}


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


async def long_process(user_id: int, message_id: int):
    async with semaphore:
        try:
            data = STATES[(user_id, message_id)]
            emails = await scrapper.scrappQuery(data["query"])
            url = await table.initTable(f"{user_id}_{message_id}", data["query"], emails)
            if STATES.get((user_id, message_id), {}).get("state") == "processing":
                await STATES[(user_id, message_id)]["message"].edit_text(
                    text=f"Процесс завершен: {url}",
                    reply_markup=None,
                    disable_web_page_preview=True
                )
            if (user_id, message_id) in TASKS:
                del TASKS[(user_id, message_id)]
            if (user_id, message_id) in STATES:
                del STATES[(user_id, message_id)]
        # except asyncio.CancelledError:
        except:
            pass


@router.message(Command("call"))
async def call_command_handler(message: Message, command: CommandObject) -> None:
    if command.args:
        reply = await message.reply(
            text="Идет процесс обработки...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]])
        )
        user_id = message.from_user.id
        message_id = reply.message_id
        STATES[(user_id, message_id)] = {"message": reply, "query": command.args, "state": "processing"}
        TASKS[(user_id, message_id)] = asyncio.create_task(long_process(user_id, message_id))
    else:
        await message.reply("Нет аргументов.")


@router.callback_query(F.data == "cancel")
async def process_callback_cancel(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    if STATES.get((user_id, message_id), {}).get("state") == "processing":
        STATES[(user_id, message_id)]["state"] = "cancelled"
        await callback_query.message.edit_text(
            text="Процесс был отменен. Нажмите 'Запуск', чтобы начать снова.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Запуск", callback_data="execute")
            ]])
        )
        await callback_query.answer(text="Процесс отменен")
        if (user_id, message_id) in TASKS:
            TASKS[(user_id, message_id)].cancel()
            del TASKS[(user_id, message_id)]


@router.callback_query(F.data == "execute")
async def process_callback_execute(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    if STATES.get((user_id, message_id), {}).get("state") == "cancelled":
        STATES[(user_id, message_id)]["state"] = "processing"
        await callback_query.message.edit_text(
            text="Идет процесс обработки...",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]])
        )
        await callback_query.answer(text="Процесс начат заново")
        TASKS[(user_id, message_id)] = asyncio.create_task(long_process(user_id, message_id))
