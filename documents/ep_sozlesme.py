"""EP Değişim Katılımcısı Sözleşmesi ("taslak_sözleşme.pdf", 10 pages).

Filling strategy (see AGENTS.md for the full write-up):

1. Page 1 (index 0): the whole intro paragraph is redacted and re-inserted via
   ``insert_textbox`` (automatic text wrapping, 12pt Times New Roman).
2. Page 2 (index 1): Section 5 is redacted from "Sözleşmede bahsi" until
   "kabul eder." and re-inserted via ``insert_htmlbox`` to get native ``<b>``
   bold for the date range (commits 7b9360c / 47220df).
3. Pages 3-4 (indexes 2-3): every sentence containing a fee value ("6930",
   "(altıbindokuyüzotuz)", "(3770) EGP", "[6930]") is rebuilt wholesale via
   ``insert_htmlbox`` with the repo TimesNewRoman fonts (``@font-face``), so
   any input length re-wraps cleanly (slot-based swaps overflowed: long
   amounts clashed with the following words, short ones left gaps - fixed
   with the Acceptance Note's region approach). See FEE_REGIONS.
4. Remaining placeholders: simple redaction + baseline-aligned insertion
   (``redact_and_collect`` / ``insert_pending``); only "Mısır", the date
   range (section-5 fallbacks) and "14/05/2026" remain slots.
5. Pages 8-10 (indexes 7-9): template screenshots are blanked and replaced by
   user-uploaded screenshots, letterboxed into fixed slots.
"""

import os

import fitz

import fill_pdf as engine
from fill_pdf import (
    FONT_BOLD,
    FONT_REGULAR,
    FONT_SIZE,
    apply_redactions,
    clear_annotations,
    clear_screenshots,
    font_available,
    insert_fonts,
    insert_pending,
    insert_screenshots,
    redact_and_collect,
)
from .base import DocumentType, Field
from .embassies import EP_COUNTRY_OPTIONS, EP_CURRENCY_BY_COUNTRY

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "taslak_sözleşme.pdf",
)

# (page_index, placeholder text in template, data key, use_bold)
REPLACEMENTS = [
    (1, "Mısır", "ulke", False),
    (1, "[01/08/2026]- [29/08/2026]", "tarih_araligi", True),
    (6, "14/05/2026", "sozlesme_tarihi", True),
]

# Minimal expansion around the found placeholder rect (x, y half-padding)
EXPANDED_RECTS = {
    "ulke": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "tarih_araligi": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
    "sozlesme_tarihi": lambda r: fitz.Rect(r.x0, r.y0 - 1, r.x1 + 1, r.y1 + 2),
}

# The variable-width fee values ("6930", "(altıbindokuyüzotuz)", "(3770) EGP",
# "[6930]") cannot be swapped slot-by-slot: any input longer than the template
# sample overflows into the following words or leaves gaps (the old app relied
# on EXPANDED_RECTS sized for the sample values). Like the Acceptance Note,
# each sentence containing a fee value is rebuilt wholesale via insert_htmlbox
# (native <b> where the template is bold), so any input length re-wraps cleanly.
#
# Template metrics: 12pt TimesNewRoman, line pitch 14.48 (line-height 1.2067).
# Calibrated (see AGENTS.md): text starts rect.x0 + 1pt; first-line baseline =
# rect.y0 + 11.93 (TNR ascent 0.891 x 12 + (lh-1)/2 x 12). Regions keep a small
# bottom margin below the last template line; taller content is auto-scaled by
# insert_htmlbox (scale_low) instead of colliding with the static text below.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TNR_ARCHIVE = fitz.Archive(ROOT)
TNR_HTML_CSS = (
    "@font-face{font-family:ep_times;src:url(TimesNewRoman.ttf)}"
    "@font-face{font-family:ep_times;font-weight:bold;src:url(TimesNewRomanBold.ttf)}"
)
FONT_SIZE_HTML = f"{FONT_SIZE}pt"
FEE_LINE_HEIGHT = "1.2067"


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fee_html(text):
    return (
        f'<p style="font-family:ep_times;font-size:{FONT_SIZE_HTML};'
        f"line-height:{FEE_LINE_HEIGHT};margin:0;padding:0;color:#000000\">"
        f"{text}</p>"
    )


