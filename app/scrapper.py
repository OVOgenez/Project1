import asyncio
import aiohttp
from bs4 import BeautifulSoup
import urllib
import re
import sys
import logging

CONTACTS = {"", "contact", "contact-us", "about", "about-us", "support", "help"}
EXTENSIONS = {"html", "css", "js", "php", "local", "webp", "mp3", "wav", "mp4", "avi", "avif", "svg", "png", "jpg", "jpeg", "gif", "bmp", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "zip", "rar", "7z"}
REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

class SiteData:
    def __init__(self, url, title = "", description = "", emails = set()):
        self.url = url
        self.title = title
        self.description = description
        self.emails = emails

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description}, emails={self.emails})"


def find_emails(data):
    emails = set()
    if isinstance(data, BeautifulSoup):
        for i in data.strings:
            emails.update(re.findall(REGEX, i))
    else:
        for i in re.findall(REGEX, data):
            if i.rsplit('.', 1)[-1].lower() not in EXTENSIONS:
                if i[:3] == "u00":
                    emails.add(i[5:])
                else:
                    emails.add(i)
    return emails
def find_emails_list(data: list):
    return [find_emails(i) for i in data]

def parse_html(data):
    return BeautifulSoup(data, "html.parser")

async def fetch_url(session, url, proxy=None, params=None, headers=None):
    try:
        async with session.get(url=url, proxy=proxy, params=params, headers=headers) as response:
            # logging.info(response.status)
            if response.status == 200:
                return await response.text()
    except Exception as e:
        # logging.info(e)
        pass
    return ""

async def process_site(session, site, black: set):
    root = urllib.parse.urlparse(site.url).netloc
    if root in black:
        htmls = await asyncio.gather(fetch_url(session, site.url))
    else:
        black.add(root)
        htmls = await asyncio.gather(fetch_url(session, site.url), *[fetch_url(session, urllib.parse.urljoin(site.url, f"/{i}")) for i in CONTACTS])
    emails = await asyncio.to_thread(find_emails_list, htmls)
    site.emails = set.union(*emails)
    return site

async def search_google(session, query, limit):

    def find_sites(soup):
        sites = []
        blocks = soup.find_all("div", attrs={"class": "g"})
        for block in blocks:
            _url = block.find("a", href=True)
            url = _url["href"] if _url else None
            if url:
                _title = block.find("h3")
                title = _title.text if _title else ""
                _description_box = block.find("div", {"style": "-webkit-line-clamp:2"})
                description = ""
                if _description_box:
                    _description = _description_box.find_all(recursive=False)
                    description = _description[-1].text if _description else ""
                sites.append(SiteData(url, title, description))
        return sites

    # _query = urllib.parse.quote_plus(query)
    start = 0
    while True:
        url = "https://www.google.com/search"
        proxy = None
        params = {
            "q": query,
            "num": min(100, limit - start + 2),
            "start": start,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        }
        html = await fetch_url(session, url, proxy, params, headers)
        soup = await asyncio.to_thread(parse_html, html)
        sites = await asyncio.to_thread(find_sites, soup)
        if len(sites) == 0:
            break
        yield sites
        start += len(sites)
        if start >= limit:
            break
        await asyncio.sleep(1)

async def scrappQuery(query: str, limit: int = 1000) -> list[SiteData]:
    results = []
    black = set()
    connector = aiohttp.TCPConnector(limit=100, ssl=False) 
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=True) as session:
        async for sites in search_google(session, query, limit):
            for i in range(0, len(sites), 10):
                sites_batch = sites[i:i + 10]
                tasks = [process_site(session, site, black) for site in sites_batch]
                results += await asyncio.gather(*tasks)
    return results

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, stream=sys.stdout)
#     asyncio.run(scrappQuery("Spécialiste des maisons en bois et saunas"))
