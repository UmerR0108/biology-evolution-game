"""Post-process pygbag's generated browser loader safely.

The generated ``index.html`` contains embedded Python. Patching only part of an
indented line can create an ``IndentationError`` and leave the browser on a gray
loader. Keep this logic in Python so tests can validate the exact transformation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TEXT_PY_SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\btype=[\"']text/python[\"'])[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_SOURCE_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)await shell\.source\(main, callback=ui_callback\)$",
    re.MULTILINE,
)
_HIDE_INFOBOX = "platform.window.infobox.style.display = 'none'"


def embedded_python_blocks(html: str) -> list[str]:
    """Return the embedded pygbag Python blocks from generated HTML."""
    return [match.group(1).strip("\n") for match in _TEXT_PY_SCRIPT_RE.finditer(html)]


def hide_pygbag_infobox(html: str) -> str:
    """Hide pygbag's gray infobox before loading the app, preserving indentation."""
    if _HIDE_INFOBOX in html:
        return html

    def replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        source_line = match.group(0)
        return f"{indent}{_HIDE_INFOBOX}\n{source_line}"

    patched, count = _SOURCE_LINE_RE.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError("Could not find pygbag shell.source loader line in index.html")
    return patched


def patch_index(path: str | Path) -> None:
    """Patch and syntax-check a generated pygbag index.html file."""
    index_path = Path(path)
    html = index_path.read_text()
    patched = hide_pygbag_infobox(html)
    for block in embedded_python_blocks(patched):
        compile(block, str(index_path), "exec")
    index_path.write_text(patched)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]) if args else Path("build/web/index.html")
    patch_index(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
