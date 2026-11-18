"""User-local XCP settings. ECU CAN IDs must be supplied explicitly."""

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path


@dataclass(frozen=True)
class XcpConfig:
    tx_id: int | None = None
    rx_id: int | None = None
    extended_id: bool = False
    fd: bool = False
    bitrate_switch: bool = False
    bitrate: int = 500000
    data_bitrate: int = 2000000
    resistance: bool = True
    address_extension: int = 0
    timeout: float = 0.5
    poll_interval: float = 0.2
    symbol_file: str = ""
    lateral_sign: int = 1
    odo_mode: str = "s20_mm"

    def validate(self, *, require_file=False):
        for name in ("extended_id", "fd", "bitrate_switch", "resistance"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"XCP {name} 必须为布尔值")
        maximum = 0x1FFFFFFF if self.extended_id else 0x7FF
        for name in ("tx_id", "rx_id"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f"请设置正确的 XCP {name}（0～0x{maximum:X}）")
        if self.tx_id == self.rx_id:
            raise ValueError("XCP 请求 ID 与响应 ID 必须不同")
        for name in ("bitrate", "data_bitrate"):
            value = getattr(self, name)
            if type(value) is not int or not 10000 <= value <= 10000000:
                raise ValueError("XCP 波特率必须为 10000～10000000 bit/s")
        if self.bitrate_switch and not self.fd:
            raise ValueError("XCP BRS 需要启用 CAN FD")
        if type(self.address_extension) is not int or not 0 <= self.address_extension <= 255:
            raise ValueError("XCP 地址扩展必须为 0～255")
        for name, low, high in (("timeout", 0.05, 5), ("poll_interval", 0.02, 60)):
            value = getattr(self, name)
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not low <= value <= high):
                raise ValueError(f"XCP {name} 必须为 {low}～{high} 秒")
        if type(self.lateral_sign) is not int or self.lateral_sign not in (-1, 1):
            raise ValueError("XCP 点线坐标方向无效")
        if self.odo_mode not in ("s20_mm", "metres_forward_left"):
            raise ValueError("XCP 里程计约定无效")
        if not isinstance(self.symbol_file, str):
            raise ValueError("XCP 变量文件路径必须为字符串")
        if require_file and (not self.symbol_file or not Path(self.symbol_file).is_file()):
            raise ValueError("请选择与当前固件匹配的 ELF、GHS MAP 或变量地址 JSON")


def settings_path():
    folder = os.environ.get("COLIGEN_CONFIG_DIR")
    if folder:
        return Path(folder) / "xcp.json"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / "COLIGEN_USS_UPPER/xcp.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "coligen-uss-upper/xcp.json"


def load_xcp_config():
    path = settings_path()
    if not path.exists():
        return XcpConfig()
    try:
        config = XcpConfig(**json.loads(path.read_text(encoding="utf-8")))
        config.validate()
        return config
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"XCP 配置文件无效：{exc}") from exc


def save_xcp_config(config):
    config.validate()
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
