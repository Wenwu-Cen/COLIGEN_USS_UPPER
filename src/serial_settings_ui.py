"""Serial configuration dialog, kept separate from the legacy connection UI."""

from tkinter import messagebox

from modern_ui import Button, COLORS, ComboBox, Label, ctk
from SerialOnlinePort import SerialConfig, available_ports, load_serial_config, save_serial_config


class SerialSettingsMixin:
    def _edit_serial_settings(self):
        if self.online_mode:
            return
        try:
            config = self._serial_config or load_serial_config()
        except ValueError as exc:
            messagebox.showwarning("串口配置", f"{exc}\n请重新配置。", parent=self)
            config = SerialConfig()
        dialog = ctk.CTkToplevel(self, fg_color=COLORS["bg"])
        dialog.title("串口 · LAUTERBACH_UPPER_DEBUG")
        dialog.resizable(False, False)
        dialog.transient(self)
        body = ctk.CTkFrame(dialog, fg_color=COLORS["panel"], corner_radius=12)
        body.pack(fill="both", expand=True, padx=18, pady=18)
        Label(body, text="串口数据采集", font=("Microsoft YaHei UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 4))
        Label(body, text="UPPER v1 · 二进制整帧 · CRC32 校验 · 8 数据位",
              text_color=COLORS["muted"]).grid(row=1, column=0, columnspan=3,
                                              sticky="w", padx=20, pady=(0, 12))
        controls = {}
        fields = (
            ("port", "串口", (), config.port),
            ("baudrate", "波特率", ("115200", "230400", "460800", "921600", "1500000", "2000000"),
             str(config.baudrate)),
            ("parity", "校验位", ("N", "E", "O"), config.parity),
            ("stopbits", "停止位", ("1", "1.5", "2"), str(config.stopbits)),
            ("timeout", "数据超时（秒）", ("0.5", "1", "2", "5"), str(config.timeout)),
            ("lateral_sign", "输入坐标", ("X向前 / Y向左", "X向前 / Y向右"),
             "X向前 / Y向左" if config.lateral_sign == 1 else "X向前 / Y向右"),
        )
        for row, (key, label, values, value) in enumerate(fields, 2):
            Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(20, 12), pady=5)
            control = ComboBox(body, values=list(values) or [value], width=240,
                               state="readonly" if key in ("parity", "stopbits", "lateral_sign")
                               else "normal")
            control.set(value)
            control.grid(row=row, column=1, sticky="ew", pady=5)
            controls[key] = control
        description = Label(body, text="", anchor="w", justify="left", wraplength=420,
                            text_color=COLORS["muted"])
        description.grid(row=8, column=0, columnspan=3, sticky="w", padx=20, pady=(4, 8))

        def refresh_ports():
            try:
                ports = available_ports()
            except OSError as exc:
                description.configure(text=f"串口扫描失败：{exc}；仍可手动输入端口。")
                return
            controls["port"].configure(values=[device for device, _ in ports] or [""])
            if not controls["port"].get() and ports:
                controls["port"].set(ports[0][0])
            description.configure(text="\n".join(f"{d} · {name}" for d, name in ports)
                                  or "未发现串口；插入设备后刷新，也可手动输入端口。")

        Button(body, text="刷新", width=55, command=refresh_ports).grid(
            row=2, column=2, padx=(6, 20), pady=5)
        refresh_ports()
        Label(body, text="配套 C 端默认使用 X向前 / Y向左。\n"
              "建议 921600、8N1；若降低波特率，请相应降低下位机发送频率。",
              justify="left", text_color=COLORS["muted"]).grid(
                  row=9, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 12))

        def save():
            try:
                candidate = SerialConfig(
                    port=controls["port"].get().strip(),
                    baudrate=int(controls["baudrate"].get()),
                    parity=controls["parity"].get(), stopbits=float(controls["stopbits"].get()),
                    timeout=float(controls["timeout"].get()),
                    lateral_sign=1 if controls["lateral_sign"].get() == "X向前 / Y向左" else -1)
                save_serial_config(candidate)
            except (OSError, ValueError) as exc:
                messagebox.showerror("串口配置", str(exc), parent=dialog)
                return
            self._serial_config = candidate
            dialog.destroy()

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=10, column=0, columnspan=3, sticky="e", padx=20, pady=(0, 18))
        Button(actions, text="取消", width=70, command=dialog.destroy).pack(side="left", padx=5)
        Button(actions, text="保存", width=70, command=save,
               fg_color=COLORS["accent"]).pack(side="left")
        dialog.after(50, dialog.grab_set)
        self._serial_dialog = dialog
