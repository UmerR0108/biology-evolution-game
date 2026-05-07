import pygame

from evogame.ui.widgets import Button, Slider, Toggle


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button})


def _release_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": button})


def _motion_event(pos, buttons=(1, 0, 0)):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "buttons": buttons, "rel": (0, 0)})


def test_button_invokes_callback_on_click():
    calls = []
    btn = Button(pygame.Rect(0, 0, 100, 30), "Go", lambda: calls.append(True))
    btn.handle_event(_click_event((50, 15)))
    assert calls == [True]


def test_button_ignores_clicks_outside():
    calls = []
    btn = Button(pygame.Rect(0, 0, 100, 30), "Go", lambda: calls.append(True))
    btn.handle_event(_click_event((200, 200)))
    assert calls == []


def test_toggle_flips_state_on_click():
    t = Toggle(pygame.Rect(0, 0, 30, 30), "Predator", initial=False)
    t.handle_event(_click_event((15, 15)))
    assert t.state is True
    t.handle_event(_click_event((15, 15)))
    assert t.state is False


def test_slider_clamps_initial():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=1.0, max_value=5.0, initial=10.0)
    assert s.value == 5.0


def test_slider_drag_updates_value():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_click_event((50, 10)))      # grab knob in middle
    s.handle_event(_motion_event((90, 10)))     # drag near right edge
    assert s.value > 5.0


def test_slider_release_stops_drag():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_click_event((50, 10)))
    s.handle_event(_release_event((50, 10)))
    s.handle_event(_motion_event((90, 10), buttons=(0, 0, 0)))
    assert s.value == 5.0  # not dragged anymore


def test_slider_keeps_tracking_when_motion_leaves_rect():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_click_event((50, 10)))
    s.handle_event(_motion_event((500, 10)))  # way outside rect
    assert s.value == 10.0


def test_slider_motion_without_prior_click_is_noop():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_motion_event((90, 10)))
    assert s.value == 5.0
