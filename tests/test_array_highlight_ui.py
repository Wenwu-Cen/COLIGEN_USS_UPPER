import math
import time
from types import SimpleNamespace
from unittest.mock import Mock

import customtkinter as ctk
import pytest

import DataSheet
import VehUpperDemo_CAN as ui
from VehUpperDemo import FrameData, ObstaclePoint, ObstacleSegment, VehicleInfo
from map_view import VIEW_WORLD
from modern_ui import ModernDataPanel


def _settle(app, duration=0.15):
    end = time.monotonic() + duration
    while time.monotonic() < end:
        app.update()
        time.sleep(0.005)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(ui, 'PdcAlarm', Mock)
    monkeypatch.setattr(ModernDataPanel, '_load_state', lambda self: {})
    monkeypatch.setattr(ctk.ScalingTracker, 'window_widgets_dict', {})
    monkeypatch.setattr(ctk.ScalingTracker, 'window_dpi_scaling_dict', {})
    monkeypatch.setattr(ctk.ScalingTracker, 'update_loop_running', False)
    monkeypatch.setattr(DataSheet, 'POINT_CLOUD_NUM', 120)
    monkeypatch.setattr(DataSheet, 'POINT_LINE_NUM', 20)
    frames = [FrameData(index) for index in range(3)]
    frames[0].points = [ObstaclePoint(2, 2000, 600, 0, 0, 0, 0),
                        ObstaclePoint(89, 3200, -1200, 0, 0, 1, 0)]
    frames[0].segments = [ObstacleSegment(7, 1500, 900, 2500, -300, 0)]
    frames[1].points = [ObstaclePoint(89, 3500, -1300, 0, 0, 1, 0)]
    frames[2].points = [ObstaclePoint(89, 0, 0, 0, 0, 0, 0)]
    for frame in frames:
        frame.timestamp_ms = 1794800000123456 + frame.frame_idx
        frame.temp = 27
    vehicle = VehicleInfo()
    vehicle.front_probes = {'FLS': (3300, 800), 'FRS': (3300, -800)}
    vehicle.rear_probes = {'RLS': (-1000, 800), 'RRS': (-1000, -800)}
    app = ui.App(vehicle, SimpleNamespace(frames=frames))
    app.geometry('1280x800+0+0')
    app.toggle_more_btn.invoke()
    _settle(app)
    try:
        yield app
    finally:
        app.destroy()


def _select(app, page, row):
    panel = app.more_panel
    panel._tab_buttons[page].invoke()
    parent = panel.tree.parent(row)
    if parent:
        panel.tree.item(parent, open=True)
    panel.tree.selection_set(row)
    panel.tree.focus(row)
    panel.tree.see(row)
    app.update()


def _halo(canvas):
    return next(item for item in canvas.find_withtag('data-highlight')
                if canvas.type(item) == 'oval')


