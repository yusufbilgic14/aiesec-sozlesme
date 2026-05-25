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
    (1, "[01/08/2026]- [29/08/2026]", "tarih_araligi", True),
    (2, "(3770) EGP", "proje_ucreti", True),
    (2, "6930", "danismanlik_ucreti", True),
    (2, "(altıbindokuyüzotuz)", "danismanlik_ucreti_yazi", False),
    (3, "[6930]", "danismanlik_ucreti_braket", True),
    (6, "14/05/2026", "sozlesme_tarihi", True),
]

TEXT_TRANSFORMS = {
    "tarih_araligi": lambda v: v,
    "danismanlik_ucreti_braket": lambda v: f"[{v}]",
}

FONT_SIZE = 12
LINE_HEIGHT = FONT_SIZE * 1.3
Y_TOLERANCE = 5

SECTION5_START_MARKER = "Sözleşmede bahsi"
SECTION5_END_MARKER = "kabul eder."

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
    "tc_kimlik": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "adres": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "eposta": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "dogum_tarihi": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "ad": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "soyad": lambda r: fitz.Rect(r.x0, r.y0 - 2, r.x1 + 60, r.y1 + 6),
    "ulke": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "tarih_araligi": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "proje_ucreti": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "danismanlik_ucreti": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "danismanlik_ucreti_yazi": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "danismanlik_ucreti_braket": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "sozlesme_tarihi": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
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


def _fill_page1_paragraph(doc, data, has_regular, has_bold):
    """White out the entire intro paragraph on page 1."""
    page = doc[0]
    # Covers all 6 lines: y=133.9 to y=206.8
    paragraph_rect = fitz.Rect(43.2, 133, 557, 220)
    page.add_redact_annot(paragraph_rect, fill=(1, 1, 1))


def _fill_page1_text(doc, data, has_regular, has_bold):
    """Insert the reformatted paragraph on page 1 after redaction."""
    page = doc[0]
    if has_regular:
        page.insert_font(fontname="TNR", fontfile=FONT_REGULAR)
    if has_bold:
        page.insert_font(fontname="TNRB", fontfile=FONT_BOLD)

    tc = data.get("tc_kimlik", "")
    adres = data.get("adres", "")
    eposta = data.get("eposta", "")
    dogum = data.get("dogum_tarihi", "")
    ad = data.get("ad", "")
    soyad = data.get("soyad", "")

    paragraph = (
        "İKTİSADİ VE TİCARİ İLİMLER TALEBELERİ STAJ KOMİTESİ DERNEĞİ adına hareket eden "
        f"Derneğin İstanbul Asya Şubesi (Bundan böyle \"AIESEC Türkiye\" olarak anılacaktır.) ile, diğer tarafta, "
        f"{tc} TC kimlik numaralı, {adres} adresinde "
        f"mukim, {eposta} elektronik posta adresi olan, {dogum} doğum tarihli, "
        f"{ad} {soyad} (bundan böyle Değişim Katılımcısı olarak anılacaktır), karşılıklı mutabakat içerisinde aşağıda yer "
        "alan sözleşme maddeleri hususunda anlaşmışlardır."
    )

    fontname = "TNR" if has_regular else "helv"

    # Use textbox for automatic wrapping
    text_rect = fitz.Rect(43.2, 133, 557, 250)
    page.insert_textbox(
        text_rect,
        paragraph,
        fontname=fontname,
        fontsize=FONT_SIZE,
        color=(0, 0, 0),
        align=fitz.TEXT_ALIGN_LEFT,
    )


def _fill_page2_section5(doc, data, has_regular, has_bold):
    page = doc[1]

    ulke = data.get("ulke", "")
    tarih_araligi = data.get("tarih_araligi", "")

    if not ulke or not tarih_araligi:
        return False

    start_areas = page.search_for(SECTION5_START_MARKER)
    end_areas = page.search_for(SECTION5_END_MARKER)

    if not start_areas or not end_areas:
        return False

    start_rect = start_areas[0]
    end_rect = None
    for area in end_areas:
        if area.y0 > start_rect.y0:
            end_rect = area
            break
    if not end_rect:
        end_rect = end_areas[-1]

    x0 = start_rect.x0
    y0 = start_rect.y0 - 3
    x1 = page.rect.x1 - start_rect.x0
    y1 = end_rect.y1 + 8

    redact_rect = fitz.Rect(x0, y0, x1, y1)
    page.add_redact_annot(redact_rect, fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    if has_regular:
        page.insert_font(fontname="TNR", fontfile=FONT_REGULAR)
    if has_bold:
        page.insert_font(fontname="TNRB", fontfile=FONT_BOLD)

    fontname = "TNR" if has_regular else "helv"

    paragraph = (
        f"Sözleşmede bahsi geçen program {ulke} ülkesinde, {tarih_araligi} tarihleri arasında "
        f"gerçekleşecektir. Değişim Katılımcısı, programın gerçekleştirileceği tarih aralığının "
        f"AIESEC tarafından 20 güne kadar tek taraflı değiştirilebileceğini kabul eder."
    )

    text_rect = fitz.Rect(x0, y0, x1, y1 + 30)

    page.insert_textbox(
        text_rect,
        paragraph,
        fontname=fontname,
        fontsize=FONT_SIZE,
        color=(0, 0, 0),
        align=fitz.TEXT_ALIGN_LEFT,
    )

    return True


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

    # Handle page 1 specially
    _fill_page1_paragraph(doc, data, has_regular, has_bold)
    doc[0].apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    _fill_page1_text(doc, data, has_regular, has_bold)

    section5_handled = _fill_page2_section5(doc, data, has_regular, has_bold)

    pending = []

    for page_idx, old_text, key, use_bold in REPLACEMENTS:
        if page_idx == 0:
            continue  # page 1 handled above
        if page_idx == 1 and section5_handled:
            continue  # section 5 handled above
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

        # Get actual baseline from page text dict
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

        expanded_rect = EXPANDED_RECTS.get(key, lambda r: r)(rect)

        page.add_redact_annot(expanded_rect, fill=(1, 1, 1))

        pending.append((page_idx, expanded_rect, rect, baseline, new_text, use_bold, key))

    for page in doc:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    _clear_screenshots(doc)

    target_pages = set(item[0] for item in pending)
    if 0 in target_pages:
        target_pages.discard(0)
    for page_idx in target_pages:
        page = doc[page_idx]
        if has_regular:
            page.insert_font(fontname="TNR", fontfile=FONT_REGULAR)
        if has_bold:
            page.insert_font(fontname="TNRB", fontfile=FONT_BOLD)

    for page_idx, expanded_rect, orig_rect, baseline, new_text, use_bold, key in pending:
        page = doc[page_idx]
        fontname = "TNRB" if (use_bold and has_bold) else ("TNR" if has_regular else "helv")

        x = orig_rect.x0
        y = baseline

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