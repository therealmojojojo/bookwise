# Complete Data Sources Guide
## Book Quality Scoring System - Unified Era-Neutral Methodology

**Last Updated**: November 4, 2025  
**Version**: 4.1  
**Methodology**: Unified Era-Neutral Quality Assessment

---

## Table of Contents

1. [Overview](#overview)
2. [Award Files (25 files)](#award-files)
3. [Best Books Lists (13 files)](#best-books-lists)
4. [Classic Series (1 file)](#classic-series)
5. [Educational Canon (3 files)](#educational-canon)
6. [Significant Books (3 tiers)](#significant-books)
7. [Canonical Authors (3 tiers)](#canonical-authors)
8. [Author Achievement Bonus System](#author-achievement-bonus-system)
9. [Scoring Impact Summary](#scoring-impact-summary)
10. [Data Statistics](#data-statistics)

---

## Overview

This directory contains **48 data source files** used to calculate era-neutral quality scores for books. The system evaluates books based on multiple dimensions of literary recognition:

- **Awards**: Professional recognition by literary institutions
- **Lists**: Editorial selection by critics and scholars
- **Canon**: Long-term academic and cultural significance
- **Significant Works**: Books by major authors or from curated collections

**Total Coverage**: ~4,290 unique books across all categories

---

## Award Files

### 1. Major International Literary Awards

#### Nobel Prize in Literature (Since 1901)
**File**: `nobel_literature.json` | **Entries**: 121

**What It Is:**
- **Highest honor in world literature** - The ultimate literary recognition
- Career achievement award (lifetime recognition)
- Awarded by Swedish Academy
- 120+ year history (since 1901)

**Why Included:**
- Represents pinnacle of literary achievement globally
- Validates an author's entire body of work
- International consensus on literary excellence
- Most prestigious literary prize in the world

**Scoring Impact:**
- **+30 points** to ALL books by Nobel-winning authors (career award)
- Applied even if specific book didn't win an award
- Example: All Toni Morrison books get 30 points from her 1993 Nobel
- **Does NOT provide additional Author Achievement Bonus** (career award already covers all books)

**Notable Winners**: García Márquez, Morrison, Ishiguro, Hemingway, Faulkner, Camus, Bob Dylan, Kazuo Ishiguro

---

### 2. Major Fiction Awards (US)

#### Pulitzer Prize for Fiction (Since 1918)
**File**: `pulitzer_fiction.json` | **Entries**: 98

**What It Is:**
- America's most prestigious literary award
- Awarded by Columbia University
- Recognizes distinguished fiction by American author

**Why Included:**
- 100+ year history of recognizing excellence
- Rigorous selection by expert panel
- Career-defining achievement

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Example: Colson Whitehead won 2 Pulitzers → His other books get 15 points (10 + 5)

**Notable Winners**: Colson Whitehead (2×), Harper Lee, Steinbeck, Philip Roth, Cormac McCarthy

---

#### National Book Award - Fiction (Since 1950)
**File**: `national_book_award_fiction.json` | **Entries**: 41

**What It Is:**
- Premier American literary award
- Awarded by National Book Foundation
- Major recognition of literary merit

**Why Included:**
- Peer recognition from literary community
- High selectivity and prestige
- Complements Pulitzer Prize

**Scoring Impact:**
- **+15 points** (significant award) - Applied to the winning book
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Total bonus: 10-15 points on other books
- Example: Jesmyn Ward won twice (Salvage the Bones, Sing, Unburied, Sing) → Her other books get 15 points

---

#### PEN/Faulkner Award (Since 1981)
**File**: `faulkneraward.json` | **Entries**: 44

**What It Is:**
- Largest peer-juried award for fiction in America
- Writers choosing writers
- Honors excellence in fiction

**Why Included:**
- Peer recognition (by fellow authors)
- Different perspective from academic/journalistic awards
- High literary standards

**Scoring Impact:**
- **+15 points** (significant award)
- Philip Roth only three-time winner

---

### 3. Major Fiction Awards (UK)

#### The Booker Prize (Since 1969)
**File**: `booker_prize.json` | **Entries**: 59

**What It Is:**
- Leading literary award for English-language fiction
- Published in UK or Ireland
- £50,000 prize

**Why Included:**
- International prestige (Commonwealth + global)
- Rigorous literary standards
- Equivalent to US Pulitzer Prize

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Example: Margaret Atwood won 2 Bookers → Her other books get 15 points (10 + 5)

**Notable Winners**: Margaret Atwood (2×), Hilary Mantel (2×), J.M. Coetzee (2×), Peter Carey (2×)

---

#### Man Booker Prize (Historical)
**File**: `manbookerprize.json` | **Entries**: 15

**What It Is:**
- Historical data for Man Booker Prize period
- Some overlap with booker_prize.json
- Same prestige as Booker Prize

**Why Included:**
- Complete historical record
- Ensures no gaps in coverage
- Equal prestige to Booker Prize

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Example: Hilary Mantel won 2 Bookers → Her other books get 15 points (10 + 5)

---

#### Women's Prize for Fiction (Since 1996)
**File**: `womens_prize_fiction.json` | **Entries**: 30

**What It Is:**
- Fiction written by women in English
- Formerly Orange Prize, Baileys Prize
- £30,000 prize

**Why Included:**
- Recognizes excellence in women's writing
- High literary standards
- Complements other major prizes

**Scoring Impact:**
- **+15 points** (significant award) - Applied to the winning book
- **Does NOT qualify author for Author Achievement Bonus**
- Rationale: Gender/demographic-specific award rather than universal literary excellence

**Notable Winners**: Barbara Kingsolver (2×), Zadie Smith, Chimamanda Ngozi Adichie

---

### 4. Major Nonfiction Awards (US)

#### Pulitzer Prize for Biography (Since 1917)
**File**: `pulitzer_biography.json` | **Entries**: 100

**What It Is:**
- Pulitzer Prize for distinguished biography by American author
- Same prestige and selectivity as Fiction Pulitzer
- Part of Pulitzer Prize system

**Why Included:**
- 100+ year history of recognizing excellence
- Equal prestige to Fiction Pulitzer
- Career-defining achievement

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books

**Notable Winners**: Ron Chernow (3×), David McCullough (2×), Robert Caro

---

#### Pulitzer Prize for History (Since 1917)
**File**: `pulitzer_history.json` | **Entries**: 98

**What It Is:**
- Pulitzer Prize for distinguished history book by American author
- Same prestige and selectivity as Fiction Pulitzer
- Part of Pulitzer Prize system

**Why Included:**
- 100+ year history of recognizing excellence
- Equal prestige to Fiction Pulitzer
- Career-defining achievement

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books

**Notable Winners**: David McCullough (2×), Barbara Tuchman (2×), Alan Taylor (3×)

---

#### Pulitzer Prize for General Nonfiction (Since 1962)
**File**: `pulitzer_general_nonfiction.json` | **Entries**: 46

**What It Is:**
- Pulitzer Prize for distinguished nonfiction by American author
- Covers science, philosophy, journalism, memoirs, etc.
- Part of Pulitzer Prize system

**Why Included:**
- Same prestige and selectivity as other Pulitzers
- Recognizes important nonfiction beyond history/biography
- Career-defining achievement

**Scoring Impact:**
- **+25 points** (book-specific major award) - Applied to the winning book
- **Multiple awards sum together** (capped at 60 total from all book awards)
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books

**Notable Winners**: Various authors across diverse subjects

---

#### National Book Award - Nonfiction (Since 1950)
**File**: `national_book_award_nonfiction.json` | **Entries**: 122

**What It Is:**
- National Book Award for nonfiction
- Equal prestige to NBA Fiction
- Major recognition of literary merit

**Why Included:**
- Peer recognition from literary community
- High selectivity and prestige
- Complements Pulitzer nonfiction prizes

**Scoring Impact:**
- **+15 points** (significant award) - Applied to the winning book
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Total bonus: 10-15 points on other books

---

#### National Book Critics Circle Awards
**Files**: 
- `nbcc_fiction.json` (50 entries)
- `nbcc_biography.json` (41 entries)
- `nbcc_history.json` (10 entries)
- `nbcc_general_nonfiction.json` (49 entries)

**What They Are:**
- Awards by book critics and reviewers
- Multiple categories (fiction, biography, history, general nonfiction)
- Critical consensus awards

**Why Included:**
- Critical consensus from professional reviewers
- High literary standards
- Complements other major awards with critic perspective

**Scoring Impact:**
- **+15 points** (significant award) - Applied to the winning book
- **Qualifies author for Author Achievement Bonus** on their other books:
  - Base: +10 points on non-award-winning books by this author
  - Critical Acclaim: +5 additional points if author won major awards for 2+ different books
  - Applies to ALL NBCC categories (fiction, biography, history, general nonfiction)

---

#### LA Times Book Prize
**Files**:
- `la_times_book_prize_fiction.json` (44 entries)
- `la_times_book_prize_nonfiction.json` (65 entries)

**What They Are:**
- Los Angeles Times Book Prizes
- Fiction and nonfiction categories
- West Coast perspective

**Why Included:**
- Major US newspaper award
- Critical selection
- Regional diversity

**Scoring Impact:**
- **+12 points** (notable award) - Applied to the winning book
- **Does NOT qualify author for Author Achievement Bonus**
- Rationale: Notable tier award; insufficient prestige for author-wide bonus

---

#### Kirkus Prize
**Files**:
- `kirkus_prize_fiction.json` (11 entries)
- `kirkus_prize_yrl.json` (52 entries - Young Readers)

**What They Are:**
- Kirkus Reviews literary prizes
- $50,000 prizes
- Fiction and Young Readers' Literature categories

**Why Included:**
- Professional book review magazine
- Significant prize money
- High literary standards

**Scoring Impact:**
- **+12 points** (notable award) - Applied to the winning book
- **Does NOT qualify author for Author Achievement Bonus**
- Rationale: Notable tier award; too new (since 2011) for author-wide bonus

---

#### Dublin Literary Award
**File**: `dublin_literary_award.json` | **Entries**: 30

**What It Is:**
- International award for novels in English
- €100,000 prize (one of the richest)
- Nominated by public libraries worldwide

**Why Included:**
- Global perspective
- Public library endorsement
- Significant prize

**Scoring Impact**: **+15 points** (significant award)

---

### 5. International Career Awards

#### Miguel de Cervantes Prize (Since 1976)
**File**: `cervantesaward.json` | **Entries**: 50

**What It Is:**
- Highest literary honor for Spanish-language authors
- Often called "Spanish Nobel Prize"
- €125,000 prize

**Why Included:**
- Represents Spanish-language literary tradition
- Career achievement recognition
- Winners: Borges, Paz, Fuentes, Vargas Llosa

**Scoring Impact:**
- **+30 points** to ALL books by Cervantes-winning authors (career award)
- Applied even if specific book didn't win an award
- **Does NOT provide additional Author Achievement Bonus** (career award already covers all books)

**Rationale**: Equal to Nobel Prize as the highest honor in Spanish-language literature

---

#### Georg Büchner Prize (Since 1923)
**File**: `georgbuchneraward.json` | **Entries**: 73

**What It Is:**
- Most important prize for German-language authors
- €50,000 prize
- Career achievement

**Why Included:**
- Represents German-language literary tradition
- Winners: Günter Grass, Heinrich Böll

**Scoring Impact**: **+12 points** (notable career award)

---

### 6. International Book Awards

#### Prix Goncourt (Since 1903)
**File**: `prix_goncourt.json` | **Entries**: 1

**What It Is:**
- France's most prestigious literary award
- Symbolic €10 (prestige worth millions)

**Why Included:**
- Over 100 years of French literary excellence
- Determines French bestsellers

**Scoring Impact**: **+15 points** (significant award)

---

### 7. Genre Awards (Science Fiction & Fantasy)

#### Hugo Awards (Since 1953)
**File**: `hugoaward.json` | **Entries**: 73

**What It Is:**
- World Science Fiction Society's premier awards
- Voted by Worldcon members (fan award)
- Most prestigious SF/F award

**Why Included:**
- Represents science fiction/fantasy excellence
- Long history (70+ years)
- Winners: Asimov, Le Guin, Jemisin

**Scoring Impact**: **+10 points** (genre award)

---

#### Nebula Awards (Since 1966)
**File**: `nebulaaward.json` | **Entries**: 59

**What It Is:**
- Science Fiction and Fantasy Writers Association
- Voted by SFWA members (professional writers)
- Peer recognition

**Why Included:**
- Professional writer recognition
- Complements Hugo (fan perspective)
- Winners: Le Guin, Gaiman

**Scoring Impact**: **+10 points** (genre award)

---

### Award Files Summary

**Total**: 25 award files, 1,382 entries

**Impact**:
- Major awards (25 pts + author bonus): Pulitzer, Booker
- Significant awards (15 pts + author bonus): NBA, NBCC, Dublin, Prix Goncourt
- Significant awards (15 pts, no author bonus): Women's Prize
- Notable awards (12 pts, no author bonus): LA Times, Kirkus, Büchner
- Genre awards (10 pts, no author bonus): Hugo, Nebula
- Career awards (20-30 pts to all books): Nobel, Cervantes

**Author Achievement Bonus Qualification**:
- Only awards with 30+ year histories of recognizing universal literary excellence
- Excludes genre/demographic-specific awards and newer notable awards

---

## Best Books Lists

### 1. Modern Library Best Novels (20th Century, 1998)

#### Modern Library 100 Best Fiction
**File**: `modernlibrarybestfiction.json` | **Entries**: 100

**What It Is:**
- Authoritative ranking of 20th-century English-language novels
- Board of critics: Daniel J. Boorstin, A.S. Byatt, Gore Vidal
- Compiled 1998

**Why Included:**
- Scholarly consensus on 20th-century masterpieces
- Ranked list (positions matter)
- Enduring influence

**Scoring Impact:**
- **Top 5: 15 points**
- **Top 20: 10 points**
- **Top 50: 7 points**
- **Top 100: 5 points**

**Top 5:**
1. Ulysses (Joyce)
2. The Great Gatsby (Fitzgerald)
3. A Portrait of the Artist (Joyce)
4. Lolita (Nabokov)
5. Brave New World (Huxley)

---

#### Modern Library 100 Best Nonfiction
**File**: `modernlibrarynonfiction.json` | **Entries**: 100

**Scoring Impact**: Same as fiction (5-15 points by rank)

---

### 2. Contemporary Lists (21st Century)

#### New York Times 100 Best Books of 21st Century (2024)
**File**: `nytimes100bestnovels.json` | **Entries**: 100

**What It Is:**
- Survey of 500+ novelists, nonfiction writers, poets, critics
- Published 2024
- Most authoritative contemporary list

**Why Included:**
- Recent critical consensus
- Broad expert participation
- Defines contemporary canon

**Scoring Impact:**
- **Top 20: 10 points**
- **Top 50: 7 points**
- **Top 100: 5 points**

**#1**: The Known World (Edward P. Jones)

---

#### The Guardian Best Novels
**File**: `guardianbestnovels.json` | **Entries**: 100

**What It Is:**
- The Guardian's ranking of greatest novels
- UK/international perspective

**Why Included:**
- Major UK newspaper
- Critical selection
- International scope

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

**#1 (21st Century)**: Wolf Hall (Hilary Mantel)

---

### 3. Historical Lists (All-Time)

#### Time Magazine 100 Best English-Language Novels (2005)
**File**: `times100bestnovels.json` | **Entries**: 97

**Period**: 1923-2005  
**Compiled by**: Lev Grossman & Richard Lacayo

**Why Included:**
- American magazine perspective
- 80+ year span

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

---

#### BBC 100 Best Novels (2003)
**File**: `bbc100bestnovels.json` | **Entries**: 100

**What It Is:**
- BBC Big Read - UK's best-loved novels
- Public poll (popular perspective)

**Why Included:**
- Reader perspective (vs. critic)
- UK cultural canon

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

**#1**: The Lord of the Rings (Tolkien)

---

#### Le Monde 100 Books of the Century (1999)
**File**: `lemonde100bestnovles.json` | **Entries**: 100

**What It Is:**
- Poll of 17,000 French participants
- European/French perspective

**Why Included:**
- Non-Anglo perspective
- Large participant base

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

---

#### Norwegian Book Club 100 Best Books
**File**: `norwegian100best.json` | **Entries**: 97

**What It Is:**
- 100 authors from 54 countries selected
- Global/non-Western perspective

**Why Included:**
- Most geographically diverse list
- International author panel

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

---

#### Telegraph 100 Novels Everyone Should Read
**File**: `telegraph_100_novels.json` | **Entries**: 100

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

---

#### Observer 100 Greatest Novels
**File**: `observer_100_greatest_novels.json` | **Entries**: 100

**Scoring Impact**: Top 20: 10 pts, Top 50: 7 pts, Top 100: 5 pts

---

### 4. Canonical Lists

#### Harold Bloom's Western Canon (1994)
**File**: `haroldbloomcanon.json` | **Entries**: 26

**What It Is:**
- Harold Bloom's essential Western literature
- Influential literary critic's selection

**Why Included:**
- Academic canonical status
- Influential in literary studies
- Focus on aesthetic excellence

**Scoring Impact**: **10 points** (canonical inclusion, unranked)

---

### 5. Contemporary Reading Lists

#### Goodreads Choice Awards - Best Fiction Top 10
**File**: `goodreads_choice_fiction_top10.json` | **Entries**: 80

**What It Is:**
- Annual reader-voted awards (top 10 per year)
- Popular reader perspective

**Why Included:**
- Contemporary reader preferences
- Complements critical lists

**Scoring Impact**: **3 points** (reader recognition)

---

#### National Endowment for the Arts - Big Read Library
**File**: `nea_big_read_library.json` | **Entries**: 68

**What It Is:**
- Books selected for community reading programs
- Curated for discussion value

**Why Included:**
- Institutional endorsement
- Educational value
- Community engagement potential

**Scoring Impact**: **5 points** (institutional recognition)

---

### Best Books Lists Summary

**Total**: 13 list files, 1,168 entries

**Impact**:
- Ranked lists: 5-15 points (by position)
- Unranked prestigious: 8-10 points
- Reader selections: 3-5 points
- **Maximum from all lists**: 25 points (capped)

---

## Classic Series

### Penguin Classics (Ongoing)
**File**: `penguinclassics.json` | **Entries**: 1,419

**What It Is:**
- Penguin's classic literature series
- Continuously curated since 1946
- Global literature representation

**Why Included:**
- Editorial selection for literary quality
- Long-term reputation (75+ years)
- International scope
- Educational standard

**Scoring Impact**: **+5 points per series** (capped at 20 points total)

**Significance**: Being selected for Penguin Classics indicates enduring literary value and educational importance.

---

## Educational Canon

### St. John's College Great Books Program
**File**: `st_johns_college_great_books.json` | **Entries**: 152

**What It Is:**
- Core curriculum at St. John's College
- Four-year "Great Books" program
- Western canonical literature

**Why Included:**
- Academic canonical status
- Required reading for liberal arts education
- Multi-generational educational use

**Scoring Impact**: **+8 points** (high educational canon)

**Significance**: These books define traditional liberal arts education.

---

### Columbia University - Literature Humanities
**File**: `columbia_lit_hum.json` | **Entries**: 22

**What It Is:**
- Columbia Core Curriculum required reading
- First-year literature course
- Western literary tradition

**Why Included:**
- Ivy League standard
- Define core education
- Academic consensus

**Scoring Impact**: **+7 points** (medium educational canon)

---

### University of Chicago Common Core
**File**: `uchicago_common_core.json` | **Entries**: 47

**What It Is:**
- UChicago's common core reading list
- Foundation of liberal arts education

**Why Included:**
- Top university standard
- Rigorous selection
- Academic prestige

**Scoring Impact**: **+7 points** (medium educational canon)

---

### Educational Canon Summary

**Total**: 3 files, 221 entries

**Impact**: 7-8 points (capped at 15 points total)

**Why Important**: Educational canon represents long-term academic consensus on essential literature.

---

## Significant Books

Three-tier system for high-quality books by recognized authors.

### Tier 1: Major Author Recognition
**File**: `significant_books.json` | **Entries**: 167 books, 39 authors

**What It Is:**
- Books by Nobel Prize winners
- Books by multiple Pulitzer/Booker winners
- Works appearing in Bloom's Canon + Modern Library

**Why Included:**
- Author's career achievement validates quality
- Fills gaps in award coverage
- Representative works by literary giants

**Scoring Impact**:
- Nobel authors: Career award points (20) + Author bonus (10)
- Major authors: Author bonus (10-15) based on recognition

**Examples**: Alice Munro, Nadine Gordimer, Doris Lessing, J.M. Coetzee

---

### Tier 2: High-Quality Curated Books
**File**: `significant_books_secondtier.json` | **Entries**: 606 books

**What It Is:**
- Books from curated best-fiction/nonfiction lists
- High-quality works not yet in awards
- Strong author reputation

**Why Included:**
- Curated by experts
- Fill coverage gaps
- Quality validation through curation

**Scoring Impact**: Based on author reputation and list appearance

---

### Tier 3: Other Curated Books
**File**: `significant_books_thirdtier.json` | **Entries**: 536 books

**What It Is:**
- Additional curated books from expert lists
- Broader quality recognition

**Why Included:**
- Comprehensive coverage
- Expert curation validates quality

**Scoring Impact**: Minimal recognition points (2-5)

---

### Significant Books Summary

**Total**: 3 tiers, 1,309 books

**Purpose**: Ensure comprehensive coverage beyond awards, recognizing quality through author reputation and expert curation.

---

## Canonical Authors

Three-tier system for pre-1970 literary masters addressing temporal bias.

### Tier S: Universal Giants
**File**: `canonical_authors_tier_s.json` | **23 authors, ~135 works**

**Who They Are:**
- Shakespeare, Tolstoy, Dostoevsky, Joyce, Cervantes, Dante, Proust, Kafka, Austen, Dickens, etc.
- Authors who transcend national boundaries
- Fundamental to any serious literature education

**Why Included:**
- Universal recognition across all literary traditions
- Works translated into virtually all major languages
- Influence spans multiple centuries
- Define the core of world literature

**Scoring Impact**:
- **+30 points** canonical baseline (all works)
- **Minimum 80 points** (underrecognition correction if needed)
- Example: Crime and Punishment gets 30 baseline + 40 correction = 75 total

**Generation Method**: Harold Bloom's Western Canon, Modern Library, university core curricula (Columbia, UChicago, St. John's), consensus among major literary historians.

---

### Tier A: Essential Moderns
**File**: `canonical_authors_tier_a.json` | **48 authors, ~218 works**

**Who They Are:**
- Camus, Hemingway, Conrad, Forster, Steinbeck, Baldwin, Borges, Woolf, Mann, Fitzgerald, etc.
- Essential for understanding 19th-20th century literature
- Major influence on literary movements

**Why Included:**
- Essential for comprehensive world literature understanding
- Defined modernism, shaped national literatures
- Widely taught in advanced literature courses

**Scoring Impact**:
- **+20 points** canonical baseline (all works)
- **Minimum 70 points** (underrecognition correction if needed)

**Generation Method**: University literature syllabi, comprehensive histories of world literature, critical consensus among scholars.

---

### Tier B: Important Regional Voices
**File**: `canonical_authors_tier_b.json` | **20 authors, ~76 works**

**Who They Are:**
- Kawabata, Mishima, Tagore, Lu Xun, Achebe, Mahfouz, Nabokov, Singer, etc.
- Important regional and genre figures
- Essential for non-Western literary traditions

**Why Included:**
- Major importance within regional/national literary traditions
- International recognition and influence
- Essential for understanding global literature

**Scoring Impact**:
- **+15 points** canonical baseline (all works)
- **Minimum 60 points** (underrecognition correction if needed)

**Generation Method**: National literary canons, UNESCO recognition, Nobel Prize patterns, scholarly consensus.

---

### Canonical Authors Summary

**Total**: 3 tiers, 91 authors, ~429 works

**Purpose**: 
- Addresses temporal bias in modern award systems
- Ensures pre-1970 masterpieces compete fairly with contemporary works
- Represents global literary traditions

**Why Essential**:
- Most major "best-of" lists created 1998-2024
- Pre-1970 literature systematically underscored
- Canonical status represents long-term literary significance

**Result**: Ulysses, War and Peace, Crime and Punishment now score 75-80 points (Outstanding/Exceptional tier) instead of 25-30.

---

## Author Achievement Bonus System

### How It Works

When an author wins a major literary award, ALL their other books (that didn't win awards themselves) receive bonus points. This recognizes that award-winning authors consistently produce high-quality work.

### Two-Tier Bonus Structure

**Base Author Bonus: +10 points**
- Applied when: Author won at least 1 major award for a different book
- Example: Colson Whitehead won Pulitzer for "The Underground Railroad" → His book "The Intuitionist" gets +10 points

**Critical Acclaim Bonus: +5 additional points (Total: 15)**
- Applied when: Author won major awards for 2+ different books
- Example: Colson Whitehead won Pulitzers for both "The Underground Railroad" AND "The Nickel Boys" → His book "The Intuitionist" gets +15 points (10 + 5)

### Which Awards Qualify Authors?

**Awards that Qualify for Author Achievement Bonus:**

**Tier 1 - Major Awards (25 points):**
- Pulitzer Prize (Fiction, Biography, History, General Nonfiction)
- Booker Prize / Man Booker Prize

**Tier 2 - Significant Awards (15 points):**
- National Book Award (Fiction, Nonfiction)
- National Book Critics Circle Awards (Fiction, Biography, History, General Nonfiction)
- Dublin Literary Award

**Awards that Do NOT Qualify:**

**Career Awards** (already apply to all books):
- Nobel Prize in Literature → Already gives 30 pts to ALL books
- Miguel de Cervantes Prize → Already gives 30 pts to ALL books

**Notable Awards** (insufficient prestige):
- LA Times Book Prize → 12 pts to winning book only
- Kirkus Prize → 12 pts to winning book only (too new: since 2011)

**Demographic/Genre-Specific Awards:**
- Women's Prize for Fiction → 15 pts to winning book only
- Hugo Award → 10 pts to winning book only
- Nebula Award → 10 pts to winning book only

**Rationale**: Author Achievement Bonus is reserved for major career-defining awards with 30+ year histories that represent universal literary excellence.

### Important Rules

**1. No Double-Counting:**
- If a book won an award itself → It gets award points, NO author bonus
- If author has Nobel Prize → All books get 30 pts career award, NO author bonus
- If author has Cervantes Prize → All books get 30 pts career award, NO author bonus
- Author bonus only applies to non-award-winning books without career awards

**2. Counting by Books, Not Awards:**
- An author who won 3 Pulitzers for the SAME book = 1 book
- An author who won Pulitzer for one book + Booker for another = 2 books ✓
- Critical Acclaim requires winning awards for 2+ DIFFERENT books

### Examples

**Example 1: Ian McEwan**
- "Amsterdam" (1998) → Won Booker Prize → Gets 25 pts from award
- "Atonement" (2002) → Won NBCC Award → Gets 15 pts from award
- "Saturday" (2005) → No awards → Gets 15 pts author bonus (10 + 5 for 2 award-winning books)

**Example 2: Colson Whitehead**
- "The Underground Railroad" (2016) → Won Pulitzer Prize → Gets 25 pts
- "The Nickel Boys" (2019) → Won Pulitzer Prize → Gets 25 pts
- "The Intuitionist" (1999) → No awards → Gets 15 pts author bonus (10 + 5)
- "John Henry Days" (2001) → No awards → Gets 15 pts author bonus (10 + 5)

**Example 3: Toni Morrison (Nobel Winner)**
- Won Nobel Prize in 1993
- ALL her books get 30 pts from Nobel (career award)
- "Beloved" also won Pulitzer → Gets 30 (Nobel) + 25 (Pulitzer) = 55 pts
- "Song of Solomon" (no other award) → Gets 30 pts (Nobel only)
- No author bonus applied (Nobel already covers all books)

**Example 4: Jesmyn Ward**
- "Salvage the Bones" (2011) → Won National Book Award → Gets 15 pts
- "Sing, Unburied, Sing" (2017) → Won National Book Award → Gets 15 pts
- "Where the Line Bleeds" (2008) → No awards → Gets 15 pts author bonus (10 + 5)

### Top Multi-Award Authors

Authors with qualifying awards for 2+ different books (qualify for 15-point bonus):

**Top Authors:**
1. **Philip Roth** - 5 qualifying award-winning books (Pulitzer + NBA wins)
2. **John Updike** - 3 qualifying award-winning books (Pulitzer wins)
3. **Cormac McCarthy** - 3 qualifying award-winning books (NBA + Pulitzer)
4. **Louise Erdrich** - 3 qualifying award-winning books (NBA wins)
5. **Edward P. Jones** - 3 qualifying award-winning books (Pulitzer + NBCC + PEN/Faulkner)
6. **Colson Whitehead** - 2 qualifying award-winning books (2× Pulitzer)
7. **Jesmyn Ward** - 2 qualifying award-winning books (2× NBA)
8. **Hilary Mantel** - 2 qualifying award-winning books (2× Booker)
9. **David McCullough** - 3 qualifying award-winning books (Pulitzer Biography + History)
10. **Ron Chernow** - 3 qualifying award-winning books (Pulitzer Biography + NBCC)

**(Approximately 50-60 authors qualify for the critical acclaim bonus with the stricter criteria)**

**Note**: Only Pulitzer, Booker, NBA, NBCC, and Dublin awards count toward this qualification.

---

## Scoring Impact Summary

### Maximum Possible Scores

**By Category:**
- **Author Career Awards**: 30 pts (Nobel, Cervantes - applies to ALL author's books)
- **Book-Specific Awards**: 60 pts (multiple awards summed, capped at 60)
- **Author Achievement Bonus**: 15 pts (only applied if book itself didn't win award)
  - Base: 10 pts (author won at least 1 major award for another book)
  - Critical Acclaim: +5 pts (author won major awards for 2+ different books)
  - Note: NOT cumulative with book awards or career awards
- **List Appearances**: 25 pts (capped across all lists)
- **Classic Series**: 20 pts (capped across all series)
- **Educational Canon**: 15 pts (capped across all canons)
- **Canonical Baseline**: 30 pts (Tier S authors - pre-1970 works)
- **Cross-Era Validation**: 20 pts (books recognized across 3+ decades)
- **Underrecognition Correction**: 40 pts (pre-1970 only, if below tier minimum)

**Practical Maximum**: ~95 points (e.g., The Grapes of Wrath)

**Important Rules:**
- Career awards (Nobel/Cervantes) override author bonus
- Book awards override author bonus
- Author bonus only applies to books that didn't win awards themselves
- Each category has maximum caps to prevent excessive stacking

---

### Score Distribution (Current System)

Based on 4,290 scored books:

| Score Range | Books | Category |
|-------------|-------|----------|
| **90-95** | 1 | Legendary |
| **80-89** | 40 | Exceptional |
| **70-79** | 143 | Outstanding |
| **60-69** | 84 | Excellent |
| **50-59** | 23 | Very Good |
| **Below 50** | 4,000+ | Varying recognition |

---

### Era-Neutral Impact

**Before (with recency boost):**
- Beloved (1987): 99 pts
- Ulysses (1922): 25 pts
- Crime and Punishment (1866): 10 pts

**After (era-neutral with canonical):**
- Ulysses (1922): 80 pts ✓
- Crime and Punishment (1866): 75 pts ✓
- Beloved (1987): 81 pts ✓

**Result**: Fair competition across all eras based on literary merit.

---

## Data Statistics

### Files by Type

| Type | Files | Entries | Purpose |
|------|-------|---------|---------|
| **Awards** | 25 | 1,382 | Professional recognition |
| **Lists** | 13 | 1,168 | Critical/editorial selection |
| **Series** | 1 | 1,419 | Publisher curation |
| **Canon** | 3 | 221 | Academic consensus |
| **Significant Books** | 3 | 1,309 | Author reputation |
| **Canonical Authors** | 3 | 429 | Era-neutral correction |
| **TOTAL** | 48 | 5,928 | Comprehensive quality assessment |

---

### Geographic Coverage

**Awards & Lists Origin:**
- United States: 40%
- United Kingdom: 30%
- Europe (France, Germany, Nordic): 20%
- International/Global: 10%

**Canonical Authors (91 total):**
- European: ~60% (diverse nations)
- American: ~25% (North & South America)
- Asian: ~8% (Japan, China, India)
- African: ~4% (Nigeria, Egypt)
- Middle Eastern: ~2%
- Australian: ~1%

---

### Temporal Coverage

**Awards**: Primarily 1950-2024 (contemporary emphasis)  
**Lists**: Mix of historical (1998-1999) and recent (2024)  
**Canon**: Ancient to modern (Dante to contemporary)  
**Canonical Authors**: Primarily pre-1970 (compensates for temporal bias)

---

## Using This Data

### For Scoring Books

**Process:**
1. Load all data sources
2. Normalize titles and authors (fuzzy matching)
3. Check book-specific awards → Sum points (cap 60)
4. Check author career awards → Add points
5. Check list appearances → Sum points (cap 25)
6. Check classic series → Add points (cap 20)
7. Check educational canon → Add points (cap 15)
8. Check canonical author status → Add baseline (15-30)
9. Calculate cross-era validation → Add bonus (0-20)
10. Apply underrecognition correction → If pre-1970 and below minimum

### Implementation

**Primary Calculator**: `src/scoring/unified_calculator.py`  
**Class**: `UnifiedQualityScoreCalculator`  
**Output**: `output/unified_methodology_scores.csv` (4,290 books)

---

## Maintenance

### Annual Updates Required

**Awards** (each year):
- Nobel Prize (October)
- Booker Prize (October/November)
- Pulitzer Prize (May)
- National Book Award (November)
- Women's Prize (June)
- Hugo Awards (August/September)
- Nebula Awards (May/June)

**Lists** (as published):
- New "best-of" lists from major publications
- Updated editions of existing lists

**Canon** (rare):
- New canonical works discovered posthumously
- Rare additions to canonical author lists

---

## Quality Assurance

**All data files**:
- ✓ Cross-referenced with official sources
- ✓ Publication years verified
- ✓ Author names standardized
- ✓ Translation variants documented
- ✓ JSON format validated

---

## Related Documentation

- **`README.md`** - Main project documentation
- **`src/README.md`** - Source code and modules documentation
- **`calibredatabase/README.md`** - Calibre database integration guide

---

**Created**: November 4, 2025  
**Last Updated**: November 4, 2025  
**Version**: 4.1  
**Total Data Sources**: 48 files, 5,928 entries, ~4,290 unique books scored

