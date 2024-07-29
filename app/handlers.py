from asyncio import sleep, create_task, CancelledError

from aiogram import F, html, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart, CommandObject

import app.scrapper as scrapper
import app.table as table

router = Router()

STATES = {}
TASKS = {}


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


async def long_process(user_id: int, message_id: int):
    try:
        data = STATES[(user_id, message_id)]
        emails = await scrapper.scrappQuery(data["query"], data["limit"])
        url = await table.initTable(f"{user_id}_{message_id}", emails)
        if STATES.get((user_id, message_id), {}).get("state") == "processing":
            await STATES[(user_id, message_id)]["msg"].edit_text(
                text=f"Процесс завершен:\n{url}",
                reply_markup=None,
                disable_web_page_preview=True
            )
        if (user_id, message_id) in TASKS:
            del TASKS[(user_id, message_id)]
        if (user_id, message_id) in STATES:
            del STATES[(user_id, message_id)]
    except CancelledError:
        pass


@router.message(Command("call"))
async def call_command_handler(message: Message, command: CommandObject) -> None:
    if command.args:
        parts = command.args.rsplit(maxsplit=1)
        if len(parts) == 2:
            p1, p2 = parts
            user_id = message.from_user.id
            message_id = message.message_id
            TASKS[(user_id, message_id)] = create_task(long_process(user_id, message_id))
            STATES[(user_id, message_id)] = {"state": "processing", "query": p1, "limit": int(p2)}
            msg = await message.reply(
                text="Идет процесс обработки...",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Отмена", callback_data=f"cancel_{message_id}")
                ]])
            )
            STATES[(user_id, message_id)]["msg"] = msg
        else:
            await message.reply("Пожалуйста, укажите запрос и лимит.")
    else:
        await message.reply("Нет аргументов.")


@router.callback_query(F.data.startswith("cancel_"))
async def process_callback_cancel(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = int(callback_query.data.split("_")[1])
    if STATES.get((user_id, message_id), {}).get("state") == "processing":
        STATES[(user_id, message_id)]["state"] = "cancelled"
        await callback_query.message.edit_text(
            text="Процесс был отменен. Нажмите 'Запуск', чтобы начать снова.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Запуск", callback_data=f"execute_{message_id}")
            ]])
        )
        await callback_query.answer(text="Процесс отменен")
        if (user_id, message_id) in TASKS:
            TASKS[(user_id, message_id)].cancel()
            del TASKS[(user_id, message_id)]


@router.callback_query(F.data.startswith("execute_"))
async def process_callback_execute(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = int(callback_query.data.split("_")[1])
    if STATES.get((user_id, message_id), {}).get("state") == "cancelled":
        STATES[(user_id, message_id)]["state"] = "processing"
        await callback_query.message.edit_text(
            text="Идет процесс обработки...",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"cancel_{message_id}")
            ]])
        )
        await callback_query.answer(text="Процесс начат заново")
        TASKS[(user_id, message_id)] = create_task(long_process(user_id, message_id))