FEE_REGIONS = [
    {  # 7.4 - danışmanlık ücreti paragraph tail (page 3 of 10, index 2)
        "page": 2,
        "redact": fitz.Rect(43.0, 487.8, 557.6, 559.8),
        "text": fitz.Rect(42.2, 486.73, 558.3, 560.2),
        "build": lambda d: (
            "4. Değişim Katılımcısı 7.3. maddede belirtilen hizmetler için AIESEC Türkiye’ye "
            f"vergiler dahil {_esc(d['danismanlik_ucreti'])} ({_esc(d['danismanlik_ucreti_yazi'])}) "
            "Türk Lirası’nı işbu sözleşmenin imzalanmasından itibaren 3 gün içerisinde ödemeyi "
            "kabul, beyan ve taahhüt eder. Kar amacı gütmeyen bir sivil toplum kuruluşu olan "
            "AIESEC Türkiye Değişim Katılımcısı’ndan tahsil edilen gelirleri dernek "
            "faaliyetlerinin fonlanması amacıyla kullanmakta olup ticari kar amacı gütmemektedir."
        ),
    },
    {  # 7.6 - proje ücreti sentence (page 3 of 10, index 2)
        "page": 2,
        "redact": fitz.Rect(43.0, 648.3, 557.6, 676.8),
        "text": fitz.Rect(42.2, 647.41, 558.3, 677.5),
        "build": lambda d: (
            "Değişim Katılımcısı Misafir Eden Şube’ye "
            f"<b>{_esc(d['proje_ucreti'])}</b> "
            "ödeme yapacağını bu hususun program eşleşme sayfasında yazanla aynı olduğunu "
            "kabul, beyan ve taahhüt eder."
        ),
    },
    {  # 7.7 - tazminat paragraph tail with [danışmanlık ücreti] (page 4 of 10, index 3)
        "page": 3,
        "redact": fitz.Rect(43.0, 385.5, 557.6, 443.0),
        "text": fitz.Rect(42.2, 384.56, 558.3, 443.65),
        "build": lambda d: (
            "katılım gerçekleştirmezse AIESEC Türkiye’nin Misafir Eden Şube’ye ödemek zorunda "
            "kalacağı tazminat miktarı olan "
            f"[{_esc(d['danismanlik_ucreti_braket'])}] "
            "TL tutarı 3 gün içerisinde AIESEC’e ödemeyi kabul, beyan ve taahhüt eder. Değişim "
            "Katılımcısı işbu tazmin bedelinin kendisinin Program katılımı nedeniyle yapılacak "
            "hazırlık ücretleri, konaklama ve sair bedelleri tazmin amaçlı olduğunu anladığını "
            "kabul ve beyan eder."
        ),
    },
]


def _rewrite_fee_regions(doc, data):
    for region in FEE_REGIONS:
        doc[region["page"]].add_redact_annot(region["redact"], fill=(1, 1, 1))
    for region in FEE_REGIONS:
        doc[region["page"]].apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    for region in FEE_REGIONS:
        doc[region["page"]].insert_htmlbox(
            region["text"], _fee_html(region["build"](data)),
            css=TNR_HTML_CSS, archive=TNR_ARCHIVE,
        )

SECTION5_START_MARKER = "Sözleşmede bahsi"
SECTION5_END_MARKER = "kabul eder."

# Pages 8-10 hold template screenshots (2 per page)
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


