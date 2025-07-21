import os
import json
import sys
import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import unicodedata


def words_to_numbers(text):
    # Map of spelled-out numbers to numerals (1-20, tens, and common ordinals)
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
        'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
        'nineteen': '19', 'twenty': '20',
        'thirty': '30', 'forty': '40', 'fifty': '50', 'sixty': '60',
        'seventy': '70', 'eighty': '80', 'ninety': '90',
        'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5',
        'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10',
        'eleventh': '11', 'twelfth': '12', 'thirteenth': '13', 'fourteenth': '14',
        'fifteenth': '15', 'sixteenth': '16', 'seventeenth': '17', 'eighteenth': '18',
        'nineteenth': '19', 'twentieth': '20'
    }
    # Replace spelled-out numbers with numerals
    def replacer(match):
        word = match.group(0).lower()
        return str(number_map.get(word, word))  # Always return a string
    pattern = re.compile(r'\b(' + '|'.join(number_map.keys()) + r')\b', re.IGNORECASE)
    return pattern.sub(replacer, text)


def normalize_title(title):
    import re
    # Convert spelled-out numbers to numerals
    title = words_to_numbers(title)
    # Remove possessive apostrophes: "world's" -> "worlds", "James'" -> "James"
    title = re.sub(r"'s\b", "s", title)
    title = re.sub(r"'\b", "", title)
    # Unicode normalization to ASCII
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    # Replace all variants of volume indicators with 'vol.' only when followed by a number
    pattern = re.compile(r'(?<!\w)(v\.?|vol\.?|volume)(?:\s*[\.\-]?\s*)(\d+)', re.IGNORECASE)
    normalized = pattern.sub(r'vol. \2', title)
    # Handle 'v' immediately followed by a number (e.g., 'v1')
    pattern_vnum = re.compile(r'(?<!\w)v(\d+)', re.IGNORECASE)
    normalized = pattern_vnum.sub(r'vol. \1', normalized)
    # Remove periods and extra punctuation except for alphanumerics and spaces
    normalized = re.sub(r'[\.\'",:;!?()\[\]{}]', '', normalized)
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    # Remove leading articles 'a' or 'the'
    normalized = re.sub(r'^(a|the)\s+', '', normalized, flags=re.IGNORECASE)
    # Remove leading zeros from numbers
    normalized = re.sub(r'\b0+(\d+)\b', r'\1', normalized)
    return normalized.strip().lower()


def expand_volume_ranges(books):
    expanded_books = []
    # Pattern for 'Vol. 1-3', 'Volume 1-3', 'V. 1-3', etc.
    vol_pattern = re.compile(r'(.*?)(?:\s+)?(?:Vol(?:\.|ume)?|V\.)(?:\s+)?(\d+)-(\d+)(.*)', re.IGNORECASE)
    # Pattern for 'Vols #-#', 'Vols. #-#', 'Volumes #-#', etc.
    vols_pattern = re.compile(r'(.*?)(?:\s+)?Vols?\.?|Volumes?(?:\s+)?(\d+)-(\d+)(.*)', re.IGNORECASE)
    for book in books:
        title = book['title']
        # Try 'Vols #-#' first
        match_vols = re.match(r'(.*?)(?:\s+)?(vols?\.?|volumes?)(?:\s+)?(\d+)-(\d+)(.*)', title, re.IGNORECASE)
        if match_vols:
            prefix = match_vols.group(1).strip()
            start = int(match_vols.group(3))
            end = int(match_vols.group(4))
            suffix = match_vols.group(5).strip()
            for i in range(start, end + 1):
                new_book = dict(book)  # Copy all fields
                vol_title = f"{prefix} Vol. {i}"
                if suffix:
                    vol_title += f" {suffix}"
                new_book['title'] = vol_title
                expanded_books.append(new_book)
            continue
        # Try 'Vol #-#' next
        match = vol_pattern.match(title)
        if match:
            prefix = match.group(1).strip()
            start = int(match.group(2))
            end = int(match.group(3))
            suffix = match.group(4).strip()
            for i in range(start, end + 1):
                new_book = dict(book)  # Copy all fields
                vol_title = f"{prefix} Vol. {i}"
                if suffix:
                    vol_title += f" {suffix}"
                new_book['title'] = vol_title
                expanded_books.append(new_book)
        else:
            expanded_books.append(book)
    return expanded_books


