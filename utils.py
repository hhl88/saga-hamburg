from __future__ import annotations


def is_empty(text):
    if text is None:
        return True
    if isinstance(text, str):
        return not (text and not text.isspace())
    return False

