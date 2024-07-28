import asyncio
import gspread

gc = gspread.service_account("service_account.json")


async def initTable(name: str, data: dict) -> str:
    spreadsheet = gc.create(name, "142kbbNhkNkte5dx0Dg-r6zq-60pL3y7L")
    worksheet = spreadsheet.sheet1
    worksheet.update([[k] + v for k, v in data.items()])
    spreadsheet.share("", perm_type="anyone", role="reader", with_link=True)
    return spreadsheet.url

if __name__ == "__main__":
    url = asyncio.run(initTable("test", {"1":["a","b"],"2":["c","d","e"]}))
    print(url)
