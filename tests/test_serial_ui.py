from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import VehUpperDemo_CAN as ui
import serial_settings_ui
from SerialOnlinePort import SerialConfig, SerialReader, build_serial_snapshot
from VehUpperDemo import VehicleInfo
from test_serial_snapshot import c_frame


def test_serial_snapshot_displays_and_preserves_clicked_reference(monkeypatch):
    monkeypatch.setattr(ui, "PdcAlarm", Mock())
    app = ui.App(VehicleInfo(), SimpleNamespace(frames=[]))
    app.geometry("1280x800")
    try:
        app.conn_backend_var.set("串口 Serial")
        app._on_backend_changed()
        assert not app.port_entry.winfo_manager()
        assert app._serial_settings_btn.winfo_manager()
        reader = SerialReader(SerialConfig(port="TEST"))
        reader.connected = True
        source = c_frame()
        reader.latest_snapshot = build_serial_snapshot(source)
        app.online_reader = reader
        app.online_mode = True
        app._online_tick()
        app.update()
        assert app.canvas.current_points[79].obj_id == 1079
        assert app.canvas.current_segments[19].cnum == 29
        assert app.canvas.driving_trail.pose == (1500, -2500, .25)
        app.canvas.capture_selection_snapshot(("point", 79))
        saved = app.canvas.selection_snapshot
        assert dict(saved.fields)["objID"] == 1079
        points = list(source.points)
        points[79] = (3000, 579, -279, 2, 3, 4)
        reader.latest_snapshot = build_serial_snapshot(replace(
            source, points=tuple(points), sequence=source.sequence+1,
            status=(*source.status[:3], source.status[3]+100000)))
        app._online_tick()
        app.update()
        assert app.canvas.selection_snapshot is saved
        assert app.canvas.current_points[79].obj_id == 3000
        assert app.canvas.highlight_target == ("point", 79)
        assert app.canvas.find_withtag("selection-snapshot")
        assert "串口" in app.status.cget("text")
    finally:
        if app.online_mode:
            app._disconnect_online()
        app.destroy()


def test_serial_configuration_dialog_opens_with_scanned_port(monkeypatch):
    monkeypatch.setattr(ui, "PdcAlarm", Mock())
    monkeypatch.setattr(serial_settings_ui, "available_ports", lambda: [("COM12", "Fixture")])
    app = ui.App(VehicleInfo(), SimpleNamespace(frames=[]))
    try:
        app._serial_config = SerialConfig(port="COM12")
        app._edit_serial_settings()
        app.update()
        dialog = app._serial_dialog
        assert dialog.winfo_exists()
        assert dialog.winfo_reqwidth() >= 400
        assert "LAUTERBACH_UPPER_DEBUG" in dialog.title()
        dialog.destroy()
    finally:
        app.destroy()
