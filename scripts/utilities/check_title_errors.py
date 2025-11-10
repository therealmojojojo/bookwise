#!/usr/bin/env python3
"""
Check award files for book title formatting errors
Identifies titles with missing spaces like "ATale" or "LittleWomen"
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Pattern to find lowercase followed by uppercase (potential error)
# But we'll exclude valid cases like McDonald, MacArthur, etc.
ERROR_PATTERN = re.compile(r'[a-z][A-Z]')

# Valid patterns that should NOT be flagged as errors
VALID_PATTERNS = [
    re.compile(r'\bMc[A-Z]'),      # McDonald, McCarthy, etc.
    re.compile(r'\bMac[A-Z]'),     # MacArthur, MacBeth, etc.
    re.compile(r'\bO\'[A-Z]'),     # O'Brien, O'Connor, etc.
    re.compile(r'\bd\'[A-Z]'),     # d'Artagnan, etc.
    re.compile(r'\bvon[A-Z]'),     # von Kleist, etc.
    re.compile(r'\bvan[A-Z]'),     # van Gogh, etc.
    re.compile(r'\bde[A-Z]'),      # de Gaulle, etc.
    re.compile(r'\bla[A-Z]'),      # la Fontaine, etc.
    re.compile(r'\ble[A-Z]'),      # le Carré, etc.
]


def is_valid_exception(title, match):
    """Check if the match is a valid exception (like McDonald)"""
    match_text = match.group(0)
    position = match.start()

    # Get context around the match
    start = max(0, position - 2)
    end = min(len(title), position + len(match_text) + 5)
    context = title[start:end]

    # Check against valid patterns
    for pattern in VALID_PATTERNS:
        if pattern.search(context):
            return True

    return False


def check_title(title):
    """Check a title for formatting errors"""
    errors = []

    for match in ERROR_PATTERN.finditer(title):
        if not is_valid_exception(title, match):
            errors.append({
                'position': match.start(),
                'pattern': match.group(0),
                'context': title[max(0, match.start()-5):min(len(title), match.end()+5)]
            })

    return errors


def check_award_file(file_path):
    """Check a single award file for title errors"""
    print(f"\n{'='*80}")
    print(f"Checking: {file_path.name}")
    print('='*80)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different JSON structures
    books = []
    if isinstance(data, list):
        books = data
    elif isinstance(data, dict):
        if 'books' in data:
            books = data['books']
        elif 'winners' in data:
            books = data['winners']
        else:
            # Try to find any list in the dict
            for value in data.values():
                if isinstance(value, list):
                    books = value
                    break

    errors_found = defaultdict(list)

    for item in books:
        # Handle different structures
        title = None
        if isinstance(item, dict):
            title = item.get('title') or item.get('book') or item.get('work')
        elif isinstance(item, str):
            title = item

        if title:
            title_errors = check_title(title)
            if title_errors:
                errors_found[title].extend(title_errors)

    if errors_found:
        print(f"\n❌ Found {len(errors_found)} title(s) with potential errors:")
        for title, errors in sorted(errors_found.items()):
            print(f"\n  Title: {title}")
            for error in errors:
                print(f"    ⚠️  Position {error['position']}: '{error['pattern']}' in '{error['context']}'")
    else:
        print("✅ No errors found")

    return errors_found


def main():
    """Main function to check all award files"""
    datasources_dir = Path('datasources')

    if not datasources_dir.exists():
        print(f"Error: {datasources_dir} not found")
        return

    # Get all JSON files
    json_files = sorted(datasources_dir.glob('*.json'))

    print("="*80)
    print("BOOK TITLE ERROR CHECKER")
    print("="*80)
    print(f"\nScanning {len(json_files)} award files for title formatting errors...")
    print("Looking for patterns like 'ATale' or 'LittleWomen' (missing spaces)")

    all_errors = {}

    for json_file in json_files:
        errors = check_award_file(json_file)
        if errors:
            all_errors[json_file.name] = errors

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if all_errors:
        total_titles = sum(len(errors) for errors in all_errors.values())
        print(f"\n❌ Found errors in {len(all_errors)} file(s)")
        print(f"   Total titles with errors: {total_titles}")

        print("\n📋 Files with errors:")
        for filename, errors in sorted(all_errors.items()):
            print(f"   - {filename}: {len(errors)} title(s)")
    else:
        print("\n✅ No errors found in any files!")

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
