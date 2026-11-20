from types import SimpleNamespace

import pytest

from map_view import local_to_map
from world_memory import ContinuousPose, WorldObstacleMemory, motion_timestamp


def test_stitches_origin_and_heading_reset_using_acquisition_time():
    tracker = ContinuousPose()
    before = [
        (15_800, 4_800, .70),
        (15_900, 4_900, .72),
        (16_000, 5_000, .74),
    ]
    for i, raw in enumerate(before):
        device = 1_500_000 if i == 1 else 1_767_227_016_359_317
        stamp = motion_timestamp(device, 'us', 1_000_000 + i*100_000)
        assert tracker.update(raw, stamp).pose == pytest.approx(raw)
    boundary = tracker.update((0, 0, 0), 1_300_000)
    assert boundary.rebased
    assert boundary.pose == pytest.approx((16_100, 5_100, .76))
    after = tracker.update((150, 20, .02), 1_400_000)
    assert not after.rebased
    assert after.pose[:2] == pytest.approx(local_to_map(150, 20, boundary.pose))
    assert after.pose[2] == pytest.approx(.78)
    tracker.break_chain()
    assert not tracker.update((0, 0, 0), 1_100_000).rebased


def test_discontinuous_teleport_does_not_stitch_or_turn_into_extra_motion():
    tracker = ContinuousPose()
    tracker.update((5000, 0, 0), 100_000)
    tracker.update((5100, 0, 0), 200_000)
    assert not tracker.update((40_000, 0, 0), 300_000).rebased
    assert not tracker.update((0, 0, 0), 1_000_000).rebased


def test_one_zero_odo_sample_does_not_permanently_shift_the_map():
    tracker = ContinuousPose()
    tracker.update((15_900, 0, 0), 100_000)
    tracker.update((16_000, 0, 0), 200_000)
    assert tracker.update((0, 0, 0), 300_000).pose == pytest.approx((16_100, 0, 0))
    assert tracker.update((16_200, 0, 0), 400_000).pose == pytest.approx((16_200, 0, 0))


def test_history_is_spatial_and_bounded_instead_of_following_reused_ids():
    memory = WorldObstacleMemory(max_points=3)
    point = lambda x,y: SimpleNamespace(x=x, y=y, index=0, is_valid=True, height=1)
    line = SimpleNamespace(sx=1000, sy=0, ex=2100, ey=0, height=1, is_valid=True)
    memory.update((0, 0, 0), [line], [point(1000, 2000)], 100_000)
    memory.update((100, 0, 0), [], [point(900, 2000)], 200_000)
    assert not list(memory.unseen())
    assert len(memory.points) == 1
    memory.update((16_000, 0, 0), [], [point(1000, 1000)], 600_000)
    assert [coords for _, coords, _, _ in memory.unseen()] == [(1000, 2000)]
    assert [coords for _, coords, _, _ in memory.unseen(lines=True)] == [(1000, 0, 2100, 0)]
    memory.update((118_000, 0, 0), [], [], 700_000)
    assert not memory.points and not memory.lines


def test_history_retention_follows_spatial_range_even_after_repeated_travel():
    memory = WorldObstacleMemory()
    point = SimpleNamespace(x=0, y=1000, is_valid=True, height=1)
    line = SimpleNamespace(sx=0, sy=-5000, ex=3000, ey=-5000, is_valid=True, height=1)
    memory.update((0, 0, 0), [line], [point], 0)
    for sequence, x in enumerate((40_000, 0, 40_000, 0, 40_000, 99_900), 1):
        memory.update((x, 0, 0), [], [], sequence*100_000)
        assert len(memory.points) == len(memory.lines) == 1
    assert not list(memory.unseen(bounds=(1000, 10_000, -2000, 2000)))
    assert list(memory.unseen(bounds=(-1000, 1000, -2000, 2000)))
    memory.update((100_100, 0, 0), [], [], 700_000)
    assert not memory.points and memory.lines  # The nearer end is still in range.
    memory.update((103_100, 0, 0), [], [], 800_000)
    assert not memory.lines


def test_repeated_fifteen_meter_rebases_keep_history_until_one_hundred_meters():
    tracker = ContinuousPose()
    memory = WorldObstacleMemory()
    point = SimpleNamespace(x=0, y=2000, is_valid=True, height=1)
    rebases = 0
    for meters in range(102):
        stamp = meters * 100_000
        view = tracker.update(((meters % 15)*1000, 0, 0), stamp)
        rebases += view.rebased
        assert view.pose[0] == pytest.approx(meters*1000)
        memory.update(view.pose, [], [point] if meters == 0 else [], stamp, skip=view.rebased)
        assert bool(memory.points) == (meters < 100)
    assert rebases == 6
