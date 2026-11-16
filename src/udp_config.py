"""Validated UDP endpoints and per-user settings for source and frozen launches."""

from dataclasses import asdict, dataclass
from ipaddress import IPv4Address
import json
import os
from pathlib import Path
import sys
import tempfile

from CanOnlinePort import _load_config


@dataclass(frozen=True)
class UdpConfig:
    bind_address: str = "192.168.98.123"
    port: int = 39001
    sender_address: str = "192.168.98.233"

    def validate(self, *, allow_ephemeral=False):
        for value, label in ((self.bind_address, "本机监听 IP"),
                             (self.sender_address, "接收来源设备 IP")):
            try:
                if not isinstance(value, str):
                    raise ValueError()
                IPv4Address(value)
            except ValueError as exc:
                raise ValueError(f"{label} 必须是有效的 IPv4 地址") from exc
        minimum = 0 if allow_ephemeral else 1
        if (isinstance(self.port, bool) or not isinstance(self.port, int)
                or not minimum <= self.port <= 65535):
            raise ValueError(f"UDP 端口须为 {minimum}..65535 的整数")


def udp_settings_path():
    override = os.environ.get("COLIGEN_CONFIG_DIR")
    if override:
        root = Path(override)
    elif sys.platform == "win32":
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData/Roaming") / "COLIGEN_USS_UPPER"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "coligen-uss-upper"
    return root / "udp_settings.json"


def load_udp_config():
    source = _load_config()
    values = dict(bind_address=source.udp_bind_address, port=source.udp_port,
                  sender_address=source.udp_sender_address)
    path = udp_settings_path()
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        saved = {}
    except ValueError as exc:
        raise ValueError(f"UDP 设置文件格式错误：{path}") from exc
    if not isinstance(saved, dict) or saved.keys() - values.keys():
        raise ValueError(f"UDP 设置文件字段无效：{path}")
    values.update(saved)
    config = UdpConfig(**values)
    config.validate()
    return config


def save_udp_config(config):
    config.validate()
    path = udp_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".udp-settings-", delete=False) as output:
            temporary = Path(output.name)
            json.dump(asdict(config), output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
