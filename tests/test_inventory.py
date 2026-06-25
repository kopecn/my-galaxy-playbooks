"""Static checks on inventory files — no live hosts required."""
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORIES = sorted((REPO_ROOT / "inventories").glob("*/hosts.yml"))


@pytest.mark.parametrize("inv", INVENTORIES, ids=lambda p: p.parent.name)
def test_inventory_parses(inv):
    """Each YAML inventory loads and defines an 'all' group with children."""
    data = yaml.safe_load(inv.read_text())
    assert "all" in data, f"{inv} is missing the top-level 'all' group"
    assert data["all"].get("children"), f"{inv} defines no child groups"
