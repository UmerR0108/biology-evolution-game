"""Post-process pygbag's generated browser loader safely.

The generated ``index.html`` contains embedded Python. Patching only part of an
indented line can create an ``IndentationError`` and leave the browser on a gray
loader. Keep this logic in Python so tests can validate the exact transformation.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_TEXT_PY_SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\btype=[\"']text/python[\"'])[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_PYGAME_WEB_BOOT_SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\bid=[\"']site[\"'])[^>]*>#<!--\s*\n?(.*?)\n?#\s*--></script>",
    re.IGNORECASE | re.DOTALL,
)
_SOURCE_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)await shell\.source\(main, callback=ui_callback\)$",
    re.MULTILINE,
)
_UME_GATE_RE = re.compile(
    r"^(?P<indent>[ \t]*)# test/wait user media interaction\n"
    r"(?P=indent)if not platform\.window\.MM\.UME:\n"
    r"(?P<body>(?:(?P=indent)[ \t]+.*\n|\n)+?)"
    r"(?P=indent)# start async top level machinery",
    re.MULTILINE,
)
_ERROR_OVERLAY_MARKER = "traceback.format_exc()"
_UME_PATCH_MARKER = "Hermes patch: skip pygbag UME gate"
_ARCHIVE_CACHE_BUSTER_MARKER = "Hermes patch: cache-bust pygbag archive"
_ARCHIVE_FETCH_RE = re.compile(r'platform\.fopen\("(?P<name>[^"]+\.(?:apk|tar\.gz))", "rb"\)')


def embedded_python_blocks(html: str) -> list[str]:
    """Return embedded Python blocks from generated pygbag HTML."""
    blocks = [match.group(1).strip("\n") for match in _TEXT_PY_SCRIPT_RE.finditer(html)]
    blocks.extend(match.group(1).strip("\n") for match in _PYGAME_WEB_BOOT_SCRIPT_RE.finditer(html))
    return blocks


def disable_pygbag_ume_gate(html: str) -> str:
    """Skip pygbag's generated media-engagement gate for mobile-safe startup."""
    if _UME_PATCH_MARKER in html:
        return html

    def replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return "\n".join(
            [
                f"{indent}# test/wait user media interaction",
                f"{indent}# {_UME_PATCH_MARKER}: Railway/mobile Safari can stay gray here even with --ume_block 0.",
                f"{indent}platform.window.MM.UME = True",
                f"{indent}# start async top level machinery",
            ]
        )

    patched, _count = _UME_GATE_RE.subn(replacement, html, count=1)
    return patched


def cache_bust_archive_fetches(html: str) -> str:
    """Append a deployment version to pygbag archive fetches to avoid stale gray-screen bundles."""
    if _ARCHIVE_CACHE_BUSTER_MARKER in html:
        return html

    version = os.environ.get("GITHUB_SHA", "local")[:12]

    def replacement(match: re.Match[str]) -> str:
        name = match.group("name")
        return f'platform.fopen("{name}?v={version}", "rb")'

    patched, count = _ARCHIVE_FETCH_RE.subn(replacement, html)
    if count < 1:
        raise RuntimeError("Could not find pygbag archive fetches in index.html")
    return f"<!-- {_ARCHIVE_CACHE_BUSTER_MARKER}: v={version} -->\n" + patched


def hide_pygbag_infobox(html: str) -> str:
    """Wrap pygbag app loading so browser startup errors are visible and syntax-safe."""
    if _ERROR_OVERLAY_MARKER in html:
        return cache_bust_archive_fetches(disable_pygbag_ume_gate(html))

    def replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        inner = f"{indent}    "
        source_line = match.group(0).lstrip()
        return "\n".join(
            [
                f'{indent}platform.window.infobox.style.display = "none"',
                f"{indent}platform.window.config.gui_divider = 1",
                f"{indent}platform.window.window_resize()",
                f"{indent}try:",
                f"{inner}{source_line}",
                f"{indent}except Exception:",
                f"{inner}import traceback",
                f'{inner}platform.window.infobox.style.display = "block"',
                f'{inner}platform.window.infobox.style.whiteSpace = "pre-wrap"',
                f"{inner}platform.window.infobox.innerText = traceback.format_exc()",
                f"{inner}raise",
            ]
        )

    patched, count = _SOURCE_LINE_RE.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError("Could not find pygbag shell.source loader line in index.html")
    return cache_bust_archive_fetches(disable_pygbag_ume_gate(patched))


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
