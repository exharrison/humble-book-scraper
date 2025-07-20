#!/bin/bash

# TEMPLATE SCRIPT for humble-book-scraper
# Copy this file to run_scraper.sh and edit the variables below for your setup.

# Edit this URL to scrape a different Humble Bundle
HUMBLE_URL="https://www.humblebundle.com/books/your-bundle-url"

# Edit these paths to point to your catalog files
HUMBLE_CATALOG="/path/to/your/humble_catalog.json"
FANATICAL_CATALOG="/path/to/your/fanatical_catalog.json"

if [[ "$1" == "--check-owned" ]]; then
    python3 scrape_humble_books.py "$HUMBLE_URL" --check-owned "$HUMBLE_CATALOG" "$FANATICAL_CATALOG"
else
    python3 scrape_humble_books.py "$HUMBLE_URL"
fi

# INSTRUCTIONS:
# 1. Copy this file to run_scraper.sh: cp run_scraper.template.sh run_scraper.sh
# 2. Edit run_scraper.sh to set your bundle URL and catalog paths.
# 3. Run ./run_scraper.sh or ./run_scraper.sh --check-owned 