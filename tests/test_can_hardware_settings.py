from dataclasses import replace

import pytest

from CanOnlinePort import SourceConfig
from can_hardware_settings import (CanHardwareSettings, VECTOR_CHANNELS, ZLG_CHANNELS,
                                   ZLG_INDICES, load_can_hardware, save_can_hardware)


def test_saved_selection_overlays_source_without_changing_bus_timing():
    source = SourceConfig(bitrate=250000, data_bitrate=1000000, canoe_app_name="CANoe")
    settings = CanHardwareSettings(59, 99, 7, 9)
    save_can_hardware(settings)
    loaded = load_can_hardware(source)
    actual = loaded.apply(source)
    assert (actual.device_type, actual.device_index, actual.channel) == (59, 99, 7)
    assert actual.canoe_channel == 9
    assert (actual.bitrate, actual.data_bitrate, actual.canoe_app_name) == (250000, 1000000, "CANoe")
    assert source.device_index == 0
    assert VECTOR_CHANNELS[actual.canoe_channel] == "CAN10"


def test_legacy_toml_channel_zero_is_still_can1():
    settings = load_can_hardware(SourceConfig())
    assert (settings.model_name, settings.zlg_channel) == ("USBCANFD-200U", 0)
    assert VECTOR_CHANNELS[settings.vector_channel] == "CAN1"
    assert ZLG_INDICES == tuple(str(i) for i in range(100))
    assert ZLG_CHANNELS == tuple(str(i) for i in range(8))


@pytest.mark.parametrize("changes", [
    {"zlg_device_index": -1}, {"zlg_device_index": 100}, {"zlg_channel": -1},
    {"zlg_channel": 8}, {"zlg_device_type": 99}, {"vector_channel": -1},
    {"vector_channel": 10}, {"zlg_device_type": 41, "zlg_channel": 7},
])
def test_out_of_range_or_unavailable_channel_is_rejected(changes):
    settings = replace(CanHardwareSettings(59, 99, 7, 9), **changes)
    with pytest.raises(ValueError):
        settings.validate()


@pytest.mark.parametrize("kind,channel", [(42, 0), (41, 1), (76, 3), (59, 7)])
def test_each_model_accepts_its_highest_physical_channel(kind, channel):
    CanHardwareSettings(kind, 99, channel, 9).validate()
