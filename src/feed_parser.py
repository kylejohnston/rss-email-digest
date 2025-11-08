"""RSS feed parser module."""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict


def parse_opml(opml_path: Path) -> List[Dict[str, str]]:
    """
    Parse OPML file and extract RSS feed URLs and titles.

    Args:
        opml_path: Path to OPML file

    Returns:
        List of dicts with 'title' and 'url' keys

    Raises:
        FileNotFoundError: If OPML file doesn't exist
    """
    if not opml_path.exists():
        raise FileNotFoundError(f"OPML file not found: {opml_path}")

    tree = ET.parse(opml_path)
    root = tree.getroot()

    feeds = []
    # Find all outline elements with xmlUrl attribute (RSS feeds)
    for outline in root.findall(".//outline[@xmlUrl]"):
        feeds.append({
            "title": outline.get("text") or outline.get("title"),
            "url": outline.get("xmlUrl")
        })

    return feeds
