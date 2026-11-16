"""Per-user CAN hardware selection, overlaid on the existing bus configuration."""

from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import sys
import tempfile


ZLG_MODELS = {
    "USBCANFD-100U": (42, 1),
    "USBCANFD-200U": (41, 2),
    "USBCANFD-400U": (76, 4),
    "USBCANFD-800U": (59, 8),
}
ZLG_INDICES = tuple(str(i) for i in range(100))
ZLG_CHANNELS = tuple(str(i) for i in range(8))
VECTOR_CHANNELS = tuple(f"CAN{i}" for i in range(1, 11))


@dataclass
class CanHardwareSettings:
    zlg_device_type: int = 41
    zlg_device_index: int = 0
    zlg_channel: int = 0
    vector_channel: int = 0

    @classmethod
    def from_source(cls, source):
        return cls(int(source.device_type), int(source.device_index), int(source.channel),
                   int(source.canoe_channel))

    @property
    def model_name(self):
        return next((name for name, (kind, _) in ZLG_MODELS.items()
                     if kind == self.zlg_device_type), None)

    def validate(self, backend=None):
        if backend in (None, "zlgcan"):
            if self.model_name is None:
                raise ValueError("请选择 USBCANFD-100U、200U、400U 或 800U")
            if type(self.zlg_device_index) is not int or not 0 <= self.zlg_device_index <= 99:
                raise ValueError("ZLG 硬件索引必须为 0～99")
            if type(self.zlg_channel) is not int or not 0 <= self.zlg_channel <= 7:
                raise ValueError("ZLG 通道索引必须为 0～7")
            count = ZLG_MODELS[self.model_name][1]
            if self.zlg_channel >= count:
                raise ValueError(f"{self.model_name} 支持通道 0～{count-1}，请调整型号或通道")
        if backend in (None, "canoe"):
            if type(self.vector_channel) is not int or not 0 <= self.vector_channel <= 9:
                raise ValueError("CANoe/Vector 通道必须为 CAN1～CAN10")

    def apply(self, source, backend=None):
        self.validate(backend)
        return replace(source, device_type=self.zlg_device_type,
                       device_index=self.zlg_device_index, channel=self.zlg_channel,
                       canoe_channel=self.vector_channel)


def settings_path():
    override = os.environ.get("COLIGEN_CONFIG_DIR")
    if override:
        return Path(override) / "can_hardware.json"
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home()/"AppData/Roaming") / "COLIGEN_USS_UPPER"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home()/".config") / "coligen-uss-upper"
    return base / "can_hardware.json"


def load_can_hardware(source=None):
    if source is None:
        from CanOnlinePort import _load_config
        source = _load_config()
    default = CanHardwareSettings.from_source(source)
    path = settings_path()
    if not path.exists():
        return default
    try:
        settings = CanHardwareSettings(**json.loads(path.read_text(encoding="utf-8")))
        settings.validate()
        return settings
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"CAN 硬件配置读取失败：{exc}") from exc


def save_can_hardware(settings):
    settings.validate()
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".can-hardware-", delete=False) as output:
            temporary = Path(output.name)
            json.dump(asdict(settings), output, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
