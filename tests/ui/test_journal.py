import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.journal import Journal


def test_journal_starts_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    assert journal.open is False


def test_journal_open_close_toggle(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.toggle()
    assert journal.open is True
    journal.toggle()
    assert journal.open is False


def test_journal_predator_toggle_affects_sim(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    # Mouse-click on the predator toggle's rect.
    rect = journal.predator_toggle.rect
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": rect.center},
    )
    assert sim.pressure.predator_on is False
    journal.handle_event(event)
    assert sim.pressure.predator_on is True


def test_journal_draw_when_closed_no_op(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)  # no error


def test_journal_draw_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)
