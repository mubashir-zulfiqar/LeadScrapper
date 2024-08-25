import requests
import random
import time

API_KEY = 'mdvuejhmd7tgx9m7i1ob'
TIMEOUT = 20  # Increase timeout value
RETRIES = 3  # Number of retries

# Function to get a list of proxies from ProxyScrape
def get_proxies():
    response = requests.get(f'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&apikey={API_KEY}')
    proxies = response.text.split('\n')
    return [proxy.strip() for proxy in proxies if proxy.strip()]

# Function to fetch URL using a random proxy from ProxyScrape with retry logic
def fetch_url_with_random_proxy(url):
    proxies = get_proxies()
    if not proxies:
        print("No proxies available")
        return None

    for attempt in range(RETRIES):
        proxy = random.choice(proxies)
        proxy_url = f'http://{proxy}'
        proxy_dict = {
            'http': proxy_url,
            'https': proxy_url,
        }
        print(f"Attempt {attempt + 1}: Using proxy {proxy}")

        try:
            response = requests.get(url, proxies=proxy_dict, timeout=TIMEOUT)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(2)  # Wait before retrying

    print("All attempts failed")
    return None

# Example usage
def main():
    url = "http://google.com"
    content = fetch_url_with_random_proxy(url)
    if content:
        print(f"Successfully fetched content from {url}")

if __name__ == "__main__":
    main()