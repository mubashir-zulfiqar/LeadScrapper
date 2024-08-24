import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def extract_emails_from_text(text):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    s = set(email_pattern.findall(text))
    logger.info(f"Extracted emails: {s}")
    return s

def extract_phone_numbers_from_text(text):
    phone_pattern = re.compile(r'\+?\d[\d -]{8,12}\d')
    s = set(phone_pattern.findall(text))
    logger.info(f"Extracted phone numbers: {s}")
    return s

def extract_contact_info(url, session):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract emails
        emails = extract_emails_from_text(response.text)
        for mailto in soup.find_all('a', href=True):
            if 'mailto:' in mailto['href']:
                email = mailto['href'].split('mailto:')[1]
                emails.add(email)

        # Extract phone numbers
        phones = extract_phone_numbers_from_text(response.text)

        return list(emails), list(phones), None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return [], [], str(e)

def get_sitemap_urls(url, session):
    sitemap_urls = set()
    sitemap_url = urljoin(url, '/sitemap.xml')  # Common sitemap URL
    logger.info(f"Fetching sitemap from {sitemap_url}")

    try:
        response = session.get(sitemap_url)
        response.raise_for_status()

        # Check if content is XML
        if 'xml' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(response.content, 'lxml-xml')  # Use 'lxml-xml' parser for XML
            for loc in soup.find_all('loc'):
                sitemap_urls.add(loc.text.strip())
            logger.info(f"Found {len(sitemap_urls)} URLs in sitemap")
        else:
            logger.warning("Sitemap is not in XML format")

    except requests.RequestException as e:
        logger.error(f"Error fetching sitemap: {e}")

    return sitemap_urls

def crawl_site(base_url, session):
    visited_urls = set()
    urls_to_visit = deque([base_url])
    all_emails = set()
    all_phones = set()

    logger.info(f"Starting crawl on {base_url}")

    while urls_to_visit:
        current_url = urls_to_visit.popleft()
        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        emails, phones, error = extract_contact_info(current_url, session)
        if error:
            logger.error(f"Error fetching {current_url}: {error}")
        all_emails.update(emails)
        all_phones.update(phones)

        # Fetch links from the current page
        try:
            response = session.get(current_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = urlparse(current_url).scheme + "://" + urlparse(current_url).hostname

            for link in soup.find_all('a', href=True):
                link_url = urljoin(base_url, link['href'])
                parsed_url = urlparse(link_url)

                # Filter out fragment-only URLs and ensure the URL is within the same domain
                if parsed_url.fragment:
                    continue

                if parsed_url.netloc == urlparse(base_url).netloc and link_url not in visited_urls and link_url not in urls_to_visit:
                    urls_to_visit.append(link_url)

        except requests.RequestException as e:
            logger.error(f"Error fetching links from {current_url}: {e}")

    logger.info(f"Crawl completed with {len(all_emails)} unique emails and {len(all_phones)} unique phones found")
    return list(all_emails), list(all_phones)

def main(input_file, output_file, max_sites=None):
    df = pd.read_excel(input_file, header=None)
    urls = df[0].dropna().tolist()  # Drop any NaN values
    if max_sites is not None:
        urls = urls[:max_sites]  # Limit the number of sites to process

    data = []
    total_sites = len(urls)
    start_time = time.time()

    for i, url in enumerate(urls):
        url = url.strip()  # Remove any leading/trailing whitespace
        if not url.startswith(('http://', 'https://')):
            data.append({
                'S/N': i + 1,
                'URL': url,
                'Emails': '',
                'Phones': '',
                'Error': 'Invalid URL (missing scheme)'
            })
            continue

        logger.info(f"Processing site {i + 1}/{total_sites}: {url}...")
        site_start_time = time.time()
        session = create_session()  # Create a session with retries and headers

        # First, try to get URLs from sitemap if available
        urls_from_sitemap = get_sitemap_urls(url, session)
        if urls_from_sitemap:
            logger.info(f"URLs obtained from sitemap: {len(urls_from_sitemap)}")
            for site_url in urls_from_sitemap:
                if site_url.startswith(('http://', 'https://')):
                    emails, phones = crawl_site(site_url, session)
                    data.append({
                        'S/N': i + 1,
                        'URL': site_url,
                        'Emails': ', '.join(emails),
                        'Phones': ', '.join(phones),
                        'Error': None
                    })
                else:
                    data.append({
                        'S/N': i + 1,
                        'URL': site_url,
                        'Emails': '',
                        'Phones': '',
                        'Error': 'Invalid URL (missing scheme)'
                    })
        else:
            emails, phones = crawl_site(url, session)
            error = None
            if not emails and not phones:
                error = "No contact info found or error occurred during crawling"

            data.append({
                'S/N': i + 1,
                'URL': url,
                'Emails': ', '.join(emails),
                'Phones': ', '.join(phones),
                'Error': error
            })

        site_end_time = time.time()
        time_consumed = site_end_time - site_start_time
        logger.info(f"Time consumed for site {i + 1}: {time_consumed:.2f} seconds")

    end_time = time.time()
    total_time = end_time - start_time
    average_time_per_site = total_time / len(urls) if urls else 0
    expected_completion_time = average_time_per_site * total_sites

    logger.info(f"Total time consumed: {total_time:.2f} seconds")
    logger.info(f"Estimated time to complete: {expected_completion_time:.2f} seconds")

    output_df = pd.DataFrame(data)
    output_df.to_excel(output_file, index=False)
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    input_file = 'collected_urls.xlsx'  # Replace with your input file path
    output_file = 'contact_details.xlsx'  # Replace with your desired output file path
    max_sites = 5  # Limit to processing 5 sites; set to None for no limit
    main(input_file, output_file, max_sites)