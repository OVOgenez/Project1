import aiohttp
import asyncio
from urllib.parse import urljoin
from googlesearch import search
from bs4 import BeautifulSoup
import re
import csv
import io

regex = re.compile(
    r"(?i)"  # Case-insensitive matching
    r"(?:[A-Z0-9!#$%&'*+/=?^_`{|}~-]+"  # Unquoted local part
    r"(?:\.[A-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"  # Dot-separated atoms in local part
    r"|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]"  # Quoted strings
    r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")"  # Escaped characters in local part
    r"@"  # Separator
    r"[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?"  # Domain name
    r"\.(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)+"  # Top-level domain and subdomains
)


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
                emails.update(re.findall(regex, soup.get_text()))
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
