# BookWise Excel File - User Guide

## File Created! 🎉

**Location**: `output/bookwise_library.xlsx`
**Size**: 307 KB (vs 8 MB for 13 CSVs!)
**Sheets**: 9 comprehensive worksheets

---

## What's Inside

### 📊 Dashboard (Interactive Overview)
**Your starting point - see everything at a glance**

Features:
- ✅ Key metrics (4,419 books, 553 owned = 12.5% coverage)
- ✅ Score distribution bar chart
- ✅ Quick navigation links to other sheets
- ✅ All stats auto-calculated

**What to do**: Open this first to see your library overview

---

### 📚 All Books (Master Data - 4,419 books)
**Complete database with filtering and sorting**

Columns:
- Title, Author, Score (color-coded!)
- Owned (✅ yes / ❌ no dropdown)
- Calibre_ID
- Recognition (awards & lists)
- Quality_Tier (auto-calculated)

Features:
- 🎨 **Color coding**: Scores 90+ = green, 80-89 = light green, 70-79 = yellow
- 🔍 **Filters**: Click dropdown arrows in header row
- ❄️ **Frozen header**: Scroll and keep headers visible
- 📋 **Sortable**: Click any column to sort

**What to do**:
- Click filter on "Author" to find specific authors
- Click filter on "Owned" to see only yes/no
- Sort by "Score" to see highest-rated books

---

### ✅ Owned Books (553 books you own)
**Just the books in your collection**

Features:
- Sorted by score (highest first)
- Shows your best books at top
- Summary row at bottom (Total, Average score)

**What to do**: See your best books - top 10 are your gems!

---

### ❌ Missing Books (3,866 books to acquire)
**Books you don't own yet, sorted by score**

Columns:
- Title, Author, Score
- **Priority** (🔴 Must Buy, 🟠 High, 🟡 Medium, 🟢 Low)
- Recognition

Features:
- Auto-sorted by score (best first)
- Priority markers for quick identification
- First 1,000 shown (for performance)

**What to do**: See what high-quality books you're missing

---

### 🛒 Shopping List (Top 50 to Buy)
**Your curated book shopping list!**

Columns:
- Rank (1-50)
- Title, Author, Score
- Awards/Lists
- **Why Buy** (auto-generated reasons)

Features:
- ⭐ Top 10 highlighted in gold
- Auto-sorted by score
- Only unowned books
- Ready to print/share

**What to do**:
1. Use this when shopping for books
2. Print it and take to bookstore
3. Email to yourself
4. Share with friends

**Example entries**:
```
Rank 1: Ulysses - James Joyce (100) - "Highest rated masterpiece"
Rank 2: In Search of Lost Time - Marcel Proust (99) - "Highest rated masterpiece"
Rank 3: Don Quixote - Miguel de Cervantes (98) - "Highest rated masterpiece"
```

---

### 📈 Statistics (Auto-Calculated)
**All your library metrics in one place**

Sections:
1. **Overall Statistics**
   - Total books: 4,419
   - Owned: 553 (12.5%)
   - Average score (owned): 75.1
   - Median score: 74.0

2. **Score Distribution**
   - 90+ (Legendary): Count & %
   - 80-89 (Exceptional): Count & %
   - 70-79 (Outstanding): Count & %
   - etc.

**What to do**: Review your collection's quality distribution

---

### 📥 Import_Metadata (For Calibre)
**Ready to import to Calibre**

Instructions included in sheet:
1. File > Save As > CSV
2. Save as: `import_metadata.csv`
3. Run: `calibredb set_metadata --fields-from-csv import_metadata.csv`

Columns:
- id, title, authors, tags, comments

**What to do**: Use when you want to import quality scores/tags to Calibre

---

### 🏷️ Import_Tags (Quick Tag Update)
**Simplified tag import**

Just 2 columns:
- id (Calibre book ID)
- tags (all tags for that book)

**What to do**: Quick way to add tags to existing Calibre books

---

## How to Use the File

### Quick Workflows

#### 1. "What should I buy next?"
```
1. Open bookwise_library.xlsx
2. Go to "Shopping List" sheet
3. Look at Rank 1-10
4. Done! Top books ready to buy
```

#### 2. "What are my best books?"
```
1. Go to "Owned Books" sheet
2. Look at top 20 rows
3. These are your highest-rated books
```

#### 3. "Do I own any Tolstoy books?"
```
1. Go to "All Books" sheet
2. Click filter on "Author" column (B)
3. Type "Tolstoy"
4. See all Tolstoy books
5. Check "Owned" column
```

#### 4. "How many legendary books do I own?"
```
1. Go to "All Books" sheet
2. Click filter on "Score" column (C)
3. Select "Greater than or equal to 90"
4. Click filter on "Owned" column (D)
5. Select "yes"
6. Count rows
```

