import pytest

from brake_light_view import BrakeLightView


@pytest.mark.parametrize("direction", [1, -1])
def test_brake_lights_detect_deceleration_and_ignore_small_speed_noise(direction):
    brake = BrakeLightView()
    for index, speed in enumerate((4, 4.05, 3.94, 3.7, 3.4)):
        brake.update(direction * speed, index * 50_000)
        assert brake.active == (index == 4)

    for ts in range(250_000, 450_000, 50_000):
        brake.update(direction * 3.4, ts)
        assert brake.active
    brake.update(direction * 3.5, 450_000)
    assert not brake.active


@pytest.mark.parametrize("speed, timestamp_us, frame_index, epoch", [
    (None, 200_000, 2, 0),
    (0, 200_000, 5, 0),
    (0, 200_000, 2, 1),
    (0, 800_000, 2, 0),
])
def test_brake_lights_reset_after_invalid_or_discontinuous_data(speed, timestamp_us, frame_index, epoch):
    brake = BrakeLightView()
    brake.update(5, 0, frame_index=0, epoch=0)
    brake.update(4, 100_000, frame_index=1, epoch=0)
    assert brake.active
    brake.update(speed, timestamp_us, frame_index=frame_index, epoch=epoch)
    assert not brake.active
