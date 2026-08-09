"""Document type registry.

Add a new supported PDF by creating a ``DocumentType`` subclass in this
package and registering it here. The app iterates ``DOCUMENT_TYPES``.
"""

from .acceptance_note import AcceptanceNoteDocument
from .ep_sozlesme import EPSozlesmeDocument

DOCUMENT_TYPES = {d.ID: d() for d in (EPSozlesmeDocument, AcceptanceNoteDocument)}