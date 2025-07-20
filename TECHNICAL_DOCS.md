# Technical Documentation

This document provides detailed technical information about the Humble Book Scraper implementation.

## Code Structure

### Main Functions

#### `main()`
**Location**: Lines 258-333  
**Purpose**: Entry point and command-line interface  
**Parameters**: Command-line arguments  
**Returns**: None  

Handles argument parsing and orchestrates the scraping workflow:
1. Parses command-line arguments
2. Calls `scrape_humble_books()` to get book data
3. Calls `expand_volume_ranges()` to process volume ranges
4. Optionally calls ownership checking functions
5. Generates output files

#### `scrape_humble_books(url)`
**Location**: Lines 230-257  
**Purpose**: Main web scraping function  
**Parameters**: `url` (string) - Humble Bundle URL  
**Returns**: `(books, bundle_title)` tuple  

Uses Playwright to:
1. Launch headless Chromium browser
2. Navigate to the Humble Bundle page
3. Wait for dynamic content to load
4. Save page HTML to `page_dump.html`
5. Extract bundle title from page metadata
6. Call `parse_books_from_html()` for data extraction

#### `parse_books_from_html(html_path)`
**Location**: Lines 190-229  
**Purpose**: Parse book data from saved HTML  
**Parameters**: `html_path` (string) - Path to HTML file  
**Returns**: List of book dictionaries  

Uses BeautifulSoup to extract:
- **Title**: From `h2.heading-medium` elements
- **Authors**: From `div.publishers-and-developers` containing "Authors:" or "Author:"
- **Format**: From `div.delivery-and-oses` containing format information
- **Image URL**: From `img.item-image` elements

## Title Processing Functions

### `normalize_title(title)`
**Location**: Lines 12-28  
**Purpose**: Basic title normalization  
**Algorithm**:
1. Standardize volume indicators (`v.`, `vol.`, `volume` → `vol.`)
2. Handle `v1`, `v2` patterns → `vol. 1`, `vol. 2`
3. Remove punctuation except alphanumerics and spaces
4. Collapse multiple spaces
5. Remove leading articles (`a`, `the`)
6. Convert to lowercase and strip whitespace

**Example**:
```
"V. 1: The Beginning!" → "vol 1 the beginning"
"Volume 2 - Epic Tale" → "vol 2 epic tale"
```

### `advanced_normalize(title)`
**Location**: Lines 70-79  
**Purpose**: Aggressive title normalization for fuzzy matching  
**Algorithm**:
1. Convert to lowercase
2. Remove possessives (`'s`)
3. Remove all punctuation
4. Remove common words (`art edition`, `edition`, `art`, `the`, `a`, `an`)
5. Normalize Unicode characters (remove diacritics)
6. Collapse spaces

**Example**:
```
"Art Edition: The Epic Tale's Beginning" → "epic tale beginning"
```

### `remove_subtitle(title)`
**Location**: Lines 80-90  
**Purpose**: Remove subtitles for better matching  
**Algorithm**:
1. Split on colon and take first part
2. Find volume number pattern (`vol. 1`, `vol 1`)
3. Remove everything after volume number

**Example**:
```
"Book Title: The Subtitle" → "Book Title"
"Vol. 1: Epic Tale" → "Vol. 1"
```

## Volume Range Expansion

### `expand_volume_ranges(books)`
**Location**: Lines 29-69  
**Purpose**: Expand volume ranges into individual volumes  
**Patterns Supported**:
- `Vol. 1-3` → `Vol. 1`, `Vol. 2`, `Vol. 3`
- `Volume 1-5` → `Vol. 1`, `Vol. 2`, `Vol. 3`, `Vol. 4`, `Vol. 5`
- `Vols. 1-3` → `Vol. 1`, `Vol. 2`, `Vol. 3`

**Algorithm**:
1. Use regex to match volume range patterns
2. Extract prefix, start number, end number, and suffix
3. Generate individual volume titles
4. Preserve metadata (authors, image_url, format) for each volume

