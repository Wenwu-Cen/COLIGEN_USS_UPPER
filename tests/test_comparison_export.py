import csv
import json
import struct

import can
import pytest

from comparison_export import export_comparison_csv
from recording_session import RawEvent, RecordingSession, export_can
from replay_capture_protocol import LEGACY_IDS
from serial_protocol import SENSOR_NAMES


def test_d4m3_exports_datagram_can_frames_and_both_output_timestamps(tmp_path):
    session = RecordingSession(tmp_path, {"settings": {"project": "D4M3", "udp_protocol": "can68"}})
    payloads = [bytes([i]) * 64 for i in range(len(LEGACY_IDS))]
    datagram = b"".join(struct.pack(">I", identifier) + data
                        for identifier, data in zip(LEGACY_IDS, payloads))
    session.raw(RawEvent("udp", "192.168.98.233", 10_000_000, b"USSD" + bytes(64)))
    session.raw(RawEvent("udp", "192.168.98.233", 20_000_000, datagram))
    session.raw(RawEvent("udp", "192.168.98.233", 40_000_000, datagram))
    session.put("input", {"boot": 77, "cycle": 8, "tick_us": 120_000})
    pdc = dict(sts=1, front=1, rear=0, dis=[75] * 12, range=[2] * 12, fault=[0] * 12)
    real = dict(timestamp_us=120_082, points=[{"x": 10, "y": -2, "height": 1}],
                lines=[], data={"pdc": pdc})
    replay = dict(real, timestamp_us=8_500, lines=[{"sx": 0, "sy": 0, "ex": 10, "ey": 50}])
    key = (77, 8, 1)
    session.put("baseline", {"key": (77, 9, 1), "scene": dict(real, timestamp_us=140_000)})
    session.put("baseline", {"key": key, "scene": real})
    session.put("replay", {"key": key, "scene": replay})
    session.put("pair", {"key": key, "baseline": real, "replay": replay})
    session.put("replay", {"key": (77, 10, 1), "scene": dict(replay, timestamp_us=48_500)})
    session.close()

    asc = tmp_path / "dependencies.asc"
    assert export_can(session.path, asc) == 40
    with can.LogReader(str(asc)) as reader:
        frames = list(reader)
    assert [(frame.arbitration_id, bytes(frame.data)) for frame in frames] == (
        list(zip(LEGACY_IDS, payloads)) * 2
    )
    assert all(frame.is_fd for frame in frames)
    assert frames[20].timestamp - frames[0].timestamp == pytest.approx(0.02)

    output = tmp_path / "timeline.csv"
    assert export_comparison_csv(session.path, output) == 3
    with output.open(encoding="utf-8-sig", newline="") as stream:
        pair, real_only, replay_only = csv.DictReader(stream)
    assert pair["status"] == "matched"
    assert [pair[field] for field in ("input_timestamp_us", "real_timestamp_us", "replay_timestamp_us")] == [
        "120000", "120082", "8500"
    ]
    assert json.loads(pair["real_points_json"]) == real["points"]
    assert json.loads(pair["replay_lines_json"]) == replay["lines"]
    assert json.loads(pair["real_pdc_json"])["probes"][SENSOR_NAMES[0]]["distance_cm"] == 75
    assert (real_only["status"], real_only["replay_timestamp_us"]) == ("real_only", "")
    assert (replay_only["status"], replay_only["real_timestamp_us"]) == ("replay_only", "")


def test_s20_timeline_uses_display_coordinates_and_excludes_placeholder_pdc(tmp_path):
    session = RecordingSession(tmp_path, {"settings": {"project": "S20"}})
    scene = {
        "timestamp_us": 123, "points": [{"x": 0, "y": 35}],
        "lines": [{"sy": 9, "ey": -11}],
        "data": {"transport": "upper_can_v1", "compare_key": [1, 1, 1], "pdc": {"sts": 0}},
    }
    session.put("pair", {"key": (1, 1, 1), "baseline": scene, "replay": scene})
    session.close()

    output = tmp_path / "timeline.csv"
    assert export_comparison_csv(session.path, output) == 1
    with output.open(encoding="utf-8-sig", newline="") as stream:
        [pair] = list(csv.DictReader(stream))
    assert json.loads(pair["real_points_json"]) == [{"x": 0, "y": -35}]
    assert json.loads(pair["real_lines_json"]) == [{"sy": -9, "ey": 11}]
    assert json.loads(pair["replay_points_json"]) == scene["points"]
    assert pair["real_pdc_json"] == pair["replay_pdc_json"] == ""
