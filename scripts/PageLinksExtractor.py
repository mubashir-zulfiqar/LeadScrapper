import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sitemap_urls(url):
    sitemap_urls = set()
    sitemap_url = urljoin(url, '/sitemap.xml')  # Common sitemap URL
    logger.info(f"Fetching sitemap from {sitemap_url}")

    try:
        response = requests.get(sitemap_url)
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

def crawl_website(start_url):
    visited_urls = set()
    urls_to_visit = deque([start_url])
    all_links = set()

    logger.info(f"Starting crawl on {start_url}")

    while urls_to_visit:
        url = urls_to_visit.popleft()

        if url in visited_urls:
            continue

        visited_urls.add(url)
        logger.info(f"Visiting {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            base_url = urlparse(url).scheme + "://" + urlparse(url).hostname

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)

                # Filter out fragment-only URLs and ensure the URL is within the same domain
                if parsed_url.fragment:
                    continue

                if parsed_url.netloc == urlparse(start_url).netloc:
                    if full_url not in visited_urls and full_url not in urls_to_visit:
                        urls_to_visit.append(full_url)
                    all_links.add(full_url)

        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")

    logger.info(f"Crawl completed with {len(all_links)} unique URLs found")
    return all_links

def main(start_url):
    urls = get_sitemap_urls(start_url)
    # urls = None

    if not urls:
        logger.info("Sitemap not found or empty. Crawling website...")
        urls = crawl_website(start_url)

    for url in sorted(urls):
        print(url)
    logger.info("Processing completed")

if __name__ == "__main__":
    # Replace this URL with the website you want to scrape
    website_url = "https://www.opendining.net/"
    main(website_url)
