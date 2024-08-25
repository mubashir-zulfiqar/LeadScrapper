# uptime_robot_test.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load UptimeRobot API key from environment variables
UPTIMEROBOT_API_KEY = os.getenv('UPTIMEROBOT_API_KEY')

def is_site_down(url):
    """
    Checks if the site is down using the UptimeRobot API.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the site is down, False otherwise.
    """
    api_url = "https://api.uptimerobot.com/v2/getMonitors"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'api_key': UPTIMEROBOT_API_KEY,
        'format': 'json',
        'urls': url
    }
    try:
        response = requests.post(api_url, headers=headers, data=payload)
        response.raise_for_status()
        result = response.json()

        monitors = result.get('monitors', [])
        if monitors:
            if monitors[0].get('status') == 2:  # Status 2 means the site is up
                print(f"Site {url} is up.")
                return False
            else:
                print(f"Site {url} is down.")
                return True
        print(f"No monitors found for {url}. Assuming site is down.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error checking site status: {e}")
        return False

if __name__ == "__main__":
    test_url = "http://www.google.com"  # Replace with the URL you want to test
    is_down = is_site_down(test_url)
    print(f"Is the site down? {'Yes' if is_down else 'No'}")