def test_clicking_sparse_point_array_highlights_the_protocol_index_without_repainting_grid(app):
    panel, canvas = app.more_panel, app.canvas
    panel._tab_buttons['obj'].invoke()
    row = 'sf_Upper_PointOutSignal[89]'
    assert panel.tree.item(row, 'text').startswith('[89]')
    panel.tree.see(row)
    app.update()
    grid = canvas.find_withtag('static')
    original = dict(zip(canvas._live_signature, canvas._live_ids))
    point = original['oval', ('pt', 89)]
    color = canvas.itemcget(point, 'fill')
    x, y, _, height = panel.tree.bbox(row)
    # Exercise actual Treeview mouse bindings, including <<TreeviewSelect>>.
    panel.tree.event_generate('<ButtonPress-1>', x=x+55, y=y+height//2)
    panel.tree.event_generate('<ButtonRelease-1>', x=x+55, y=y+height//2)
    app.update()
    assert canvas.highlight_target == ('point', 89)
    px, py = canvas.world_to_canvas(3200, -1200)
    assert canvas.coords(_halo(canvas)) == pytest.approx((px-10, py-10, px+10, py+10))
    assert canvas.find_withtag('static') == grid
    current = dict(zip(canvas._live_signature, canvas._live_ids))
    assert all(current[key] == item for key, item in original.items())
    assert canvas.itemcget(point, 'fill') == color
    assert any(canvas.itemcget(item, 'text') == 'POINT[89]'
               for item in canvas.find_withtag('data-highlight') if canvas.type(item) == 'text')


def test_line_field_selection_highlights_its_line_and_both_endpoints(app):
    canvas = app.canvas
    _select(app, 'line', 'sf_Upper_LineOutSignal[7].wEndy')
    assert canvas.highlight_target == ('line', 7)
    items = canvas.find_withtag('data-highlight')
    lines = [item for item in items if canvas.type(item) == 'line']
    assert sorted(float(canvas.itemcget(item, 'width')) for item in lines) == [4, 8]
    expected = (*canvas.world_to_canvas(1500, 900), *canvas.world_to_canvas(2500, -300))
    for line in lines:
        assert canvas.coords(line) == pytest.approx(expected)
    assert sum(canvas.type(item) == 'oval' for item in items) == 2
    _select(app, 'obj', 'sf_Upper_PointOutSignal[2].x')
    assert canvas.highlight_target == ('point', 2)
    assert len(canvas.find_withtag('data-highlight')) == 2


def test_selection_tracks_current_frame_and_never_marks_missing_or_zero_data_at_origin(app):
    canvas, panel = app.canvas, app.more_panel
    row = 'sf_Upper_PointOutSignal[89].x'
    _select(app, 'obj', row)
    halo = _halo(canvas)
    app._jump_to_frame(1)
    app.update()
    assert panel.tree.selection() == (row,)
    assert panel.tree.item('sf_Upper_PointOutSignal[89]', 'open')
    assert _halo(canvas) == halo
    px, py = canvas.world_to_canvas(3500, -1300)
    assert canvas.coords(halo) == pytest.approx((px-10, py-10, px+10, py+10))
    app._jump_to_frame(2)
    app.update()
    assert not canvas.find_withtag('data-highlight')
    assert canvas.highlight_target == ('point', 89)
    app._jump_to_frame(0)
    app.update()
    assert canvas.find_withtag('data-highlight')
    _select(app, 'obj', 'sf_Upper_PointOutSignal[88]')
    assert not canvas.find_withtag('data-highlight')


def test_tab_changes_and_layer_visibility_clear_only_the_visible_highlight(app):
    canvas = app.canvas
    _select(app, 'obj', 'sf_Upper_PointOutSignal[2]')
    canvas._toggle_obj_mode()
    assert not canvas.find_withtag('data-highlight')
    canvas._toggle_obj_mode()
    assert canvas.find_withtag('data-highlight')
    app.more_panel._tab_buttons['raw'].invoke()
    app.update()
    assert canvas.highlight_target is None
    assert not canvas.find_withtag('data-highlight')


def test_highlight_obeys_world_pose_pan_and_zoom(app):
    canvas = app.canvas
    _select(app, 'obj', 'sf_Upper_PointOutSignal[89]')
    canvas.set_view_mode(VIEW_WORLD)
    points = [ObstaclePoint(89, 3200, -1200, 0, 0, 1, 0)]
    canvas.set_obstacles([], points, vehicle_pose=(1000, 2000, math.pi/2))
    # Expected absolute position: (2200, 5200).
    px, py = canvas.view_to_canvas(2200, 5200)
    assert canvas.coords(_halo(canvas)) == pytest.approx((px-10, py-10, px+10, py+10))
    canvas.offset_x += 50
    canvas.offset_y -= 25
    canvas.scale *= 1.2
    canvas._draw()
    px, py = canvas.view_to_canvas(2200, 5200)
    assert canvas.coords(_halo(canvas)) == pytest.approx((px-10, py-10, px+10, py+10))


def test_frame_status_is_in_header_and_wraps_inside_minimum_and_wide_windows(app):
    assert app.info_label.master is app._header_info
    assert app._header_info.master is app._toolbar
    original = app.info_label.cget('text')
    assert all(text in original for text in ('TS:', 'Gear:', 'Speed:', 'Temp:'))
    for width in (880, 1280, 1920):
        app.geometry(f'{width}x800+0+0')
        _settle(app)
        label, header = app.info_label, app._header_info
        assert label.winfo_rooty() < app.canvas.winfo_rooty()
        assert label.winfo_rooty()+label.winfo_height() <= (
            app._toolbar.winfo_rooty()+app._toolbar.winfo_height())
        assert label.winfo_rootx() >= header.winfo_rootx()
        assert label.winfo_rootx()+label.winfo_width() <= (
            header.winfo_rootx()+header.winfo_width()+2)
        assert label._label.winfo_reqwidth() <= label.winfo_width()+2
        assert label._label.winfo_reqheight() <= label.winfo_height()+2
        assert label.cget('text') == original
        assert label.cget('wraplength') <= header.winfo_width()
