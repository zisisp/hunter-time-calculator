MHN Quest Scraper

A Python tool to scrape Monster Hunter Now data from mhn.quest and export it to structured JSON for RAG/LLM usage.

Prerequisites

Python 3.10+

Playwright (for handling the JavaScript SPA)

Installation

# 1. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install browser binaries
playwright install chromium


Usage

Normal Mode

Runs faster, outputs final JSON files to the current directory.

python scrape_mhn_quest.py


Debug Mode

Runs slower (longer waits), saves HTML dumps of every page for inspection, and enables verbose logging.

python scrape_mhn_quest.py --mode debug


Output Files:

mhnow_data_all.json: The complete database.

mhnow_monsters.json, mhnow_weapons.json, etc.: Individual categories.

scrape_report.json: Success counts and error logs.

debug_*.html: Raw HTML dumps (Debug mode only).

Testing

Run the test suite to validate data structures and parsing logic logic without hitting the live site.

pytest test_scrape_mhn_quest.py


Maintenance

The site mhn.quest is a fan site and its structure may change.
If the scraper returns empty lists:

Run in --mode debug.

Open the generated debug_monsters.html (or relevant section).

Inspect the HTML to find the new CSS classes or IDs.

Update the CONFIG dictionary at the top of scrape_mhn_quest.py.