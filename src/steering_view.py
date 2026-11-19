"""Estimate front-wheel and simulated steering-wheel angles from ODO poses."""

import math

from map_view import local_to_map, rear_axle_local, valid_pose


DEFAULT_STEERING_RATIO = 16


def steering_wheel_angle(front_wheel_deg):
    return None if front_wheel_deg is None else front_wheel_deg * DEFAULT_STEERING_RATIO


def format_odometry(value, steering_deg):
    pose = valid_pose(value)
    if pose is None:
        return "ODO  X —   Y —   航向 —   |   前轮估算 —   方向盘模拟 —"
    x, y, yaw = pose
    wheel_deg = steering_wheel_angle(steering_deg)
    front = "—" if steering_deg is None else f"{steering_deg:+.1f}°"
    wheel = "—" if wheel_deg is None else f"{wheel_deg:+.1f}°"
    return (f"ODO  X {x/1000:+.3f} m   Y {y/1000:+.3f} m   航向 {math.degrees(yaw):+.1f}°"
            f"   |   前轮估算 {front}   方向盘模拟 {wheel}")


class SteeringView:
    """Low-speed bicycle model in rear-axle coordinates, for display only."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.angle_deg = None
        self.tread_phase = 0.0
        self._last = None
        self._anchor = None

    def update(self, pose, timestamp_us, vehicle, *, frame_index=None, epoch=None):
        pose = valid_pose(pose)
        if pose is None:
            self.reset()
            return
        axle = rear_axle_local(vehicle)
        x, y = local_to_map(*axle, pose)
        yaw = pose[2]
        sample = x, y, yaw, timestamp_us, frame_index, epoch, axle
        last = self._last
        if last == sample:
            return
        self._last = sample
        if (last is None or axle != last[6] or epoch != last[5]
                or frame_index is not None and last[4] is not None and frame_index != last[4]+1
                or timestamp_us and last[3] and not 0 < timestamp_us-last[3] <= 500_000
                or math.hypot(x-last[0], y-last[1]) > 2_000):
            self.angle_deg, self.tread_phase, self._anchor = None, 0.0, sample
            return

        def relative(a):
            turn = math.remainder(yaw-a[2], math.tau)
            heading = a[2]+turn/2
            dx, dy = x-a[0], y-a[1]
            return dx*math.cos(heading)+dy*math.sin(heading), -dx*math.sin(heading)+dy*math.cos(heading), turn

        step, _, _ = relative(last)
        if abs(step) >= 1:
            self.tread_phase = (self.tread_phase + step / 180) % 1.0
        anchor = self._anchor
        distance, sideways, turn = relative(anchor)
        if abs(distance) < 25:
            if not timestamp_us or timestamp_us-anchor[3] >= 450_000:
                self.angle_deg, self._anchor = None, sample
            return

        self._anchor = sample
        if abs(sideways) > max(15, abs(distance)*0.35) or abs(turn) > math.pi/4:
            self.angle_deg = None
            return
        wheelbase = (getattr(vehicle, "profile_data", None) or {}).get("wheelbase_mm")
        wheelbase = wheelbase or vehicle.length * 0.58  # Match the drawn axles if unspecified.
        # The chord is projected along the midpoint yaw. Reverse travel has a
        # negative distance, so left steering keeps its sign in reverse.
        curvature = 2 * math.sin(turn/2) / distance
        angle = math.degrees(math.atan(wheelbase * curvature))
        self.angle_deg = round(max(-40, min(40, angle)), 1) if abs(angle) >= 0.5 else 0.0
