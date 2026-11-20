from types import SimpleNamespace

import pytest

from legacy_obstacle_coordinates import POINT_LINE_FIELD, POINT_LINE_LEFT, POINT_LINE_RIGHT
from log_parser import LogParser
from map_view import local_to_map, map_to_local
from viewer_models import VehicleInfo


def _recorded_turn(sign, *, count=45, marker="", line_direction=False):
    """A moving car observes one stationary wall and a marker on the wall."""
    blocks = [f"VehicleInfo: V1.0\n{marker}"]
    for index in range(count):
        pose = (index * 105, index * 22, .013 * index)

        def raw(x, y):
            longitudinal, lateral = map_to_local(x, y, pose)
            return round(longitudinal), sign * round(lateral)

        sx, sy = raw(1500, -2500)
        ex, ey = raw(8600, -2500)
        px, py = raw(6300, -2500)
        direction = " cDirect = 3" if line_direction else ""
        blocks.append(
            f"=== Frame Index: {index+1} ===\n"
            f"TimeStamp_us = {1_000_000+index*60_000} GearLever = 3 VehicleSpeed = 6\n"
            "[sf_Upper_OdoOutSignal]\nOdometryConvention = mm_right_forward\n"
            f"odo_x = {-pose[1]} odo_y = {pose[0]} odo_ang = {pose[2]}\n"
            "[sf_Upper_PointOutSignal]\n"
            f"Point[5] ObjID = 27 x = {px} y = {py} cHight = 1 SNS_Txindex = 4 SNS_Rxindex = 5\n"
            "[sf_Upper_LineOutSignal]\n"
            f"Line[0] cNum = 3 cHight = 1 cObjType = 3 wStartx = {sx} wStarty = {sy} "
            f"wEndx = {ex} wEndy = {ey} wDist = 2500{direction}\n")
    return "\n".join(blocks)


def _load(tmp_path, text):
    path = tmp_path / "copy.txt"
    path.write_text(text, encoding="utf-8")
    parser = LogParser(path)
    parser.parse()
    return parser


def _assert_wall_is_fixed(frames, lateral=-2500):
    for frame in frames:
        point, = frame.points
        line, = frame.segments
        assert point.obj_id == 27 and line.cnum == 3 and line.dist == 2500
        assert local_to_map(point.x, point.y, frame.vehicle_pose) == pytest.approx((6300, lateral), abs=1)
        assert local_to_map(line.sx, line.sy, frame.vehicle_pose) == pytest.approx((1500, lateral), abs=1)
        assert local_to_map(line.ex, line.ey, frame.vehicle_pose) == pytest.approx((8600, lateral), abs=1)


def test_legacy_file_aligns_display_odo_without_moving_the_wall_to_the_other_side(tmp_path):
    text = _recorded_turn(-1)
    log = _load(tmp_path, text)
    assert log.obstacle_note and not log.pose_note
    frame = log.frames[18]
    assert frame.vehicle_pose == pytest.approx((1890, -396, -.234))
    assert (frame.odo_x, frame.odo_y, frame.odo_ang) == pytest.approx((-396, 1890, .234))
    assert log.frames[0].points[0].y == 2500  # Stored positive Y remains vehicle-left.
    _assert_wall_is_fixed(log.frames, lateral=2500)
    assert log.filepath.read_text(encoding="utf-8") == text


def test_unmarked_but_already_aligned_input_is_left_unchanged(tmp_path):
    log = _load(tmp_path, _recorded_turn(1))
    assert not log.obstacle_note
    _assert_wall_is_fixed(log.frames)


@pytest.mark.parametrize("flags", [{"count": 14}, {"line_direction": True},
                                   {"marker": f"{POINT_LINE_FIELD} = {POINT_LINE_LEFT}"}])
def test_ambiguous_or_newer_input_is_not_auto_mirrored(tmp_path, flags):
    log = _load(tmp_path, _recorded_turn(-1, **flags))
    assert not log.obstacle_note
    assert log.frames[0].points[0].y == 2500


def test_explicit_convention_can_fix_a_short_clip_and_new_writer_declares_left(tmp_path):
    from viewer_controller import ViewerController

    log = _load(tmp_path, _recorded_turn(-1, count=2, marker=f"{POINT_LINE_FIELD} = {POINT_LINE_RIGHT}"))
    assert log.obstacle_note
    _assert_wall_is_fixed(log.frames)
    holder = SimpleNamespace(vehicle=VehicleInfo())
    assert f"{POINT_LINE_FIELD} = {POINT_LINE_LEFT}\n" in ViewerController._build_record_header(holder)
