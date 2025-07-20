import os
import json
import sys
import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import unicodedata


def normalize_title(title):
    import re
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
    return normalized.strip().lower()


def expand_volume_ranges(books):
    expanded_books = []
    # Pattern for 'Vol. 1-3', 'Volume 1-3', 'V. 1-3', etc.
    vol_pattern = re.compile(r'(.*?)(?:\s+)?(?:Vol(?:\.|ume)?|V\.)(?:\s+)?(\d+)-(\d+)(.*)', re.IGNORECASE)
    # Pattern for 'Vols #-#', 'Vols. #-#', 'Volumes #-#', etc.
    vols_pattern = re.compile(r'(.*?)(?:\s+)?Vols?\.?|Volumes?(?:\s+)?(\d+)-(\d+)(.*)', re.IGNORECASE)
    for book in books:
        title = book['title']
        img_url = book.get('image_url')
        authors = book.get('authors')
        format_detail = book.get('format')
        # Try 'Vols #-#' first
        match_vols = re.match(r'(.*?)(?:\s+)?(vols?\.?|volumes?)(?:\s+)?(\d+)-(\d+)(.*)', title, re.IGNORECASE)
        if match_vols:
            prefix = match_vols.group(1).strip()
            start = int(match_vols.group(3))
            end = int(match_vols.group(4))
            suffix = match_vols.group(5).strip()
            for i in range(start, end + 1):
                vol_title = f"{prefix} Vol. {i}"
                if suffix:
                    vol_title += f" {suffix}"
                expanded_books.append({'title': vol_title, 'image_url': img_url, 'authors': authors, 'format': format_detail})
            continue
        # Try 'Vol #-#' next
        match = vol_pattern.match(title)
        if match:
            prefix = match.group(1).strip()
            start = int(match.group(2))
            end = int(match.group(3))
            suffix = match.group(4).strip()
            for i in range(start, end + 1):
                vol_title = f"{prefix} Vol. {i}"
                if suffix:
                    vol_title += f" {suffix}"
                expanded_books.append({'title': vol_title, 'image_url': img_url, 'authors': authors, 'format': format_detail})
        else:
            expanded_books.append(book)
    return expanded_books


def advanced_normalize(title):
    # Lowercase, remove possessives, punctuation, edition/volume words, diacritics, and collapse spaces
    title = title.lower()
    title = re.sub(r"'s\b", "", title)
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = re.sub(r'\b(art edition|edition|art|the|a|an)\b', '', title)
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = re.sub(r'\s+', ' ', title)
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
    owned_titles_sub = []  # (subtitle_normalized, set(authors), bundle_name)
    bundle_lookup = {}  # advanced_normalized_title -> set of bundle names
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
                                    owned_titles_sub.append((sub_norm_title, authors, bundle_name))
                                    bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                    # Fallback to previous logic for other structures
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
                                owned_titles_sub.append((sub_norm_title, authors, bundle_name))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
                            elif isinstance(entry, str):
                                norm_title = normalize_title(entry)
                                adv_norm_title = advanced_normalize(entry)
                                sub_norm_title = advanced_normalize(remove_subtitle(entry))
                                owned_titles.add(norm_title)
                                owned_titles_adv.add(adv_norm_title)
                                owned_titles_sub.append((sub_norm_title, set(), bundle_name))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
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
                                owned_titles_sub.append((sub_norm_title, authors, bundle_name))
                                bundle_lookup.setdefault(adv_norm_title, set()).add(bundle_name)
            except Exception as e:
                print(f"Warning: Could not read {catalog_file}: {e}")
    return owned_titles, owned_titles_adv, owned_titles_sub, bundle_lookup

def mark_ownership_status(books, owned_titles, owned_titles_adv, owned_titles_sub, owned_titles_authors, bundle_lookup):
    for book in books:
        title = book['title']
        authors = set(a.lower() for a in (book.get('authors') or []))
        norm = normalize_title(title)
        adv_norm = advanced_normalize(title)
        sub_norm = advanced_normalize(remove_subtitle(title))
        matched_bundles = set()
        # 1. Strict
        if norm in owned_titles:
            book['ownership_status'] = 'owned'
            matched_bundles |= bundle_lookup.get(adv_norm, set())
        # 2. Improved normalization
        elif adv_norm in owned_titles_adv:
            book['ownership_status'] = 'probably owned'
            matched_bundles |= bundle_lookup.get(adv_norm, set())
        # 3. Fuzzy/subtitle
        else:
            best_score = 0
            best_match = None
            best_bundles = set()
            for owned, owned_authors, bundle_name in owned_titles_sub:
                score = fuzz.ratio(sub_norm, owned)
                if score > best_score:
                    best_score = score
                    best_match = (owned, owned_authors)
                    best_bundles = {bundle_name}
                elif score == best_score:
                    best_bundles.add(bundle_name)
            if best_score >= 90:
                # 4. Author boost
                if authors and best_match and authors & best_match[1]:
                    book['ownership_status'] = 'probably owned'
                else:
                    book['ownership_status'] = 'maybe owned'
                matched_bundles |= best_bundles
            else:
                book['ownership_status'] = 'not owned'
        book['matched_bundles'] = sorted(matched_bundles)
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
            books.append({
                'title': title,
                'authors': authors,
                'format': format_detail,
                'image_url': img_url
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
        html_path = 'humble-book-scraper/page_dump.html'
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
        owned_titles, owned_titles_adv, owned_titles_sub, bundle_lookup = load_owned_titles(humble_catalog_path, fanatical_catalog_path)
        # Build a set of all authors for subtitle matches
        owned_titles_authors = set()
        for _, authors, _ in owned_titles_sub:
            owned_titles_authors |= authors
        expanded_books = mark_ownership_status(expanded_books, owned_titles, owned_titles_adv, owned_titles_sub, owned_titles_authors, bundle_lookup)
    # Save plain text file
    output_file = 'humble-book-scraper/book_titles.txt'
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
    json_file = f"humble-book-scraper/{bundle_segment}.json"
    json_data = {
        'bundle_title': bundle_title,
        'books': expanded_books
    }
    with open(json_file, 'w', encoding='utf-8') as jf:
        json.dump(json_data, jf, indent=2, ensure_ascii=False)
    print(f"Saved book data with images to {json_file}")

if __name__ == "__main__":
    main() 