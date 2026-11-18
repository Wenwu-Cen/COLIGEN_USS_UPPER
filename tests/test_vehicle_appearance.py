import math
import tkinter as tk

import pytest

from map_view import VIEW_WORLD
from modern_ui import WorkspaceCanvas
from test_vehicle_profiles import sample_profile
from vehicle_appearance import vehicle_body_bounds
from viewer_models import VehicleInfo


def legacy_vehicle():
    vehicle = VehicleInfo()
    vehicle.front_probes = {"FLS": (3500, 800), "FRS": (3500, -800)}
    vehicle.rear_probes = {"RLS": (-1000, 800), "RRS": (-1000, -800)}
    return vehicle


def test_body_uses_dimensions_with_sparse_or_no_sensors_and_recorded_origins():
    vehicle = legacy_vehicle()
    probes = vehicle.all_probes()
    assert vehicle_body_bounds(vehicle) == (-1000, 3922, -938, 938)
    vehicle.front_probes["FLS"] = (3400, 500)
    assert vehicle_body_bounds(vehicle) == (-1000, 3922, -938, 938)
    assert probes[0] == ("FLS", 3500, 800)
    empty = VehicleInfo()
    assert vehicle_body_bounds(empty) == (-2461, 2461, -938, 938)
    profile = sample_profile(origin_from_rear_mm=2500).to_dict()
    profile["custom_body"] = False
    from vehicle_profiles import VehicleProfile
    recorded = VehicleProfile.from_dict(profile).to_vehicle()
    assert recorded.body_bounds is None
    assert vehicle_body_bounds(recorded) == (-2500, 2500, -1000, 1000)


@pytest.fixture(scope="module")
def root():
    window = tk.Tk()
    window.geometry("1000x760+0+0")
    window.attributes("-alpha", 0)
    window.update()
    yield window
    window.destroy()


@pytest.fixture
def canvas(root):
    canvas = WorkspaceCanvas(root, legacy_vehicle())
    canvas.pack(fill="both", expand=True)
    root.update()
    yield canvas
    canvas.destroy()
    root.update_idletasks()


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("yaw", [0, math.pi/4, math.pi/2])
def test_artwork_keeps_dimensioned_bounds_and_rotates_every_detail(canvas, manual, yaw):
    if manual:
        canvas.vehicle = sample_profile(origin_from_rear_mm=2500).to_vehicle()
    before = canvas.vehicle.all_probes()
    bounds = vehicle_body_bounds(canvas.vehicle)
    canvas.set_obstacles([], [], vehicle_pose=(10000, -20000, yaw))
    canvas.set_view_mode(VIEW_WORLD)
    canvas._reset_view()
    body, = canvas.find_withtag("vehicle-body")
    coords = canvas.coords(body)
    local = [canvas.canvas_to_world(x, y) for x, y in zip(coords[::2], coords[1::2])]
    assert (min(x for x, _ in local), max(x for x, _ in local),
            min(y for _, y in local), max(y for _, y in local)) == pytest.approx(bounds)
    assert len([i for i in canvas.find_withtag("vehicle-wheel")
                if canvas.type(i) == "polygon"]) == 4
    assert len(canvas.find_withtag("vehicle-headlamp")) == 2
    assert len(canvas.find_withtag("vehicle-taillamp")) == 2
    for tag in ("vehicle-glass", "vehicle-roof", "vehicle-wheel",
                "vehicle-headlamp", "vehicle-taillamp"):
        assert canvas.find_withtag(tag)
        for item in canvas.find_withtag(tag):
            coords = canvas.coords(item)
            for x, y in zip(coords[::2], coords[1::2]):
                wx, wy = canvas.canvas_to_world(x, y)
                assert bounds[0]-1e-6 <= wx <= bounds[1]+1e-6
                assert bounds[2]-1e-6 <= wy <= bounds[3]+1e-6
    assert canvas.vehicle.all_probes() == before
    if manual:
        axles = canvas.find_withtag("vehicle-axle")
        assert len(axles) == 2
        assert all(canvas.itemcget(item, "state") == "hidden" for item in axles)
        canvas.show_vehicle_labels = True
        canvas._draw()
        axles = canvas.find_withtag("vehicle-axle")
        assert all(canvas.itemcget(item, "state") == "normal" for item in axles)
        actual = [canvas.canvas_to_world(*canvas.coords(item)[:2])[0] for item in axles]
        assert actual == pytest.approx((-1500, 1500))


def test_probe_status_uses_exact_mount_and_fault_takes_priority_over_pdc(canvas):
    canvas.set_obstacles([], [], pdc_ranges=[("FLS", 2, 150)],
                         probe_faults=(0,)*12, vehicle_pose=(0, 0, math.pi/3))
    shapes = {key: (coords, opts) for _, key, coords, opts in canvas._iter_indicator_shapes()}
    coords, options = shapes["probe", "FLS"]
    assert ((coords[0]+coords[2])/2, (coords[1]+coords[3])/2) == pytest.approx(
        canvas.world_to_canvas(*canvas.vehicle.front_probes["FLS"]))
    assert options["fill"] == canvas._pdc_color(2)
    canvas.set_obstacles([], [], pdc_ranges=[("FLS", 2, 150)], probe_faults=(0,)*11+(1,))
    shapes = {key: opts for _, key, _, opts in canvas._iter_indicator_shapes()}
    assert shapes["probe", "FLS"]["fill"] == "#FF3B5C"
    assert shapes["probe", "FRS"]["fill"] != "#FF3B5C"


def test_zoom_simplifies_artwork_and_live_updates_reuse_static_vehicle(canvas):
    canvas._fit_on_resize = False
    canvas.scale = .12
    canvas._draw()
    detailed = canvas.find_withtag("vehicle-layer")
    assert canvas.find_withtag("vehicle-roof")
    canvas.set_obstacles([], [], pdc_ranges=[("FLS", 1, 100)])
    assert canvas.find_withtag("vehicle-layer") == detailed
    canvas.scale = .02
    canvas._draw()
    assert canvas.find_withtag("vehicle-roof")
    assert len(canvas.find_withtag("vehicle-layer")) < len(detailed)
    canvas.scale = .005
    canvas._draw()
    assert canvas.find_withtag("vehicle-body")
    assert not canvas.find_withtag("vehicle-roof")
    assert not canvas.find_withtag("vehicle-wheel")
    canvas.scale = .12
    canvas._draw()
    assert len(canvas.find_withtag("vehicle-layer")) == len(detailed)


def test_fit_includes_actual_body_even_when_sensor_envelope_is_smaller(canvas):
    canvas._reset_view()
    back, front, right, left = vehicle_body_bounds(canvas.vehicle)
    for point in ((back, right), (back, left), (front, right), (front, left)):
        x, y = canvas.world_to_canvas(*point)
        assert 0 < x < canvas.winfo_width()
        assert 0 < y < canvas.winfo_height()
