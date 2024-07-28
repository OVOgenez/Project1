import aiohttp
import asyncio
from urllib.parse import urljoin
from googlesearch import search
from bs4 import BeautifulSoup
import re
import csv
import io

regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


async def emailsToCSV(email_dict):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Website', 'Emails'])
    for site, emails in email_dict.items():
        writer.writerow([site, ', '.join(emails)])
    output.seek(0)
    return output


async def fetch_emails_from_page(session, url):
    emails = set()
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                for x in soup.strings:
                    emails.update(re.findall(regex, x))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return emails

async def fetch_emails_from_contact_pages(session, base_url):
    contact_pages = ['contact', 'contact-us', 'about', 'about-us', 'support', 'help']
    tasks = [fetch_emails_from_page(session, urljoin(base_url, f'/{page}')) for page in contact_pages]
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

async def scrappQuery(query, limit=10):
    email_dict = {}
    async with aiohttp.ClientSession() as session:
        search_results = await search_google(query, limit)
        tasks = [process_site(session, site) for site in search_results]
        results = await asyncio.gather(*tasks)
        for result in results:
            email_dict.update(result)
    return email_dict


if __name__ == "__main__":
    search_query = 'example query'
    emails_by_sites = asyncio.run(scrappQuery(search_query))
    print("Collected emails by site:", emails_by_sites)
    for k, v in emails_by_sites.items():
        print(k, " : ")
        for i in v:
            print(" ", i)
