"""Parse local policy documents into source-linked sections without model calls."""
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


@dataclass(frozen=True)
class Section:
    label: str
    heading: str
    text: str
    page: int = 0
    line_start: int = 0
    line_end: int = 0


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(c for c in text if c in "\n\t" or ord(c) >= 32)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_markdown(text: str) -> list[Section]:
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    lines = text.replace("\r\n", "\n").splitlines()
    start = 0
    if lines and re.match(r"# LVB-\d{2}:", lines[0]):
        start = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
    output, body = [], []
    label, heading, first_line = "preamble", "Introduction", start + 1
    heading_number = 0

    def flush(last_line):
        content = clean_text("\n".join(body))
        if content:
            output.append(Section(label, heading, content, line_start=first_line, line_end=last_line))
        body.clear()

    for i in range(start, len(lines)):
        line = lines[i]
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            flush(i)
            heading_number += 1
            heading = match.group(1)
            numbered = re.match(r"^(\d+(?:\.\d+)*)\.?\s+", heading)
            label = numbered.group(1) if numbered else f"heading-{heading_number}"
            first_line = i + 2
        elif not re.match(r"^\s*(\x60{3,}|~{3,})", line):
            body.append(line)
    flush(len(lines))
    labels = [section.label for section in output]
    if len(labels) != len(set(labels)):
        raise ValueError("Duplicate section identifiers would make citations ambiguous.")
    if not output:
        raise ValueError("Document has no substantive text.")
    return output


def parse_html(text: str) -> list[Section]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for node in soup.select("script, style, nav, footer, noscript, template, [hidden]"):
        node.decompose()
    for node in soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(node.name[1])
        node.replace_with(f"\n{'#' * level} {node.get_text(' ', strip=True)}\n")
    content = (soup.body or soup).get_text("\n", strip=True)
    return [Section(s.label, s.heading, s.text) for s in parse_markdown(content)]


def parse_pdf(path: Path) -> list[Section]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs must be supplied as an authorized unencrypted copy.")
    pages = [(p.extract_text() or "").splitlines() for p in reader.pages]
    if not pages:
        raise ValueError("PDF contains no pages.")
    for number, lines in enumerate(pages, 1):
        if not clean_text("\n".join(lines)):
            raise ValueError(f"PDF page {number} has no extractable text; OCR or blank-page review is required.")
    repeated = set()
    if len(pages) > 1:
        counts = {}
        for lines in pages:
            for line in {item.strip() for item in lines[:2] + lines[-2:]}:
                if line:
                    counts[line] = counts.get(line, 0) + 1
        repeated = {line for line, count in counts.items() if count == len(pages)}
    output = []
    for number, lines in enumerate(pages, 1):
        kept = [line for i, line in enumerate(lines)
                if not ((i < 2 or i >= len(lines) - 2) and line.strip() in repeated)
                and not (i >= len(lines) - 2 and re.fullmatch(r"\s*\d+\s*(?:/\s*\d+)?\s*", line))]
        content = clean_text("\n".join(kept))
        if not content:
            raise ValueError(f"PDF page {number} has no content after header/footer cleanup.")
        output.append(Section(f"page-{number}", f"Page {number}", content, page=number))
    return output


def parse_document(path: Path) -> list[Section]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix not in {".md", ".txt", ".html", ".htm"}:
        raise ValueError(f"Unsupported policy format: {suffix}")
    text = path.read_text(encoding="utf-8-sig")
    if suffix in {".html", ".htm"}:
        return parse_html(text)
    if suffix == ".md":
        return parse_markdown(text)
    content = clean_text(text)
    if not content:
        raise ValueError("Text document is empty.")
    return [Section("text", "Document text", content, line_start=1, line_end=len(text.splitlines()))]
