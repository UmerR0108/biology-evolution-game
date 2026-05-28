import re
from pathlib import Path

from patch_pygbag_loader import (
    cache_bust_archive_fetches,
    disable_pygbag_ume_gate,
    embedded_python_blocks,
    hide_pygbag_infobox,
)


ROOT = Path(__file__).resolve().parents[1]


def test_railway_dockerfile_hides_pygbag_infobox_before_game_loop_finishes():
    dockerfile = (ROOT / "Dockerfile").read_text()
    patcher = (ROOT / "patch_pygbag_loader.py").read_text()

    assert "pygbag --build --ume_block 0" in dockerfile
    assert "patch_pygbag_loader.py build/web/index.html" in dockerfile
    assert "traceback.format_exc()" in patcher
    assert "shell\\.source" in patcher


def test_railway_uses_dockerfile_builder_instead_of_railpack():
    railway_json = (ROOT / "railway.json").read_text()

    assert '"builder": "DOCKERFILE"' in railway_json
    assert "RAILPACK" not in railway_json


def test_railway_server_disables_browser_cache_for_stale_gray_screens():
    serve_py = (ROOT / "serve.py").read_text()
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "Cache-Control" in serve_py
    assert "no-store" in serve_py
    assert "serve.py" in dockerfile


def test_pygbag_loader_patch_hides_gray_infobox_before_long_lived_game_loop():
    html = """
<html><body>
<script type="text/python">
async def main():
            await shell.source(main, callback=ui_callback)
            async with platform.fopen("biology-evolution-game.apk", "rb") as archive:
                pass
</script>
</body></html>
"""

    patched = hide_pygbag_infobox(html)
    assert "traceback.format_exc()" in patched
    assert re.search(r"^            platform\.window\.infobox\.style\.display = \"none\"$", patched, re.MULTILINE)
    assert re.search(r"^            platform\.window\.window_resize\(\)$", patched, re.MULTILINE)
    assert re.search(r"^            try:$", patched, re.MULTILINE)
    assert re.search(r"^                await shell\.source\(main, callback=ui_callback\)$", patched, re.MULTILINE)
    assert re.search(r"^                platform\.window\.infobox\.innerText = traceback\.format_exc\(\)$", patched, re.MULTILINE)
    assert "Hermes patch: cache-bust pygbag archive" in patched
    for block in embedded_python_blocks(patched):
        compile(block, "patched-index.html", "exec")


def test_embedded_python_blocks_extracts_pygame_web_boot_script():
    html = '''<html><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module id="site" async defer>#<!--
async def custom_site():
    await shell.source(main, callback=ui_callback)
asyncio.run(custom_site())
# --></script><head></head></html>'''

    blocks = embedded_python_blocks(html)

    assert len(blocks) == 1
    assert "async def custom_site" in blocks[0]
    compile(blocks[0], "generated-index.html", "exec")


def test_pygbag_loader_patch_cache_busts_archive_fetches_for_stale_github_pages_assets(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abcdef1234567890")
    html = """
<html><body>
<script type="text/python">
async def load_archives():
    async with platform.fopen("biology-evolution-game.apk", "rb") as archive:
        pass
    async with platform.fopen("biology-evolution-game.tar.gz", "rb") as archive:
        pass
</script>
</body></html>
"""

    patched = cache_bust_archive_fetches(html)

    assert 'platform.fopen("biology-evolution-game.apk?v=abcdef123456", "rb")' in patched
    assert 'platform.fopen("biology-evolution-game.tar.gz?v=abcdef123456", "rb")' in patched
    assert "Hermes patch: cache-bust pygbag archive" in patched
    for block in embedded_python_blocks(patched):
        compile(block, "patched-index.html", "exec")


def test_pygbag_loader_patch_skips_mobile_ume_gate_even_when_template_ignores_flag():
    html = """
<html><body>
<script type="text/python">
async def custom_site():
    main = appdir / "assets" / "main.py"

    # test/wait user media interaction
    if not platform.window.MM.UME:

        msg  = "Ready to start ! Please click/touch page"
        platform.window.infobox.innerText = msg
        while not platform.window.MM.UME:
            await asyncio.sleep(.1)
    # start async top level machinery if not started and add a console in any case if requested.
    await TopLevel_async_handler.start_toplevel(platform.shell, console=window.python.config.debug)
</script>
</body></html>
"""

    patched = disable_pygbag_ume_gate(html)

    assert "Hermes patch: skip pygbag UME gate" in patched
    assert "platform.window.MM.UME = True" in patched
    assert "while not platform.window.MM.UME" not in patched
    assert "Ready to start" not in patched
    for block in embedded_python_blocks(patched):
        compile(block, "patched-index.html", "exec")


def test_browser_entrypoint_uses_pygbag_asyncio_run_after_loader_hides_gray_overlay():
    main_py = (ROOT / "main.py").read_text()

    assert 'sys.platform == "emscripten"' in main_py
    assert "asyncio.run(browser_main())" in main_py
    assert "asyncio.create_task(browser_main())" not in main_py
    assert "asyncio.run(main())" in main_py
    assert "traceback.format_exc()" in main_py
    assert "infobox.innerText = message" in main_py
    assert "loader patch hides the gray infobox before awaiting" in main_py


def test_dockerfile_uses_loader_patch_script_not_brittle_inline_replacement():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "patch_pygbag_loader.py" in dockerfile
    assert "s.replace(needle" not in dockerfile
