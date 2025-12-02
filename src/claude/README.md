# Monster Hunter Now Data Scraper

A production-ready Python scraper for extracting game data from [mhn.quest](http://mhn.quest) for use in RAG/LLM applications.

## Features

- **Comprehensive Data Extraction**: Scrapes monsters, weapons, armor, skills, and items
- **Dual Mode Operation**: Normal mode for production, debug mode for development
- **Structured JSON Output**: Clean, standardized format perfect for RAG knowledge bases
- **Error Resilience**: Continues scraping even if individual sections fail
- **Debug Support**: Saves HTML dumps and detailed logs in debug mode
- **Automated Reporting**: Generates summary reports of scraping operations
- **Test Suite**: Full test coverage with pytest

## Requirements

- Python 3.10 or higher
- Playwright (headless browser automation)

## Installation

### 1. Clone or download the project files

```bash
# Create project directory
mkdir mhn_scraper
cd mhn_scraper

# Copy the three Python files into this directory:
# - scrape_mhn_quest_gemini.py
# - test_scrape_mhn_quest_gemini.py
# - sample_output.json (example output)
```

### 2. Install Python dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install playwright pytest

# Install Playwright browsers
playwright install chromium
```

## Usage

### Normal Mode (Production)

Run the scraper in normal mode with concise logging:

```bash
python scrape_mhn_quest_gemini.py --mode normal
```

Or simply:

```bash
python scrape_mhn_quest_gemini.py
```

**Output:**
- `output/mhnow_data_all.json` - All data combined
- `output/mhnow_monsters.json` - Monster data only
- `output/mhnow_weapons.json` - Weapon data only
- `output/mhnow_armor.json` - Armor data only
- `output/mhnow_skills.json` - Skill data only
- `output/mhnow_items.json` - Item data only
- `output/scrape_report.json` - Scraping statistics and errors

### Debug Mode (Development)

Run in debug mode for detailed logging and HTML dumps:

```bash
python scrape_mhn_quest_gemini.py --mode debug
```

**Additional Output:**
- `debug/debug_monsters.html` - Raw HTML for monsters page
- `debug/debug_weapons.html` - Raw HTML for weapons page
- `debug/debug_armor.html` - Raw HTML for armor page
- `debug/debug_skills.html` - Raw HTML for skills page
- `debug/debug_items.html` - Raw HTML for items page

Debug mode also:
- Prints detailed progress information
- Uses longer wait times for page rendering
- Logs the number of entries found before filtering

## Running Tests

### Run all tests

```bash
pytest test_scrape_mhn_quest_gemini.py -v
```

### Run specific test

```bash
pytest test_scrape_mhn_quest_gemini.py::test_monster_creation -v
```

### Run with coverage

```bash
pip install pytest-cov
pytest test_scrape_mhn_quest_gemini.py --cov=scrape_mhn_quest --cov-report=html
```

## Configuration

The scraper uses configurable selectors that can be adjusted based on the actual website structure. To modify selectors:

1. Run in debug mode to save HTML dumps
2. Inspect the HTML files in the `debug/` directory
3. Update the `selectors` dictionary in the `ScraperConfig` class in `scrape_mhn_quest.py`

Example selector configuration:

```python
self.selectors = {
    "monsters": {
        "container": ".monster-list",  # Container holding all monsters
        "item": ".monster-card",        # Individual monster card
        "name_en": ".name-en",          # English name selector
        "name_jp": ".name-jp",          # Japanese name selector
        "weakness": ".weakness",        # Weakness elements
        "materials": ".material",       # Material drops
    },
    # ... other sections
}
```

## Output Format

All data follows a consistent JSON structure:

### Monster Entry
```json
{
  "type": "monster",
  "en": "Great Jagras",
  "jp": "ドスジャグラス",
  "weakness": ["fire", "thunder"],
  "materials": ["Jagras Scale", "Jagras Hide"],
  "habitat": "Forest",
  "notes": "Pack leader that swallows prey whole."
}
```

### Weapon Entry
```json
{
  "type": "weapon",
  "en": "Iron Sword I",
  "jp": "鉄刀【禊】",
  "weapon_class": "Great Sword",
  "rarity": "2"
}
```

### Armor Entry
```json
{
  "type": "armor",
  "en": "Jagras Mail",
  "jp": "ジャグラスメイル",
  "slot": "chest",
  "skills": ["Attack Boost Lv1", "Speed Eating Lv1"]
}
```

### Skill Entry
```json
{
  "type": "skill",
  "en": "Attack Boost",
  "jp": "攻撃",
  "category": "offense",
  "description": "Increases attack power."
}
```

### Item Entry
```json
{
  "type": "item",
  "en": "Potion",
  "jp": "回復薬",
  "category": "consumable",
  "description": "Restores health."
}
```

## Architecture

The scraper follows a modular architecture:

1. **Configuration Layer** (`ScraperConfig`): Centralized configuration for URLs, selectors, and timing
2. **Data Models**: Typed dataclasses for each game object type (Monster, Weapon, Armor, Skill, Item)
3. **Scraper Core** (`MHNQuestScraper`): Main scraping logic with section-specific parsers
4. **Helper Methods**: Text extraction, list extraction, and error handling utilities
5. **Output Layer**: JSON serialization and report generation

### Key Design Decisions

- **Playwright over Selenium**: Better JavaScript handling and modern async API
- **Async/Await**: Efficient concurrent operations
- **Fallback Selectors**: Multiple selector options for robustness
- **Graceful Degradation**: Continues on partial failures
- **Type Safety**: Dataclasses provide structure and validation

## Troubleshooting

### No data extracted

1. Run in debug mode: `python scrape_mhn_quest.py --mode debug`
2. Check the HTML files in `debug/` directory
3. Update selectors in `ScraperConfig` based on actual DOM structure
4. Verify the site URLs in `sections` dictionary

### Timeout errors

- Increase wait times in `ScraperConfig`:
  ```python
  normal_wait: int = 5000  # Increase from 3000
  debug_wait: int = 10000  # Increase from 6000
  ```

### Missing fields

- Fields are optional and omitted if empty
- Check debug logs to see what was found
- Verify selectors match the actual HTML structure

### Playwright installation issues

```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright
playwright install chromium --force
```

## Customization

### Adding New Sections

To add a new data type (e.g., "decorations"):

1. Add URL to `sections` in `ScraperConfig.__post_init__`
2. Add selectors to `selectors` dictionary
3. Create a dataclass (e.g., `Decoration`)
4. Add parser method (e.g., `_parse_decorations`)
5. Update `scrape_all()` to include new section

### Changing Output Format

Modify the dataclass `to_dict()` methods or adjust the `save_data()` method to change output structure.

## License

This scraper is provided as-is for educational and data extraction purposes. Please respect the terms of service of mhn.quest when using this tool.

## Contributing

To contribute:

1. Test changes with `pytest`
2. Ensure code follows existing style
3. Add tests for new features
4. Update documentation

## Support

For issues or questions:

1. Check debug HTML dumps
2. Review selector configuration
3. Verify site structure hasn't changed
4. Run tests to validate setup