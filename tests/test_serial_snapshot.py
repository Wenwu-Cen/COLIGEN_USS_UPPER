from pathlib import Path
from types import SimpleNamespace

import pytest

from SerialOnlinePort import build_serial_snapshot, SerialConfig, load_serial_config, save_serial_config
from serial_protocol import UpperStreamDecoder
from VehUpperDemo import App, LogParser, VehicleInfo


FIXTURE = Path(__file__).parent / "fixtures" / "upper_serial_variables_v1.bin"


def c_frame():
    decoder = UpperStreamDecoder()
    frames = decoder.feed(FIXTURE.read_bytes())
    assert decoder.decode_errors == 0
    assert len(frames) == 1
    return frames[0]


def test_c_variable_export_converts_every_array_and_field():
    source = c_frame()
    assert len(FIXTURE.read_bytes()) == 1634
    assert len(source.points) == 80
    assert len(source.lines) == 20
    assert source.points[79] == (1079, 179, -279, 1, 3, 4)
    snapshot = build_serial_snapshot(source)
    lines, points, gear, speed, raw, ranges, slots, _, _ = snapshot.frame
    assert snapshot.timestamp_us == 1234567890123
    assert (gear, speed) == (2, 12.5)
    assert snapshot.data["odo"] == (1.5, -2.5, .25)
    assert (points[79].index, points[79].obj_id, points[79].x, points[79].y) == (
        79, 1079, 179, -279)
    assert (lines[19].index, lines[19].cnum, lines[19].dist) == (19, 29, 500)
    assert raw[11].de == 332 and raw[11].de_width == 61
    assert snapshot.data["vehicle_demo"]["probes"]["FLS"] == (3900, 850)
    assert len(ranges) == 12
    assert len(slots) == 1
    assert slots[0].pts[0] == (100, 200)
    assert slots[0].pts[-1] == (1100, -1200)
    assert (slots[0].a_type, slots[0].f_type) == (1, 2)


def test_axis_conversion_applies_to_geometry_pose_and_vehicle_together():
    snapshot = build_serial_snapshot(c_frame(), lateral_sign=-1)
    assert snapshot.frame[1][79].y == 279
    assert snapshot.frame[0][19].sy == 200
    assert snapshot.frame[6][0].pts[-1] == (1100, 1200)
    assert snapshot.data["odo"] == (1.5, 2.5, -.25)
    assert snapshot.data["vehicle_demo"]["probes"]["FLS"] == (3900, -850)


def test_serial_recording_replays_identifiers_pose_and_raw_widths():
    snapshot = build_serial_snapshot(c_frame())
    lines, points, gear, speed, raw, _, slots, front, rear = snapshot.frame
    recorder = SimpleNamespace(record_frames=[], _record_raw_csv=[], vehicle=VehicleInfo())
    App._record_frame(
        recorder, 1, snapshot.timestamp_us, gear, speed, 123, front, 7, rear, 8,
        lines, points, raw, slots, snap=snapshot.data, timestamp_unit="us",
        sample_timestamp_us=1700000000123456, vehicle_pose=(1500, -2500, .25))
    body = recorder.record_frames[0].split("\n", 1)[1]
    frame = LogParser("")._parse_frame(1, body)
    assert (frame.points[79].index, frame.points[79].obj_id) == (79, 1079)
    assert (frame.segments[19].index, frame.segments[19].cnum) == (19, 29)
    assert (frame.raw_probes[11].de, frame.raw_probes[11].de_width) == (332, 61)
    assert frame.vehicle_pose == (1500, -2500, .25)
    assert frame.timestamp_unit == "us"
    assert (frame.freq_front_val, frame.freq_rear_val) == (7, 8)
    assert frame.probe_pos["FLS"] == (3900, 850)


def test_serial_settings_save_and_load_in_user_config():
    config = SerialConfig(port="COM12", baudrate=460800, parity="E", timeout=2, lateral_sign=-1)
    save_serial_config(config)
    assert load_serial_config() == config


@pytest.mark.parametrize("changes", [
    {"port": ""}, {"baudrate": 0}, {"bytesize": 7}, {"parity": "invalid"},
    {"stopbits": 3}, {"timeout": float("nan")}, {"lateral_sign": 0},
])
def test_invalid_serial_settings_are_rejected(changes):
    config = SerialConfig(port="COM3")
    for key, value in changes.items():
        setattr(config, key, value)
    with pytest.raises(ValueError):
        config.validate()
