import asyncio

from aiogram import F, html, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart, CommandObject

import app.scrapper as scrapper
import app.table as table

router = Router()
semaphore = asyncio.Semaphore()

TASKS: dict[tuple[int, int]: asyncio.Task] = {}


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


async def long_process(message: Message, query: str):
    async with semaphore:
        try:
            chat_id = message.chat.id
            message_id = message.message_id
            emails = await scrapper.scrappQuery(query)
            link = await table.initTable(f"{chat_id}_{message_id}", query, emails)
            text = [
                f"{html.bold("Query:")} {query}",
                f"",
                f"✅ {html.bold("Completed:")} {link}",
            ]
            if (chat_id, message_id) in TASKS:
                del TASKS[(chat_id, message_id)]
                await message.edit_text(
                    text="\n".join(text),
                    reply_markup=None,
                    disable_web_page_preview=True
                )
        # except asyncio.CancelledError:
        except:
            pass


@router.message(Command("search"))
async def search_command_handler(message: Message, command: CommandObject) -> None:
    if command.args:
        query = command.args
        text = [
            f"{html.bold("Query:")} {query}",
            f"",
            f"⏳ {html.bold("Executing...")}",
        ]
        reply = await message.reply(
            text="\n".join(text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Abort", callback_data="abort")
            ]])
        )
        chat_id = reply.chat.id
        message_id = reply.message_id
        TASKS[(chat_id, message_id)] = asyncio.create_task(long_process(reply, query))
    else:
        await message.reply(html.bold("Empty query."))


@router.callback_query(F.data == "abort")
async def abort_callback_query_handler(callback_query: CallbackQuery):
    message = callback_query.message
    chat_id = message.chat.id
    message_id = message.message_id
    if (chat_id, message_id) in TASKS:
        query = message.text.split("\n", 1)[0].split(": ", 1)[-1]
        TASKS.pop((chat_id, message_id)).cancel()
        text = [
            f"{html.bold("Query:")} {query}",
            f"",
            f"❌ {html.bold("Aborted.")}",
        ]
        await message.edit_text(
            text="\n".join(text),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Execute", callback_data="execute")
            ]])
        )
        await callback_query.answer(text="Process aborted")


@router.callback_query(F.data == "execute")
async def execute_callback_query_handler(callback_query: CallbackQuery):
    message = callback_query.message
    chat_id = message.chat.id
    message_id = message.message_id
    if (chat_id, message_id) not in TASKS:
        query = message.text.split("\n", 1)[0].split(": ", 1)[-1]
        TASKS[(chat_id, message_id)] = asyncio.create_task(long_process(message, query))
        text = [
            f"{html.bold("Query:")} {query}",
            f"",
            f"⏳ {html.bold("Executing...")}",
        ]
        await message.edit_text(
            text="\n".join(text),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Abort", callback_data="abort")
            ]])
        )
        await callback_query.answer(text="Process executed")
