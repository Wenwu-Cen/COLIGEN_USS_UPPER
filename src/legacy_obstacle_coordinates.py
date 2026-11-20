"""Identify older mirrored TXT point/line coordinates from stationary walls."""

import math

from map_view import local_to_map
from world_memory import motion_timestamp


POINT_LINE_FIELD = "PointLineConvention"
POINT_LINE_LEFT = "x_forward_y_left"
POINT_LINE_RIGHT = "x_forward_y_right"


def _long_lines(frame):
    return {(s.index, s.cnum, s.height, s.obj_type): s for s in frame.segments
            if math.hypot(s.ex - s.sx, s.ey - s.sy) >= 1800}


def _world_line(segment, pose, sign):
    a = local_to_map(segment.sx, sign * segment.sy, pose)
    b = local_to_map(segment.ex, sign * segment.ey, pose)
    return a, b, math.atan2(b[1] - a[1], b[0] - a[0])


def _line_error(lines, poses, sign):
    """Compare supporting lines; endpoints may slide along the same object."""
    p, q, heading = _world_line(lines[0], poses[0], sign)
    c, s = math.cos(heading), math.sin(heading)
    length = math.dist(p, q)
    angle_error = offset_error = 0.0
    overlap = True
    for line, pose in zip(lines[1:], poses[1:]):
        a, b, angle = _world_line(line, pose, sign)
        angle_error = max(angle_error, abs(math.remainder(angle - heading, math.pi)))
        dx, dy = (a[0] + b[0]) / 2 - p[0], (a[1] + b[1]) / 2 - p[1]
        offset_error = max(offset_error, abs(c*dy - s*dx))
        projections = [(x-p[0])*c + (y-p[1])*s for x, y in (a, b)]
        overlap = overlap and min(projections) <= length + 350 and max(projections) >= -350
    return math.degrees(angle_error), offset_error, overlap


def _is_clear_winner(best, alternate):
    angle, offset, overlap = best
    return overlap and angle <= 2 and offset <= 200 and (alternate[0] >= 8 or alternate[1] >= 650)


def has_mirrored_legacy_obstacles(frames):
    """Require repeated turn windows with stationary, overlapping world lines.

    Call only for unmarked, legacy-structured TXT with matching native ODO.
    Working by line orientation *and* offset rejects 'fixes' that keep a
    direction constant but slide the obstacle sideways during the turn.
    """
    right_windows = 0
    for start in range(0, len(frames) - 14, 4):
        window = frames[start:start+15]
        start_pose, end_pose = window[0].vehicle_pose, window[-1].vehicle_pose
        if start_pose is None or end_pose is None:
            continue
        yaw_change = abs(math.degrees(math.remainder(end_pose[2] - start_pose[2], math.tau)))
        if not 5 <= yaw_change <= 24 or not 200 < math.dist(start_pose[:2], end_pose[:2]) < 6000:
            continue
        poses = [frame.vehicle_pose for frame in window]
        if any(p is None for p in poses) or any(
                math.dist(a[:2], b[:2]) > 2000 or abs(math.remainder(b[2]-a[2], math.tau)) > .45
                for a, b in zip(poses, poses[1:])):
            continue  # Exclude ODO resets and unrelated sections of a drive.
        times = [motion_timestamp(f.timestamp_ms, f.timestamp_unit, f.sample_timestamp_us) for f in window]
        if not 150_000 <= times[-1] - times[0] <= 2_500_000 or any(
                b < a or b-a > 500_000 for a, b in zip(times, times[1:])):
            continue
        first, middle, last = (_long_lines(window[i]) for i in (0, 7, 14))
        saw_right = False
        for key in first.keys() & middle.keys() & last.keys():
            lines = first[key], middle[key], last[key]
            samples = poses[0], poses[7], poses[-1]
            left = _line_error(lines, samples, 1)
            right = _line_error(lines, samples, -1)
            if _is_clear_winner(left, right):
                return False  # Keep the saved data if the evidence disagrees.
            saw_right |= _is_clear_winner(right, left)
        right_windows += saw_right
    return right_windows >= 3
