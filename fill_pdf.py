"""Shared PDF-filling engine for the ASYA document generator.

This module contains the low-level, document-agnostic building blocks used by
every document type in ``documents/``:

- Font resolution (bundled Times New Roman, with broad fallbacks)
- Placeholder discovery + rect picking (``search_for`` / ``_pick_rect``)
- Baseline extraction (exact text baseline from the page text dict)
- Redaction (white-out) of placeholder areas
- Text re-insertion at the original baseline
- Screenshot slot clearing and insertion

Document-specific logic (template path, field list, which placeholders to
replace, paragraph rewrites, screenshot layout) lives in ``documents/``.
"""

import io
import os

import fitz
from PIL import Image

FONT_SEARCH_PATHS = [
    os.path.dirname(os.path.abspath(__file__)),
    "/System/Library/Fonts/Supplemental",
    "/usr/share/fonts/truetype/msttcorefonts",
    "/usr/share/fonts/truetype/liberation",
]


def _find_font(name):
    for d in FONT_SEARCH_PATHS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


FONT_REGULAR = (
    _find_font("TimesNewRoman.ttf")
    or _find_font("Times New Roman.ttf")
    or _find_font("LiberationSerif-Regular.ttf")
    or _find_font("times.ttf")
)
FONT_BOLD = (
    _find_font("TimesNewRomanBold.ttf")
    or _find_font("Times New Roman Bold.ttf")
    or _find_font("LiberationSerif-Bold.ttf")
    or _find_font("timesbd.ttf")
)

FONT_SIZE = 12
LINE_HEIGHT = FONT_SIZE * 1.3
Y_TOLERANCE = 5

FONTNAME_REGULAR = "TNR"
FONTNAME_BOLD = "TNRB"


def font_available(font_path):
    return font_path is not None and os.path.exists(font_path)


def insert_fonts(page, has_regular, has_bold):
    """Embed bundled Times New Roman faces into ``page``."""
    if has_regular:
        page.insert_font(fontname=FONTNAME_REGULAR, fontfile=FONT_REGULAR)
    if has_bold:
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)


def font_name(use_bold, has_regular, has_bold):
    if use_bold and has_bold:
        return FONTNAME_BOLD
    if has_regular:
        return FONTNAME_REGULAR
    return "helv"


def clear_annotations(doc):
    """Remove every annotation from every page (redactions are re-added by us)."""
    for page in doc:
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot


def apply_redactions(doc):
    for page in doc:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)


def _pick_rect(areas):
    """Pick one rect when a placeholder string matches multiple locations.

    Multiple matches on the same line (within Y_TOLERANCE) are merged into a
    single bounding rect. If several distinct lines matched, the lowest one is
    used (this was the fix for "destructive combined redaction when text
    appears in multiple locations", commit d736b92).
    """
    if len(areas) == 1:
        return areas[0]

    groups = {}
    for area in areas:
        y_key = round(area.y0 / Y_TOLERANCE)
        groups[y_key] = area if y_key not in groups else fitz.Rect(
            min(groups[y_key].x0, area.x0),
            min(groups[y_key].y0, area.y0),
            max(groups[y_key].x1, area.x1),
            max(groups[y_key].y1, area.y1),
        )

    if len(groups) == 1:
        return list(groups.values())[0]

    return groups[max(groups.keys())]


def find_baseline(page, rect, old_text):
    """Extract the exact text baseline from the page text dict.

    Inserting at ``rect.y1 - font_size * 0.22`` is only an approximation; the
    real baseline (span origin y) keeps the replacement vertically aligned with
    the original placeholder (commit 5614248).
    """
    baseline = rect.y1 - FONT_SIZE * 0.22
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if old_text in span["text"]:
                    baseline = span["origin"][1]
                    break
    return baseline


def redact_and_collect(doc, page_idx, old_text, new_text, use_bold, expand_fn):
    """Redact a placeholder and return insert info, or None if not found.

    - ``old_text``: placeholder string living inside the template PDF.
    - ``expand_fn(rect) -> fitz.Rect``: minimal expansion around the found rect
      so neighbouring pixels are fully covered without nuking other content.
    """
    page = doc[page_idx]
    areas = page.search_for(old_text)
    if not areas:
        return None

    rect = _pick_rect(areas)
    baseline = find_baseline(page, rect, old_text)
    expanded_rect = expand_fn(rect) if expand_fn else rect

    page.add_redact_annot(expanded_rect, fill=(1, 1, 1))

    return {
        "page": page_idx,
        "expanded_rect": expanded_rect,
        "orig_rect": rect,
        "baseline": baseline,
        "text": new_text,
        "bold": use_bold,
    }


def insert_pending(doc, pending, has_regular, has_bold):
    """After redactions are applied, write all pending texts at their baselines.

    Fonts are embedded once per target page. Page 0 is skipped because its
    fonts were already embedded by its dedicated paragraph rewrite.
    """
    target_pages = {item["page"] for item in pending}
    target_pages.discard(0)
    for page_idx in target_pages:
        insert_fonts(doc[page_idx], has_regular, has_bold)

    for item in pending:
        page = doc[item["page"]]
        page.insert_text(
            (item["orig_rect"].x0, item["baseline"]),
            item["text"],
            fontname=font_name(item["bold"], has_regular, has_bold),
            fontsize=FONT_SIZE,
            color=(0, 0, 0),
        )


def _insert_screenshot(page, image_bytes, rect):
    """Insert an image into ``rect``, letterboxed (contain fit), centered."""
    page.clean_contents()
    new_rect = fitz.Rect(rect)

    img_doc = fitz.open(fitz.Matrix(0, 0), image_bytes)
    img_page = img_doc[0]
    img_w = img_page.rect.width
    img_h = img_page.rect.height
    img_doc.close()

    scale_x = new_rect.width / img_w
    scale_y = new_rect.height / img_h
    scale = min(scale_x, scale_y)

    display_w = img_w * scale
    display_h = img_h * scale

    offset_x = new_rect.x0 + (new_rect.width - display_w) / 2
    offset_y = new_rect.y0 + (new_rect.height - display_h) / 2

    img_rect = fitz.Rect(offset_x, offset_y, offset_x + display_w, offset_y + display_h)

    page.insert_image(img_rect, stream=image_bytes)


def clear_screenshots(doc, page_indexes):
    """Blank out every existing screenshot image on the given pages.

    Old template screenshots are replaced by a 1x1 white JPEG, then every image
    bbox on the page gets a white redaction so no trace remains.
    """
    img_white = Image.new("RGB", (1, 1), (255, 255, 255))
    buf = io.BytesIO()
    img_white.save(buf, format="JPEG", quality=10)
    white_jpeg = buf.getvalue()

    for page_idx in page_indexes:
        page = doc[page_idx]
        original_xrefs = [img[0] for img in page.get_images()]
        if not original_xrefs:
            continue

        for xref in original_xrefs:
            doc.update_stream(xref, white_jpeg)
            doc.xref_set_key(xref, "Width", "1")
            doc.xref_set_key(xref, "Height", "1")
            doc.xref_set_key(xref, "Length", str(len(white_jpeg)))

        for inf in page.get_image_info():
            rect = fitz.Rect(inf["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)


def insert_screenshots(doc, layout, screenshots):
    """Place ``screenshots`` into the slots defined by ``layout``."""
    slot_index = 0
    for page_layout in layout:
        page = doc[page_layout["page"]]
        for slot in page_layout["slots"]:
            if slot_index < len(screenshots):
                _insert_screenshot(page, screenshots[slot_index], slot["rect"])
            slot_index += 1