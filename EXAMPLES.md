# Usage Examples

This document provides practical examples of how to use the Humble Book Scraper in different scenarios.

## Example 1: Basic Scraping

### Command
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/comics-bundle-example"
```

### Output Files Generated

**`book_titles.txt`**:
```
Saga Vol. 1
Saga Vol. 2
Saga Vol. 3
Paper Girls Vol. 1
Paper Girls Vol. 2
Bitch Planet Vol. 1: Extraordinary Machine
Bitch Planet Vol. 2: President Bitch
Lady Mechanika Vol. 1
Lady Mechanika Vol. 2
Lady Mechanika Vol. 3

Total books: 10
```

**`comics-bundle-example.json`**:
```json
{
  "bundle_title": "Humble Comics Bundle: Example Bundle",
  "books": [
    {
      "title": "Saga Vol. 1",
      "authors": [
        "Written by: Brian K. Vaughan",
        "Art by: Fiona Staples"
      ],
      "format": "PDF, ePUB, MOBI, PRC, and CBZ",
      "image_url": "https://hb.imgix.net/example-cover.jpg"
    },
    {
      "title": "Saga Vol. 2",
      "authors": [
        "Written by: Brian K. Vaughan",
        "Art by: Fiona Staples"
      ],
      "format": "PDF, ePUB, MOBI, PRC, and CBZ",
      "image_url": "https://hb.imgix.net/example-cover.jpg"
    }
  ]
}
```

## Example 2: With Ownership Checking

### Command
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/comics-bundle-example" --check-owned /home/user/humble_catalog.json /home/user/fanatical_catalog.json
```

### Sample Catalog Files

**`humble_catalog.json`**:
```json
{
  "bundles": [
    {
      "human_name": "Humble Comics Bundle: Image Comics 30th Anniversary",
      "books": [
        {
          "Book Title": "Saga Vol. 1",
          "Authors": ["Brian K. Vaughan", "Fiona Staples"]
        },
        {
          "Book Title": "Saga Vol. 2",
          "Authors": ["Brian K. Vaughan", "Fiona Staples"]
        }
      ]
    }
  ]
}
```

**`fanatical_catalog.json`**:
```json
[
  {
    "title": "Paper Girls Vol. 1",
    "authors": ["Brian K. Vaughan"]
  }
]
```

### Output with Ownership Status

**`book_titles.txt`**:
```
Saga Vol. 1 [OWNED]
Saga Vol. 2 [OWNED]
Paper Girls Vol. 1 [OWNED]
Paper Girls Vol. 2
Bitch Planet Vol. 1: Extraordinary Machine [MAYBE OWNED]
Bitch Planet Vol. 2: President Bitch
Lady Mechanika Vol. 1
Lady Mechanika Vol. 2
Lady Mechanika Vol. 3

Total books: 9

--- Maybe Owned ---
Bitch Planet Vol. 1: Extraordinary Machine

--- Suspected Not Owned ---
Paper Girls Vol. 2
Bitch Planet Vol. 2: President Bitch
Lady Mechanika Vol. 1
Lady Mechanika Vol. 2
Lady Mechanika Vol. 3
```

**`comics-bundle-example.json`** (with ownership data):
```json
{
  "bundle_title": "Humble Comics Bundle: Example Bundle",
  "books": [
    {
      "title": "Saga Vol. 1",
      "authors": [
        "Written by: Brian K. Vaughan",
        "Art by: Fiona Staples"
      ],
      "format": "PDF, ePUB, MOBI, PRC, and CBZ",
      "image_url": "https://hb.imgix.net/example-cover.jpg",
      "ownership_status": "owned",
      "matched_bundles": [
        "Humble Comics Bundle: Image Comics 30th Anniversary"
      ]
    },
    {
      "title": "Paper Girls Vol. 1",
      "authors": ["Brian K. Vaughan"],
      "format": "PDF, ePUB, MOBI, PRC, and CBZ",
      "image_url": "https://hb.imgix.net/example-cover.jpg",
      "ownership_status": "owned",
      "matched_bundles": ["Fanatical Bundle"]
    }
  ]
}
```

## Example 3: Volume Range Expansion

### Input Bundle with Volume Ranges
A Humble Bundle containing:
- "Saga Vol. 1-3"
- "Paper Girls Vol. 1-2"
- "Bitch Planet Vol. 1-4"

