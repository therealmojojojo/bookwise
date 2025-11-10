# Book Enrichment Pipeline

AI-powered metadata generation and semantic search for Calibre libraries.

## Overview

Enriches books with AI-generated tags, themes, descriptions, and vector embeddings for semantic search.

**Pipeline**: Calibre DB + Quality Scores → Claude API → OpenAI Embeddings → ChromaDB

**Data Storage**:
- **ChromaDB** (`~/Library/Application Support/bookwise/vectors/`): Embeddings + metadata (primary source)
- **Calibre**: AI tags imported via `calibredb`
- **Status files** (`output/enrichment/`): Progress tracking

## Quick Start

```bash
# 1. Generate input (finds un-enriched books)
python3 src/dataenrichment/generate_enrichment_input.py

# 2. Enrich with AI
python3 src/dataenrichment/enrich_books.py --yes

# 3. Import tags to Calibre
python3 src/dataenrichment/add_tags_to_calibre.py --yes

# 4. Check status
python3 src/dataenrichment/check_enrichment_status.py

# 5. Test search
python3 src/dataenrichment/search_books.py "books about resilience"
```

## Prerequisites

```bash
# Install dependencies
pip install anthropic openai chromadb

# Configure .env
CALIBRE_DB_PATH=/path/to/metadata.db
CALIBRE_LIBRARY_PATH=/path/to/calibre
CHROMADB_PATH=~/Library/Application Support/bookwise/vectors/
CALIBREDB_PATH=/Applications/calibre.app/Contents/MacOS/calibredb
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OUTPUT_DIR=./output
DATASOURCES_DIR=./datasources
```

## Workflow

### 1. Generate Input (`generate_enrichment_input.py`)

Creates JSONL file with books needing enrichment.

**Deduplication layers**:
1. Filter for Calibre library books
2. Filter for books with quality scores
3. Skip books in `enrichment_status.json`
4. Skip books already in ChromaDB

**Outputs**:
- `output/enrichment/books_to_enrich.jsonl` - Books to process
- `output/enrichment/enrichment_plan.txt` - Cost estimate

```bash
python3 src/dataenrichment/generate_enrichment_input.py
```

### 2. Enrich Books (`enrich_books.py`)

Processes books through Claude API and OpenAI embeddings.

**For each book**:
1. **Claude API**: Generate tags, themes, enhanced description
2. **OpenAI API**: Create 3072-dimension embedding from metadata
3. **ChromaDB**: Store embedding + metadata
4. **Status file**: Track completion

**Commands**:
```bash
# Standard run
python3 src/dataenrichment/enrich_books.py --yes

# Resume after interruption
python3 src/dataenrichment/enrich_books.py --resume --yes

# Small batch (testing)
python3 src/dataenrichment/enrich_books.py --batch-size 10 --yes

# Check status
python3 src/dataenrichment/enrich_books.py --status
```

**Cost tracking**: Progress saved after each book (safe to interrupt with Ctrl+C)

### 3. Import to Calibre (`add_tags_to_calibre.py`)

Adds AI-generated tags to Calibre using `calibredb`.

**Tag types**:
- **Topic tags**: `fiction`, `historical`, `science fiction`
- **Award tags**: `Award: Pulitzer Prize - Fiction`, `Award: Nobel Prize`
- **List tags**: `List: Best Fiction`, `List: Modern Library 100`
- **Canon tags**: `Canon: Tier S`, `Canon: Tier A`

```bash
# Preview changes
python3 src/dataenrichment/add_tags_to_calibre.py --dry-run

# Apply tags
python3 src/dataenrichment/add_tags_to_calibre.py --yes

# Check Calibre compatibility
python3 src/dataenrichment/add_tags_to_calibre.py --verify
```

**Note**: Close Calibre GUI before running (database lock issues).

### 4. Check Status (`check_enrichment_status.py`)

View enrichment progress and costs.

```bash
python3 src/dataenrichment/check_enrichment_status.py
```

