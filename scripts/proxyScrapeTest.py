import requests
import logging

API_KEY = 'mdvuejhmd7tgx9m7i1ob'
TEST_URL = 'http://www.google.com'
TIMEOUT = 5  # Timeout for proxy test

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

def test_proxies(proxies):
    """
    Tests the fetched proxies by making a request to a test URL.

    Args:
        proxies (list): List of proxy addresses to test.

    Returns:
        list: A list of working proxies.
    """
    working_proxies = []
    for proxy in proxies:
        proxy_url = f'http://{proxy}'
        proxies_dict = {
            'http': proxy_url,
            'https': proxy_url,
        }
        try:
            response = requests.get(TEST_URL, proxies=proxies_dict, timeout=TIMEOUT)
            if response.status_code == 200:
                logger.info(f"Proxy {proxy} is working")
                working_proxies.append(proxy)
            else:
                logger.warning(f"Proxy {proxy} failed with status code {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Proxy {proxy} failed: {e}")
    return working_proxies

if __name__ == "__main__":
    proxies = get_proxies()
    logger.info(f"Fetched {len(proxies)} proxies")
    working_proxies = test_proxies(proxies)
    logger.info(f"{len(working_proxies)} proxies are working")