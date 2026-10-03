"""Helpers that make untrusted text safe to embed in prompts and filenames."""

import re

# ChatML control tokens (and common look-alikes) must never come from document text.
_CHATML = re.compile(r"<\|\s*(?:im_start|im_end|endoftext|system|user|assistant)\s*\|>", re.IGNORECASE)
_WIN_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

MAX_CONTEXT_CHARS = 12000  # Hard cap on document text placed in a single prompt


def sanitize_prompt_text(text: str, limit: int = MAX_CONTEXT_CHARS) -> str:
    """Strip prompt-control tokens and cap length."""
    if not text:
        return ""
    cleaned = _CHATML.sub("", str(text))
    return cleaned[:limit]


def safe_filename(name: str, fallback: str = "page", max_len: int = 120) -> str:
    """Return a Windows-safe file name stem (no path separators, no reserved names)."""
    name = _WIN_ILLEGAL.sub("_", str(name or "")).strip(" .")
    parts = name.rsplit(".", 1)
    if len(parts) == 2:
        stem, ext = parts
        ext = "." + ext
    else:
        stem, ext = name, ""
        
    if stem.upper() in _WIN_RESERVED:
        stem = f"_{stem}"
        
    allowed_len = max(0, max_len - len(ext))
    stem = stem[:allowed_len]
    return (stem + ext).rstrip(" .") or fallback
