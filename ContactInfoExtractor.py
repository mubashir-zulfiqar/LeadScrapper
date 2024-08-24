import logging
import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

API_KEY = 'mdvuejhmd7tgx9m7i1ob'
TIMEOUT = 20  # Increase timeout value
RETRIES = 3  # Number of retries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_proxies():
    """
    Fetches a list of proxies from ProxyScrape.

    Returns:
        list: A list of proxy addresses.
    """
    response = requests.get(f'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&apikey={API_KEY}')
    proxies = response.text.split('\n')
    return [proxy.strip() for proxy in proxies if proxy.strip()]

def create_session():
    """
    Creates a requests.Session with custom headers and retry logic.

    Returns:
        requests.Session: Configured session with user-agent header and retry logic.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_with_proxy(session, url):
    """
    Fetches the URL using the session, retries with proxies if blocked.

    Args:
        session (requests.Session): The session to use for making requests.
        url (str): The URL to fetch.

    Returns:
        requests.Response: The response object.
    """
    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.warning(f"Initial request failed: {e}")
        proxies = get_proxies()
        for attempt in range(RETRIES):
            if not proxies:
                break
            proxy = random.choice(proxies)
            proxy_url = f'http://{proxy}'
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url,
            }
            logger.info(f"Attempt {attempt + 1}: Using proxy {proxy}")
            try:
                response = session.get(url, timeout=TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request with proxy {proxy} failed: {e}")
                time.sleep(2)  # Wait before retrying
        raise requests.RequestException("All attempts failed")

def extract_emails_from_text(text):
    """
    Extracts email addresses from the given text using regex and BeautifulSoup.

    Args:
        text (str): The text content to search for email addresses.

    Returns:
        set: A set of extracted email addresses.
    """
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emails = set(email_pattern.findall(text))

    # Extract emails from mailto links
    soup = BeautifulSoup(text, 'html.parser')
    for mailto in soup.find_all('a', href=True):
        if 'mailto:' in mailto['href']:
            email = mailto['href'].split('mailto:')[1]
            emails.add(email)

    logger.info(f"Extracted emails: {emails}")
    return emails

def extract_phone_numbers_from_text(text):
    """
    Extracts phone numbers from the given text using regex.

    Args:
        text (str): The text content to search for phone numbers.

    Returns:
        set: A set of extracted phone numbers.
    """
    phone_pattern = re.compile(
        r'(\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})|'  # US, Canada
        r'(\+44[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # UK
        r'(\+61[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # Australia
        r'(\+49[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # Germany
        r'(\+33[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # France
        r'(\+91[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # India
        r'(\+86[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # China
        r'(\+55[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # Brazil
        r'(\+81[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # Japan
        r'(\+92[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})|'  # Pakistan
        r'(\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,9})'  # General valid-looking numbers
    )
    phone_numbers = set(phone_pattern.findall(text))

    # Flatten the tuples and filter out empty strings
    phone_numbers = {num for match in phone_numbers for num in match if num}

    logger.info(f"Extracted phone numbers: {phone_numbers}")
    return phone_numbers

def extract_contact_info(url, session):
    """
    Fetches the content of the given URL and extracts emails and phone numbers.

    Args:
        url (str): The URL to fetch content from.
        session (requests.Session): The session to use for making requests.

    Returns:
        tuple: A tuple containing lists of emails, phone numbers, and an error message (if any).
    """
    try:
        response = fetch_with_proxy(session, url)
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
    """
    Attempts to fetch a sitemap from the given URL and extracts URLs from it.

    Args:
        url (str): The base URL to fetch the sitemap from.
        session (requests.Session): The session to use for making requests.

    Returns:
        set: A set of URLs found in the sitemap.
    """
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
    """
    Crawls the given base URL and its internal links to extract emails and phone numbers.

    Args:
        base_url (str): The base URL to start crawling from.
        session (requests.Session): The session to use for making requests.

    Returns:
        tuple: A tuple containing lists of all unique emails and phone numbers found.
    """
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
            response = fetch_with_proxy(session, current_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = urlparse(current_url).scheme + "://" + urlparse(current_url).hostname

            for link in soup.find_all('a', href=True):
                link_url = urljoin(base_url, link['href'])
                parsed_url = urlparse(link_url)

                # Filter out fragment-only URLs and ensure the URL is within the same domain
                if parsed_url.fragment:
                    continue

                if parsed_url.netloc == urlparse(
                        base_url).netloc and link_url not in visited_urls and link_url not in urls_to_visit:
                    urls_to_visit.append(link_url)

        except requests.RequestException as e:
            logger.error(f"Error fetching links from {current_url}: {e}")

    logger.info(f"Crawl completed with {len(all_emails)} unique emails and {len(all_phones)} unique phones found")
    return list(all_emails), list(all_phones)

def main(input_file, output_file, max_sites=None):
    """
    Main function to read URLs from an input file, extract contact information, and save results to an output file.

    Args:
        input_file (str): Path to the input Excel file containing URLs.
        output_file (str): Path to the output Excel file to save results.
        max_sites (int, optional): Maximum number of sites to process. Defaults to None.
    """
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
    input_file = 'collected_urls-dev.xlsx'  # Replace with your input file path
    output_file = 'contact_details.xlsx'  # Replace with your desired output file path
    max_sites = 5  # Limit to processing 5 sites; set to None for no limit
    main(input_file, output_file, max_sites)