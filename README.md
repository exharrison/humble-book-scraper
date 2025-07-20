# Humble Book Scraper

A Python script for scraping book information from Humble Bundle book bundles and checking ownership status against existing catalogs.

## Overview

The Humble Book Scraper is a powerful tool designed to extract detailed information about books from Humble Bundle book bundles. It can scrape book titles, authors, formats, and cover images, then optionally check if you already own these books by comparing against your existing Humble Bundle and Fanatical catalogs.

## Features

- **Web Scraping**: Uses Playwright to scrape Humble Bundle pages and extract book information
- **Ownership Checking**: Compares scraped books against your existing catalogs to determine ownership status
- **Smart Title Matching**: Advanced title normalization and fuzzy matching for accurate ownership detection
- **Volume Range Expansion**: Automatically expands volume ranges (e.g., "Vol. 1-3" becomes individual volumes)
- **Multiple Output Formats**: Generates both plain text and JSON output files
- **Author Matching**: Uses author information to improve ownership detection accuracy
- **Bundle Tracking**: Tracks which bundles contain each book for reference

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone or download the script files** to your desired directory

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

### Dependencies

The script requires the following Python packages:
- `requests` - HTTP library for web requests
- `beautifulsoup4` - HTML parsing library
- `playwright` - Browser automation for web scraping
- `rapidfuzz` - Fuzzy string matching for title comparison

## Usage

### Basic Usage

Scrape a Humble Bundle without checking ownership:

```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/your-bundle-url"
```

### With Ownership Checking

Scrape a Humble Bundle and check ownership against your catalogs:

```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/your-bundle-url" --check-owned /path/to/humble_catalog.json /path/to/fanatical_catalog.json
```

### Using the Shell Script

For convenience, you can use the provided shell script:

1. **Edit the script** (`run_scraper.sh`) to set your desired URL and catalog paths:
   ```bash
   # Edit this URL to scrape a different Humble Bundle
   HUMBLE_URL="https://www.humblebundle.com/books/your-bundle-url"
   
   # Edit these paths to point to your catalog files
   HUMBLE_CATALOG="/path/to/your/humble_catalog.json"
   FANATICAL_CATALOG="/path/to/your/fanatical_catalog.json"
   ```

2. **Run the script**:
   ```bash
   # Basic scraping
   ./run_scraper.sh
   
   # With ownership checking
   ./run_scraper.sh --check-owned
   ```

## Output Files

The script generates several output files in the `humble-book-scraper/` directory:

### 1. `book_titles.txt`
A plain text file containing all book titles with ownership status markers:
```
Saga Vol. 1 [OWNED]
Saga Vol. 2 [OWNED]
Paper Girls Vol. 1 [PROBABLY OWNED]
New Book Title [MAYBE OWNED]
Another Book Title
```

### 2. `{bundle-name}.json`
A detailed JSON file containing comprehensive book information:
```json
{
  "bundle_title": "Humble Comics Bundle: Example Bundle",
  "books": [
    {
      "title": "Book Title",
      "authors": ["Author Name"],
      "format": "PDF, ePUB, MOBI, PRC, and CBZ",
      "image_url": "https://example.com/cover.jpg",
      "ownership_status": "owned",
      "matched_bundles": ["Bundle Name 1", "Bundle Name 2"]
    }
  ]
}
```

### 3. `page_dump.html`
A temporary HTML file containing the scraped page content (for debugging purposes).

## Ownership Status Levels

When ownership checking is enabled, books are categorized into four levels:

- **`owned`**: Exact title match found in your catalogs
- **`probably owned`**: High-confidence match using advanced normalization
- **`maybe owned`**: Fuzzy match with 90%+ similarity score
- **`not owned`**: No match found in your catalogs

## Catalog File Formats

### Humble Bundle Catalog Format
```json
{
  "bundles": [
    {
      "human_name": "Bundle Name",
      "books": [
        {
          "Book Title": "Book Name",
          "Authors": ["Author 1", "Author 2"]
        }
      ]
    }
  ]
}
```

### Fanatical Catalog Format
```json
[
  {
    "title": "Book Name",
    "authors": ["Author 1", "Author 2"]
  }
]
```

## Technical Details

### Title Normalization

The script uses multiple levels of title normalization for accurate matching:

1. **Basic Normalization**: Removes punctuation, standardizes volume indicators
2. **Advanced Normalization**: Removes possessives, edition words, diacritics
3. **Subtitle Removal**: Strips subtitles after colons or volume numbers
4. **Fuzzy Matching**: Uses RapidFuzz for similarity scoring

### Volume Range Expansion

The script automatically expands volume ranges:
- "Vol. 1-3" → "Vol. 1", "Vol. 2", "Vol. 3"
- "Volumes 1-5" → "Vol. 1", "Vol. 2", "Vol. 3", "Vol. 4", "Vol. 5"

### Web Scraping Process

1. Uses Playwright to load the Humble Bundle page
2. Waits for dynamic content to load
3. Extracts book information from HTML elements
4. Saves page content for parsing with BeautifulSoup
5. Processes each book item to extract title, authors, format, and image URL

## Troubleshooting

### Common Issues

1. **Playwright Installation**: If you encounter browser-related errors, ensure Playwright is properly installed:
   ```bash
   playwright install chromium
   ```

2. **Permission Errors**: Make sure the script has write permissions in the output directory

3. **Catalog File Errors**: Verify your catalog files are valid JSON and follow the expected format

4. **Network Issues**: The script requires internet access to scrape Humble Bundle pages

### Debug Mode

To debug scraping issues, check the generated `page_dump.html` file to see what content was actually scraped from the page.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the script.

## License

This script is provided as-is for personal use. Please respect Humble Bundle's terms of service when using this tool. 