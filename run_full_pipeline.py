#!/usr/bin/env python3
"""
BookWise Full Pipeline Runner

Executes the complete BookWise workflow from start to finish:
1. Analyze Calibre library (coverage, awards, generate reports)
2. Generate enrichment input (find books needing AI tags/embeddings)
3. Enrich books (Claude API + OpenAI embeddings + ChromaDB)
4. Update Calibre (import AI-generated tags via calibredb)
5. Re-analyze library (refresh reports with updated data)

Usage:
    python3 run_full_pipeline.py                    # Full pipeline
    python3 run_full_pipeline.py --skip-analysis    # Skip initial analysis
    python3 run_full_pipeline.py --skip-enrichment  # Skip enrichment phase
    python3 run_full_pipeline.py --dry-run          # Show what would run
    python3 run_full_pipeline.py --batch-size 50    # Limit enrichment to 50 books
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime
import time

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

def print_step(step_num, total_steps, message):
    """Print step indicator"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Step {step_num}/{total_steps}] {message}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-' * 80}{Colors.ENDC}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")

def run_command(cmd, description, dry_run=False, ignore_errors=False):
    """Execute a shell command and handle errors"""
    print(f"\n{Colors.CYAN}→ {description}...{Colors.ENDC}")
    print(f"  Command: {' '.join(cmd)}")

    if dry_run:
        print_info("DRY RUN - Command not executed")
        return True

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print_success(f"{description} completed")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print_warning(f"{description} failed (continuing anyway)")
            return True
        else:
            print_error(f"{description} failed with exit code {e.returncode}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Run the complete BookWise pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Steps:
  1. Initial Analysis    - Analyze Calibre library, generate coverage reports
  2. Generate Input      - Find books needing enrichment
  3. Enrich Books        - Generate AI tags/themes and embeddings
  4. Update Calibre      - Import tags to Calibre database
  5. Final Analysis      - Re-analyze with updated data

Examples:
  # Run everything
  python3 run_full_pipeline.py

  # Skip initial analysis (if already done recently)
  python3 run_full_pipeline.py --skip-analysis

  # Dry run to see what would execute
  python3 run_full_pipeline.py --dry-run

  # Process only 50 books (testing)
  python3 run_full_pipeline.py --batch-size 50
        """
    )

    parser.add_argument('--skip-analysis', action='store_true',
                        help='Skip initial library analysis')
    parser.add_argument('--skip-enrichment', action='store_true',
                        help='Skip book enrichment phase')
    parser.add_argument('--skip-calibre-update', action='store_true',
                        help='Skip Calibre tag import')
    parser.add_argument('--skip-final-analysis', action='store_true',
                        help='Skip final re-analysis')
    parser.add_argument('--batch-size', type=int,
                        help='Limit enrichment to N books (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would run without executing')
    parser.add_argument('--resume-enrichment', action='store_true',
                        help='Resume enrichment from where it left off')

    args = parser.parse_args()

    # Validate we're in the project root
    project_root = Path(__file__).parent
    if not (project_root / 'src').exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)

    # Print pipeline overview
    print_header("BookWise Full Pipeline Runner")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {project_root}")

    if args.dry_run:
        print_warning("DRY RUN MODE - No commands will be executed")

    # Count total steps
    total_steps = 5
    current_step = 0

    start_time = time.time()

    # =========================================================================
    # STEP 1: Initial Analysis
    # =========================================================================
    if not args.skip_analysis:
        current_step += 1
        print_step(current_step, total_steps, "Initial Library Analysis")
        print_info("Running coverage analysis, awards analysis, and generating reports")

        success = run_command(
            ['python3', 'src/calibrebrowser/analyze_library.py', '--all'],
            "Library analysis",
            dry_run=args.dry_run
        )

        if not success and not args.dry_run:
            print_error("Initial analysis failed. Cannot continue.")
            sys.exit(1)
    else:
        print_info("Skipping initial analysis (--skip-analysis)")

    # =========================================================================
    # STEP 2: Generate Enrichment Input
    # =========================================================================
    if not args.skip_enrichment:
        current_step += 1
        print_step(current_step, total_steps, "Generate Enrichment Input")
        print_info("Finding books that need AI enrichment")

        success = run_command(
            ['python3', 'src/dataenrichment/generate_enrichment_input.py', '--force-regenerate'],
            "Generate enrichment input",
            dry_run=args.dry_run
        )

        if not success and not args.dry_run:
            print_error("Input generation failed. Cannot continue.")
            sys.exit(1)
    else:
        print_info("Skipping enrichment preparation")

    # =========================================================================
    # STEP 3: Enrich Books (Claude + OpenAI + ChromaDB)
    # =========================================================================
    if not args.skip_enrichment:
        current_step += 1
        print_step(current_step, total_steps, "Enrich Books with AI")
        print_info("Generating tags, themes, and embeddings (this may take several minutes)")

        cmd = ['python3', 'src/dataenrichment/enrich_books.py', '--yes']

        if args.batch_size:
            cmd.extend(['--batch-size', str(args.batch_size)])
            print_info(f"Processing limited to {args.batch_size} books")

        if args.resume_enrichment:
            cmd.append('--resume')
            print_info("Resuming from previous run")

        success = run_command(
            cmd,
            "Book enrichment",
            dry_run=args.dry_run
        )

        if not success and not args.dry_run:
            print_error("Enrichment failed. Cannot continue.")
            sys.exit(1)
    else:
        print_info("Skipping enrichment phase (--skip-enrichment)")

    # =========================================================================
    # STEP 4: Update Calibre Database
    # =========================================================================
    if not args.skip_calibre_update:
        current_step += 1
        print_step(current_step, total_steps, "Update Calibre Database")
        print_info("Importing AI-generated tags to Calibre")
        print_warning("Make sure Calibre GUI is closed!")

        # Give user time to close Calibre
        if not args.dry_run:
            print("\nWaiting 5 seconds for you to close Calibre...")
            time.sleep(5)

        success = run_command(
            ['python3', 'src/dataenrichment/add_tags_to_calibre.py', '--yes'],
            "Calibre tag import",
            dry_run=args.dry_run,
            ignore_errors=False  # Don't ignore errors here - important step
        )

        if not success and not args.dry_run:
            print_error("Calibre update failed. Cannot continue.")
            print_info("Make sure Calibre GUI is closed and try again")
            sys.exit(1)
    else:
        print_info("Skipping Calibre update (--skip-calibre-update)")

    # =========================================================================
    # STEP 5: Final Re-Analysis
    # =========================================================================
    if not args.skip_final_analysis:
        current_step += 1
        print_step(current_step, total_steps, "Final Library Re-Analysis")
        print_info("Regenerating reports with updated data")

        success = run_command(
            ['python3', 'src/calibrebrowser/analyze_library.py', '--all'],
            "Final analysis",
            dry_run=args.dry_run
        )

        if not success and not args.dry_run:
            print_warning("Final analysis failed (non-critical)")
    else:
        print_info("Skipping final analysis (--skip-final-analysis)")

    # =========================================================================
    # COMPLETION SUMMARY
    # =========================================================================
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print_header("Pipeline Complete!")
    print(f"Total time: {minutes}m {seconds}s")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not args.dry_run:
        print("\n" + Colors.BOLD + "Next Steps:" + Colors.ENDC)
        print("  1. Open Calibre to see the updated tags and metadata")
        print("  2. Check output/enrichment/ for enrichment logs")
        print("  3. Check output/ for analysis reports and Excel workbook")
        print("  4. Test semantic search: python3 src/dataenrichment/search_books.py 'your query'")

    print("\n" + Colors.GREEN + "✓ All done!" + Colors.ENDC + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Pipeline interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
