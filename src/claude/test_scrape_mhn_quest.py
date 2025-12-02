#!/usr/bin/env python3
"""
Tests for Monster Hunter Now scraper

Run with: pytest test_scrape_mhn_quest_gemini.py -v
or: python -m pytest test_scrape_mhn_quest_gemini.py -v
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from scrape_mhn_quest import (
  ScraperConfig,
  MHNQuestScraper,
  Monster,
  Weapon,
  Armor,
  Skill,
  Item,
  setup_logging
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def config():
  """Create a test configuration."""
  config = ScraperConfig()
  config.output_dir = Path("/tmp/mhn_test_output")
  config.debug_dir = Path("/tmp/mhn_test_debug")
  return config


@pytest.fixture
def logger():
  """Create a test logger."""
  return setup_logging(debug_mode=True)


@pytest.fixture
def scraper(config, logger):
  """Create a test scraper instance."""
  return MHNQuestScraper(config, logger, debug_mode=False)


# ============================================================================
# HTML FIXTURES FOR TESTING PARSERS
# ============================================================================

SAMPLE_MONSTER_HTML = """
<div class="monster-card">
    <div class="name-en">Great Jagras</div>
    <div class="name-jp">ドスジャグラス</div>
    <div class="weakness">Fire</div>
    <div class="weakness">Thunder</div>
    <div class="material">Jagras Scale</div>
    <div class="material">Jagras Hide</div>
</div>
"""

SAMPLE_WEAPON_HTML = """
<div class="weapon-card">
    <div class="name-en">Iron Sword</div>
    <div class="name-jp">鉄刀</div>
    <div class="type">Great Sword</div>
    <div class="rarity">2</div>
</div>
"""

SAMPLE_ARMOR_HTML = """
<div class="armor-card">
    <div class="name-en">Leather Helm</div>
    <div class="name-jp">レザーヘルム</div>
    <div class="slot">Head</div>
    <div class="skill">Defense Boost</div>
</div>
"""

SAMPLE_SKILL_HTML = """
<div class="skill-card">
    <div class="name-en">Attack Boost</div>
    <div class="name-jp">攻撃力UP</div>
    <div class="description">Increases attack power</div>
</div>
"""

SAMPLE_ITEM_HTML = """
<div class="item-card">
    <div class="name-en">Potion</div>
    <div class="name-jp">回復薬</div>
    <div class="category">Consumable</div>
    <div class="description">Restores health</div>