def _fill_page1_paragraph(doc):
    """White out the entire intro paragraph on page 1 (covers 6 lines)."""
    page = doc[0]
    paragraph_rect = fitz.Rect(43.2, 133, 557, 220)
    page.add_redact_annot(paragraph_rect, fill=(1, 1, 1))


def _fill_page1_text(doc, data, has_regular, has_bold):
    """Insert the reformatted paragraph on page 1 after redaction."""
    page = doc[0]
    insert_fonts(page, has_regular, has_bold)

    tc = data.get("tc_kimlik", "")
    adres = data.get("adres", "")
    eposta = data.get("eposta", "")
    dogum = data.get("dogum_tarihi", "")
    ad = data.get("ad", "")
    soyad = data.get("soyad", "")

    paragraph = (
        "İKTİSADİ VE TİCARİ İLİMLER TALEBELERİ STAJ KOMİTESİ DERNEĞİ adına hareket eden "
        f'Derneğin İstanbul Asya Şubesi (Bundan böyle "AIESEC Türkiye" olarak anılacaktır.) ile, diğer tarafta, '
        f"{tc} TC kimlik numaralı, {adres} adresinde "
        f"mukim, {eposta} elektronik posta adresi olan, {dogum} doğum tarihli, "
        f"{ad} {soyad} (bundan böyle Değişim Katılımcısı olarak anılacaktır), karşılıklı mutabakat içerisinde aşağıda yer "
        "alan sözleşme maddeleri hususunda anlaşmışlardır."
    )

    fontname = "TNR" if has_regular else "helv"

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
    """Rewrite section 5 on page 2 with native bold via insert_htmlbox."""
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

    insert_fonts(page, has_regular, has_bold)

    text_rect = fitz.Rect(x0, y0, x1, y1 + 30)

    ulke_esc = ulke.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    tarih_esc = tarih_araligi.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = (
        f'<p style="font-family:serif;font-size:{FONT_SIZE}pt;line-height:1.35;'
        f'margin:0;padding:0;color:#000000">'
        f"Sözleşmede bahsi geçen program {ulke_esc} ülkesinde, "
        f"<b>{tarih_esc}</b> tarihleri arasında "
        f"gerçekleşecektir. Değişim Katılımcısı, programın gerçekleştirileceği tarih aralığının "
        f"AIESEC tarafından 20 güne kadar tek taraflı değiştirilebileceğini kabul eder."
        f"</p>"
    )

    page.insert_htmlbox(text_rect, html)

    return True


