#!/usr/bin/env python3
"""Generate an RSS feed of the latest Native Instruments Reaktor User Library uploads.

The old feed scraped the HTML listing on native-instruments.com, which is long
gone. The library now lives behind a public JSON API, so this script reads that
API and writes an RSS 2.0 document.

The output file is served as .php on the SDF so a Content-Type header can be
set; the PHP wrapper at the top of the file exists purely to emit that header.
"""

import sys
import json
import datetime
import email.utils
import urllib.request
from xml.sax.saxutils import escape, quoteattr

API_URL = (
    "https://api-userlibrary.nicom.native-cloud.com/api/library"
    "?limit=20&page=1&librarySlug=reaktor"
)
DETAIL_URL = "https://userlibrary.native-instruments.com/reaktor/item/{id}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

HEADER = """<?php header('Content-Type: application/rss+xml; charset=UTF-8'); ?><?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Reaktor User Library</title>
    <link>https://userlibrary.native-instruments.com/reaktor</link>
    <atom:link href="<?php echo ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') ? 'https' : 'http').'://'.$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI']; ?>" rel="self" type="application/rss+xml" />
    <description>Latest uploads to the Native Instruments Reaktor User Library</description>
    <language>en</language>
    <docs>https://validator.w3.org/feed/docs/rss2.html</docs>
    <generator>Python</generator>
"""

FOOTER = """  </channel>
</rss>
"""


def fetch_items():
    """Return the latest Reaktor library items, newest first."""
    request = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return payload.get("data", [])


def rfc822(timestamp):
    """Convert an ISO-8601 UTC timestamp to an RFC-822 pubDate, or None."""
    if not timestamp:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return email.utils.format_datetime(parsed, usegmt=True)
    except (ValueError, TypeError, AttributeError):
        return None


def clean_text(text):
    """Normalise line endings and strip surrounding whitespace."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def description_for(item):
    """Build the HTML body of an RSS item's <description> element."""
    parts = []

    cover = item.get("coverImage")
    if cover:
        parts.append("<img src=%s />" % quoteattr(cover))

    text = clean_text(item.get("subtitle") or item.get("description"))
    if text:
        parts.append(escape(text).replace("\n", "<br/>"))

    byline = []
    user = (item.get("user") or {}).get("name")
    if user:
        byline.append("by %s" % escape(user))
    meta = " / ".join(
        name
        for name in (
            (item.get("type") or {}).get("name"),
            (item.get("category") or {}).get("name"),
        )
        if name
    )
    if meta:
        byline.append(escape(meta))
    if byline:
        parts.append(" \u00b7 ".join(byline))

    return "<br/>".join(parts)


def image_mime_type(url):
    """Guess a MIME type from a cover image URL extension."""
    if not url:
        return None
    url = url.lower()
    if url.endswith(".png"):
        return "image/png"
    if url.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if url.endswith(".gif"):
        return "image/gif"
    if url.endswith(".webp"):
        return "image/webp"
    return None


def item_xml(item):
    """Render one library item as an RSS <item> element."""
    title = escape(clean_text(item.get("title")))
    link = DETAIL_URL.format(id=item["id"])
    link_esc = escape(link)
    description = description_for(item)

    pub_date = rfc822(item.get("createdAt"))
    date_line = ("      <pubDate>%s</pubDate>\n" % pub_date) if pub_date else ""

    media_lines = ""
    cover = item.get("coverImage")
    if cover:
        media_lines += "      <media:thumbnail url=%s />\n" % quoteattr(cover)
        mime = image_mime_type(cover)
        if mime:
            media_lines += (
                "      <media:content url=%s medium=\"image\" type=\"%s\" />\n"
                % (quoteattr(cover), mime)
            )

    return (
        "    <item>\n"
        f"      <title>{title}</title>\n"
        f"      <link>{link_esc}</link>\n"
        f'      <guid isPermaLink="true">{link_esc}</guid>\n'
        f"{date_line}"
        f"{media_lines}"
        f"      <description><![CDATA[{description}]]></description>\n"
        "    </item>\n"
    )


def generate(output_file):
    """Fetch the latest items and write the RSS document to output_file."""
    items = fetch_items()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(HEADER)
        for item in items:
            f.write(item_xml(item))
        f.write(FOOTER)
    return len(items)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: %s <output-file>\n" % sys.argv[0])
        sys.exit(1)
    try:
        count = generate(sys.argv[1])
        print("Wrote %d items to %s" % (count, sys.argv[1]))
    except Exception as exc:
        sys.stderr.write("Failed to update feed: %s\n" % exc)
        sys.exit(1)
