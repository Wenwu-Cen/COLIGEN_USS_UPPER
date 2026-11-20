from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import app as ui
from map_view import VIEW_WORLD, world_overview_bounds
from modern_ui import ModernDataPanel
from viewer_models import ObstaclePoint, ObstacleSegment, VehicleInfo


def test_overview_uses_a_hundred_meter_square_even_when_route_is_longer():
    assert world_overview_bounds((9000, 4000), (0, 40_000, -5000, 5000)) == (
        -30_000, 70_000, -50_000, 50_000)
    assert world_overview_bounds((9000, 4000), (0, 105_000, -5000, 5000)) == (
        -41_000, 59_000, -46_000, 54_000)


def test_world_overview_keeps_history_after_fifteen_meter_input_window_rolls(monkeypatch):
    monkeypatch.setattr(ui, "PdcAlarm", Mock)
    monkeypatch.setattr(ModernDataPanel, "_load_state", lambda self: {})
    app = ui.App(VehicleInfo(), SimpleNamespace(frames=[]))
    app.geometry("1200x830")
    app.attributes("-alpha", 0)
    try:
        app.update()
        app.map_view_combo._dropdown_callback(VIEW_WORLD)
        canvas = app.canvas
        canvas.prepare_online_view()
        point = ObstaclePoint(0, 1200, 2200, 0, 0, 1, 0)
        segment = ObstacleSegment(0, 1200, 2200, 7200, 2200, 1)
        canvas.set_obstacles([segment], [point], vehicle_pose=(0, 0, 0), timestamp_us=100_000)
        bounds = canvas._world_fit_bounds
        assert bounds[1]-bounds[0] == bounds[3]-bounds[2] == 100_000
        border, = canvas.find_withtag("world-overview")
        left, top, right, bottom = canvas.coords(border)
        assert 0 < left < right < canvas.winfo_width()
        assert 0 < top < bottom < canvas.winfo_height()
        assert (right-left)/canvas.scale == pytest.approx(100_000)
        assert (bottom-top)/canvas.scale == pytest.approx(100_000)
        expected_point = canvas.map_to_canvas(1200, 2200)
        for m in range(1, 41):
            canvas.set_obstacles([], [], vehicle_pose=((m % 15)*1000, 0, 0),
                                 timestamp_us=(m+1)*100_000)
        assert canvas.driving_trail.pose == pytest.approx((40_000, 0, 0))
        assert canvas._world_fit_bounds == bounds and canvas.find_withtag("world-overview") == (border,)
        shapes = {key[0]: coords for _, key, coords, _ in canvas._iter_live_shapes()
                  if key[0].startswith("history-")}
        x1, y1, x2, y2 = shapes["history-point"]
        assert ((x1+x2)/2, (y1+y2)/2) == pytest.approx(expected_point)
        assert shapes["history-line"][:2] == pytest.approx(expected_point)
        app.parking_overview_btn.invoke()
        assert not canvas.find_withtag("world-overview")
        app.world_overview_btn.invoke()
        assert canvas.find_withtag("world-overview")
        assert canvas._world_fit_bounds != bounds
    finally:
        app.destroy()
