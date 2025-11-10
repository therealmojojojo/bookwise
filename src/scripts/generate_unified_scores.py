#!/usr/bin/env python3
"""
Generate Award Books with Era-Neutral Scoring
Creates complete output using the ERA-NEUTRAL methodology (formerly "unified")
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scoring import BookScoreCalculator, create_calculator
from src.utils.normalizers import normalize_title, normalize_author
from src.config import settings


def generate_unified_output():
    """Generate complete scoring output using era-neutral methodology"""

    print("=" * 80)
    print("GENERATING ERA-NEUTRAL METHODOLOGY SCORES")
    print("=" * 80)
    print()

    # Initialize era-neutral calculator
    calculator = create_calculator()
    
    print("Extracting all books from data sources...")
    
    # Collect all unique books from the calculator's loaded data
    all_books = {}
    
    # From book awards
    for key, awards_list in calculator.book_awards.items():
        for award_data in awards_list:
            title = award_data.get('title', '')
            author = award_data.get('author', '')
            if title and author:
                book_key = (title, author)
                if book_key not in all_books:
                    all_books[book_key] = {
                        'title': title,
                        'author': author,
                        'awards': [],
                        'lists': [],
                        'recognitions': []
                    }
                all_books[book_key]['awards'].append(award_data)
    
    # From book lists
    for key, lists_data in calculator.book_lists.items():
        for list_entry in lists_data:
            title = list_entry.get('title', '')
            author = list_entry.get('author', '')
            if title and author:
                book_key = (title, author)
                if book_key not in all_books:
                    all_books[book_key] = {
                        'title': title,
                        'author': author,
                        'awards': [],
                        'lists': [],
                        'recognitions': []
                    }
                all_books[book_key]['lists'].append(list_entry)
    
    # From classic series
    for key, series_data in calculator.classic_series.items():
        for entry in series_data:
            title = entry.get('title', '')
            author = entry.get('author', '')
            if title and author:
                book_key = (title, author)
                if book_key not in all_books:
                    all_books[book_key] = {
                        'title': title,
                        'author': author,
                        'awards': [],
                        'lists': [],
                        'recognitions': []
                    }
                all_books[book_key]['recognitions'].append(f"Classic Series: {entry.get('series', '')}")
    
    # From educational canon
    for key, canon_data in calculator.educational_canon.items():
        for entry in canon_data:
            title = entry.get('title', '')
            author = entry.get('author', '')
            if title and author:
                book_key = (title, author)
                if book_key not in all_books:
                    all_books[book_key] = {
                        'title': title,
                        'author': author,
                        'awards': [],
                        'lists': [],
                        'recognitions': []
                    }
                all_books[book_key]['recognitions'].append(f"Educational Canon: {entry.get('canon', '')}")
    
    # From significant authors
    if hasattr(calculator, 'significant_authors'):
        for author_key, author_data in calculator.significant_authors.items():
            for book in author_data.get('books', []):
                title = book.get('title', '')
                author_name = author_data.get('author', '')
                if title and author_name:
                    book_key = (title, author_name)
                    if book_key not in all_books:
                        all_books[book_key] = {
                            'title': title,
                            'author': author_name,
                            'awards': [],
                            'lists': [],
                            'recognitions': []
                        }
                    all_books[book_key]['recognitions'].append(f"Significant Author: {author_data.get('recognition', '')}")
    
    print(f"✓ Found {len(all_books)} unique books")
    print()
    
    # Calculate unified scores for all books
    print("Calculating unified scores...")
    scored_books = []
    
    for i, (book_key, book_data) in enumerate(all_books.items(), 1):
        if i % 500 == 0:
            print(f"  Processed {i}/{len(all_books)} books...")
        
        title = book_data['title']
        author = book_data['author']
        
        # Calculate score using unified methodology
        score_obj = calculator.calculate_score(0, title, author)
        
        # Build recognition string
        recognition_parts = []
        
        # Add awards
        for award in score_obj.awards:
            if award and not award.startswith("Canonical") and not award.startswith("Pre-1970") and not award.startswith("Enduring") and not award.startswith("Established"):
                recognition_parts.append(award)
        
        # Format recognition string
        recognition_str = '; '.join(recognition_parts) if recognition_parts else ''
        
        scored_books.append({
            'title': title,
            'author': author,
            'awards_and_recognition': recognition_str,
            'final_score': score_obj.base_score,
            'scoring_details': score_obj.scoring_details
        })
    
    print(f"✓ Calculated scores for {len(scored_books)} books")
    print()
    
    # Sort by score (descending)
    scored_books.sort(key=lambda x: x['final_score'], reverse=True)
    
    # Generate output CSV
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / 'all_books_quality_scores.csv'
    
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'title', 'author', 'awards_and_recognition', 'final_score'
        ])
        writer.writeheader()
        
        for book in scored_books:
            writer.writerow({
                'title': book['title'],
                'author': book['author'],
                'awards_and_recognition': book['awards_and_recognition'],
                'final_score': book['final_score']
            })
    
    print(f"✓ Created: {csv_file}")
    print()
    
    # Generate summary report
    report_file = output_dir / 'all_books_quality_scores_REPORT.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("ERA-NEUTRAL METHODOLOGY SCORING REPORT\n")
        f.write("Timeless Quality Assessment (No Recency Bias)\n")
        f.write("=" * 100 + "\n\n")

        total_books = len(scored_books)
        avg_score = sum(b['final_score'] for b in scored_books) / total_books if total_books > 0 else 0

        f.write(f"Total Books: {total_books}\n")
        f.write(f"Average Score: {avg_score:.1f}\n")
        f.write(f"Highest Score: {scored_books[0]['final_score']:.0f}\n")
        f.write(f"Methodology: ERA-NEUTRAL (no recency boost, canonical baseline, cross-era validation)\n")
        f.write("\n\n")
        
        # Score distribution
        ranges = [
            ('Legendary (90+)', 90, 999),
            ('Exceptional (80-89)', 80, 89),
            ('Outstanding (70-79)', 70, 79),
            ('Excellent (60-69)', 60, 69),
            ('Very Good (50-59)', 50, 59),
            ('Good (40-49)', 40, 49),
            ('Solid (30-39)', 30, 39),
            ('Notable (20-29)', 20, 29),
            ('Recognized (10-19)', 10, 19),
            ('Limited (0-9)', 0, 9)
        ]
        
        f.write("SCORE DISTRIBUTION\n")
        f.write("-" * 100 + "\n")
        
        for label, min_s, max_s in ranges:
            count = sum(1 for b in scored_books if min_s <= b['final_score'] <= max_s)
            pct = (count / total_books * 100) if total_books > 0 else 0
            f.write(f"{label:<25} {count:5d} books ({pct:5.1f}%)\n")
        
        f.write("\n\n")
        
        # Top 100 books
        f.write("TOP 100 BOOKS - ERA-NEUTRAL METHODOLOGY\n")
        f.write("=" * 100 + "\n\n")
        
        for i, book in enumerate(scored_books[:100], 1):
            f.write(f"{i:3d}. {book['title']}\n")
            f.write(f"     Author: {book['author']}\n")
            f.write(f"     Score: {book['final_score']:.0f}\n")
            if book['awards_and_recognition']:
                f.write(f"     Recognition: {book['awards_and_recognition'][:150]}...\n" if len(book['awards_and_recognition']) > 150 else f"     Recognition: {book['awards_and_recognition']}\n")
            f.write("\n")
    
    print(f"✓ Created: {report_file}")
    print()
    
    print("=" * 80)
    print("ERA-NEUTRAL SCORING COMPLETE")
    print("=" * 80)
    print()
    print(f"Generated: all_books_quality_scores.csv ({len(scored_books)} books)")
    print(f"Report: all_books_quality_scores_REPORT.txt")
    print()


if __name__ == '__main__':
    generate_unified_output()