**Shows**:
- Total books in library
- Scored books count
- Enriched books count
- Pending books
- API call counts and costs

### 5. Detect Score Changes (`detect_score_changes.py`)

Re-enrich books when quality scores change.

**Use case**: After updating canonical author lists or award data.

```bash
# Update datasources
vim datasources/canonical_authors_tier_a.json

# Regenerate scores
python3 src/scripts/generate_unified_scores.py

# Detect changes
python3 src/dataenrichment/detect_score_changes.py

# Re-enrich changed books
python3 src/dataenrichment/enrich_books.py --input books_to_reenrich.jsonl --yes

# Re-import tags
python3 src/dataenrichment/add_tags_to_calibre.py --yes
```

### 6. Search Books (`search_books.py`)

Test semantic search on enriched library.

```bash
# Basic search
python3 src/dataenrichment/search_books.py "resilience during hardship"

# With quality filter
python3 src/dataenrichment/search_books.py "space exploration" --min-quality 70 --limit 10
```

## File Structure

```
src/dataenrichment/
├── generate_enrichment_input.py  # Step 1: Find un-enriched books
├── enrich_books.py               # Step 2: AI enrichment
├── add_tags_to_calibre.py        # Step 3: Import to Calibre
├── check_enrichment_status.py    # Monitoring
├── detect_score_changes.py       # Re-enrichment detection
└── search_books.py               # Test semantic search

output/enrichment/
├── books_to_enrich.jsonl         # Input for enrichment
├── enriched_books.jsonl          # Enrichment results
├── enrichment_status.json        # Progress tracking
├── enrichment_progress.json      # Cost tracking
└── enrichment_plan.txt           # Cost estimates
```

## ChromaDB Schema

**Collection**: `book_metadata_embeddings`

**Metadata fields**:
- `title`, `author`, `publication_year`
- `quality_score` (0-100)
- `tags` (list): AI-generated topic tags
- `themes` (list): Thematic elements
- `description` (str): Enhanced description
- `awards` (str): Recognition and awards

**Embedding**: 3072 dimensions (OpenAI `text-embedding-3-large`)

**Embedding input**:
```
Title: {title}
Author: {author}
Description: {description}
Tags: {tags}
Themes: {themes}
Awards: {awards}
Quality Score: {quality_score}
```

## API Costs

**Claude API** (Sonnet 3.5):
- ~$0.10 per 100 books
- Generates: tags, themes, description, publication year

**OpenAI Embeddings** (`text-embedding-3-large`):
- ~$0.02 per 100 books
- 3072-dimension vectors

**Total**: ~$0.12 per 100 books

## Troubleshooting

**ChromaDB not found**:
```bash
# Verify path
ls ~/Library/Application\ Support/bookwise/vectors/chroma.sqlite3

# Create if missing
python3 -c "import chromadb; chromadb.PersistentClient(path='~/Library/Application Support/bookwise/vectors/')"
```

**Calibre database locked**:
- Close Calibre GUI before running `add_tags_to_calibre.py`
- Wait 5 seconds after closing

**API key errors**:
- Check `.env` file has correct keys
- Test: `echo $ANTHROPIC_API_KEY` (should not be empty)

**Resume after interruption**:
```bash
# Enrichment tracks progress automatically
python3 src/dataenrichment/enrich_books.py --resume --yes
```

**Re-enrich specific books**:
```bash
# Create custom input JSONL with book_id, title, author, quality_score
python3 src/dataenrichment/enrich_books.py --input custom_books.jsonl --yes
```

## Data Safety

**Primary source of truth**: ChromaDB  
**Regenerable**: All JSONL files, status files  
**Version controlled**: Source code, datasources  
**Not tracked**: `output/`, ChromaDB, Calibre database  

**Backup strategy**:
```bash
# ChromaDB
tar -czf chromadb_backup.tar.gz ~/Library/Application\ Support/bookwise/vectors/

# Status files
cp -r output/enrichment/ enrichment_backup_$(date +%Y%m%d)/
```

