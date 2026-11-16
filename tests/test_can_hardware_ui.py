from types import SimpleNamespace
from unittest.mock import Mock

import VehUpperDemo_CAN as ui
from CanOnlinePort import CanReader, SourceConfig
from can_hardware_settings import load_can_hardware
from VehUpperDemo import VehicleInfo


def create_app(monkeypatch):
    monkeypatch.setattr(ui, "PdcAlarm", Mock())
    app = ui.App(VehicleInfo(), SimpleNamespace(frames=[]))
    app.geometry("1280x800")
    app.update()
    return app


def select(app, backend):
    app.conn_backend_var.set(backend)
    app._on_backend_changed()
    app.update()


def test_zlg_range_and_saved_selected_hardware_reaches_reader(monkeypatch):
    readers = []

    def factory(port, backend):
        reader = ui._reader_factory(port, backend)
        reader.start = Mock()
        readers.append(reader)
        return reader

    monkeypatch.setattr(ui._legacy, "OnlineReader", factory)
    app = create_app(monkeypatch)
    try:
        assert "ZLG-USBCANFD" in app.conn_backend_combo.cget("values")
        assert "ZLG-USBCANFD-200U" not in app.conn_backend_combo.cget("values")
        select(app, "ZLG-USBCANFD")
        assert app._zlg_options.winfo_manager() == "pack"
        assert not app._vector_options.winfo_manager()
        assert app._zlg_controls["device_index"].cget("values") == list(map(str, range(100)))
        assert app._zlg_controls["channel"].cget("values") == list(map(str, range(8)))
        app._zlg_controls["model"].set("USBCANFD-800U")
        app._zlg_controls["device_index"].set("99")
        app._zlg_controls["channel"].set("7")
        app._toggle_online()
        reader = readers[-1]
        assert isinstance(reader, CanReader)
        assert (reader.config.device_type, reader.config.device_index, reader.config.channel) == (59, 99, 7)
        assert app._zlg_controls["channel"].cget("state") == "disabled"
        assert load_can_hardware(SourceConfig()).zlg_channel == 7
        app._disconnect_online()
        assert app._zlg_controls["channel"].cget("state") == "readonly"
        # Real CTk virtual events originate from the internal entry.
        model = app._zlg_controls["model"]
        model.set("USBCANFD-200U")
        model._entry.event_generate("<<ComboboxSelected>>")
        app.update()
        assert app._zlg_controls["channel"].get() == "0"
        assert load_can_hardware(SourceConfig()).zlg_device_type == 41
    finally:
        if app.online_mode:
            app._disconnect_online()
        app.destroy()


def test_vector_can10_maps_to_application_channel_nine(monkeypatch):
    readers = []

    def factory(port, backend):
        reader = ui._reader_factory(port, backend)
        reader.start = Mock()
        readers.append(reader)
        return reader

    monkeypatch.setattr(ui._legacy, "OnlineReader", factory)
    app = create_app(monkeypatch)
    try:
        select(app, "CANoe/Vector")
        combo = app._vector_channel_combo
        assert combo.cget("values") == [f"CAN{i}" for i in range(1, 11)]
        assert combo.get() == "CAN1"
        assert not app._zlg_options.winfo_manager()
        assert app._vector_options.winfo_manager() == "pack"
        combo.set("CAN10")
        app._toggle_online()
        assert readers[-1].config.canoe_channel == 9
        assert "CAN10" in readers[-1].display_name
        assert combo.cget("state") == "disabled"
        app._disconnect_online()
        assert load_can_hardware(SourceConfig()).vector_channel == 9
    finally:
        if app.online_mode:
            app._disconnect_online()
        app.destroy()
