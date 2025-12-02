import argparse
import json
import logging
import time
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

# Third-party imports
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# --- CONFIGURATION & SELECTORS ---
CONFIG = {
  "base_url": "https://mhn.quest",
  "sections": {
    "monsters": {
      "url_suffix": "/monster",
      "container_selector": "div.monster-list, table.monster-table",
      "item_selector": "div.monster-card, tr.monster-row"
    },
    "weapons": {
      "url_suffix": "/weapon",
      "container_selector": "div.weapon-list",
      "item_selector": "div.weapon-card"
    },
    "armor": {
      "url_suffix": "/armor",
      "container_selector": "div.armor-list",
      "item_selector": "div.armor-card"
    },
    "skills": {
      "url_suffix": "/skill",
      "container_selector": "div.skill-list",
      "item_selector": "div.skill-card"
    },
    "items": {
      "url_suffix": "/material",
      "container_selector": "div.material-list",
      "item_selector": "div.material-card"
    }
  },
  "timeouts": {
    "normal": 4000,
    "debug": 8000
  }
}

class MHNScraper:
  def __init__(self, mode: str = "normal"):
    self.mode = mode
    self.data: Dict[str, List[Dict]] = {
      "monsters": [],
      "weapons": [],
      "armor": [],
      "skills": [],
      "items": []
    }
    self.report = {
      "global_errors": [],
      "sections": {}
    }
    self._setup_logging()

  def _setup_logging(self):
    level = logging.DEBUG if self.mode == "debug" else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    self.logger = logging.getLogger(__name__)

  def _wait_time(self) -> int:
    return CONFIG["timeouts"]["debug"] if self.mode == "debug" else CONFIG["timeouts"]["normal"]

  def _save_debug_html(self, content: str, section_name: str):
    if self.mode == "debug":
      filename = f"debug_{section_name}.html"
      with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
      self.logger.debug(f"Saved debug HTML to {filename}")

  # --- POPUP HANDLER (NEW) ---
  def _handle_consent_popup(self, page: Page):
    """
    Detects and closes the GDPR/Cookie Consent popup if it appears.
    """
    try:
      # Look for a button with text "Consent" (case insensitive usually works with text=)
      # We use a short timeout so we don't block forever if it doesn't exist.
      consent_btn = page.get_by_role("button", name="Consent", exact=True)

      if consent_btn.is_visible(timeout=5000):
        self.logger.info("GDPR Popup detected. Clicking 'Consent'...")
        consent_btn.click()
        # Wait a moment for the popup to fade out and content to become interactive
        page.wait_for_timeout(2000)
      else:
        self.logger.debug("No GDPR popup found (or it loaded too slowly).")

    except Exception as e:
      # Don't crash the script if popup handling fails, just log it.
      self.logger.warning(f"Popup check encountered an issue (ignoring): {e}")

  # --- PARSING LOGIC ---

  def parse_monsters(self, html: str) -> List[Dict]:
    """Parses HTML content to extract monster data."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    rows = soup.select(CONFIG["sections"]["monsters"]["item_selector"])

    # Fallback if specific config selector fails
    if not rows:
      self.logger.debug("Specific monster selector not found, trying generic fallback.")
      rows = soup.find_all("div", class_=lambda x: x and "card" in x)

    for row in rows:
      try:
        name_en = row.find(text=True, recursive=False) or "Unknown Monster"
        name_jp = "TODO"

        weaknesses = [img['alt'] for img in row.find_all('img') if 'weak' in (img.get('class', []) or [])]

        entry = {
          "type": "monster",
          "en": str(name_en).strip(),
          "jp": name_jp,
          "weakness": weaknesses,
          "materials": [],
          "notes": ""
        }
        results.append(entry)
      except Exception as e:
        self.logger.warning(f"Failed to parse a monster row: {e}")

    return results

  def parse_skills(self, html: str) -> List[Dict]:
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    rows = soup.select(CONFIG["sections"]["skills"]["item_selector"])

    for row in rows:
      try:
        name = row.find("h3") or row.find("div", class_="name")
        desc = row.find("p") or row.find("div", class_="description")

        entry = {
          "type": "skill",
          "en": name.get_text(strip=True) if name else "Unknown Skill",
          "jp": "",
          "description": desc.get_text(strip=True) if desc else "",
          "notes": ""
        }
        results.append(entry)
      except Exception:
        continue
    return results

  # --- PLACEHOLDERS FOR OTHER SECTIONS ---
  # NOTE: You must implement the logic below once you see the debug HTML structure.
  # Currently, they return 1 placeholder item so you know the pipeline works.

  def parse_weapons(self, html: str) -> List[Dict]:
    return [{"type": "weapon", "en": "Example Weapon", "jp": "例", "weapon_class": "Sword"}]

  def parse_armor(self, html: str) -> List[Dict]:
    return [{"type": "armor", "en": "Example Helm", "jp": "例", "slot": "head"}]

  def parse_items(self, html: str) -> List[Dict]:
    return [{"type": "item", "en": "Iron Ore", "jp": "鉄鉱石", "category": "material"}]

  # --- BROWSER INTERACTION ---

  def fetch_and_process(self, section_key: str, parser_func):
    url = f"{CONFIG['base_url']}{CONFIG['sections'][section_key]['url_suffix']}"
    self.logger.info(f"Scraping section: {section_key} from {url}")

    with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()

      try:
        page.goto(url)

        # --- NEW: HANDLE POPUP ---
        self._handle_consent_popup(page)
        # -------------------------

        try:
          page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout:
          self.logger.warning("Network idle timeout - proceeding anyway.")

        time.sleep(self._wait_time() / 1000)

        content = page.content()
        self._save_debug_html(content, section_key)

        items = parser_func(content)
        self.data[section_key] = items

        count = len(items)
        self.logger.info(f"Extracted {count} {section_key}.")

        self.report["sections"][section_key] = {
          "count": count,
          "errors": [] if count > 0 else ["No items found - check selectors"]
        }

      except Exception as e:
        err_msg = f"Critical failure in {section_key}: {str(e)}"
        self.logger.error(err_msg)
        self.report["sections"][section_key] = {"count": 0, "errors": [err_msg]}
        self.report["global_errors"].append(err_msg)

      finally:
        browser.close()

  def run(self):
    self.logger.info(f"Starting MHN Scraper in {self.mode.upper()} mode.")

    self.fetch_and_process("monsters", self.parse_monsters)
    self.fetch_and_process("skills", self.parse_skills)
    self.fetch_and_process("items", self.parse_items)
    self.fetch_and_process("weapons", self.parse_weapons)
    self.fetch_and_process("armor", self.parse_armor)

    self._write_output()

  def _write_output(self):
    main_file = "mhnow_data_all.json"
    with open(main_file, "w", encoding="utf-8") as f:
      json.dump(self.data, f, indent=2, ensure_ascii=False)
    self.logger.info(f"Written main database to {main_file}")

    for key, items in self.data.items():
      filename = f"mhnow_{key}.json"
      with open(filename, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    with open("scrape_report.json", "w", encoding="utf-8") as f:
      json.dump(self.report, f, indent=2)

    self.logger.info("Scraping completed. Check scrape_report.json for details.")

def main():
  parser = argparse.ArgumentParser(description="MHN Quest Scraper")
  parser.add_argument("--mode", choices=["normal", "debug"], default="normal", help="Execution mode")
  args = parser.parse_args()

  scraper = MHNScraper(mode=args.mode)
  scraper.run()

if __name__ == "__main__":
  main()