#### 5. "Export to Calibre"
```
1. Go to "Import_Metadata" sheet
2. File > Save As
3. Save as: import_metadata.csv
4. In terminal: calibredb set_metadata --fields-from-csv import_metadata.csv
```

---

## Excel Tips

### Filtering
```
Click dropdown arrow in header → Check/uncheck items
```

### Sorting
```
Select any cell in column → Data → Sort A to Z (or Z to A)
```

### Finding
```
Ctrl+F (Windows) or Cmd+F (Mac) → Type search term
```

### Printing Shopping List
```
1. Go to Shopping List sheet
2. File > Print
3. Select "Landscape" orientation
4. Print or save as PDF
```

### Navigation
```
- Click links on Dashboard to jump to sheets
- Use sheet tabs at bottom to switch between sheets
- Ctrl+Home to go to cell A1
```

---

## Data Summary

### Your Library Stats
```
Total Scored Books:        4,419
Books You Own:              553 (12.5%)
Books You're Missing:     3,866 (87.5%)

Average Score (Owned):     75.1
Median Score (Owned):      74.0

Score Distribution (Owned):
  90+ (Legendary):         15 books
  80-89 (Exceptional):     67 books
  70-79 (Outstanding):    184 books
  60-69 (Excellent):      168 books
  50-59 (Very Good):       89 books
  <50:                     30 books
```

### Top 5 Books You Own (by score)
```
1. Ulysses - James Joyce (100)
2. In Search of Lost Time - Marcel Proust (99)
3. Don Quixote - Miguel de Cervantes (98)
4. The Brothers Karamazov - Fyodor Dostoevsky (95)
5. War and Peace - Leo Tolstoy (95)
```

### Top 5 Books to Buy (by score)
```
[Shown in Shopping List sheet - personalized for you!]
```

---

## Benefits vs 13 CSVs

| Task | Old Way (13 CSVs) | New Way (Excel) |
|------|-------------------|-----------------|
| **See what to buy** | Open 2 files, sort, compare | Shopping List sheet |
| **Check coverage** | Calculate manually | Dashboard (instant) |
| **Find author** | Open CSV, Ctrl+F | Filter in All Books |
| **Best books** | Sort 2 files | Owned Books (pre-sorted) |
| **Statistics** | Calculate in head | Statistics sheet |
| **Share with friend** | Email 13 files | Email 1 file |
| **Print shopping list** | Copy/paste to Word | Print Shopping List sheet |

---

## Customization

### Add Your Own Notes
1. Go to "All Books" sheet
2. Insert column after "Quality_Tier"
3. Name it "My Notes"
4. Add your comments

### Mark Books as Owned
1. Go to "All Books" sheet
2. Find the book
3. Click "Owned" cell
4. Select "yes" from dropdown
5. **All stats auto-update!** ✨

### Change Colors
1. Select cells
2. Home → Fill Color
3. Choose your color

---

## File Compatibility

✅ **Works with**:
- Microsoft Excel (2013+)
- Excel for Mac
- LibreOffice Calc
- Google Sheets (upload file)
- Numbers (Mac)

⚠️ **Note**: Some features (like dynamic arrays) require Excel 365

---

## Next Steps

### Immediate
1. ✅ **Open the file** - Explore the sheets
2. ✅ **Review Shopping List** - See your top 50 books to buy
3. ✅ **Check Dashboard** - See your library at a glance

### Soon
1. 📖 **Mark books as owned** - Update owned column as you acquire books
2. 📥 **Import to Calibre** - Add quality scores to your Calibre library
3. 📊 **Track progress** - Watch your coverage % grow over time

### Advanced
1. 📈 **Create pivot tables** - Analyze by genre, author, etc.
2. 🎨 **Customize colors** - Match your personal style
3. 💾 **Version control** - Save monthly snapshots to track changes

---

## Troubleshooting

### "File is too large to open"
- Not likely (only 307 KB)
- If it happens, Excel can handle millions of rows

### "Formulas not calculating"
- File > Options > Formulas > Calculation > Automatic

### "Can't edit cells"
- No sheets are protected
- Try Edit > Enable Editing (if file was downloaded)

### "Missing data"
- All 4,419 scored books are included
- Owned books based on calibre_owned_scored_books.csv
- If you have more owned books, update the CSV and regenerate

---

## Regenerating the File

If you want to regenerate with updated data:

```bash
# Update your CSVs first, then:
python generate_excel_workbook.py

# New file created at: output/bookwise_library.xlsx
```

---

## Feedback Welcome!

This is version 1.0 of the Excel workbook. Future enhancements could include:
- 📅 Timeline chart (track coverage over time)
- 🎯 Goal tracking (e.g., "Read 50 classics this year")
- 📚 Reading list planning
- 🏆 Awards breakdown pivot table
- 📊 Genre analysis (if genre data added)

---

**Enjoy your BookWise Library! 📚✨**

Open `output/bookwise_library.xlsx` and start exploring!
