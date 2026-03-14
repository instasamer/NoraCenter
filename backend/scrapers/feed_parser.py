"""Lightweight RSS/Atom parser using lxml (no feedparser dependency)."""

from datetime import datetime
from email.utils import parsedate_to_datetime

from lxml import etree


class FeedEntry:
    """A single entry/item from an RSS or Atom feed."""

    def __init__(self, title: str = "", link: str = "", summary: str = "",
                 published: datetime | None = None):
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published


def parse_feed(xml_text: str) -> list[FeedEntry]:
    """Parse RSS 2.0 or Atom feed XML into a list of FeedEntry objects."""
    entries = []

    try:
        # Remove encoding declaration if present (lxml handles bytes vs str)
        if xml_text.startswith("<?xml"):
            xml_text = xml_text.split("?>", 1)[-1] if "?>" in xml_text else xml_text

        root = etree.fromstring(xml_text.encode("utf-8", errors="replace"),
                                parser=etree.XMLParser(recover=True))
    except Exception:
        return entries

    if root is None:
        return entries

    # Detect feed type
    tag = root.tag.lower().split("}")[-1] if "}" in root.tag else root.tag.lower()

    if tag == "rss":
        entries = _parse_rss(root)
    elif tag == "feed":
        entries = _parse_atom(root)
    elif tag == "rdf":
        entries = _parse_rdf(root)
    else:
        # Try to find items anyway
        entries = _parse_rss(root) or _parse_atom(root)

    return entries


def _parse_rss(root) -> list[FeedEntry]:
    """Parse RSS 2.0 format."""
    entries = []
    # Find all <item> elements anywhere in the tree
    for item in root.iter():
        local = item.tag.split("}")[-1] if "}" in item.tag else item.tag
        if local != "item":
            continue

        title = _get_child_text(item, "title")
        link = _get_child_text(item, "link")
        desc = _get_child_text(item, "description") or _get_child_text(item, "summary")
        pub_date = _parse_date(_get_child_text(item, "pubDate") or
                               _get_child_text(item, "date") or
                               _get_child_text(item, "published"))

        if title or link:
            entries.append(FeedEntry(title=title, link=link, summary=desc or "",
                                     published=pub_date))
    return entries


def _parse_atom(root) -> list[FeedEntry]:
    """Parse Atom format."""
    entries = []
    for item in root.iter():
        local = item.tag.split("}")[-1] if "}" in item.tag else item.tag
        if local != "entry":
            continue

        title = _get_child_text(item, "title")
        summary = _get_child_text(item, "summary") or _get_child_text(item, "content")
        pub_date = _parse_date(_get_child_text(item, "published") or
                               _get_child_text(item, "updated"))

        # Atom uses <link href="..."/> or <link>url</link>
        link = ""
        for child in item:
            child_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_local == "link":
                link = child.get("href", "") or (child.text or "").strip()
                if link and child.get("rel", "alternate") == "alternate":
                    break

        if title or link:
            entries.append(FeedEntry(title=title, link=link, summary=summary or "",
                                     published=pub_date))
    return entries


def _parse_rdf(root) -> list[FeedEntry]:
    """Parse RDF/RSS 1.0 format (same item structure as RSS)."""
    return _parse_rss(root)


def _get_child_text(element, local_name: str) -> str:
    """Get text of a child element, ignoring namespaces."""
    for child in element:
        child_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if child_local == local_name:
            return (child.text or "").strip()
    return ""


def _parse_date(text: str) -> datetime | None:
    """Try to parse a date string from RSS/Atom feeds."""
    if not text:
        return None

    # Try RFC 2822 (RSS pubDate format)
    try:
        return parsedate_to_datetime(text)
    except Exception:
        pass

    # Try ISO 8601 (Atom format)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d",
                "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None
