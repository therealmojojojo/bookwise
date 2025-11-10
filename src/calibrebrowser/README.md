# Calibre Browser Module

Tools for browsing, analyzing, and generating metadata for Calibre libraries.

## Overview

This module contains scripts that interact with your Calibre library database to:
- Analyze award-winning books and authors in your collection
- Compare scored books against your library coverage
- Generate Calibre import files (metadata and tags)
- Create detailed awards breakdowns (owned and missing books)
- Find unprocessed books that haven't been quality-scored
- Clean up old output files

**All scripts use READ-ONLY database connections** - safe to run anytime.

## 🚀 Quick Start: Unified Analyzer

**Recommended:** Use the unified analyzer for all operations:

```bash
# Interactive menu (easiest)
python3 src/calibrebrowser/analyze_library.py

# Or run specific analyses
python3 src/calibrebrowser/analyze_library.py --coverage     # Coverage analysis
python3 src/calibrebrowser/analyze_library.py --awards       # Awards analysis
python3 src/calibrebrowser/analyze_library.py --imports      # Generate imports
python3 src/calibrebrowser/analyze_library.py --detail       # Awards breakdown
python3 src/calibrebrowser/analyze_library.py --unprocessed  # Find unprocessed
python3 src/calibrebrowser/analyze_library.py --all          # Run everything
python3 src/calibrebrowser/analyze_library.py --clean        # Cleanup
```

---

## Scripts

### 1. analyze_calibre_awards.py

**Purpose:** Analyze how many award-winning authors and books are in your Calibre library.

**Usage:**
```bash
cd /path/to/bookwise
python3 src/calibrebrowser/analyze_calibre_awards.py
```

**What it does:**
- Reads all 25 award JSON files from datasources
- Queries your Calibre library for matches
- Counts award-winning authors and books you own
- Shows which awards are well-represented in your collection

**Output:**
- `output/matched_authors.txt` - Award-winning authors in your library
- `output/matched_books.txt` - Award-winning books in your library
- Console report with statistics

**Performance:** ~5-10 seconds

---

### 2. analyze_calibre_coverage.py

**Purpose:** Analyze which high-quality books you own vs. missing from your library.

**Usage:**
```bash
cd /path/to/bookwise
python3 src/calibrebrowser/analyze_calibre_coverage.py
```

**What it does:**
- Compares scored books CSV with your Calibre library
- Shows coverage percentages by author and score tier
- Lists top missing books you might want to acquire
- Identifies authors with most missing high-quality books

**Output:**
- `output/calibre_owned_scored_books.csv` - Books you own with scores
- `output/calibre_missing_scored_books.csv` - High-quality books you don't own
- Console report with statistics

**Performance:** ~5-10 seconds

---

### 3. find_unprocessed_books.py

**Purpose:** Identify books in your Calibre library that haven't been quality-scored yet.

**Usage:**
```bash
cd /path/to/bookwise
python3 src/calibrebrowser/find_unprocessed_books.py
```

**What it does:**
- Loads the processed books list
- Compares with your entire Calibre library
- Identifies books not in the scored dataset
- These may be books without awards/recognition or needing addition to datasources

**Output:**
- `output/unprocessed_books.csv` - Books in library not yet scored
- Shows Calibre ID, title, author, and date added

**Performance:** ~5-10 seconds

---

### 4. generate_calibre_imports.py

**Purpose:** Create Calibre import files for updating your library with quality scores and tags.

**Usage:**
```bash
cd /path/to/bookwise
python3 src/calibrebrowser/generate_calibre_imports.py
```

**What it does:**
- Loads scored books from CSV
- Queries your Calibre library for matches
- Uses title variant matching for better accuracy
- Generates import-ready files with metadata and tags

**Output:**
- `output/calibre_metadata_updates.csv` - Complete metadata for import
- `output/calibre_tags_import.csv` - Simplified tags for easy import

**Performance:** ~10-15 seconds

---

### 5. analyze_calibre_awards_detail.py

**Purpose:** Create detailed CSV breakdowns of awards and lists for owned and missing books.

**Usage:**
```bash
cd /path/to/bookwise
python3 src/calibrebrowser/analyze_calibre_awards_detail.py
```

**What it does:**
- Loads scored books with award/list details
- Matches against your Calibre library
- Generates detailed breakdowns showing gaps in lists
- Same CSV format for owned and missing books

**Output:**
- `output/calibre_all_awards_recognitions.csv` - Awards/lists for books YOU OWN
- `output/calibre_missing_awards_recognitions.csv` - Awards/lists for books YOU DON'T OWN  
- `output/calibre_list_rankings.csv` - Ranked list positions (owned books)
- `output/calibre_lists_summary.txt` - Human-readable summary

**Example use case:** See which books you're missing from "BBC 100 Best Novels" by rank:
```csv
award_or_list,type,rank,title,author,quality_score
BBC 100 Best Novels,list,1,The Lord of the Rings,J.R.R. Tolkien,25.0  # You own
BBC 100 Best Novels,list,3,His Dark Materials,Philip Pullman,10.0    # Missing
BBC 100 Best Novels,list,7,Winnie the Pooh,A.A. Milne,10.0         # Missing
```

