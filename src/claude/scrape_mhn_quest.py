#!/usr/bin/env python3
"""
Monster Hunter Now Data Scraper for mhn.quest

This script extracts game data (monsters, weapons, armor, skills, items)
from http://mhn.quest and outputs structured JSON files for RAG/LLM use.

Author: Production-ready scraper
Version: 1.0.0
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ScraperConfig:
  """Central configuration for the scraper."""
  base_url: str = "http://mhn.quest"

  # Section URLs - these are guessed based on typical SPA structures
  # Adjust these after inspecting the actual site navigation
  sections: Dict[str, str] = None

  # Selectors configuration - to be refined after DOM inspection
  # These are placeholder selectors that should be updated based on actual site structure
  selectors: Dict[str, Dict[str, str]] = None

  # Timing configuration
  normal_wait: int = 3000  # milliseconds
  debug_wait: int = 6000   # milliseconds

  # Output configuration
  output_dir: Path = Path("./output")
  debug_dir: Path = Path("./debug")

  def __post_init__(self):
    if self.sections is None:
      # Default section URLs - adjust based on actual site structure
      self.sections = {
        "monsters": f"{self.base_url}/#/monster",
        "weapons": f"{self.base_url}/#/weapon",
        "armor": f"{self.base_url}/#/armor",
        "skills": f"{self.base_url}/#/skill",
        "items": f"{self.base_url}/#/item",
      }

    if self.selectors is None:
      # Default selectors - MUST BE UPDATED based on actual DOM structure
      # These are common patterns for game databases
      self.selectors = {
        "monsters": {
          "container": ".monster-list, .card-container, [class*='monster']",
          "item": ".monster-card, .list-item, [class*='item']",
          "name_en": ".name-en, .name, [lang='en']",
          "name_jp": ".name-jp, [lang='ja']",
          "weakness": ".weakness, .element",
          "materials": ".material, .drop",
        },
        "weapons": {
          "container": ".weapon-list, .card-container",
          "item": ".weapon-card, .list-item",
          "name_en": ".name-en, .name",
          "name_jp": ".name-jp, [lang='ja']",
          "weapon_class": ".type, .class",
          "rarity": ".rarity, .stars",
        },
        "armor": {
          "container": ".armor-list, .card-container",
          "item": ".armor-card, .list-item",
          "name_en": ".name-en, .name",
          "name_jp": ".name-jp, [lang='ja']",
          "slot": ".slot, .piece",
          "skills": ".skill",
        },
        "skills": {
          "container": ".skill-list, .card-container",
          "item": ".skill-card, .list-item",
          "name_en": ".name-en, .name",
          "name_jp": ".name-jp, [lang='ja']",
          "description": ".description, .desc",
        },
        "items": {
          "container": ".item-list, .card-container",
          "item": ".item-card, .list-item",
          "name_en": ".name-en, .name",
          "name_jp": ".name-jp, [lang='ja']",
          "category": ".category, .type",
          "description": ".description, .desc",
        },
      }


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(debug_mode: bool = False) -> logging.Logger:
  """Configure logging based on mode."""
  level = logging.DEBUG if debug_mode else logging.INFO
  logging.basicConfig(
      level=level,
      format='%(asctime)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
  )
  return logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class GameDataEntry:
  """Base class for game data entries."""
  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary, removing None values."""
    data = asdict(self)
    return {k: v for k, v in data.items() if v is not None and v != "" and v != []}


@dataclass
class Monster(GameDataEntry):
  type: str = "monster"
  en: str = ""
  jp: str = ""
  weakness: List[str] = None
  materials: List[str] = None
  habitat: str = ""
  notes: str = ""

  def __post_init__(self):
    if self.weakness is None:
      self.weakness = []
    if self.materials is None:
      self.materials = []


@dataclass
class Weapon(GameDataEntry):
  type: str = "weapon"
  en: str = ""
  jp: str = ""
  weapon_class: str = ""
  rarity: str = ""
  notes: str = ""


@dataclass
class Armor(GameDataEntry):
  type: str = "armor"
  en: str = ""
  jp: str = ""
  slot: str = ""
  skills: List[str] = None
  notes: str = ""

  def __post_init__(self):
    if self.skills is None:
      self.skills = []


@dataclass
class Skill(GameDataEntry):
  type: str = "skill"
  en: str = ""
  jp: str = ""
  category: str = ""
  description: str = ""
  notes: str = ""


