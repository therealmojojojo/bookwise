#!/usr/bin/env python3
"""
Calibre Library Analyzer - Unified Entry Point
A single command-line interface for all Calibre library analysis tools

Run from anywhere:
  python3 src/calibrebrowser/analyze_library.py
  python3 src/calibrebrowser/analyze_library.py --coverage
  python3 src/calibrebrowser/analyze_library.py --clean
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from src.config.settings import settings


def show_menu():
    """Display interactive menu"""
    print("\n" + "=" * 80)
    print("CALIBRE LIBRARY ANALYZER")
    print("=" * 80)
    print("\nAvailable Analyses:")
    print()
    print("  1. Coverage Analysis")
    print("     - Compare your library against all scored books")
    print("     - Shows score distribution and top books owned/missing")
    print("     - Output: calibre_enrichment_ready.jsonl + bookwise_library.xlsx")
    print()
    print("  2. Awards Analysis")
    print("     - Analyzes which specific awards are in your library")
    print("     - Shows per-award statistics and author coverage")
    print("     - Output: matched_authors.txt + matched_books.txt")
    print()
    print("  3. Generate Calibre Imports")
    print("     - Creates CSV files for importing metadata and tags into Calibre")
    print("     - Output: calibre_metadata_updates.csv + calibre_tags_import.csv")
    print()
    print("  4. Detailed Awards Breakdown")
    print("     - Creates detailed CSVs showing owned and missing books by award/list")
    print("     - Output: calibre_all_awards_recognitions.csv + calibre_missing_awards_recognitions.csv")
    print()
    print("  5. Find Unprocessed Books")
    print("     - Lists books in your library not yet quality-scored")
    print("     - Helps identify books to add to datasources")
    print("     - Output: unprocessed_books.csv")
    print()
    print("  6. Full Analysis (Run All)")
    print("     - Runs all analyses in sequence")
    print("     - Generates all output files")
    print()
    print("  7. Cleanup Output Files")
    print("     - Remove old analysis output files")
    print("     - Frees up space and starts fresh")
    print()
    print("  0. Exit")
    print()
    print("=" * 80)


def run_excel_generation():
    """Generate Excel workbook"""
    print("\n📊 Generating Excel Workbook...")
    print("-" * 80)

    # Import and run the Excel generation script
    import subprocess
    excel_script = Path(__file__).parent.parent.parent / 'scripts' / 'utilities' / 'generate_excel_workbook.py'

    if not excel_script.exists():
        print(f"⚠️  Warning: Excel generation script not found at {excel_script}")
        print("   Skipping Excel generation.")
        return

    try:
        result = subprocess.run(
            ['python3', str(excel_script)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating Excel workbook: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        raise

def run_coverage_analysis():
    """Run coverage analysis and generate Excel workbook"""
    print("\n🔍 Running Coverage Analysis...")
    print("-" * 80)
    from src.calibrebrowser import analyze_calibre_coverage
    analyze_calibre_coverage.main()

    # After coverage analysis, generate Excel workbook
    run_excel_generation()


def run_awards_analysis():
    """Run awards analysis"""
    print("\n🏆 Running Awards Analysis...")
    print("-" * 80)
    from src.calibrebrowser import analyze_calibre_awards
    analyze_calibre_awards.main()


def run_import_generation():
    """Generate Calibre import files"""
    print("\n📝 Generating Calibre Import Files...")
    print("-" * 80)
    from src.calibrebrowser import generate_calibre_imports
    generate_calibre_imports.main()

def run_awards_detail_analysis():
    """Run detailed awards analysis"""
    print("\n🏆 Analyzing Awards by List/Award...")
    print("-" * 80)
    from src.calibrebrowser import analyze_calibre_awards_detail
    analyze_calibre_awards_detail.main()


def run_unprocessed_finder():
    """Find unprocessed books"""
    print("\n📚 Finding Unprocessed Books...")
    print("-" * 80)
    from src.calibrebrowser import find_unprocessed_books
    find_unprocessed_books.main()


def run_full_analysis():
    """Run all analyses"""
    print("\n🚀 Running Full Analysis (All Tools)...")
    print("=" * 80)
    
    analyses = [
        ("Coverage Analysis", run_coverage_analysis),
        ("Awards Analysis", run_awards_analysis),
        ("Generate Calibre Imports", run_import_generation),
        ("Detailed Awards Breakdown", run_awards_detail_analysis),
        ("Unprocessed Books Finder", run_unprocessed_finder),
    ]
    
    for i, (name, func) in enumerate(analyses, 1):
        print(f"\n[{i}/5] {name}")
        print("=" * 80)
        try:
            func()
            print(f"✓ {name} completed successfully")
        except Exception as e:
            print(f"✗ Error in {name}: {e}")
            if input("\nContinue with remaining analyses? (y/n): ").lower() != 'y':
                break
    
    print("\n" + "=" * 80)
    print("FULL ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nAll output files saved to: {settings.OUTPUT_DIR}")


def cleanup_output_files(dry_run=False, force=False):
    """Clean up output files from previous analyses"""
    import os
    
    output_dir = Path(settings.OUTPUT_DIR)
    
    # Define output files that can be cleaned
    # NOTE: Excludes all_books_quality_scores.csv and _REPORT.txt
    # as these are the core scoring outputs (not Calibre-specific)
    output_files = [
        # Coverage analysis (new format)
        'calibre_enrichment_ready.jsonl',
        'bookwise_library.xlsx',

        # Legacy coverage analysis (deprecated)
        'calibre_owned_scored_books.csv',
        'calibre_missing_scored_books.csv',

        # Awards analysis
        'matched_authors.txt',
        'matched_books.txt',
        
        # Calibre import files
        'calibre_metadata_updates.csv',
        'calibre_tags_import.csv',
        
        # Detailed awards breakdown
        'calibre_list_rankings.csv',
        'calibre_all_awards_recognitions.csv',
        'calibre_missing_awards_recognitions.csv',
        'calibre_lists_summary.txt',
        
        # Unprocessed books
        'unprocessed_books.csv',
        
        # Legacy/deprecated files
        'calibre_missing_awards_books.csv',  # Old name
        'calibre_update_commands.sh',        # Removed feature
        'all_award_books_with_scores.csv',   # Intermediate file
    ]
    
    print("\n🧹 Cleanup Output Files")
    print("=" * 80)
    print()
    
    # Check which files exist
    existing_files = []
    total_size = 0
    
    for filename in output_files:
        filepath = output_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            existing_files.append((filename, size))
            total_size += size
    
    if not existing_files:
        print("✓ No output files to clean - directory is already clean!")
        return
    
    # Display files
    print(f"Found {len(existing_files)} output file(s):")
    print()
    for filename, size in existing_files:
        size_kb = size / 1024
        if size_kb < 1024:
            print(f"  • {filename:<50} ({size_kb:>8.1f} KB)")
        else:
            size_mb = size_kb / 1024
            print(f"  • {filename:<50} ({size_mb:>8.2f} MB)")
    
    print()
    total_mb = total_size / (1024 * 1024)
    print(f"Total size: {total_mb:.2f} MB")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - No files will be deleted")
        return
    
    # Confirm deletion
    if not force:
        print("⚠️  This will permanently delete these files!")
        response = input("Continue with cleanup? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("\n✗ Cleanup cancelled")
            return
    
    # Delete files
    print()
    deleted_count = 0
    failed_count = 0
    
    for filename, size in existing_files:
        filepath = output_dir / filename
        try:
            filepath.unlink()
            print(f"  ✓ Deleted: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Failed to delete {filename}: {e}")
            failed_count += 1
    
    print()
    print("=" * 80)
    print(f"✓ Cleanup complete!")
    print(f"  Deleted: {deleted_count} file(s) ({total_mb:.2f} MB freed)")
    if failed_count > 0:
        print(f"  Failed: {failed_count} file(s)")
    print("=" * 80)


def interactive_mode():
    """Run in interactive menu mode"""
    while True:
        show_menu()
        
        try:
            choice = input("Select option (0-7): ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye!")
                sys.exit(0)
            elif choice == '1':
                run_coverage_analysis()
            elif choice == '2':
                run_awards_analysis()
            elif choice == '3':
                run_import_generation()
            elif choice == '4':
                run_awards_detail_analysis()
            elif choice == '5':
                run_unprocessed_finder()
            elif choice == '6':
                run_full_analysis()
            elif choice == '7':
                cleanup_output_files(dry_run=False, force=False)
            else:
                print("\n❌ Invalid option. Please select 0-7.")
                continue
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Calibre Library Analyzer - Unified analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive menu (default)
  python analyze_library.py
  
  # Run specific analysis
  python analyze_library.py --coverage           # Coverage analysis
  python analyze_library.py --awards             # Awards analysis
  python analyze_library.py --imports            # Generate Calibre imports
  python analyze_library.py --detail             # Detailed awards breakdown
  python analyze_library.py --unprocessed        # Find unprocessed books
  
  # Run all analyses
  python analyze_library.py --all
  
  # Cleanup output files
  python analyze_library.py --clean                    # With confirmation
  python analyze_library.py --clean --dry-run          # See what would be deleted
  python analyze_library.py --clean --force            # No confirmation
  python analyze_library.py --clean --coverage         # Clean then run coverage
  
  # Quiet mode (minimal output)
  python analyze_library.py --coverage --quiet
        """
    )
    
    # Analysis options
    parser.add_argument('-c', '--coverage', action='store_true',
                        help='Run coverage analysis (scored books in your library)')
    parser.add_argument('-a', '--awards', action='store_true',
                        help='Run awards analysis (award-winning books/authors)')
    parser.add_argument('-i', '--imports', action='store_true',
                        help='Generate Calibre import files (metadata and tags)')
    parser.add_argument('-d', '--detail', action='store_true',
                        help='Generate detailed awards breakdown by list/award')
    parser.add_argument('-u', '--unprocessed', action='store_true',
                        help='Find unprocessed books in library')
    parser.add_argument('--all', action='store_true',
                        help='Run all analyses')
    
    # Cleanup options
    parser.add_argument('--clean', action='store_true',
                        help='Clean up output files from previous analyses')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted (use with --clean)')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Force cleanup without confirmation (use with --clean)')
    
    # Options
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode (minimal output)')
    parser.add_argument('--interactive', action='store_true',
                        help='Force interactive menu mode')
    
    args = parser.parse_args()
    
    # If no arguments or --interactive, run interactive mode
    if len(sys.argv) == 1 or args.interactive:
        interactive_mode()
        return
    
    # Command-line mode
    try:
        # Handle cleanup first if requested
        if args.clean:
            cleanup_output_files(dry_run=args.dry_run, force=args.force)
            # Exit after cleanup unless other analyses are requested
            if not (args.coverage or args.awards or args.imports or args.detail or args.unprocessed or args.all):
                sys.exit(0)
        
        if args.all:
            run_full_analysis()
        else:
            ran_something = args.clean  # Count cleanup as doing something
            
            if args.coverage:
                run_coverage_analysis()
                ran_something = True
            
            if args.awards:
                run_awards_analysis()
                ran_something = True
            
            if args.imports:
                run_import_generation()
                ran_something = True
            
            if args.detail:
                run_awards_detail_analysis()
                ran_something = True
            
            if args.unprocessed:
                run_unprocessed_finder()
                ran_something = True
            
            if not ran_something:
                print("No analysis selected. Use --help for options.")
                sys.exit(1)
        
        print("\n✓ Analysis complete!")
        print(f"Output files saved to: {settings.OUTPUT_DIR}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
