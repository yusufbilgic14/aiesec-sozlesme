"""Acceptance Note (visa support letter) — template "Taslak_Acceptance_Note.pdf".

Single-page English letter. The GUIDE copy of the template places numbered
markers (1-10) next to every replaceable value; that map:

    1  sender / letterhead address (top right, Istanbul Asia)
    2  target country ("Germany" — appears 4 times, incl. the Consulate
       address line)
    3  participant name ("Ayşenur İnce" — appears 6 times, incl. the title
       "Acceptance Note for ...")
    4/5  program start / end dates
    6  host Local Committee ("AACHEN" — appears twice)
    7-10  date of birth / passport number / date of issue / date of expiry

Implementation notes:

- Values are bold Calibri 10pt; the participant address line is regular 10pt;
  the letterhead address is Arial-BoldMT 8.5pt. We render replacements with the
  bundled Times New Roman (regular / bold) at the matching size, on the exact
  extracted baseline.
- Repeated placeholders (name, country, LC) are handled with
  ``redact_all_instances`` — each occurrence gets its own redaction, because
  "single lowest rect" would replace only one of them.
- The dates exist twice: combined span "17.07.2026- 28.08.2026 " (visa period
  line) and standalone spans on the "starting on ... ending ..." line. The
  combined span is replaced as one piece; the standalone ones are disambiguated
  with a y-zone filter.
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
    insert_pending,
    redact_all_instances,
)
from .base import DocumentType, Field

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Taslak_Acceptance_Note.pdf",
)

# Standalone program dates sit at y~411; the combined visa-period span (also
# containing both dates) sits at y~346 and must NOT be matched here.
ZONE_STANDALONE_DATES = fitz.Rect(0, 390, 595, 440)


def _expand_tight(r):
    """Minimal expansion for short inline values (dates, LC, passport...)."""
    return fitz.Rect(r.x0 - 0.5, r.y0 - 1, r.x1 + 1.5, r.y1 + 1.5)


def _expand_name(r):
    """Name sits inline with surrounding punctuation (commas); keep it tight."""
    return fitz.Rect(r.x0 - 0.5, r.y0 - 1, r.x1 + 3, r.y1 + 1.5)


def _expand_address(r):
    """Participant address line: room for longer addresses to the right."""
    return fitz.Rect(r.x0 - 0.5, r.y0 - 1, r.x1 + 160, r.y1 + 1.5)


def _expand_letterhead(r):
    """Top-right letterhead address: room for longer addresses to the right."""
    return fitz.Rect(r.x0 - 0.5, r.y0 - 1, r.x1 + 60, r.y1 + 1.5)


# (placeholder text in template, data key, use_bold, expand_fn, zone, size)
REPLACEMENTS = [
    ("Ayşenur İnce", "name", True, _expand_name, None, 10.0),
    ("Germany", "ulke", True, _expand_tight, None, 10.0),
    ("AACHEN", "host_lc", True, _expand_tight, None, 10.0),
    ("17.07.2026- 28.08.2026 ", "tarih_araligi", True, _expand_tight, None, 10.0),
    ("17.07.2026", "baslangic_tarihi", True, _expand_tight, ZONE_STANDALONE_DATES, 10.0),
    ("28.08.2026", "bitis_tarihi", True, _expand_tight, ZONE_STANDALONE_DATES, 10.0),
    ("30.07.1998", "dogum_tarihi", True, _expand_tight, None, 10.0),
    ("U35237737", "pasaport_no", True, _expand_tight, None, 10.0),
    ("18.11.2022", "duzenlenme_tarihi", True, _expand_tight, None, 10.0),
    ("18.11.2032", "gecerlilik_tarihi", True, _expand_tight, None, 10.0),
    ("Bostancı mah. İpekçi sok. Pırlanta Apt. No:1-3 Daire:11 Kadıköy/İstanbul",
     "adres", False, _expand_address, None, 10.0),
    ("Gümüşsuyu, İnönü Cd. No:10, 34437 Beyoğlu/İstanbul",
     "sirket_adresi", True, _expand_letterhead, None, 8.5),
]


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
            Field("ulke", "Program Ülkesi *", help="Şablondaki 'Germany' yazan tüm yerler değişir"),
            Field("host_lc", "Host Local Committee *", help="ör: AACHEN"),
            Field("baslangic_tarihi", "Program Başlangıç Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("bitis_tarihi", "Program Bitiş Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("adres", "Adres *", help="Katılımcının ikamet adresi"),
            Field("dogum_tarihi", "Doğum Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("pasaport_no", "Pasaport Numarası *", help="ör: U35237737", half=True),
            Field("duzenlenme_tarihi", "Pasaport Düzenlenme Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("gecerlilik_tarihi", "Pasaport Geçerlilik Tarihi *", placeholder="DD.MM.YYYY", half=True),
            Field("sirket_adresi", "Şube Adresi (üst sağ) *", help="Mektup antetindeki adres"),
        ]

    def assemble_data(self, form):
        baslangic = form["baslangic_tarihi"].strip()
        bitis = form["bitis_tarihi"].strip()
        return {
            "name": form["name"].strip(),
            "ulke": form["ulke"].strip(),
            "host_lc": form["host_lc"].strip(),
            "baslangic_tarihi": baslangic,
            "bitis_tarihi": bitis,
            "tarih_araligi": f"{baslangic}- {bitis} ",
            "adres": form["adres"].strip(),
            "dogum_tarihi": form["dogum_tarihi"].strip(),
            "pasaport_no": form["pasaport_no"].strip(),
            "duzenlenme_tarihi": form["duzenlenme_tarihi"].strip(),
            "gecerlilik_tarihi": form["gecerlilik_tarihi"].strip(),
            "sirket_adresi": form["sirket_adresi"].strip(),
        }

    def output_filename(self, data):
        return f"{data['name'].replace(' ', '_')}_acceptance_note.pdf"

    def fill(self, data, screenshots=None):
        doc = fitz.open(TEMPLATE_PATH)

        has_regular = font_available(FONT_REGULAR)
        has_bold = font_available(FONT_BOLD)

        clear_annotations(doc)

        pending = []
        for old_text, key, use_bold, expand_fn, zone, size in REPLACEMENTS:
            new_text = data.get(key, "")
            if not new_text:
                continue
            items = redact_all_instances(
                doc, 0, old_text, new_text, use_bold, expand_fn, zone, size
            )
            pending.extend(items)

        apply_redactions(doc)

        # Page 0 is skipped by insert_pending's font embedding; this single-page
        # template needs its fonts embedded explicitly.
        insert_fonts(doc[0], has_regular, has_bold)

        insert_pending(doc, pending, has_regular, has_bold)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes