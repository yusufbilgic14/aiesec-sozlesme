"""Acceptance Note (visa support letter) — template "Taslak_Acceptance_Note.pdf".

Single-page English letter. Uses the SAME filling formula as the EP contract:

- Every region containing variable values is fully redacted (white-out) and
  then re-inserted as a complete sentence/paragraph built from the form data
  via ``insert_htmlbox`` — exactly like EP page 1 ("insert_textbox") and EP
  section 5 ("insert_htmlbox" for native <b> bold, commits 7b9360c/47220df).
- Because sentences are rebuilt from the inputs, spacing around values is
  always correct and any input length wraps naturally. Plain character-level
  placeholder swaps are NOT used here: mid-sentence values (name, dates,
  country, LC) would collide with the surrounding static text and leave
  fixed template spaces behind.
- Static regions (intro paragraphs, "Dear Sir / Madam,", closing block) are
  left untouched in their original fonts.

The GUIDE copy of the template places numbered markers (1-10) next to every
replaceable value; that map:

    1  sender / letterhead address (top right)
    2  target country ("Germany"; incl. the Consulate address line)
    3  participant name ("Ayşenur İnce")
    4/5  program start / end dates
    6  host Local Committee ("AACHEN")
    7-10  date of birth / passport number / date of issue / date of expiry
"""
import os

import fitz

from fill_pdf import (
    FONT_BOLD,
    FONT_REGULAR,
    apply_redactions,
    clear_annotations,
    font_available,
    insert_fonts,
)
from .base import DocumentType, Field
from .embassies import COUNTRY_OPTIONS, mission_for, missions_for

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Taslak_Acceptance_Note.pdf",
)

# Calibri is metric-compatible with the free, OFL-licensed Carlito font.
# insert_htmlbox normally renders its built-in CharisSIL serif; passing an
# Archive + @font-face CSS makes it use Carlito-Regular/Bold at exact sizes,
# so line breaks and glyph metrics match the template's Calibri layout.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARLITO_ARCHIVE = fitz.Archive(ROOT)
HTML_CSS = (
    "@font-face{font-family:carlito;src:url(Carlito-Regular.ttf)}"
    "@font-face{font-family:carlito;font-weight:bold;src:url(Carlito-Bold.ttf)}"
    "@font-face{font-family:liberation;src:url(LiberationSans-Regular.ttf)}"
    "@font-face{font-family:liberation;font-weight:bold;src:url(LiberationSans-Bold.ttf)}"
)

# Every region whose OLD text must be blanked out, and into which the rebuilt
# content is inserted. Region tops are calibrated for Carlito: first-line
# baseline = rect.y0 + 10.75pt (10pt), + 8.65pt (8.5pt letterhead), and
# + 16pt for the details block (line-height 2.4 adds half extra leading).
REGIONS = [
    ("letterhead", fitz.Rect(300, 156.95, 573.9, 176)),  # top-right sender address (8.5pt, right-aligned, Liberation/Arial-metric)
    ("visa_officer", fitz.Rect(53, 171.95, 578.9, 196)),  # salutation line (10pt, right-aligned like template)
    ("title", fitz.Rect(40, 203.85, 555, 228)),  # "Acceptance Note for <name>" (centered)
    ("para3", fitz.Rect(53, 342.55, 557, 394)),  # visa request sentence
    ("para4", fitz.Rect(53, 380.75, 557, 433)),  # confirmation + program details
    ("details", fitz.Rect(53, 451.7, 557, 597)),  # "The following are his details:" block
    ("para5", fitz.Rect(53, 601.25, 557, 638)),  # bottom paragraph (contains name)
]

LEADING = "font-family:carlito;margin:0;padding:0;color:#000000"


