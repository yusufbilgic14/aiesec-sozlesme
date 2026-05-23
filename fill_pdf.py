import fitz
import os

TEMPLATE_PATH = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__))), "taslak_sözleşme.pdf")

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


FONT_REGULAR = _find_font("TimesNewRoman.ttf") or _find_font("Times New Roman.ttf") or _find_font("LiberationSerif-Regular.ttf") or _find_font("times.ttf")
FONT_BOLD = _find_font("TimesNewRomanBold.ttf") or _find_font("Times New Roman Bold.ttf") or _find_font("LiberationSerif-Bold.ttf") or _find_font("timesbd.ttf")

REPLACEMENTS = [
    (0, "39931582910", "tc_kimlik", False),
    (0, "Mehmet Akif mah. Mimar Sinan Cad. Alınteri sk. No19", "adres", False),
    (0, "ycharputlu@gmail.com", "eposta", False),
    (0, "19.08.2004", "dogum_tarihi", False),
    (0, "Yusuf Can", "ad", False),
    (0, "Harputlu", "soyad", False),
    (1, "Mısır", "ulke", False),
    (1, "[01/08/2026]", "baslangic_tarihi", True),
    (1, "[29/08/2026]", "bitis_tarihi", True),
    (2, "(3770) EGP", "odeme_bilgisi", True),
    (6, "14/05/2026", "sozlesme_tarihi", True),
]

TEXT_TRANSFORMS = {
    "baslangic_tarihi": lambda v: f"[{v}]",
    "bitis_tarihi": lambda v: f"[{v}]",
    "odeme_bilgisi": lambda v: v,
}

FONT_SIZE = 12
LINE_HEIGHT = FONT_SIZE * 1.3
Y_TOLERANCE = 5

SCREENSHOT_PAGES = [7, 8, 9]

SCREENSHOT_LAYOUT = [
    {"page": 7, "slots": [
        {"rect": fitz.Rect(36, 50, 551, 344)},
        {"rect": fitz.Rect(36, 353, 551, 633)},
    ]},
    {"page": 8, "slots": [
        {"rect": fitz.Rect(38, 50, 549, 316)},
        {"rect": fitz.Rect(38, 321, 549, 599)},
    ]},
    {"page": 9, "slots": [
        {"rect": fitz.Rect(46, 50, 557, 332)},
        {"rect": fitz.Rect(46, 332, 557, 605)},
    ]},
]

EXPANDED_RECTS = {
    "tc_kimlik": lambda r: fitz.Rect(r.x0, r.y0, 111.9, r.y1 + LINE_HEIGHT),
    "adres": lambda r: fitz.Rect(r.x0, r.y0, 506.1, r.y1 + LINE_HEIGHT),
    "eposta": lambda r: fitz.Rect(r.x0, r.y0, 204.6, r.y1 + LINE_HEIGHT),
    "dogum_tarihi": lambda r: fitz.Rect(r.x0, r.y0, 415.2, r.y1 + LINE_HEIGHT),
    "ad": lambda r: fitz.Rect(r.x0, r.y0, 557.0, r.y1 + LINE_HEIGHT),
    "soyad": lambda r: fitz.Rect(r.x0, r.y0, 83.2, r.y1 + LINE_HEIGHT),
    "ulke": lambda r: fitz.Rect(r.x0, r.y0, 261.3, r.y1 + LINE_HEIGHT),
    "baslangic_tarihi": lambda r: fitz.Rect(r.x0, r.y0, 393.9, r.y1 + LINE_HEIGHT),
    "bitis_tarihi": lambda r: fitz.Rect(r.x0, r.y0, 465.1, r.y1 + LINE_HEIGHT),
    "odeme_bilgisi": lambda r: fitz.Rect(r.x0, r.y0, 318.5, r.y1 + LINE_HEIGHT),
    "sozlesme_tarihi": lambda r: fitz.Rect(r.x0, r.y0, 324.8, r.y1 + LINE_HEIGHT),
}


def _pick_rect(areas):
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


def _insert_screenshot(page, image_bytes, rect):
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


def _clear_screenshots(doc):
    from PIL import Image
    import io

    img_white = Image.new("RGB", (1, 1), (255, 255, 255))
    buf = io.BytesIO()
    img_white.save(buf, format="JPEG", quality=10)
    white_jpeg = buf.getvalue()

    for page_idx in SCREENSHOT_PAGES:
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


def fill_contract(data: dict, screenshots: list = None) -> bytes:
    doc = fitz.open(TEMPLATE_PATH)

    has_regular = FONT_REGULAR is not None and os.path.exists(FONT_REGULAR)
    has_bold = FONT_BOLD is not None and os.path.exists(FONT_BOLD)

    for page in doc:
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot

    pending = []

    for page_idx, old_text, key, use_bold in REPLACEMENTS:
        new_text = data.get(key, "")
        if not new_text:
            continue

        transform = TEXT_TRANSFORMS.get(key)
        if transform:
            new_text = transform(new_text)

        page = doc[page_idx]
        areas = page.search_for(old_text)
        if not areas:
            continue

        rect = _pick_rect(areas)

        for area in areas:
            page.add_redact_annot(area, fill=(1, 1, 1))

        pending.append((page_idx, rect, new_text, use_bold, key))

    for page in doc:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    _clear_screenshots(doc)

    target_pages = set(item[0] for item in pending)
    for page_idx in target_pages:
        page = doc[page_idx]
        if has_regular:
            page.insert_font(fontname="TNR", fontfile=FONT_REGULAR)
        if has_bold:
            page.insert_font(fontname="TNRB", fontfile=FONT_BOLD)

    for page_idx, rect, new_text, use_bold, key in pending:
        page = doc[page_idx]
        fontname = "TNRB" if (use_bold and has_bold) else ("TNR" if has_regular else "helv")

        x = rect.x0
        y = rect.y0 + FONT_SIZE * 0.78

        page.insert_text(
            (x, y),
            new_text,
            fontname=fontname,
            fontsize=FONT_SIZE,
            color=(0, 0, 0),
        )

    if screenshots:
        slot_index = 0
        for page_layout in SCREENSHOT_LAYOUT:
            page = doc[page_layout["page"]]
            for slot in page_layout["slots"]:
                if slot_index < len(screenshots):
                    img_bytes = screenshots[slot_index]
                    _insert_screenshot(page, img_bytes, slot["rect"])
                slot_index += 1

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes