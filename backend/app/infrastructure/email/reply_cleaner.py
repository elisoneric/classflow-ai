"""
Strips quoted history and signature blocks from a lecturer's email reply
before it reaches the AI interpreter — see PROJECT.md §11 and §16 ("Email
reply parsing is inherently messy"). Deliberately simple regex-based
heuristics rather than a full quote-parsing library: covers the common
top-posting clients (Gmail, Outlook, Apple Mail) without an extra
dependency; known to be imperfect on unusual mail clients.
"""

import re

_QUOTE_HEADER_PATTERNS = [
    re.compile(r"^\s*On .{0,120} wrote:\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*From:\s*.+$", re.MULTILINE),
]

_SIGNATURE_DELIMITER = re.compile(r"^--\s*$", re.MULTILINE)


def clean_reply(raw_body: str) -> str:
    text = raw_body.replace("\r\n", "\n")

    cut_points = [m.start() for m in (p.search(text) for p in _QUOTE_HEADER_PATTERNS) if m]
    sig_match = _SIGNATURE_DELIMITER.search(text)
    if sig_match:
        cut_points.append(sig_match.start())

    if cut_points:
        text = text[: min(cut_points)]

    lines = [line for line in text.split("\n") if not line.lstrip().startswith(">")]
    return "\n".join(lines).strip()