@dataclass
class Item(GameDataEntry):
  type: str = "item"
  en: str = ""
  jp: str = ""
  category: str = ""
  description: str = ""
  notes: str = ""


# ============================================================================
# SCRAPER CLASS
# ============================================================================

class MHNQuestScraper:
  """Main scraper class for Monster Hunter Now data."""

  def __init__(self, config: ScraperConfig, logger: logging.Logger, debug_mode: bool = False):
    self.config = config
    self.logger = logger
    self.debug_mode = debug_mode
    self.report = {
      "monsters": {"count": 0, "errors": []},
      "weapons": {"count": 0, "errors": []},
      "armor": {"count": 0, "errors": []},
      "skills": {"count": 0, "errors": []},
      "items": {"count": 0, "errors": []},
      "global_errors": []
    }

    # Ensure output directories exist
    self.config.output_dir.mkdir(parents=True, exist_ok=True)
    if self.debug_mode:
      self.config.debug_dir.mkdir(parents=True, exist_ok=True)

  async def scrape_all(self) -> Dict[str, List[Dict]]:
    """Main entry point to scrape all sections."""
    self.logger.info("Starting Monster Hunter Now data extraction...")

    all_data = {
      "monsters": [],
      "weapons": [],
      "armor": [],
      "skills": [],
      "items": []
    }

    async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      context = await browser.new_context(
          viewport={'width': 1920, 'height': 1080},
          user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      )
      page = await context.new_page()

      # Scrape each section
      for section_name in ["monsters", "weapons", "armor", "skills", "items"]:
        try:
          self.logger.info(f"Scraping {section_name}...")
          data = await self._scrape_section(page, section_name)
          all_data[section_name] = data
          self.report[section_name]["count"] = len(data)
          self.logger.info(f"✓ {section_name}: {len(data)} entries")
        except Exception as e:
          error_msg = f"Failed to scrape {section_name}: {str(e)}"
          self.logger.error(error_msg)
          self.report[section_name]["errors"].append(error_msg)

      await browser.close()

    return all_data

  async def _scrape_section(self, page: Page, section_name: str) -> List[Dict]:
    """Scrape a specific section of the site."""
    url = self.config.sections[section_name]
    selectors = self.config.selectors[section_name]
    wait_time = self.config.debug_wait if self.debug_mode else self.config.normal_wait

    # Navigate to section
    try:
      await page.goto(url, wait_until='domcontentloaded', timeout=30000)
      await page.wait_for_timeout(wait_time)

      # Additional wait for dynamic content
      try:
        # Try to wait for common container selectors
        await page.wait_for_selector(
            f"{selectors['container']}, .content, main, [role='main']",
            timeout=10000
        )
      except PlaywrightTimeout:
        self.logger.warning(f"Timeout waiting for container in {section_name}, proceeding anyway")

    except Exception as e:
      self.logger.error(f"Failed to load {section_name}: {e}")
      raise

    # Save debug HTML if in debug mode
    if self.debug_mode:
      html_content = await page.content()
      debug_file = self.config.debug_dir / f"debug_{section_name}.html"
      debug_file.write_text(html_content, encoding='utf-8')
      self.logger.debug(f"Saved debug HTML to {debug_file}")

    # Parse the section based on type
    if section_name == "monsters":
      return await self._parse_monsters(page, selectors)
    elif section_name == "weapons":
      return await self._parse_weapons(page, selectors)
    elif section_name == "armor":
      return await self._parse_armor(page, selectors)
    elif section_name == "skills":
      return await self._parse_skills(page, selectors)
    elif section_name == "items":
      return await self._parse_items(page, selectors)
    else:
      return []

  async def _parse_monsters(self, page: Page, selectors: Dict[str, str]) -> List[Dict]:
    """Parse monster data from the page."""
    monsters = []

    try:
      # Try multiple selector strategies
      item_selector = selectors['item']

      # Get all monster items
      items = await page.query_selector_all(item_selector)

      if not items:
        # Fallback: try to find any repeated structure
        self.logger.warning("Primary selector found no items, trying fallback")
        items = await page.query_selector_all("div[class*='card'], li, tr")

      self.logger.debug(f"Found {len(items)} potential monster entries")

      for item in items:
        try:
          # Extract English name
          name_en = await self._extract_text(item, selectors['name_en'])
          if not name_en:
            continue  # Skip if no name found

          # Extract Japanese name
          name_jp = await self._extract_text(item, selectors['name_jp'])

          # Extract weakness elements
          weakness = await self._extract_list(item, selectors['weakness'])

          # Extract materials
          materials = await self._extract_list(item, selectors['materials'])

          monster = Monster(
              en=name_en,
              jp=name_jp,
              weakness=weakness,
              materials=materials
          )

          monsters.append(monster.to_dict())

        except Exception as e:
          self.logger.debug(f"Error parsing monster item: {e}")
          continue

    except Exception as e:
      self.logger.error(f"Error in monster parsing: {e}")

    # If we got no results, log a warning
    if not monsters:
      self.logger.warning("No monsters extracted - selectors may need adjustment")

    return monsters

  async def _parse_weapons(self, page: Page, selectors: Dict[str, str]) -> List[Dict]:
    """Parse weapon data from the page."""
    weapons = []

    try:
      items = await page.query_selector_all(selectors['item'])

      if not items:
        items = await page.query_selector_all("div[class*='card'], li, tr")

      self.logger.debug(f"Found {len(items)} potential weapon entries")

      for item in items:
        try:
          name_en = await self._extract_text(item, selectors['name_en'])
          if not name_en:
            continue

          name_jp = await self._extract_text(item, selectors['name_jp'])
          weapon_class = await self._extract_text(item, selectors['weapon_class'])
          rarity = await self._extract_text(item, selectors['rarity'])

          weapon = Weapon(
              en=name_en,
              jp=name_jp,
              weapon_class=weapon_class,
              rarity=rarity
          )

          weapons.append(weapon.to_dict())

        except Exception as e:
          self.logger.debug(f"Error parsing weapon item: {e}")
          continue

    except Exception as e:
      self.logger.error(f"Error in weapon parsing: {e}")

    return weapons

  async def _parse_armor(self, page: Page, selectors: Dict[str, str]) -> List[Dict]:
    """Parse armor data from the page."""
    armor_list = []

    try:
      items = await page.query_selector_all(selectors['item'])

      if not items:
        items = await page.query_selector_all("div[class*='card'], li, tr")

      self.logger.debug(f"Found {len(items)} potential armor entries")

      for item in items:
        try:
          name_en = await self._extract_text(item, selectors['name_en'])
          if not name_en:
            continue

          name_jp = await self._extract_text(item, selectors['name_jp'])
          slot = await self._extract_text(item, selectors['slot'])
          skills = await self._extract_list(item, selectors['skills'])

          armor = Armor(
              en=name_en,
              jp=name_jp,
              slot=slot,
              skills=skills
          )

          armor_list.append(armor.to_dict())

        except Exception as e:
          self.logger.debug(f"Error parsing armor item: {e}")
          continue

    except Exception as e:
      self.logger.error(f"Error in armor parsing: {e}")

    return armor_list

  async def _parse_skills(self, page: Page, selectors: Dict[str, str]) -> List[Dict]:
    """Parse skill data from the page."""
    skills = []

    try:
      items = await page.query_selector_all(selectors['item'])

      if not items:
        items = await page.query_selector_all("div[class*='card'], li, tr")

      self.logger.debug(f"Found {len(items)} potential skill entries")

      for item in items:
        try:
          name_en = await self._extract_text(item, selectors['name_en'])
          if not name_en:
            continue

          name_jp = await self._extract_text(item, selectors['name_jp'])
          description = await self._extract_text(item, selectors['description'])

          skill = Skill(
              en=name_en,
              jp=name_jp,
              description=description
          )

          skills.append(skill.to_dict())

        except Exception as e:
          self.logger.debug(f"Error parsing skill item: {e}")
          continue

    except Exception as e:
      self.logger.error(f"Error in skill parsing: {e}")

    return skills

  async def _parse_items(self, page: Page, selectors: Dict[str, str]) -> List[Dict]:
    """Parse item data from the page."""
    items_list = []

    try:
      items = await page.query_selector_all(selectors['item'])

      if not items:
        items = await page.query_selector_all("div[class*='card'], li, tr")

      self.logger.debug(f"Found {len(items)} potential item entries")

      for item in items:
        try:
          name_en = await self._extract_text(item, selectors['name_en'])
          if not name_en:
            continue

          name_jp = await self._extract_text(item, selectors['name_jp'])
          category = await self._extract_text(item, selectors['category'])
          description = await self._extract_text(item, selectors['description'])

          item_obj = Item(
              en=name_en,
              jp=name_jp,
              category=category,
              description=description
          )

          items_list.append(item_obj.to_dict())

        except Exception as e:
          self.logger.debug(f"Error parsing item: {e}")
          continue

    except Exception as e:
      self.logger.error(f"Error in item parsing: {e}")

    return items_list

  async def _extract_text(self, element, selector: str) -> str:
    """Extract text from an element using a selector."""
    try:
      # Try each selector in the comma-separated list
      for sel in selector.split(','):
        sel = sel.strip()
        sub_element = await element.query_selector(sel)
        if sub_element:
          text = await sub_element.text_content()
          return text.strip() if text else ""
    except Exception:
      pass
    return ""

  async def _extract_list(self, element, selector: str) -> List[str]:
    """Extract a list of text values from elements matching a selector."""
    items = []
    try:
      for sel in selector.split(','):
        sel = sel.strip()
        sub_elements = await element.query_selector_all(sel)
        for sub_elem in sub_elements:
          text = await sub_elem.text_content()
          if text and text.strip():
            items.append(text.strip())
        if items:  # If we found items with this selector, stop trying others
          break
    except Exception:
      pass
    return items

  def save_data(self, all_data: Dict[str, List[Dict]]):
    """Save scraped data to JSON files."""
    self.logger.info("Saving data to JSON files...")

    # Save combined file
    combined_file = self.config.output_dir / "mhnow_data_all.json"
    combined_data = []
    for section_data in all_data.values():
      combined_data.extend(section_data)

    with open(combined_file, 'w', encoding='utf-8') as f:
      json.dump(combined_data, f, indent=2, ensure_ascii=False)
    self.logger.info(f"✓ Saved {len(combined_data)} total entries to {combined_file}")

    # Save individual files
    for section_name, data in all_data.items():
      if data:  # Only save if we have data
        section_file = self.config.output_dir / f"mhnow_{section_name}.json"
        with open(section_file, 'w', encoding='utf-8') as f:
          json.dump(data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"✓ Saved {section_name}: {len(data)} entries")

    # Save report
    report_file = self.config.output_dir / "scrape_report.json"
    self.report["timestamp"] = datetime.now().isoformat()
    with open(report_file, 'w', encoding='utf-8') as f:
      json.dump(self.report, f, indent=2)
    self.logger.info(f"✓ Saved scrape report to {report_file}")

  def print_summary(self):
    """Print a summary of the scraping operation."""
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)

    for section in ["monsters", "weapons", "armor", "skills", "items"]:
      data = self.report[section]
      print(f"{section.capitalize()}: {data['count']} entries")
      if data['errors']:
        print(f"  Errors: {data['errors']}")

    if self.report['global_errors']:
      print(f"\nGlobal Errors: {self.report['global_errors']}")

    print("="*60 + "\n")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main_async(mode: str = "normal"):
  """Async main function."""
  debug_mode = (mode == "debug")
  logger = setup_logging(debug_mode)
  config = ScraperConfig()

  scraper = MHNQuestScraper(config, logger, debug_mode)

  try:
    # Scrape all data
    all_data = await scraper.scrape_all()

    # Save results
    scraper.save_data(all_data)

    logger.info("Scraping completed successfully!")

  except Exception as e:
    logger.error(f"Scraping failed: {e}", exc_info=True)
    scraper.report['global_errors'].append(str(e))

  finally:
    # Always print summary, even if there were errors
    scraper.print_summary()

  # Return error code based on whether we got any data
  total_entries = sum(scraper.report[section]["count"] for section in ["monsters", "weapons", "armor", "skills", "items"])
  return 0 if total_entries > 0 else 1


def main():
  """Entry point for the script."""
  parser = argparse.ArgumentParser(
      description="Monster Hunter Now data scraper for mhn.quest"
  )
  parser.add_argument(
      '--mode',
      choices=['normal', 'debug'],
      default='normal',
      help='Run mode: normal (default) or debug (verbose logging, save HTML dumps)'
  )

  args = parser.parse_args()

  # Run async main
  exit_code = asyncio.run(main_async(args.mode))
  sys.exit(exit_code)


if __name__ == "__main__":
  main()