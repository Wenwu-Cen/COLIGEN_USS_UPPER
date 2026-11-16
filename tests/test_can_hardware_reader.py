from dataclasses import replace
from types import SimpleNamespace
import sys

import pytest

import CanOnlinePort as source


@pytest.mark.parametrize("channel", [0, 9])
def test_vector_application_channel_is_forwarded_without_off_by_one(monkeypatch, channel):
    config = replace(source.SourceConfig(), canoe_channel=channel)
    reader = source.CanReader(backend="canoe", config=config)
    captured = {}

    class Bus:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def recv(self, timeout):
            reader._stop_event.set()
            return None

    monkeypatch.setattr(source, "_prepare_vector_library", lambda: None)
    monkeypatch.setitem(sys.modules, "can.interfaces.vector", SimpleNamespace(VectorBus=Bus))
    reader._run_canoe()
    assert captured["channel"] == channel
    assert captured["app_name"] == "CANoe"
    assert captured["bitrate"] == 500000
    assert f"CAN{channel+1}" in reader.display_name


def test_reader_forwards_800u_device_99_channel_7_to_selected_channel_adapter(monkeypatch):
    import zlg_can_bus
    config = replace(source.SourceConfig(), device_type=59, device_index=99, channel=7)
    reader = source.CanReader(backend="zlgcan", config=config)
    captured = {}

    class Bus:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def recv(self, timeout):
            reader._stop_event.set()
            return None

    monkeypatch.setattr(zlg_can_bus, "ZlgCanBus", Bus)
    monkeypatch.setattr(source, "_find_zlg_library_dir", lambda: "vendor-library")
    reader._run_live()
    assert (captured["device_type"], captured["device_index"], captured["channel"]) == (59, 99, 7)
    assert (captured["bitrate"], captured["dbitrate"]) == (500000, 2000000)
    assert "通道 7" in reader.display_name
