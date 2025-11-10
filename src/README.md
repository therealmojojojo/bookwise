# Book Recommendation System - Source Code

This directory contains the modular source code for the Book Quality Score Calculator and recommendation system.

## Directory Structure

```
src/
├── config/                     # Configuration management
│   ├── __init__.py
│   ├── settings.py            # Loads settings from .env file
│   └── award_config.py        # Award and list definitions with scoring weights
│
├── scoring/                    # Score calculation engine
│   ├── __init__.py
│   ├── models.py              # Data models (BookScore)
│   ├── calculator.py          # Era-neutral BookScoreCalculator
│   ├── data_loader.py         # Data loading and parsing
│   ├── scoring_engine.py      # Core scoring logic
│   └── constants.py           # Scoring constants and thresholds
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── normalizers.py         # Text normalization for fuzzy matching
│   ├── parser.py              # Parse data files
│   └── database.py            # Calibre database read-only access
│
├── calibrebrowser/             # Calibre library browser and analysis tools
│   ├── __init__.py
│   ├── analyze_calibre_awards.py         # Analyze award-winning books in library
│   ├── analyze_calibre_coverage.py       # Compare scored books vs. library
│   ├── find_unprocessed_books.py         # Find unscored books in library
│   └── generate_calibre_metadata_updates.py  # Generate import files
│
├── dataenrichment/             # AI-powered metadata enrichment
│   ├── __init__.py
│   └── (various enrichment scripts)
│
├── librarian/                  # MCP server for AI integration
│   ├── __init__.py
│   └── (API server components)
│
└── scripts/                    # Core scoring and generation scripts
    ├── __init__.py
    ├── generate_unified_scores.py         # Generate quality scores
    └── generate_excel_workbook.py         # Generate Excel workbook
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `python-dotenv` for environment configuration.

### 2. Configure Environment

Copy `env.template` to `.env` and update with your paths:

```bash
cp env.template .env
nano .env  # Edit with your actual paths
```

**Required settings:**
```bash
CALIBRE_DB_PATH=/path/to/Calibre/metadata.db
DATASOURCES_DIR=/path/to/bookwise/datasources
OUTPUT_DIR=/path/to/bookwise/output
```

See [env.template](../env.template) for all available configuration options.

### 3. Generate Scores

Run the primary scoring script:

```bash
python src/scripts/generate_unified_scores.py
```

This automatically:
- Loads all data sources (awards, lists, significant books, canonical authors)
- Extracts unique books from all sources
- Calculates era-neutral quality scores
- Generates CSV and report files

**Output:**
- `output/all_books_quality_scores.csv`
- `output/all_books_quality_scores_REPORT.txt`

### 4. Generate Excel Workbook (Optional)

Create an interactive Excel workbook with dashboards and analysis:

```bash
python src/scripts/generate_excel_workbook.py
```

**Output:**
- `output/bookwise_library.xlsx` - Comprehensive workbook with 9 sheets

See `EXCEL_FILE_GUIDE.md` for detailed workbook usage instructions.

## Scoring Methodology

The system uses **era-neutral quality assessment** to fairly evaluate books across all time periods.

### Base Scoring (0-135 points)

1. **Author Career Awards** (0-30 pts)
   - Nobel Prize in Literature: 30 points
   - Miguel de Cervantes Prize: 30 points
   - Applied to ALL books by winning authors

2. **Book-Specific Awards** (0-60 pts, capped)
   - Major Awards (25 pts): Pulitzer, Booker, Man Booker
   - Significant Awards (15 pts): National Book Award, NBCC, Dublin Literary
   - Notable Awards (12 pts): LA Times, Kirkus Prize
   - Genre Awards (10 pts): Hugo, Nebula
   - Multiple awards sum together, capped at 60 points

3. **Author Achievement Bonus** (0-15 pts)
   - Base: 10 points for other books by major award-winning authors
   - Critical Acclaim: +5 points if author won awards for 2+ different books
   - Only applied if the book itself didn't win an award

4. **List Appearances** (0-25 pts, capped)
   - Modern Library, NYTimes, Guardian, Time, BBC, etc.
   - Ranked lists: Top 5 (15 pts), Top 20 (10 pts), Top 50 (7 pts), Top 100 (5 pts)
   - Unranked lists: 10 points (Harold Bloom Canon)
   - Goodreads Choice: 3 points, NEA Big Read: 5 points

5. **Classic Series** (0-20 pts, capped)
   - Penguin Classics: 5 points
   - Multiple series appearances stack up to cap

6. **Educational Canon** (0-15 pts, capped)
   - St. John's College: 8 points
   - Columbia/UChicago: 7 points
   - Multiple canon appearances stack up to cap

### Era-Neutral Enhancements (0-70 points)

These ensure pre-1970 classics compete fairly with contemporary award winners:

1. **Canonical Baseline Points** (0-30 pts)
   - Tier S (Universal Giants): +30 pts
     - Shakespeare, Tolstoy, Dostoevsky, Cervantes, Homer
   - Tier A (Essential Moderns): +20 pts
     - Joyce, Woolf, Kafka, Mann, Proust, Fitzgerald
   - Tier B (Important Voices): +15 pts
     - Regional canonical authors, important literary figures
   - Based on `datasources/canonical_authors_tier_*.json` (429 works total)

2. **Cross-Era Validation Bonus** (0-20 pts)
   - Lists from 3+ decades: +20 pts ("Enduring Masterpiece")
   - Lists from 2+ decades: +10 pts ("Established Classic")
   - Rewards sustained recognition over time
   - Applied to ALL books regardless of era

3. **Underrecognition Correction** (0-40 pts, pre-1970 only)
   - Only applied if canonical work scores below tier minimum
   - Tier S minimum: 80 pts
   - Tier A minimum: 70 pts
   - Tier B minimum: 60 pts
   - Ensures canonical masterpieces compete fairly

**Key Principle:** No recency boost. Publication date provides no advantage or disadvantage.

See main [README.md](../README.md) for detailed methodology documentation.

---

## Module Documentation

### config.settings
Loads configuration from `.env` file and provides settings throughout the application.

**Key settings:**
- `CALIBRE_DB_PATH`: Path to Calibre database
- `DATASOURCES_DIR`: Path to datasources folder
- `OUTPUT_DIR`: Path for output files
- `SCORE_*`: Scoring weight configurations

### config.award_config
Defines all awards, lists, and series with their point values and metadata.

**Key structures:**
- `AWARD_FILES`: Book-specific awards (Pulitzer, Booker, etc.)
- `CAREER_AWARD_FILES`: Author career awards (Nobel, Cervantes)
- `LIST_FILES`: Best-of lists with ranking-based scoring
- `CLASSIC_SERIES_FILES`: Classic series (Penguin Classics)
- `EDUCATIONAL_CANON_FILES`: Academic canon lists

### scoring.calculator
`BookScoreCalculator` class that implements the era-neutral scoring methodology using composition.

**Key methods:**
- `calculate_score(book_id, title, author, publication_year)`: Main scoring function
- Returns `BookScore` object with complete breakdown

**Architecture:**
- Uses `BookDataLoader` for data management
- Uses `ScoringEngine` for score calculation
- Maintains backward compatibility through properties

**Features:**
- Loads canonical authors (429 works)
- Applies canonical baseline points
- Calculates cross-era validation bonuses
- Applies underrecognition correction

**This is the PRIMARY scoring system used by the project.**

### scoring.data_loader
`BookDataLoader` class that handles loading and parsing of all data sources.

**Key methods:**
- `load_all()`: Load all award, list, and canonical data
- Supports multiple JSON formats
- Error handling for missing files

### scoring.scoring_engine
`ScoringEngine` class that contains pure scoring logic.

**Key methods:**
- `calculate_score()`: Core scoring algorithm
- `_apply_canonical_baseline()`: Baseline points for canonical works
- `_apply_cross_era_validation()`: Multi-decade recognition bonus
- `_apply_underrecognition_correction()`: Pre-1970 adjustment

### scoring.models
Data classes for representing book scores and scoring details.

**Key classes:**
- `BookScore`: Complete score with breakdown and awards list

### scoring.constants
Scoring constants and thresholds.

**Key constants:**
- Tier baselines (S: 30, A: 20, B: 15)
- Tier minimums (S: 80, A: 70, B: 60)
- Cross-era validation bonuses
- Underrecognition correction limits

### utils.normalizers
Text normalization functions for fuzzy matching of titles and authors.

**Key functions:**
- `normalize_title(title, author)`: Creates match key for books
- `normalize_author(author)`: Creates match key for authors
- Handles accents, punctuation, articles (the/a/an), case

### utils.parser
Parses curated book list files to extract book information.

### utils.database
Read-only access to Calibre database for book metadata.

**Note:** All database access is read-only to comply with Calibre safety rules.

---

## Core Scripts (scripts/ directory)

### generate_unified_scores.py
**Purpose:** Generate complete era-neutral quality scores for all books in datasources.

**Usage:**
```bash
python src/scripts/generate_unified_scores.py
```

**What it does:**
- Uses `BookScoreCalculator` for era-neutral scoring
- Loads all data sources (awards, lists, significant books, canonical authors)
- Extracts all unique books automatically
- Calculates quality scores with canonical baseline and cross-era validation
- Generates comprehensive CSV and human-readable report

**Output:**
- `output/all_books_quality_scores.csv` - Complete scored books
- `output/all_books_quality_scores_REPORT.txt` - Detailed report

**Performance:** ~10-15 seconds

### generate_excel_workbook.py
**Purpose:** Generate an interactive Excel workbook with library analysis.

**Usage:**
```bash
python src/scripts/generate_excel_workbook.py
```

**What it does:**
- Reads scored books CSV and Calibre ownership data
- Creates 9 comprehensive worksheets
- Adds interactive features (filtering, color coding, formulas)
- Generates shopping lists and statistics

**Output:**
- `output/bookwise_library.xlsx` - Interactive Excel workbook

**Sheets included:**
1. Dashboard - Interactive overview
2. All Books - Master database with filtering
3. Owned Books - Your collection sorted by score
4. Missing Books - High-quality books to acquire
5. Shopping List - Top 50 unowned books
6. Statistics - Auto-calculated metrics
7-9. Import sheets for Calibre

See `EXCEL_FILE_GUIDE.md` for detailed usage instructions.

---

## Calibre Browser Tools (calibrebrowser/ directory)

Tools for browsing, analyzing, and generating metadata for Calibre libraries. All scripts use **read-only** database connections.

See **[calibrebrowser/README.md](calibrebrowser/README.md)** for complete documentation.

### 1. analyze_calibre_awards.py
Analyze how many award-winning authors and books are in your library.

**Usage:**
```bash
python src/calibrebrowser/analyze_calibre_awards.py
```

---

### 2. analyze_calibre_coverage.py
Analyze which high-quality books you own vs. missing from your library.

**Usage:**
```bash
python src/calibrebrowser/analyze_calibre_coverage.py
```

---

### 3. find_unprocessed_books.py
Identify books in your Calibre library that haven't been quality-scored yet.

**Usage:**
```bash
python src/calibrebrowser/find_unprocessed_books.py
```

---

### 4. generate_calibre_metadata_updates.py
Create Calibre import files for updating your library with quality scores.

**Usage:**
```bash
python src/calibrebrowser/generate_calibre_metadata_updates.py
```

---

### Typical Workflow

1. **Generate Scores** (monthly or when datasources updated):
   ```bash
   python src/scripts/generate_unified_scores.py
   ```

2. **Generate Excel Workbook** (for easy analysis and shopping):
   ```bash
   python src/scripts/generate_excel_workbook.py
   ```
   Then open `output/bookwise_library.xlsx` for interactive exploration

3. **Analyze Coverage** (see what high-quality books you're missing):
   ```bash
   python src/calibrebrowser/analyze_calibre_coverage.py
   ```

4. **Create Calibre Updates** (after acquiring new books):
   ```bash
   python src/calibrebrowser/generate_calibre_metadata_updates.py
   ```

5. **Check Awards** (curiosity - see your award-winning books):
   ```bash
   python src/calibrebrowser/analyze_calibre_awards.py
   ```

6. **Find Unprocessed** (identify books not in scoring system):
   ```bash
   python src/calibrebrowser/find_unprocessed_books.py
   ```

### Notes

- All Calibre browser scripts use **read-only** database connections (safe to run anytime)
- Scripts handle large libraries efficiently (12,000+ books)
- Fuzzy matching handles slight name/title variations
- All output goes to `output/` directory

---

## Development

### Adding New Data Sources

1. Add JSON file to `datasources/` following the unified format
2. Update `src/config/award_config.py` with the new file
3. Define point values and metadata
4. Test with `generate_unified_scores.py`

### Modifying Scoring Weights

Edit `src/config/award_config.py` to change point values for:
- Award tiers (major, significant, notable, genre)
- List rankings (top 5, top 20, etc.)
- Classic series and educational canon

Or use `.env` file to override specific values:
```bash
SCORE_MAJOR_AWARD=25
SCORE_LIST_TOP5=15
```

### Testing Changes

Run the primary scoring script and compare output:
```bash
python src/scripts/generate_unified_scores.py
```

Check the report file for score distribution and validate against expected results.

---

## Additional Documentation

- **Main README**: [../README.md](../README.md) - Complete project documentation
- **Data Sources Guide**: [../datasources/DATA_SOURCES_GUIDE.md](../datasources/DATA_SOURCES_GUIDE.md)
- **Calibre Database**: [../calibredatabase/README.md](../calibredatabase/README.md)

---

## Archive

Deprecated scripts and legacy code are in `../archive/` including:
- Old scoring methodologies
- One-time data migration scripts
- Historical comparison tools
- Encoding fix utilities

See `../archive/scripts/README.md` for details.
