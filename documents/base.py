"""Base abstractions for document types in the ASYA generator.

Each supported PDF (EP Sözleşmesi, Acceptance Note, ...) is a subclass of
``DocumentType`` registered in ``documents/__init__.py``. The Streamlit app
only talks to this interface, so adding a new template never touches UI code.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Field:
    """One form field; rendered by the Streamlit app."""

    key: str
    label: str
    kind: str = "text"  # "text" | "number"
    required: bool = True
    placeholder: str = ""
    help: str = ""
    max_chars: int = 0
    half: bool = False  # renders paired with the next half field in a 2-col row


class DocumentType:
    """Interface every document implementation must provide."""

    ID = ""
    NAME = ""
    DESCRIPTION = ""
    TEMPLATE_PATH = ""
    TEMPLATE_MISSING_HINT = ""
    SCREENSHOTS_HELP = ""

    # -- Form -----------------------------------------------------------------

    def fields(self) -> List[Field]:
        raise NotImplementedError

    def required_keys(self) -> List[str]:
        return [f.key for f in self.fields() if f.required]

    def assemble_data(self, form: Dict[str, Any]) -> Dict[str, Any]:
        """Map raw form values to the keys expected by ``fill``."""
        return {key: form.get(key) for key in self.required_keys()}

    # -- Screenshots ------------------------------------------------------------

    def supports_screenshots(self) -> bool:
        return False

    def screenshot_layout(self) -> Optional[List[dict]]:
        """List of {"page": int, "slots": [{"rect": fitz.Rect}, ...]}."""
        return None

    def screenshot_slot_count(self) -> int:
        layout = self.screenshot_layout() or []
        return sum(len(entry["slots"]) for entry in layout)

    # -- Output ----------------------------------------------------------------

    def output_filename(self, data: Dict[str, Any]) -> str:
        return f"{self.ID}.pdf"

    # -- Filling ---------------------------------------------------------------

    def template_available(self) -> bool:
        return bool(self.TEMPLATE_PATH) and os.path.exists(self.TEMPLATE_PATH)

    def fill(self, data: Dict[str, Any], screenshots: Optional[List] = None) -> bytes:
        raise NotImplementedError

    def run(self, form: Dict[str, Any], screenshots: Optional[List] = None) -> bytes:
        data = self.assemble_data(form)
        return self.fill(data, screenshots)