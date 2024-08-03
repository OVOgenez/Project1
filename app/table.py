import asyncio
import gspread

import app.scrapper as scrapper

gc = gspread.service_account("service_account.json")


def _initTable(name: str, title: str, data: list[scrapper.SiteData]) -> str:
    spreadsheet = gc.create(name, "142kbbNhkNkte5dx0Dg-r6zq-60pL3y7L")
    worksheet = spreadsheet.sheet1
    worksheet.update_title(title)
    worksheet.update([["URL", "TITLE", "DESCRIPTION", "EMAILS"]] + [[i.url, i.title, i.description, *i.emails] for i in data])
    spreadsheet.share("", perm_type="anyone", role="reader", with_link=True)
    return spreadsheet.url

async def initTable(name: str, title: str, data: list[scrapper.SiteData]) -> str:
    return await asyncio.to_thread(_initTable, name, title, data)