### Output After Expansion
```
Saga Vol. 1
Saga Vol. 2
Saga Vol. 3
Paper Girls Vol. 1
Paper Girls Vol. 2
Bitch Planet Vol. 1
Bitch Planet Vol. 2
Bitch Planet Vol. 3
Bitch Planet Vol. 4

Total books: 9
```

## Example 4: Using the Shell Script

### Setup `run_scraper.sh`
```bash
#!/bin/bash

# Edit this URL to scrape a different Humble Bundle
HUMBLE_URL="https://www.humblebundle.com/books/comics-bundle-example"

# Edit these paths to point to your catalog files
HUMBLE_CATALOG="/home/user/humble_catalog.json"
FANATICAL_CATALOG="/home/user/fanatical_catalog.json"

if [[ "$1" == "--check-owned" ]]; then
    python3 scrape_humble_books.py "$HUMBLE_URL" --check-owned "$HUMBLE_CATALOG" "$FANATICAL_CATALOG"
else
    python3 scrape_humble_books.py "$HUMBLE_URL"
fi
```

### Usage
```bash
# Make executable
chmod +x run_scraper.sh

# Basic scraping
./run_scraper.sh

# With ownership checking
./run_scraper.sh --check-owned
```

## Example 5: Processing Different Bundle Types

### Comics Bundle
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/comics-bundle"
```

### Programming Books Bundle
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/programming-books"
```

### Fiction Bundle
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/fiction-bundle"
```

## Example 6: Error Handling

### Invalid URL
```bash
python3 scrape_humble_books.py "https://invalid-url.com"
# Error: Could not scrape page or invalid URL
```

### Missing Catalog File
```bash
python3 scrape_humble_books.py "https://humblebundle.com/books/bundle" --check-owned /nonexistent/file.json /another/nonexistent.json
# Warning: Could not read /nonexistent/file.json: [Errno 2] No such file or directory
```

### Network Issues
```bash
python3 scrape_humble_books.py "https://www.humblebundle.com/books/bundle"
# Error: Network timeout or connection failed
```

## Example 7: Advanced Usage Patterns

### Batch Processing Multiple Bundles
```bash
#!/bin/bash
bundles=(
    "https://www.humblebundle.com/books/bundle1"
    "https://www.humblebundle.com/books/bundle2"
    "https://www.humblebundle.com/books/bundle3"
)

for bundle in "${bundles[@]}"; do
    echo "Processing: $bundle"
    python3 scrape_humble_books.py "$bundle" --check-owned humble_catalog.json fanatical_catalog.json
    sleep 5  # Be respectful to the server
done
```

### Filtering Results
```bash
# Get only books you don't own
grep -v "\[OWNED\]\|\[PROBABLY OWNED\]" book_titles.txt

# Get only books you might own
grep "\[MAYBE OWNED\]" book_titles.txt

# Count total books
grep -c "^[^\[-]" book_titles.txt
```

### JSON Processing with jq
```bash
# Extract all book titles
jq '.books[].title' bundle-name.json

# Find books with specific authors
jq '.books[] | select(.authors[] | contains("Brian K. Vaughan")) | .title' bundle-name.json

# Count books by ownership status
jq '.books | group_by(.ownership_status) | map({status: .[0].ownership_status, count: length})' bundle-name.json
```

## Example 8: Integration with Other Tools

### Import to Spreadsheet
```bash
# Convert JSON to CSV for spreadsheet import
python3 -c "
import json
import csv
import sys

with open('bundle-name.json', 'r') as f:
    data = json.load(f)

with open('bundle-name.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Authors', 'Format', 'Ownership Status'])
    for book in data['books']:
        writer.writerow([
            book['title'],
            '; '.join(book.get('authors', [])),
            book.get('format', ''),
            book.get('ownership_status', 'not owned')
        ])
"
```

### Database Import
```bash
# Example SQLite import
python3 -c "
import json
import sqlite3

conn = sqlite3.connect('books.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT,
        authors TEXT,
        format TEXT,
        ownership_status TEXT,
        bundle_name TEXT
    )
''')

with open('bundle-name.json', 'r') as f:
    data = json.load(f)

for book in data['books']:
    cursor.execute('''
        INSERT INTO books (title, authors, format, ownership_status, bundle_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        book['title'],
        '; '.join(book.get('authors', [])),
        book.get('format', ''),
        book.get('ownership_status', 'not owned'),
        data['bundle_title']
    ))

conn.commit()
conn.close()
"
``` 