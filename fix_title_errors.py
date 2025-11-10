#!/usr/bin/env python3
"""
Fix book title formatting errors in award files
Adds spaces before uppercase letters where missing
"""

import json
import re
from pathlib import Path

# Pattern to find lowercase followed by uppercase (potential error)
ERROR_PATTERN = re.compile(r'[a-z][A-Z]')

# Valid patterns that should NOT be fixed
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


def fix_title(title):
    """Fix a title by adding spaces before uppercase letters"""
    fixed = title
    offset = 0

    for match in ERROR_PATTERN.finditer(title):
        if not is_valid_exception(title, match):
            # Add space between lowercase and uppercase
            position = match.start() + 1 + offset  # +1 to insert after lowercase
            fixed = fixed[:position] + ' ' + fixed[position:]
            offset += 1

    return fixed


def fix_award_file(file_path, dry_run=True):
    """Fix title errors in a single award file"""
    print(f"\nProcessing: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Track changes
    changes = []

    # Handle different JSON structures
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                for key in ['title', 'book', 'work']:
                    if key in item:
                        original = item[key]
                        fixed = fix_title(original)
                        if original != fixed:
                            changes.append((original, fixed))
                            if not dry_run:
                                item[key] = fixed
            elif isinstance(item, str):
                original = item
                fixed = fix_title(original)
                if original != fixed:
                    changes.append((original, fixed))
                    if not dry_run:
                        data[i] = fixed

    elif isinstance(data, dict):
        # Find the list of books
        for main_key, main_value in data.items():
            if isinstance(main_value, list):
                for i, item in enumerate(main_value):
                    if isinstance(item, dict):
                        for key in ['title', 'book', 'work']:
                            if key in item:
                                original = item[key]
                                fixed = fix_title(original)
                                if original != fixed:
                                    changes.append((original, fixed))
                                    if not dry_run:
                                        item[key] = fixed
                    elif isinstance(item, str):
                        original = item
                        fixed = fix_title(original)
                        if original != fixed:
                            changes.append((original, fixed))
                            if not dry_run:
                                main_value[i] = fixed

    if changes:
        print(f"  {'Would fix' if dry_run else 'Fixed'} {len(changes)} title(s):")
        for original, fixed in changes:
            print(f"    ✏️  '{original}' → '{fixed}'")

        if not dry_run:
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  ✅ File updated")
    else:
        print("  ✅ No changes needed")

    return len(changes)


def main():
    """Main function"""
    import sys

    dry_run = '--apply' not in sys.argv

    datasources_dir = Path('datasources')

    # Files with known errors
    files_with_errors = [
        'bbc100bestnovels.json',
        'guardianbestnovels.json',
        'lemonde100bestnovles.json',
        'modernlibrarynonfiction.json',
        'norwegian100best.json',
        'nytimes100bestnovels.json',
    ]

    print("="*80)
    print("BOOK TITLE ERROR FIXER")
    print("="*80)

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified")
        print("   Run with --apply to actually fix the files")
    else:
        print("\n⚠️  APPLY MODE - Files will be modified!")

    print(f"\nProcessing {len(files_with_errors)} file(s)...\n")

    total_changes = 0

    for filename in files_with_errors:
        file_path = datasources_dir / filename
        if file_path.exists():
            changes = fix_award_file(file_path, dry_run)
            total_changes += changes
        else:
            print(f"\n⚠️  File not found: {filename}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if dry_run:
        print(f"\n✅ Would fix {total_changes} title(s) across {len(files_with_errors)} file(s)")
        print("\nRun with --apply to apply these changes")
    else:
        print(f"\n✅ Fixed {total_changes} title(s) across {len(files_with_errors)} file(s)")

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