def advanced_normalize(title):
    # Convert spelled-out numbers to numerals
    title = words_to_numbers(title)
    # Remove possessive apostrophes: "world's" -> "worlds", "James'" -> "James"
    title = re.sub(r"'s\b", "s", title)
    title = re.sub(r"'\b", "", title)
    # Lowercase, remove possessives, punctuation, edition/volume words, diacritics, and collapse spaces
    title = title.lower()
    # Remove common stopwords and edition/volume words, including 'tp', 'vol', 'v'
    title = re.sub(r'\b(art edition|edition|art|the|a|an|and|of|tp|vol|v)\b', '', title)
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = re.sub(r'\s+', ' ', title)
    # Remove leading zeros from numbers
    title = re.sub(r'\b0+(\d+)\b', r'\1', title)
    return title.strip()

def remove_subtitle(title):
    # Remove anything after a colon or after a volume number (e.g., 'Vol. 1: Subtitle')
    # Remove after colon
    title = title.split(':')[0]
    # Remove after volume number (e.g., 'Vol. 1 Subtitle')
    m = re.search(r'(vol\.? \d+)', title, re.IGNORECASE)
    if m:
        idx = m.end()
        title = title[:idx]
    return title.strip()

def load_owned_titles(humble_catalog_path, fanatical_catalog_path):
    owned_titles = set()
    owned_titles_adv = set()
    owned_titles_sub = []  # (subtitle_normalized, set(authors), bundle_name, original_title)
    bundle_lookup = {}  # advanced_normalized_title -> set of bundle names
    normalized_title_to_catalog = {}  # normalized_title -> list of (original_title, bundle_name)
    for catalog_file in [humble_catalog_path, fanatical_catalog_path]:
        if catalog_file and os.path.exists(catalog_file):
            try:
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle Humble catalog structure: bundles -> books -> 'Book Title'
                    if isinstance(data, dict) and "bundles" in data:
                        for bundle in data["bundles"]:
                            bundle_name = bundle.get("human_name") or "Unknown Bundle"
                            for book in bundle.get("books", []):
                                title = book.get("Book Title")
                                authors = set(a.lower() for a in book.get("Authors", []))
                                if title:
                                    norm_title = normalize_title(title)
                                    adv_norm_title = advanced_normalize(title)
                                    sub_norm_title = advanced_normalize(remove_subtitle(title))
                                    owned_titles.add(norm_title)
                                    owned_titles_adv.add(adv_norm_title)
                                    owned_titles_sub.append((sub_norm_title, authors, bundle_name, title))
                                    bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                                    normalized_title_to_catalog.setdefault(norm_title, []).append((title, bundle_name))
                    elif isinstance(data, list):
                        for entry in data:
                            bundle_name = "Unknown Bundle"
                            if isinstance(entry, dict) and 'title' in entry:
                                title = entry['title']
                                authors = set(a.lower() for a in entry.get('authors', []))
                                norm_title = normalize_title(title)
                                adv_norm_title = advanced_normalize(title)
                                sub_norm_title = advanced_normalize(remove_subtitle(title))
                                owned_titles.add(norm_title)
                                owned_titles_adv.add(adv_norm_title)
                                owned_titles_sub.append((sub_norm_title, authors, bundle_name, title))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                                normalized_title_to_catalog.setdefault(norm_title, []).append((title, bundle_name))
                            elif isinstance(entry, str):
                                norm_title = normalize_title(entry)
                                adv_norm_title = advanced_normalize(entry)
                                sub_norm_title = advanced_normalize(remove_subtitle(entry))
                                owned_titles.add(norm_title)
                                owned_titles_adv.add(adv_norm_title)
                                owned_titles_sub.append((sub_norm_title, set(), bundle_name, entry))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                                normalized_title_to_catalog.setdefault(norm_title, []).append((entry, bundle_name))
                    elif isinstance(data, dict):
                        for entry in data.get('books', []):
                            bundle_name = "Unknown Bundle"
                            if isinstance(entry, dict) and 'title' in entry:
                                title = entry['title']
                                authors = set(a.lower() for a in entry.get('authors', []))
                                norm_title = normalize_title(title)
                                adv_norm_title = advanced_normalize(title)
                                sub_norm_title = advanced_normalize(remove_subtitle(title))
                                owned_titles.add(norm_title)
                                owned_titles_adv.add(adv_norm_title)
                                owned_titles_sub.append((sub_norm_title, authors, bundle_name, title))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                                normalized_title_to_catalog.setdefault(norm_title, []).append((title, bundle_name))
            except Exception as e:
                print(f"Warning: Could not read {catalog_file}: {e}")
    return owned_titles, owned_titles_adv, owned_titles_sub, bundle_lookup, normalized_title_to_catalog

