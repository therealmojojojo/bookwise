#!/bin/bash
# Cleanup temporary enrichment files
# These files can be regenerated from ChromaDB and Calibre

cd "$(dirname "$0")/../.."

echo "Cleaning up temporary enrichment files..."
echo "==========================================="
echo

# Check if files exist before deleting
ENRICHMENT_DIR="output/enrichment"

if [ ! -d "$ENRICHMENT_DIR" ]; then
    echo "✓ No enrichment directory found (nothing to clean)"
    exit 0
fi

# List what will be deleted
echo "Files to be deleted:"
echo

deleted=0

for file in \
    "$ENRICHMENT_DIR/books_to_enrich.jsonl" \
    "$ENRICHMENT_DIR/books_to_reenrich.jsonl" \
    "$ENRICHMENT_DIR/books_to_update_in_calibre.jsonl" \
    "$ENRICHMENT_DIR/enrichment_plan.txt" \
    "$ENRICHMENT_DIR/enrichment_progress.json" \
    "$ENRICHMENT_DIR/enrichment_status.json" \
    "$ENRICHMENT_DIR/enriched_books.jsonl"
do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "  - $(basename "$file") ($size)"
        rm "$file"
        deleted=$((deleted + 1))
    fi
done

echo
if [ $deleted -eq 0 ]; then
    echo "✓ No temporary files found"
else
    echo "✓ Deleted $deleted temporary file(s)"
    echo
    echo "Data preserved in:"
    echo "  ✓ ChromaDB: ~/Library/Application Support/bookwise/vectors/"
    echo "  ✓ Calibre: Your library database (with imported tags)"
fi

echo
echo "To regenerate deleted files if needed:"
echo "  - books_to_enrich.jsonl: python3 src/dataenrichment/generate_enrichment_input.py"
echo "  - books_to_reenrich.jsonl: python3 src/dataenrichment/detect_score_changes.py"
echo "  - enriched_books.jsonl: Export from ChromaDB (see DATA_ARCHITECTURE.md)"


