"""Acceptance Note ("Kabul Notu") — new document type.

NOTE: The template PDF has not been provided yet. Once it is available:

1. Drop the template into the project root (e.g. ``taslak_acceptance_note.pdf``).
2. Fill in ``TEMPLATE_PATH`` if the filename differs.
3. Define the form fields in ``fields()``.
4. Implement ``fill()`` following `ep_sozlesme.py`'s pattern:
   - scan the template with section 4 (marker-based redaction) and/or simple
     placeholder replacement (``redact_and_collect`` + ``insert_pending``)
   - ``TEXT_TRANSFORMS`` / ``EXPANDED_RECTS`` maps for value formatting and
     redaction expansion
   - plain-text fields at 12pt with ``engine.insert_text`` at the extracted
     baseline; paragraph rewrites via ``insert_textbox`` / ``insert_htmlbox``
   - handle dates with ``FIELD_DESCRIPTIONS`` / date inputs if the template
     has date inputs (see AGENTS.md)
5. No changes are needed in ``app.py`` — the document registry picks it up
   automatically and renders the dynamic form.
"""
import os

from .base import DocumentType

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "taslak_acceptance_note.pdf",
)


class AcceptanceNoteDocument(DocumentType):
    ID = "acceptance_note"
    NAME = "Acceptance Note"
    DESCRIPTION = "Kabul Notu (yeni) — şablon dosyası henüz sağlanmadı"
    TEMPLATE_PATH = TEMPLATE_PATH
    TEMPLATE_MISSING_HINT = (
        "Acceptance Note şablonu henüz eklenmedi. Şablon PDF'i sağlanınca bu "
        "belge türü otomatik olarak aktif hale gelecek — form ve doldurma "
        "mantığı aynı altyapıyı kullanacak."
    )

    def fields(self):
        return []  # TODO: şablon sağlandığında alanlar tanımlanacak

    def fill(self, data, screenshots=None):
        raise NotImplementedError("Acceptance Note henüz uygulanmadı (şablon bekleniyor).")