def mark_ownership_status(books, owned_titles, owned_titles_adv, owned_titles_sub, owned_titles_authors, bundle_lookup, normalized_title_to_catalog):
    for book in books:
        title = book['title']
        authors = set(a.lower() for a in (book.get('authors') or []))
        norm = normalize_title(title)
        adv_norm = advanced_normalize(title)
        sub_norm = advanced_normalize(remove_subtitle(title))
        bundle_to_titles = {}
        # 1. Strict
        if norm in owned_titles:
            book['ownership_status'] = 'owned'
            for catalog_title, bundle_name in normalized_title_to_catalog.get(norm, []):
                bundle_to_titles.setdefault(bundle_name, set()).add(catalog_title)
        # 2. Improved normalization
        elif adv_norm in owned_titles_adv:
            book['ownership_status'] = 'probably owned'
            for owned, owned_authors, bundle_name, original_title in owned_titles_sub:
                if adv_norm == advanced_normalize(owned):
                    bundle_to_titles.setdefault(bundle_name, set()).add(original_title)
        # 3. Fuzzy/subtitle
        else:
            best_score = 0
            best_matches = []
            for owned, owned_authors, bundle_name, original_title in owned_titles_sub:
                # Compare as sorted sets of words for order-insensitive matching
                sub_norm_set = ' '.join(sorted(set(sub_norm.split())))
                owned_set = ' '.join(sorted(set(owned.split())))
                score = fuzz.ratio(sub_norm_set, owned_set)
                if score > best_score:
                    best_score = score
                    best_matches = [(owned, owned_authors, bundle_name, original_title)]
                elif score == best_score:
                    best_matches.append((owned, owned_authors, bundle_name, original_title))
            if best_score >= 90:
                author_boost = any(authors & owned_authors for _, owned_authors, _, _ in best_matches)
                if authors and author_boost:
                    book['ownership_status'] = 'probably owned'
                else:
                    book['ownership_status'] = 'maybe owned'
                for owned, owned_authors, bundle_name, original_title in best_matches:
                    bundle_to_titles.setdefault(bundle_name, set()).add(original_title)
            else:
                book['ownership_status'] = 'not owned'
        matched_bundles = [
            {'bundle_name': bundle, 'matched_titles': sorted(list(titles))}
            for bundle, titles in bundle_to_titles.items()
        ]
        book['matched_bundles'] = matched_bundles
    return books


def parse_books_from_html(html_path):
    books = []
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        for details_view in soup.select('.tier-item-details-view'):
            # Title
            title_el = details_view.select_one('h2.heading-medium')
            title = title_el.get_text(strip=True) if title_el else None
            # Authors
            authors = []
            for pubdev in details_view.select('div.publishers-and-developers'):
                text = pubdev.get_text()
                if 'Authors:' in text or 'Author:' in text:
                    spans = pubdev.select('span')
                    if len(spans) == 1 and 'Author:' in text:
                        # Split by comma for single span with multiple authors
                        authors = [a.strip() for a in spans[0].get_text(strip=True).split(',')]
                    else:
                        authors = [span.get_text(strip=True) for span in spans]
                    break
            # Format
            format_detail = None
            for delivery in details_view.select('div.delivery-and-oses.icons-and-blurbs'):
                span = delivery.select_one('span.fine-print')
                if span and any(fmt in span.get_text() for fmt in ['PDF', 'ePUB', 'CBZ']):
                    format_detail = span.get_text(strip=True)
                    break
            # Image
            img_el = details_view.select_one('img.item-image')
            img_url = img_el['data-lazy'] if img_el and img_el.has_attr('data-lazy') else (img_el['src'] if img_el and img_el.has_attr('src') else None)
            # Tier price
            tier_price = None
            header_area = details_view.select_one('.header-area')
            if header_area:
                # Try to get .tier-price first, then .msrp if not found
                price_el = header_area.select_one('.tier-price') or header_area.select_one('.msrp')
                if price_el:
                    tier_price = price_el.get_text(strip=True)
            books.append({
                'title': title,
                'authors': authors,
                'format': format_detail,
                'image_url': img_url,
                'tier_price': tier_price
            })
    return books


def scrape_humble_books(url):
    books = []
    bundle_title = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')
        # Save the page content to a file for inspection (optional, can be removed later)
        html_path = './page_dump.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        # Extract bundle title using the correct selector
        title_el = page.query_selector('head > title')
        if title_el:
            bundle_title = title_el.inner_text().strip()
        browser.close()
    # Parse books from the saved HTML
    books = parse_books_from_html(html_path)
    return books, bundle_title


def main():
    usage = ("Usage: python3 scrape_humble_books.py <HUMBLE_BUNDLE_URL> [--check-owned <HUMBLE_CATALOG_PATH> <FANATICAL_CATALOG_PATH>]")
    if len(sys.argv) < 2:
        print(usage)
        sys.exit(1)
    url = sys.argv[1]
    check_owned = False
    humble_catalog_path = None
    fanatical_catalog_path = None
    if len(sys.argv) > 2 and sys.argv[2] == '--check-owned':
        if len(sys.argv) < 5:
            print("Error: --check-owned requires two additional arguments: <HUMBLE_CATALOG_PATH> <FANATICAL_CATALOG_PATH>")
            print(usage)
            sys.exit(1)
        check_owned = True
        humble_catalog_path = sys.argv[3]
        fanatical_catalog_path = sys.argv[4]
    books, bundle_title = scrape_humble_books(url)
    expanded_books = expand_volume_ranges(books)
    if check_owned:
        owned_titles, owned_titles_adv, owned_titles_sub, bundle_lookup, normalized_title_to_catalog = load_owned_titles(humble_catalog_path, fanatical_catalog_path)
        # Build a set of all authors for subtitle matches
        owned_titles_authors = set()
        for _, authors, _, _ in owned_titles_sub:
            owned_titles_authors |= authors
        expanded_books = mark_ownership_status(expanded_books, owned_titles, owned_titles_adv, owned_titles_sub, owned_titles_authors, bundle_lookup, normalized_title_to_catalog)
    # Save plain text file
    output_file = './book_titles.txt'
    not_owned = []
    probably_owned = []
    maybe_owned = []
    with open(output_file, 'w', encoding='utf-8') as f:
        for book in expanded_books:
            status = book.get('ownership_status', 'not owned')
            status_marker = {
                'owned': ' [OWNED]',
                'probably owned': ' [PROBABLY OWNED]',
                'maybe owned': ' [MAYBE OWNED]',
                'not owned': ''
            }.get(status, '')
            f.write(book['title'] + status_marker + '\n')
            if check_owned:
                if status == 'not owned':
                    not_owned.append(book['title'])
                elif status == 'probably owned':
                    probably_owned.append(book['title'])
                elif status == 'maybe owned':
                    maybe_owned.append(book['title'])
        f.write(f"\nTotal books: {len(expanded_books)}\n")
        if check_owned and probably_owned:
            f.write("\n--- Probably Owned ---\n")
            for title in probably_owned:
                f.write(title + '\n')
        if check_owned and maybe_owned:
            f.write("\n--- Maybe Owned ---\n")
            for title in maybe_owned:
                f.write(title + '\n')
        if check_owned and not_owned:
            f.write("\n--- Suspected Not Owned ---\n")
            for title in not_owned:
                f.write(title + '\n')
    print(f"Saved {len(expanded_books)} book titles to {output_file}")
    # Save JSON file
    parsed_url = urlparse(url)
    bundle_segment = os.path.basename(parsed_url.path)
    json_file = f"./{bundle_segment}.json"
    json_data = {
        'bundle_title': bundle_title,
        'books': expanded_books
    }
    with open(json_file, 'w', encoding='utf-8') as jf:
        json.dump(json_data, jf, indent=2, ensure_ascii=False)
    print(f"Saved book data with images to {json_file}")

if __name__ == "__main__":
    main() 