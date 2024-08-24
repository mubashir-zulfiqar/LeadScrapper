import pandas as pd
import re


# Function to check if a string is a valid URL
def is_valid_url(url):
    # A basic URL pattern, you can use more complex patterns if needed
    pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(pattern, url) is not None


# Path to the Excel file
file_path = 'websites_list.xlsx'

try:
    # Read the Excel file
    df = pd.read_excel(file_path, engine='openpyxl')

    # Create an empty list to store URLs
    urls = []

    # Iterate through each cell in the dataframe
    for column in df.columns:
        for cell in df[column]:
            if pd.notna(cell) and isinstance(cell, str) and is_valid_url(cell):
                urls.append(cell)

    # Remove duplicates if necessary
    urls = list(set(urls))

    # Print or save the collected URLs
    print("Collected URLs:")
    for url in urls:
        print(url)

    # Optionally, save URLs to a new Excel file
    urls_df = pd.DataFrame(urls, columns=['URLs'])
    urls_df.to_excel('collected_urls.xlsx', index=False)

except Exception as e:
    print(f"An error occurred: {e}")