## Ownership Checking System

### `load_owned_titles(humble_catalog_path, fanatical_catalog_path)`
**Location**: Lines 91-153  
**Purpose**: Load and normalize owned book titles from catalogs  
**Returns**: 4-tuple of data structures for different matching strategies

**Data Structures**:
1. `owned_titles` (set): Basic normalized titles
2. `owned_titles_adv` (set): Advanced normalized titles  
3. `owned_titles_sub` (list): Subtitle-normalized titles with authors and bundle names
4. `bundle_lookup` (dict): Maps normalized titles to bundle names

**Catalog Format Support**:
- Humble Bundle format with `bundles` → `books` → `Book Title`
- Fanatical format with direct book list
- Fallback formats for compatibility

### `mark_ownership_status(books, owned_titles, owned_titles_adv, owned_titles_sub, owned_titles_authors, bundle_lookup)`
**Location**: Lines 155-189  
**Purpose**: Determine ownership status for each book  
**Algorithm**: Multi-level matching strategy

**Matching Levels**:
1. **Strict Match**: Exact `normalize_title()` match
   - Status: `'owned'`
   
2. **Advanced Match**: Exact `advanced_normalize()` match
   - Status: `'probably owned'`
   
3. **Fuzzy Match**: RapidFuzz similarity ≥ 90%
   - Status: `'probably owned'` (if authors match) or `'maybe owned'`
   
4. **No Match**: Similarity < 90%
   - Status: `'not owned'`

**Author Boost**: If fuzzy match has author overlap, upgrade to `'probably owned'`

## Data Structures

### Book Dictionary
```python
{
    'title': str,                    # Book title
    'authors': list[str],            # List of authors
    'format': str,                   # Format information (PDF, ePUB, etc.)
    'image_url': str,                # Cover image URL
    'ownership_status': str,         # 'owned', 'probably owned', 'maybe owned', 'not owned'
    'matched_bundles': list[str]     # Bundle names where this book was found
}
```

### Output JSON Structure
```python
{
    'bundle_title': str,             # Humble Bundle title
    'books': list[Book]              # List of book dictionaries
}
```

## Error Handling

### Web Scraping Errors
- Playwright browser launch failures
- Network timeouts
- Invalid URLs
- Missing HTML elements

### File I/O Errors
- Catalog file not found
- Invalid JSON format
- Permission errors
- Encoding issues

### Data Processing Errors
- Malformed HTML
- Missing required fields
- Unicode normalization failures

## Performance Considerations

### Memory Usage
- HTML page dumps can be large (300KB+)
- Book lists with volume expansion can grow significantly
- Catalog loading keeps multiple normalized versions in memory

### Processing Time
- Web scraping: 5-15 seconds depending on page size
- Title normalization: O(n) where n = number of books
- Ownership checking: O(n*m) where m = number of owned books
- Volume expansion: O(n*r) where r = average range size

### Optimization Strategies
- Use sets for O(1) title lookups
- Batch processing for large catalogs
- Lazy loading of catalog data
- Efficient regex patterns

## Dependencies and Versions

### Core Dependencies
- `playwright` ≥ 1.20.0 - Browser automation
- `beautifulsoup4` ≥ 4.9.0 - HTML parsing
- `rapidfuzz` ≥ 2.0.0 - Fuzzy string matching
- `requests` ≥ 2.25.0 - HTTP requests (optional)

### Python Version
- Minimum: Python 3.7
- Recommended: Python 3.8+

### Browser Requirements
- Chromium browser (installed via Playwright)
- Headless mode supported
- No additional browser dependencies

## Testing and Validation

### Input Validation
- URL format checking
- File existence verification
- JSON structure validation
- HTML element presence verification

### Output Validation
- Required fields present
- Data type consistency
- UTF-8 encoding
- JSON serialization

### Edge Cases Handled
- Empty book lists
- Missing author information
- Malformed volume ranges
- Unicode characters in titles
- Duplicate book entries 