class EPSozlesmeDocument(DocumentType):
    ID = "ep_sozlesme"
    NAME = "EP Sözleşmesi"
    DESCRIPTION = "Değişim Katılımcısı Sözleşmesi (mevcut düzen)"
    TEMPLATE_PATH = TEMPLATE_PATH
    SCREENSHOTS_HELP = (
        "Sözleşmenin son 3 sayfasındaki ekran görüntülerini yükleyin. En fazla 6 görsel "
        "(her sayfada 2 adet). Yüklemezseniz sayfalar boş olacaktır."
    )

    def fields(self):
        return [
            Field("tc_kimlik", "TC Kimlik No *", max_chars=11),
            Field("ad", "Ad (First Name) *"),
            Field("soyad", "Soyad (Last Name) *"),
            Field("adres", "Adres *"),
            Field("eposta", "E-posta *"),
            Field("dogum_tarihi", "Doğum Tarihi *", placeholder="DD/MM/YYYY"),
            Field(
                "ulke",
                "Program Ülkesi *",
                kind="select",
                options=EP_COUNTRY_OPTIONS,
                help="Para birimi alanı seçilen ülkeye göre otomatik dolar (elle değiştirilebilir)",
            ),
            Field("baslangic_tarihi", "Başlangıç Tarihi *", placeholder="DD/MM/YYYY", half=True),
            Field("bitis_tarihi", "Bitiş Tarihi *", placeholder="DD/MM/YYYY", half=True),
            Field("proje_ucreti_tutar", "Karşı Şubenin Proje Ücreti (Tutar) *", kind="number", half=True),
            Field("proje_ucreti_para", "Karşı Şubenin Proje Ücreti (Para Birimi) *", help="ör: EGP, USD, EUR", half=True, default_from="ulke"),
            Field("danismanlik_ucreti", "Danışmanlık Ücreti *", kind="number", half=True),
            Field("danismanlik_ucreti_yazi", "Danışmanlık Ücreti (Yazıyla) *", help="ör: altıbindokuyüzotuz", half=True),
            Field("sozlesme_tarihi", "Sözleşme Tarihi *", placeholder="DD/MM/YYYY"),
        ]

    def field_default(self, key, parent_value=None):
        if key == "proje_ucreti_para":
            return EP_CURRENCY_BY_COUNTRY.get(parent_value or "")
        return super().field_default(key, parent_value)

    def assemble_data(self, form):
        return {
            "tc_kimlik": form["tc_kimlik"].strip(),
            "ad": form["ad"].strip(),
            "soyad": form["soyad"].strip(),
            "adres": form["adres"].strip(),
            "eposta": form["eposta"].strip(),
            "dogum_tarihi": form["dogum_tarihi"].strip(),
            "ulke": form["ulke"].strip(),
            "baslangic_tarihi": form["baslangic_tarihi"].strip(),
            "bitis_tarihi": form["bitis_tarihi"].strip(),
            "tarih_araligi": f"[{form['baslangic_tarihi'].strip()}]- [{form['bitis_tarihi'].strip()}]",
            "proje_ucreti": f"({form['proje_ucreti_tutar']}) {form['proje_ucreti_para'].strip()}",
            "danismanlik_ucreti": str(form["danismanlik_ucreti"]),
            "danismanlik_ucreti_yazi": form["danismanlik_ucreti_yazi"].strip(),
            "danismanlik_ucreti_braket": str(form["danismanlik_ucreti"]),
            "sozlesme_tarihi": form["sozlesme_tarihi"].strip(),
        }

    def supports_screenshots(self):
        return True

    def screenshot_layout(self):
        return SCREENSHOT_LAYOUT

    def output_filename(self, data):
        return f"{data['ad']}_{data['soyad']}_sözleşme.pdf"

    def fill(self, data, screenshots=None):
        doc = fitz.open(TEMPLATE_PATH)

        has_regular = font_available(FONT_REGULAR)
        has_bold = font_available(FONT_BOLD)

        clear_annotations(doc)

        # Page 1 (index 0): full paragraph rewrite
        _fill_page1_paragraph(doc)
        doc[0].apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        _fill_page1_text(doc, data, has_regular, has_bold)

        # Page 2 (index 1): section 5 paragraph rewrite
        section5_handled = _fill_page2_section5(doc, data, has_regular, has_bold)

        # Pages 3-4 (indexes 2-3): fee-value sentences rebuilt wholesale
        # (variable-width values would overflow their slots otherwise)
        _rewrite_fee_regions(doc, data)

        # All other placeholders
        pending = []
        for page_idx, old_text, key, use_bold in REPLACEMENTS:
            if page_idx == 0:
                continue  # page 1 handled above
            if page_idx == 1 and section5_handled:
                continue  # section 5 handled above

            new_text = data.get(key, "")
            if not new_text:
                continue

            expand_fn = EXPANDED_RECTS.get(key)
            item = redact_and_collect(doc, page_idx, old_text, new_text, use_bold, expand_fn)
            if item:
                pending.append(item)

        apply_redactions(doc)

        # Blank out the template screenshots on pages 8-10
        clear_screenshots(doc, SCREENSHOT_PAGES)

        insert_pending(doc, pending, has_regular, has_bold)

        if screenshots:
            insert_screenshots(doc, SCREENSHOT_LAYOUT, screenshots)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes