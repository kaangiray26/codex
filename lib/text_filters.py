import re
from pydantic import BaseModel
from typing import Any, Mapping, Optional

from pipecat.utils.text.base_text_filter import BaseTextFilter

class CitationFilter(BaseTextFilter):
    """Removes citations from text in TextFrames."""

    class InputParams(BaseModel):
        enable_text_filter: Optional[bool] = True

    def __init__(self, params: InputParams = InputParams(), **kwargs):
        super().__init__(**kwargs)
        self._settings = params
        self._interrupted = False

    def update_settings(self, settings: Mapping[str, Any]):
        for key, value in settings.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)

    def filter(self, text: str) -> str:
        # Remove citations in the format [1], [2], etc.
        filtered_text = re.sub(r"\[\d+\]", "", text)
        return filtered_text

    def handle_interruption(self):
        self._interrupted = True

    def reset_interruption(self):
        self._interrupted = False