</div>
"""


# ============================================================================
# DATA MODEL TESTS
# ============================================================================

def test_monster_creation():
  """Test Monster dataclass creation and serialization."""
  monster = Monster(
      en="Great Jagras",
      jp="ドスジャグラス",
      weakness=["fire", "thunder"],
      materials=["Jagras Scale", "Jagras Hide"]
  )

  data = monster.to_dict()

  assert data["type"] == "monster"
  assert data["en"] == "Great Jagras"
  assert data["jp"] == "ドスジャグラス"
  assert "fire" in data["weakness"]
  assert "thunder" in data["weakness"]
  assert len(data["materials"]) == 2


def test_weapon_creation():
  """Test Weapon dataclass creation and serialization."""
  weapon = Weapon(
      en="Iron Sword",
      jp="鉄刀",
      weapon_class="Great Sword",
      rarity="2"
  )

  data = weapon.to_dict()

  assert data["type"] == "weapon"
  assert data["en"] == "Iron Sword"
  assert data["weapon_class"] == "Great Sword"
  assert data["rarity"] == "2"


def test_armor_creation():
  """Test Armor dataclass creation and serialization."""
  armor = Armor(
      en="Leather Helm",
      jp="レザーヘルム",
      slot="Head",
      skills=["Defense Boost"]
  )

  data = armor.to_dict()

  assert data["type"] == "armor"
  assert data["slot"] == "Head"
  assert "Defense Boost" in data["skills"]


def test_empty_fields_removed():
  """Test that empty fields are removed from output."""
  monster = Monster(
      en="Test Monster",
      jp="",
      weakness=[],
      materials=None
  )

  data = monster.to_dict()

  assert "en" in data
  assert "jp" not in data  # Empty string removed
  assert "weakness" not in data  # Empty list removed
  assert "materials" not in data  # None removed


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

def test_config_initialization():
  """Test that configuration initializes with defaults."""
  config = ScraperConfig()

  assert config.base_url == "http://mhn.quest"
  assert "monsters" in config.sections
  assert "weapons" in config.sections
  assert config.normal_wait == 3000
  assert config.debug_wait == 6000


def test_config_selectors():
  """Test that selectors are properly configured."""
  config = ScraperConfig()

  assert "monsters" in config.selectors
  assert "name_en" in config.selectors["monsters"]
  assert "name_jp" in config.selectors["monsters"]
  assert "weakness" in config.selectors["monsters"]


# ============================================================================
# SCRAPER INITIALIZATION TESTS
# ============================================================================

def test_scraper_initialization(scraper):
  """Test scraper initialization."""
  assert scraper.config is not None
  assert scraper.logger is not None
  assert scraper.report is not None
  assert "monsters" in scraper.report
  assert "weapons" in scraper.report


def test_scraper_creates_directories(scraper):
  """Test that scraper creates necessary directories."""
  assert scraper.config.output_dir.exists()


# ============================================================================
# MOCK ELEMENT FOR TESTING PARSERS
# ============================================================================

class MockElement:
  """Mock Playwright element for testing."""

  def __init__(self, html: str):
    self.html = html
    self._elements = {}
    self._parse_html(html)

  def _parse_html(self, html: str):
    """Simple HTML parser to extract elements by class."""
    import re
    # Extract divs with classes
    pattern = r'<div class="([^"]+)">([^<]+)</div>'
    matches = re.findall(pattern, html)
    for class_name, content in matches:
      if class_name not in self._elements:
        self._elements[class_name] = []
      self._elements[class_name].append(content)

  async def query_selector(self, selector: str):
    """Mock query_selector."""
    # Remove leading dot from class selector
    class_name = selector.lstrip('.')
    if class_name in self._elements and self._elements[class_name]:
      elem = MockElement("")
      elem._content = self._elements[class_name][0]
      return elem
    return None

  async def query_selector_all(self, selector: str):
    """Mock query_selector_all."""
    class_name = selector.lstrip('.')
    if class_name in self._elements:
      elements = []
      for content in self._elements[class_name]:
        elem = MockElement("")
        elem._content = content
        elements.append(elem)
      return elements
    return []

  async def text_content(self):
    """Mock text_content."""
    return getattr(self, '_content', '')


# ============================================================================
# PARSER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extract_text(scraper):
  """Test _extract_text helper method."""
  element = MockElement(SAMPLE_MONSTER_HTML)

  # Test extracting name
  name = await scraper._extract_text(element, ".name-en")
  assert name == "Great Jagras"

  # Test extracting Japanese name
  name_jp = await scraper._extract_text(element, ".name-jp")
  assert name_jp == "ドスジャグラス"


@pytest.mark.asyncio
async def test_extract_list(scraper):
  """Test _extract_list helper method."""
  element = MockElement(SAMPLE_MONSTER_HTML)

  # Test extracting weakness list
  weaknesses = await scraper._extract_list(element, ".weakness")
  assert len(weaknesses) == 2
  assert "Fire" in weaknesses
  assert "Thunder" in weaknesses

  # Test extracting materials list
  materials = await scraper._extract_list(element, ".material")
  assert len(materials) == 2
  assert "Jagras Scale" in materials


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_parse_monster_from_html(scraper):
  """Test parsing a monster from HTML fixture."""
  # Create mock page
  mock_page = MagicMock()
  element = MockElement(SAMPLE_MONSTER_HTML)
  mock_page.query_selector_all = AsyncMock(return_value=[element])

  # Parse monsters
  selectors = scraper.config.selectors["monsters"]
  monsters = await scraper._parse_monsters(mock_page, selectors)

  # Verify results
  assert len(monsters) == 1
  monster = monsters[0]
  assert monster["type"] == "monster"
  assert monster["en"] == "Great Jagras"
  assert monster["jp"] == "ドスジャグラス"


@pytest.mark.asyncio
async def test_parse_weapon_from_html(scraper):
  """Test parsing a weapon from HTML fixture."""
  mock_page = MagicMock()
  element = MockElement(SAMPLE_WEAPON_HTML)
  mock_page.query_selector_all = AsyncMock(return_value=[element])

  selectors = scraper.config.selectors["weapons"]
  weapons = await scraper._parse_weapons(mock_page, selectors)

  assert len(weapons) == 1
  weapon = weapons[0]
  assert weapon["type"] == "weapon"
  assert weapon["en"] == "Iron Sword"
  assert weapon["weapon_class"] == "Great Sword"


# ============================================================================
# OUTPUT TESTS
# ============================================================================

def test_save_data(scraper, tmp_path):
  """Test data saving functionality."""
  # Override output directory for test
  scraper.config.output_dir = tmp_path

  # Create test data
  test_data = {
    "monsters": [
      {"type": "monster", "en": "Test Monster", "jp": "テストモンスター"}
    ],
    "weapons": [
      {"type": "weapon", "en": "Test Weapon", "jp": "テスト武器"}
    ],
    "armor": [],
    "skills": [],
    "items": []
  }

  # Save data
  scraper.save_data(test_data)

  # Verify files were created
  assert (tmp_path / "mhnow_data_all.json").exists()
  assert (tmp_path / "mhnow_monsters.json").exists()
  assert (tmp_path / "mhnow_weapons.json").exists()
  assert (tmp_path / "scrape_report.json").exists()

  # Verify content
  with open(tmp_path / "mhnow_data_all.json", 'r', encoding='utf-8') as f:
    data = json.load(f)
    assert len(data) == 2  # 1 monster + 1 weapon


def test_report_generation(scraper):
  """Test that report is properly populated."""
  scraper.report["monsters"]["count"] = 64
  scraper.report["weapons"]["count"] = 120
  scraper.report["monsters"]["errors"].append("Test error")

  assert scraper.report["monsters"]["count"] == 64
  assert scraper.report["weapons"]["count"] == 120
  assert len(scraper.report["monsters"]["errors"]) == 1


# ============================================================================
# SMOKE TEST
# ============================================================================

def test_smoke_config_and_setup():
  """Smoke test: verify basic setup works without errors."""
  config = ScraperConfig()
  logger = setup_logging(debug_mode=False)
  scraper = MHNQuestScraper(config, logger, debug_mode=False)

  assert scraper is not None
  assert scraper.config.base_url == "http://mhn.quest"
  assert len(scraper.report) > 0


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_json_schema_validation():
  """Test that output follows expected JSON schema."""
  monster = Monster(
      en="Test",
      jp="テスト",
      weakness=["fire"],
      materials=["Test Material"]
  ).to_dict()

  # Required fields
  assert "type" in monster
  assert "en" in monster
  assert "jp" in monster

  # Type must be correct
  assert monster["type"] == "monster"

  # Lists must be lists
  assert isinstance(monster["weakness"], list)
  assert isinstance(monster["materials"], list)


def test_unicode_handling():
  """Test that Japanese characters are properly handled."""
  monster = Monster(
      en="Great Jagras",
      jp="ドスジャグラス"
  )

  data = monster.to_dict()
  assert data["jp"] == "ドスジャグラス"

  # Test JSON serialization
  json_str = json.dumps(data, ensure_ascii=False)
  assert "ドスジャグラス" in json_str


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extract_text_handles_missing_element(scraper):
  """Test that _extract_text handles missing elements gracefully."""
  element = MockElement("<div></div>")

  # Should return empty string, not raise exception
  result = await scraper._extract_text(element, ".nonexistent")
  assert result == ""


@pytest.mark.asyncio
async def test_parse_handles_empty_page(scraper):
  """Test that parser handles pages with no data."""
  mock_page = MagicMock()
  mock_page.query_selector_all = AsyncMock(return_value=[])

  selectors = scraper.config.selectors["monsters"]
  monsters = await scraper._parse_monsters(mock_page, selectors)

  # Should return empty list, not crash
  assert monsters == []


if __name__ == "__main__":
  # Run tests with pytest
  pytest.main([__file__, "-v"])