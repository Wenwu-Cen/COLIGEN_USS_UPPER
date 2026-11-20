"""Continuous display poses and bounded point/line memory for the world view."""

from collections import OrderedDict
from dataclasses import dataclass
import math

from display_clock import timestamp_to_us
from map_view import local_to_map, valid_pose


def motion_timestamp(timestamp, unit, sample_us=0):
    """Prefer acquisition time: some devices switch counter domains mid-stream."""
    if sample_us:
        return sample_us
    return timestamp_to_us(timestamp, unit) if timestamp is not None else None


@dataclass(frozen=True)
class WorldSample:
    pose: tuple | None
    rebased: bool = False


class ContinuousPose:
    """Stitch a near-origin odometry reset into the existing display frame."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._offset = (0.0, 0.0, 0.0)
        self.break_chain()

    def break_chain(self):
        self._last = None
        self._velocity = None
        self._pending = None

    def update(self, raw, timestamp_us):
        raw = valid_pose(raw)
        if raw is None:
            return WorldSample(None)
        x, y, yaw = raw
        if self._pending is not None:
            offset, previous, restart, restart_time = self._pending
            elapsed = timestamp_us - restart_time if timestamp_us is not None else math.inf
            from_restart = math.dist(raw[:2], restart[:2])
            if (0 <= elapsed <= 350_000 and from_restart >= 2_200
                    and math.dist(raw[:2], previous[0][:2]) <= 1_200):
                # A lone zero or short run of zero samples is a dropout if the
                # original odometry returns nearby. Discard the provisional offset.
                self._offset, self._last = offset, previous
                self._pending = None
            elif not 0 <= elapsed <= 350_000 or from_restart > 450:
                self._pending = None
        ox, oy, rotation = self._offset
        wx, wy = local_to_map(x, y, self._offset)
        heading = math.remainder(yaw + rotation, math.tau)
        pose = wx, wy, heading
        rebased = False
        if self._last is not None:
            old_raw, old_pose, old_time = self._last
            dt = (timestamp_us - old_time) / 1e6 if timestamp_us is not None and old_time is not None else 0
            jump = math.dist(raw[:2], old_raw[:2])
            turn = math.remainder(heading - old_pose[2], math.tau)
            if (0 < dt <= .5 and self._velocity is not None
                    and jump >= 2_200 and math.hypot(x, y) <= 650
                    and abs(math.remainder(yaw, math.tau)) <= math.radians(8)):
                # The ECU restarted its local axes. Extrapolate just one short
                # sample, then let the new axes drive subsequent motion.
                vx, vy, omega = self._velocity
                lead = min(dt, .18)
                wx, wy = old_pose[0] + vx*lead, old_pose[1] + vy*lead
                heading = math.remainder(old_pose[2] + omega*lead, math.tau)
                rotation = math.remainder(heading - yaw, math.tau)
                dx, dy = local_to_map(x, y, (0, 0, rotation))
                self._pending = self._offset, self._last, raw, timestamp_us
                self._offset = wx-dx, wy-dy, rotation
                pose = wx, wy, heading
                rebased = True
            elif 0 < dt <= .5 and jump <= 2_000 and abs(turn) <= .5:
                velocity = (wx-old_pose[0])/dt, (wy-old_pose[1])/dt, turn/dt
                if math.hypot(*velocity[:2]) <= 20_000 and abs(velocity[2]) <= 2:
                    previous = self._velocity or velocity
                    self._velocity = tuple(.65*v + .35*p for v, p in zip(velocity, previous))
            elif dt != 0 or jump:
                self._velocity = None
        self._last = raw, pose, timestamp_us
        return WorldSample(pose, rebased)


class WorldObstacleMemory:
    """Keep observed geometry within a moving, 100 m world-space radius."""

    RADIUS_MM = 100_000
    CELL_MM = 350

    def __init__(self, max_points=16_000, max_lines=3200):
        self.max_points = max_points
        self.max_lines = max_lines
        self.revision = 0
        self.clear()

    def clear(self):
        self.points = OrderedDict()
        self.lines = OrderedDict()
        self._live_points = set()
        self._live_lines = set()
        self._center = None
        self._last_sample_us = None
        self._time = 0
        self.revision += 1

    def _point_key(self, xy):
        return tuple(math.floor(v/self.CELL_MM) for v in xy)

    def _in_range(self, coords, center):
        dx, dy = coords[0]-center[0], coords[1]-center[1]
        if len(coords) == 4:
            vx, vy = coords[2]-coords[0], coords[3]-coords[1]
            length_sq = vx*vx + vy*vy
            if length_sq:
                closest = max(0.0, min(1.0, -(dx*vx+dy*vy)/length_sq))
                dx, dy = dx+closest*vx, dy+closest*vy
        return dx*dx+dy*dy <= self.RADIUS_MM**2

    def _move_window(self, center):
        if center == self._center:
            return
        self._center = center
        for entries in (self.points, self.lines):
            expired = [key for key, (coords, _, _) in entries.items() if not self._in_range(coords, center)]
            for key in expired:
                del entries[key]

    def update(self, pose, segments, points, timestamp_us, *, skip=False):
        dt = (timestamp_us - self._last_sample_us
              if timestamp_us is not None and self._last_sample_us is not None else 50_000)
        self._last_sample_us = timestamp_us
        self._time += dt if 0 <= dt <= 1_000_000 else 50_000
        if pose is None:
            self._live_points, self._live_lines = set(), set()
            self.revision += 1
            return
        center = pose[:2]
        self._move_window(center)
        live_points, live_lines = set(), set()
        if not skip:
            for p in points:
                if not p.is_valid:
                    continue
                xy = local_to_map(p.x, p.y, pose)
                if not all(map(math.isfinite, xy)) or not self._in_range(xy, center):
                    continue
                i, j = self._point_key(xy)
                neighbors = ((i+di, j+dj) for di in (-1, 0, 1) for dj in (-1, 0, 1))
                nearest = min(((math.dist(xy, self.points[k][0]), k)
                               for k in neighbors if k in self.points), default=(math.inf, (i, j)))
                key = nearest[1] if nearest[0] <= 220 else (i, j)
                self.points[key] = xy, p.height, self._time
                self.points.move_to_end(key)
                live_points.add(key)
            for s in segments:
                if not s.is_valid:
                    continue
                a, b = sorted((local_to_map(s.sx, s.sy, pose), local_to_map(s.ex, s.ey, pose)))
                coords = (*a, *b)
                if not all(map(math.isfinite, coords)) or not self._in_range(coords, center):
                    continue
                # A coarser endpoint grid absorbs ordinary jitter without
                # merging lines that simply cross at the same midpoint.
                key = tuple(round(v/750) for v in coords)
                self.lines[key] = coords, s.height, self._time
                self.lines.move_to_end(key)
                live_lines.add(key)
        self._live_points, self._live_lines = live_points, live_lines
        for entries, cap in ((self.points, self.max_points), (self.lines, self.max_lines)):
            while len(entries) > cap:
                entries.popitem(last=False)
        self.revision += 1

    def unseen(self, lines=False, *, bounds=None):
        entries, live = (self.lines, self._live_lines) if lines else (self.points, self._live_points)
        for key, (coords, height, time) in entries.items():
            if key in live:
                continue
            if bounds is not None:
                x1, x2, y1, y2 = bounds
                x, y = coords[:2]
                if lines:
                    ex, ey = coords[2:]
                    if (max(x, ex) < x1 or min(x, ex) > x2
                            or max(y, ey) < y1 or min(y, ey) > y2):
                        continue
                elif not (x1 <= x <= x2 and y1 <= y <= y2):
                    continue
            age = self._time - time
            shade = 0 if age < 150_000 else 1 if age < 400_000 else 2
            yield key, coords, height, shade