**Performance:** ~10-15 seconds

---

### 6. analyze_library.py (UNIFIED ANALYZER)

**Purpose:** Single entry point for all Calibre library analyses with interactive menu.

**Usage:**
```bash
# Interactive menu
cd /path/to/bookwise
python3 src/calibrebrowser/analyze_library.py

# Or run specific analyses
python3 src/calibrebrowser/analyze_library.py --coverage     # Coverage
python3 src/calibrebrowser/analyze_library.py --awards       # Awards
python3 src/calibrebrowser/analyze_library.py --imports      # Imports
python3 src/calibrebrowser/analyze_library.py --detail       # Awards detail
python3 src/calibrebrowser/analyze_library.py --unprocessed  # Unprocessed
python3 src/calibrebrowser/analyze_library.py --all          # Everything
python3 src/calibrebrowser/analyze_library.py --clean        # Cleanup
```

**What it does:**
- Provides interactive menu for all analyses
- Runs multiple analyses in sequence
- Tracks progress and handles errors gracefully
- Cleanup old output files

**Analyses included:**
1. Coverage Analysis (analyze_calibre_coverage.py)
2. Awards Analysis (analyze_calibre_awards.py)
3. Generate Calibre Imports (generate_calibre_imports.py)
4. Detailed Awards Breakdown (analyze_calibre_awards_detail.py)
5. Find Unprocessed Books (find_unprocessed_books.py)

**Performance:** ~30-60 seconds for full analysis (all 5 scripts)

---

## Configuration

All scripts use centralized configuration from `src/config/settings.py` which loads from `.env`:

```python
from src.config.settings import settings

CALIBRE_DB_PATH = settings.CALIBRE_DB_PATH
DATASOURCES_DIR = settings.DATASOURCES_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
```

Required `.env` settings:
```bash
CALIBRE_DB_PATH=/path/to/your/Calibre/metadata.db
DATASOURCES_DIR=/path/to/bookwise/datasources
OUTPUT_DIR=/path/to/bookwise/output
```

---

## Typical Workflow

1. **Analyze Awards** (see what award-winning books you have):
   ```bash
   python3 src/calibrebrowser/analyze_calibre_awards.py
   ```

2. **Analyze Coverage** (see what high-quality books you're missing):
   ```bash
   python3 src/calibrebrowser/analyze_calibre_coverage.py
   ```

3. **Create Calibre Updates** (after acquiring new books):
   ```bash
   python3 src/calibrebrowser/generate_calibre_metadata_updates.py
   ```

4. **Find Unprocessed** (identify books not in scoring system):
   ```bash
   python3 src/calibrebrowser/find_unprocessed_books.py
   ```

---

### 5. Cleanup Output Files

**Purpose:** Remove old analysis output files to free up space or start fresh.

**Usage:**
```bash
# Interactive prompt with confirmation
python3 -m src.calibrebrowser.calibre_analyzer --clean

# See what would be deleted (safe preview)
python3 -m src.calibrebrowser.calibre_analyzer --clean --dry-run

# Force cleanup without confirmation
python3 -m src.calibrebrowser.calibre_analyzer --clean --force

# Cleanup then run fresh analysis
python3 -m src.calibrebrowser.calibre_analyzer --clean --coverage
```

**What it does:**
- Lists all output files with their sizes
- Shows total space that would be freed
- Safely removes files with confirmation (unless --force)
- Can be combined with other commands

**Output files cleaned:**
- Coverage analysis: `calibre_owned_scored_books.csv`, `calibre_missing_scored_books.csv`
- Awards analysis: `matched_authors.txt`, `matched_books.txt`
- Metadata generation: `calibre_metadata_updates.csv`, `calibre_tags_import.csv`, etc.
- Unprocessed books: `unprocessed_books.csv`
- Award analysis intermediate: `all_award_books_with_scores.csv`

**Files EXCLUDED from cleanup (preserved):**
- `all_books_quality_scores.csv` - Core scoring output
- `all_books_quality_scores_REPORT.txt` - Core scoring report

**Safety features:**
- Shows file list and total size before deletion
- Requires confirmation (type "yes")
- Use `--dry-run` to preview without deleting
- Use `--force` for automation/scripting

**Performance:** Instant

---

## Safety Notes

- ✅ All scripts use **READ-ONLY** database connections
- ✅ Safe to run anytime (even while Calibre is running)
- ✅ Scripts handle large libraries efficiently (12,000+ books)
- ✅ Fuzzy matching handles slight name/title variations
- ✅ All output goes to `output/` directory

**Never modify Calibre database structure** - See `calibredatabase/PROJECT_RULES.md` for complete safety guidelines.

---

## Dependencies

- Python 3.7+
- sqlite3 (built-in)
- Standard library modules only

---

## Related Documentation

- **Main README**: `/README.md` - Complete project documentation
- **Source Code**: `/src/README.md` - Module documentation
- **Calibre Database**: `/calibredatabase/README.md` - Database integration guide
- **Safety Rules**: `/calibredatabase/PROJECT_RULES.md` - Critical database rules

