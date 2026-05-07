import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _headless_pygame():
    """Force pygame's SDL backend into dummy mode so tests don't need a display."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    yield


@pytest.fixture
def pygame_surface():
    """Provide a 200x200 pygame Surface for UI rendering tests."""
    import pygame

    pygame.init()
    surface = pygame.Surface((200, 200))
    yield surface
    pygame.quit()
