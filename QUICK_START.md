# Quick Start Guide

Get up and running with the Humble Book Scraper in minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. Basic Usage (No Ownership Checking)

```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/your-bundle-url"
```

This will:
- Scrape the Humble Bundle page
- Extract all book information
- Save results to `book_titles.txt` and `{bundle-name}.json`

## 3. With Ownership Checking

First, prepare your catalog files:
- **Humble Bundle catalog**: JSON file with your owned Humble Bundle books
- **Fanatical catalog**: JSON file with your owned Fanatical books

Then run:
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/your-bundle-url" --check-owned /path/to/humble_catalog.json /path/to/fanatical_catalog.json
```

## 4. Using the Shell Script (Recommended)

1. Edit `run_scraper.sh`:
   ```bash
   # Set your Humble Bundle URL
   HUMBLE_URL="https://www.humblebundle.com/books/your-bundle-url"
   
   # Set your catalog file paths
   HUMBLE_CATALOG="/path/to/your/humble_catalog.json"
   FANATICAL_CATALOG="/path/to/your/fanatical_catalog.json"
   ```

2. Run:
   ```bash
   # Basic scraping
   ./run_scraper.sh
   
   # With ownership checking
   ./run_scraper.sh --check-owned
   ```

## Output Files

- `book_titles.txt` - Simple list with ownership status
- `{bundle-name}.json` - Detailed book information with metadata
- `page_dump.html` - Raw HTML for debugging

## Ownership Status

- `[OWNED]` - Definitely own this book
- `[PROBABLY OWNED]` - High confidence match
- `[MAYBE OWNED]` - Possible match
- No marker - Not found in your catalogs

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Look at `page_dump.html` if scraping fails
- Verify your catalog files are valid JSON 