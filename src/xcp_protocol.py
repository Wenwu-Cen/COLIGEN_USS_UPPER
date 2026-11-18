"""Read-only XCP-on-CAN polling: CONNECT, SET_MTA, UPLOAD and DISCONNECT."""

import threading
import time

import can


class XcpError(RuntimeError):
    pass


class XcpClient:
    def __init__(self, bus, config, stop_event=None):
        config.validate()
        self.bus, self.config = bus, config
        self.stop_event = stop_event or threading.Event()
        self.byte_order = "little"
        self.max_cto = 8
        self.connected = False
        self.failed = False
        self.bytes_total = 0
        self.requests = 0

    def command(self, packet):
        if self.failed:
            raise XcpError("XCP 会话已失效，请重新连接")
        if self.stop_event.is_set():
            raise InterruptedError("XCP 已停止")
        try:
            self.bus.send(can.Message(
                arbitration_id=self.config.tx_id, is_extended_id=self.config.extended_id,
                is_fd=self.config.fd, bitrate_switch=self.config.bitrate_switch,
                data=packet.ljust(8, b"\0"), check=True), timeout=self.config.timeout)
            self.requests += 1
            deadline = time.monotonic() + self.config.timeout
            while not self.stop_event.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"XCP 0x{packet[0]:02X} 响应超时；请核对 ID、通道及 ECU XCP 状态")
                message = self.bus.recv(timeout=min(remaining, 0.05))
                if (message is None or message.is_error_frame or message.is_remote_frame
                        or not message.is_rx or message.arbitration_id != self.config.rx_id
                        or message.is_extended_id != self.config.extended_id
                        or message.is_fd != self.config.fd):
                    continue
                data = bytes(message.data)
                if not data:
                    continue
                if data[0] == 0xFF:
                    return data
                if data[0] == 0xFE:
                    code = data[1] if len(data) > 1 else 0
                    detail = {0x20: "命令不支持", 0x22: "参数超范围", 0x24: "访问被拒绝",
                              0x25: "资源锁定，需 ECU 侧解锁"}.get(code, "ECU 拒绝命令")
                    raise XcpError(f"XCP 错误 0x{code:02X}：{detail}")
                # DAQ, event and service packets are never command responses.
            raise InterruptedError("XCP 已停止")
        except Exception:
            # CAN CTOs have no transaction ID. Never retry after a timeout and
            # risk accepting a delayed UPLOAD response for another address.
            self.failed = True
            raise

    def connect(self):
        # Drain the device RX queue before starting a new command session.
        for _ in range(1024):
            if self.bus.recv(timeout=0) is None:
                break
            if self.stop_event.is_set():
                raise InterruptedError("XCP 已停止")
        reply = self.command(b"\xFF\x00")
        if len(reply) < 8:
            raise XcpError("XCP CONNECT 响应不完整")
        self.connected = True
        mode = reply[2]
        self.byte_order = "big" if mode & 1 else "little"
        if (mode >> 1) & 3:
            raise XcpError("当前 XCP 仅支持 BYTE 地址粒度，ECU 返回 WORD/DWORD 或保留值")
        self.max_cto = reply[3]
        if not 8 <= self.max_cto <= (64 if self.config.fd else 8):
            raise XcpError("ECU MAX_CTO 与所选 CAN/CAN FD 模式不匹配")

    def read(self, address, size):
        if not self.connected:
            raise XcpError("XCP 尚未连接")
        if type(address) is not int or type(size) is not int or size <= 0 or not 0 < address < address + size <= 0x100000000:
            raise ValueError("XCP 读取地址或长度无效")
        self.command(b"\xF6\x00\x00" + bytes([self.config.address_extension])
                     + address.to_bytes(4, self.byte_order))
        result = bytearray()
        while len(result) < size:
            count = min(size - len(result), self.max_cto - 1)
            response = self.command(bytes((0xF5, count)))
            if len(response) < count + 1:
                self.failed = True
                raise XcpError("XCP UPLOAD 响应长度不足")
            result.extend(response[1:count + 1])
        self.bytes_total += len(result)
        return bytes(result)

    def close(self):
        if self.connected and not self.failed:
            # Called by the reader thread; no UI waits for a disconnect ACK.
            try:
                self.bus.send(can.Message(
                    arbitration_id=self.config.tx_id, is_extended_id=self.config.extended_id,
                    is_fd=self.config.fd, bitrate_switch=self.config.bitrate_switch,
                    data=b"\xFE" + bytes(7)), timeout=0.05)
            except (OSError, can.CanError):
                pass
        self.connected = False
