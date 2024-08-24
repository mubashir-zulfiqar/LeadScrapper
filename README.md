# LeadScrapper

LeadScrapper is a collection of Python scripts designed to extract contact information (emails and phone numbers) from websites. The project includes several modules, each with a specific purpose, such as extracting URLs from an Excel sheet, crawling websites, and extracting contact information.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [UrlCollectorFromSheet](#urlcollectorfromsheet)
  - [PageLinksExtractor](#pagelinksextractor)
  - [ContactInfoExtractor](#contactinfoextractor)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/LeadScrapper.git
    cd LeadScrapper
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### UrlCollectorFromSheet

This script reads URLs from an Excel file and validates them.

#### Usage

1. Place your Excel file containing URLs in the project directory.
2. Update the `file_path` variable in `UrlCollectorFromSheet.py` to the path of your Excel file.
3. Run the script:
    ```sh
    python UrlCollectorFromSheet.py
    ```

#### Example

# Path to the Excel file
file_path = 'websites_list.xlsx'

# PageLinksExtractor

This script crawls a website to extract all internal links.

## Usage

1. **Update the `website_url` Variable**

   Open the `PageLinksExtractor.py` file and update the `website_url` variable to the URL of the website you want to crawl.

   ```python
   if __name__ == "__main__":
       # Replace this URL with the website you want to scrape
       website_url = "https://www.example.com/"
       main(website_url)


# ContactInfoExtractor

This script extracts contact information (emails and phone numbers) from a list of websites.

## Usage

1. **Prepare Your Input File**

   Place your input Excel file containing URLs in the project directory.

2. **Update File Paths**

   Open the `ContactInfoExtractor.py` file and update the `input_file` and `output_file` variables to the paths of your input and output Excel files.

   ```python
   if __name__ == "__main__":
       input_file = 'collected_urls.xlsx'  # Replace with your input file path
       output_file = 'contact_details.xlsx'  # Replace with your desired output file path
       max_sites = 5  # Limit to processing 5 sites; set to None for no limit
       main(input_file, output_file, max_sites)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
