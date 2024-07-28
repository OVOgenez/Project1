import asyncio
import aiohttp
from urllib.parse import urljoin
from googlesearch import search
from bs4 import BeautifulSoup
import re

REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


async def fetch_emails_from_page(session, url):
    emails = set()
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                for i in soup.strings:
                    emails.update(re.findall(REGEX, i))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return emails

async def fetch_emails_from_contact_pages(session, base_url):
    contact_pages = ["contact", "contact-us", "about", "about-us", "support", "help"]
    tasks = [fetch_emails_from_page(session, urljoin(base_url, f"/{page}")) for page in contact_pages]
    results = await asyncio.gather(*tasks)
    return set().union(*results)

async def process_site(session, site):
    email_dict = {site: []}
    main_page_task = fetch_emails_from_page(session, site)
    contact_page_task = fetch_emails_from_contact_pages(session, site)
    main_page_emails, contact_pages_emails = await asyncio.gather(main_page_task, contact_page_task)
    email_dict[site].extend(main_page_emails | contact_pages_emails)
    return email_dict

async def search_google(query, limit):
    return list(search(query, num_results=limit))

async def scrappQuery(query: str, limit: int = 10) -> dict:
    email_dict = {}
    async with aiohttp.ClientSession() as session:
        search_results = await search_google(query, limit)
        tasks = [process_site(session, site) for site in search_results]
        results = await asyncio.gather(*tasks)
        for result in results:
            email_dict.update(result)
    return email_dict


if __name__ == "__main__":
    emails = asyncio.run(scrappQuery("test"))
    print(emails)
