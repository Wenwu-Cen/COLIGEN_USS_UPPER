from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import viewer_controller
from viewer_controller import ViewerController
from viewer_models import FrameData


class Playback(ViewerController):
    def __init__(self, timestamps, speed):
        self.frames = [FrameData(i) for i in range(len(timestamps))]
        for frame, stamp in zip(self.frames, timestamps):
            frame.timestamp_ms = stamp
            frame.timestamp_unit = "us"
        self.current_frame_idx = 0
        self.playing = False
        self.play_speed = speed
        self.play_after_id = None
        self.play_btn = SimpleNamespace(config=Mock())
        self.now_ns = 0
        self.draw_ns = 0
        self.visits = []
        self.timer = None

    def _jump_to_frame(self, index, *, render=True):
        self.current_frame_idx = index
        self.visits.append((index, render))
        if render:
            self.now_ns += self.draw_ns

    def after(self, delay, callback):
        assert self.timer is None
        self.timer = delay, callback
        return "timer"

    def after_cancel(self, timer_id):
        assert timer_id == "timer" and self.timer is not None
        self.timer = None

    def run_next_timer(self):
        delay, callback = self.timer
        self.timer = None
        self.now_ns += delay * 1_000_000
        callback()


@pytest.mark.parametrize("speed,first_delay,second_delay", [(1, 20, 36), (2, 10, 16)])
def test_playback_uses_frame_intervals_without_accumulating_draw_time(
        monkeypatch, speed, first_delay, second_delay):
    app = Playback([1000, 21000, 61000], speed)
    monkeypatch.setattr(viewer_controller.time, "monotonic_ns", lambda: app.now_ns)
    app.draw_ns = 4_000_000

    app._start_play()
    assert app.current_frame_idx == 0
    assert app.timer[0] == first_delay
    app.run_next_timer()
    assert app.current_frame_idx == 1
    assert app.timer[0] == second_delay
    app.run_next_timer()
    assert app.current_frame_idx == 2
    assert not app.playing and app.timer is None


def test_changing_speed_and_seeking_replaces_the_pending_timer(monkeypatch):
    app = Playback([0, 20000, 60000], 1)
    monkeypatch.setattr(viewer_controller.time, "monotonic_ns", lambda: app.now_ns)
    app._start_play()
    app._set_play_speed(2)
    assert app.timer[0] == 10
    app._on_slider_move(1)
    assert app.timer[0] == 20
    app._stop_play()
    assert app.current_frame_idx == 1 and app.timer is None


def test_late_timer_consumes_every_due_frame_and_renders_the_latest(monkeypatch):
    app = Playback([0, 20000, 40000, 60000, 80000], 1)
    monkeypatch.setattr(viewer_controller.time, "monotonic_ns", lambda: app.now_ns)
    app._start_play()
    app.now_ns = 45_000_000
    app.run_next_timer()
    assert app.visits == [(1, False), (2, False), (3, True)]
    assert app.timer[0] == 15
    app.run_next_timer()
    assert app.visits[-1] == (4, True)
    assert not app.playing


@pytest.mark.parametrize("before,after,expected", [
    ((1000, "us", 8000), (21000, "us", 38000), 30000),
    ((0, "ms", 0), (20, "ms", 0), 20000),
    ((1, "ms", 8000), (21, "ms", 0), 20000),
    ((1, "ms", 8000), (21, "ms", 8000), 20000),
    ((21, "us", 0), (10, "us", 0), 100000),
    ((0, "auto", 0), (21, "auto", 0), 100000),
    ((1_704_067_200_000, "auto", 0), (1_704_067_200_020, "auto", 0), 20000),
    ((1_704_067_200_000, "auto", 0), (21, "auto", 0), 100000),
])
def test_playback_interval_handles_timestamp_sources_and_legacy_frames(before, after, expected):
    frames = [SimpleNamespace(timestamp_ms=stamp, timestamp_unit=unit, sample_timestamp_us=sample)
              for stamp, unit, sample in (before, after)]
    assert ViewerController._replay_interval_us(*frames) == expected