def _esc(s):
    """Escape user data entering the htmlbox (commits 47220df pitfall)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_regions_html(data):
    name = _esc(data["name"])
    ulke = _esc(data["ulke"])
    lc = _esc(data["host_lc"])
    start = _esc(data["baslangic_tarihi"])
    end = _esc(data["bitis_tarihi"])
    adres = _esc(data["adres"])
    dogum = _esc(data["dogum_tarihi"])
    pasaport = _esc(data["pasaport_no"])
    duzenlenme = _esc(data["duzenlenme_tarihi"])
    gecerlilik = _esc(data["gecerlilik_tarihi"])
    sirket_adresi = _esc(data["sirket_adresi"])
    misyon = _esc(data["mission_title"])

    def p(body, size=10, align="left", line_height=1.35, family="carlito"):
        return (
            f'<p style="{LEADING};font-family:{family};font-size:{size}pt;'
            f'line-height:{line_height};text-align:{align}">{body}</p>'
        )

    return {
        "letterhead": p(
            f"<b>{sirket_adresi}</b>", size=8.5, align="right",
            line_height=1.2, family="liberation"
        ),
        "visa_officer": p(
            f"The Visa Officer, <b>{misyon}</b>",
            align="right",
        ),
        "title": p(f"Acceptance Note for <b>{name}</b>", align="center"),
        "para3": p(
            f"With this document, we hereby request for a visa for the period "
            f"<b>{start}- {end}</b> for Ms. <b>{name}</b>, She will be taking part "
            f"in a project in <b>{ulke}</b> in Local Committee <b>{lc}</b> for the "
            f"above said period."
        ),
        "para4": p(
            f"With this letter, AIESEC Istanbul Asia confirmed that <b>{name}</b>, who has "
            f"been selected by <b>{lc}</b>, <b>{ulke}</b> as a part of our Global Volunteer "
            f"Program. <b>{name}</b> is going to take a traineeship project in <b>{ulke}</b> "
            f"starting on <b>{start}</b> ending <b>{end}</b> for a maximum period of "
            f"2 months."
        ),
        "details": "".join([
            p(f"Name (as in passport): <b>{name}</b>", line_height=2.4),
            p(f"Address: {adres}", line_height=2.4),
            p(f"Date of Birth: <b>{dogum}</b>", line_height=2.4),
            p(f"Passport Number: <b>{pasaport}</b>", line_height=2.4),
            p(f"Date of Issue: <b>{duzenlenme}</b>", line_height=2.4),
            p(f"Date of Expiry: <b>{gecerlilik}</b>", line_height=2.4),
        ]),
        "para5": p(
            f"AIESEC is the world's largest youth-run organization present in 112 countries "
            f"and <b>{name}</b> has been selected for the volunteer position. Throughout the "
            f"project, the AIESEC association is undertaking to assure accommodation."
        ),
    }


class AcceptanceNoteDocument(DocumentType):
    ID = "acceptance_note"
    NAME = "Acceptance Note"
    DESCRIPTION = "Vize destek mektubu (Ingilizce, tek sayfa)"
    TEMPLATE_PATH = TEMPLATE_PATH
    TEMPLATE_MISSING_HINT = (
        "Acceptance Note şablonu bulunamadı. 'Taslak_Acceptance_Note.pdf' "
        "dosyasının proje kökünde olduğundan emin olun."
    )

    def fields(self):
        return [
            Field("name", "Ad Soyad (pasaporttaki haliyle) *", help="ör: Ayşenur İnce"),
            Field(
                "ulke",
                "Program Ülkesi (vize başvurusu yapılacak ülke) *",
                kind="select",
                options=COUNTRY_OPTIONS,
                help="Seçilen ülkenin Türkiye'deki büyükelçilik/başkonsolosluk adresi antete yazılır",
            ),
            Field(
                "sehir",
                "Başvuru yapılacak temsilcilik *",
                kind="select",
                depends_on="ulke",
                help="Ülkede birden fazla temsilcilik varsa şehir seçilir",
            ),
            Field("host_lc", "Host Local Committee *", help="ör: AACHEN"),
            Field("baslangic_tarihi", "Program Başlangıç Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("bitis_tarihi", "Program Bitiş Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("adres", "Adres *", help="Katılımcının ikamet adresi"),
            Field("dogum_tarihi", "Doğum Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("pasaport_no", "Pasaport Numarası *", help="ör: U35237737", half=True),
            Field("duzenlenme_tarihi", "Pasaport Düzenlenme Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("gecerlilik_tarihi", "Pasaport Geçerlilik Tarihi *", placeholder="DD.MM.YYYY", half=True),
        ]

    def field_options(self, key, parent_value=None):
        if key == "sehir":
            return [m["label"] for m in missions_for(parent_value or "")]
        return super().field_options(key, parent_value)

    def assemble_data(self, form):
        ulke = form["ulke"]
        misyon = mission_for(ulke, form["sehir"])
        baslangic = form["baslangic_tarihi"].strip()
        bitis = form["bitis_tarihi"].strip()
        return {
            "name": form["name"].strip(),
            "ulke": ulke,
            "host_lc": form["host_lc"].strip(),
            "baslangic_tarihi": baslangic,
            "bitis_tarihi": bitis,
            "adres": form["adres"].strip(),
            "dogum_tarihi": form["dogum_tarihi"].strip(),
            "pasaport_no": form["pasaport_no"].strip(),
            "duzenlenme_tarihi": form["duzenlenme_tarihi"].strip(),
            "gecerlilik_tarihi": form["gecerlilik_tarihi"].strip(),
            "sirket_adresi": misyon["address"],
            "mission_title": misyon["title"],
        }

    def output_filename(self, data):
        return f"{data['name'].replace(' ', '_')}_AN.pdf"

    def fill(self, data, screenshots=None):
        doc = fitz.open(TEMPLATE_PATH)
        page = doc[0]

        has_regular = font_available(FONT_REGULAR)
        has_bold = font_available(FONT_BOLD)

        clear_annotations(doc)

        # 1) White out every dynamic region (EP page-1/section-5 style)
        for _name, rect in REGIONS:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        apply_redactions(doc)

        # 2) Embed the bundled fonts, then rebuild each region from the data
        insert_fonts(page, has_regular, has_bold)

        html = _build_regions_html(data)
        for name, rect in REGIONS:
            page.insert_htmlbox(rect, html[name], css=HTML_CSS, archive=CARLITO_ARCHIVE)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes