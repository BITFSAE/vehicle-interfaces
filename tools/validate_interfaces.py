#!/usr/bin/env python3
"""校验正式 DBC、Proto、Nanopb 配置、文档链接和公开仓库边界。"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import cantools


ROOT = Path(__file__).resolve().parents[1]
DBC_FILES = (
    ROOT / "can/Vehicle_CanA.dbc",
    ROOT / "can/Vehicle_CanB.dbc",
    ROOT / "can/Vehicle_CanC.dbc",
    ROOT / "can/Vehicle_Can1.dbc",
)
PROTO_FILE = ROOT / "telemetry/fsae_telemetry.proto"
OPTIONS_FILE = ROOT / "telemetry/fsae_telemetry.options"


def expected_frames() -> dict[str, tuple[tuple[int, int, bool], ...]]:
    """关键实现帧的 ID、DLC 和标准/扩展类型回归表。"""
    can1: list[tuple[int, int, bool]] = [
        *((0x180050F3 + (index << 16), 8, True) for index in range(36)),
        *((0x184050F3 + (index << 16), 8, True) for index in range(6)),
        (0x186050F4, 7, True),
        (0x186150F4, 6, True),
        (0x186250F4, 8, True),
        (0x186350F4, 8, True),
        *((0x186450F4 + (index << 16), 6, True) for index in range(3)),
        (0x186750F4, 2, True),
        (0x186850F4, 8, True),
        (0x186950F4, 8, True),
        (0x186A50F4, 8, True),
        (0x186B50F4, 8, True),
        (0x186C50F4, 8, True),
        (0x186C51F4, 8, True),
        (0x186D50F4, 8, True),
        (0x187650F4, 8, True),
        (0x187750F4, 6, True),
        (0x187850F4, 8, True),
        (0x187F50F4, 4, True),
        (0x18A050F5, 8, True),
        (0x18A450F4, 8, True),
        (0x18A650F4, 8, True),
        (0x18A750F4, 8, True),
    ]
    canb: list[tuple[int, int, bool]] = [
        (0x401, 8, False), (0x402, 8, False), (0x404, 8, False),
        (0x405, 8, False), (0x490, 6, False), (0x491, 8, False),
        (0x4A0, 8, False), (0x4A3, 8, False), (0x4A4, 8, False),
        (0x4B0, 7, False), (0x4B1, 8, False), (0x4B2, 8, False),
        *((0x512 + index, 6, False) for index in range(8)),
        (0x1806E5F4, 5, True), (0x18FF50E5, 8, True),
    ]
    return {"Vehicle_Can1.dbc": tuple(can1), "Vehicle_CanB.dbc": tuple(canb)}


def expected_signals() -> dict[str, tuple[tuple[int, str, int, int, str, bool, float], ...]]:
    """关键字段的起始位、长度、字节序、符号和缩放回归表。"""
    return {
        "Vehicle_Can1.dbc": (
            (0x186050F4, "BatteryVoltage", 7, 16, "big_endian", False, 0.1),
            (0x186050F4, "BatteryCurrent", 23, 16, "big_endian", True, 0.1),
            (0x186250F4, "FanSpeed", 48, 8, "little_endian", False, 100.0),
            (0x186950F4, "LastPrechargeSuccessTime", 15, 16, "big_endian", False, 1.0),
            (0x18A050F5, "ToolProtocolVersion", 4, 4, "little_endian", False, 1.0),
            (0x18A650F4, "ResponseDetail", 55, 16, "big_endian", False, 1.0),
        ),
        "Vehicle_CanB.dbc": (
            (0x4A0, "DischargeCurrentLimit", 0, 16, "little_endian", False, 0.1),
            (0x4A3, "LimitReason", 24, 16, "little_endian", False, 1.0),
            (0x4A4, "FinalDischargePowerLimit", 16, 16, "little_endian", False, 0.1),
            (0x4B0, "BatteryCurrent", 23, 16, "big_endian", True, 0.1),
            (0x512, "ResultValue", 16, 32, "little_endian", True, 1.0),
            (0x1806E5F4, "LegacyRequestVoltage", 7, 16, "big_endian", False, 0.1),
        ),
    }


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_dbc() -> None:
    required = expected_frames()
    required_signals = expected_signals()
    for path in DBC_FILES:
        if not path.is_file():
            fail(f"缺少正式 DBC：{path.relative_to(ROOT)}")
        database = cantools.database.load_file(path, strict=True)
        frame_ids: set[int] = set()
        for message in database.messages:
            if message.frame_id in frame_ids:
                fail(f"{path.name} 存在重复 CAN ID 0x{message.frame_id:X}")
            frame_ids.add(message.frame_id)
        expected = required.get(path.name, ())
        for frame_id, dlc, is_extended in expected:
            try:
                message = database.get_message_by_frame_id(frame_id)
            except KeyError:
                fail(f"{path.name} 缺少实现帧 0x{frame_id:X}")
            if message.length != dlc or message.is_extended_frame != is_extended:
                frame_type = "扩展" if is_extended else "标准"
                fail(
                    f"{path.name} 帧 0x{frame_id:X} 与实现不符："
                    f"需要 DLC={dlc}/{frame_type}，实际 DLC={message.length}/"
                    f"{'扩展' if message.is_extended_frame else '标准'}"
                )
        for frame_id, signal_name, start, length, byte_order, is_signed, scale in required_signals.get(path.name, ()):
            message = database.get_message_by_frame_id(frame_id)
            try:
                dbc_signal = message.get_signal_by_name(signal_name)
            except KeyError:
                fail(f"{path.name} 帧 0x{frame_id:X} 缺少字段 {signal_name}")
            actual = (
                dbc_signal.start,
                dbc_signal.length,
                dbc_signal.byte_order,
                dbc_signal.is_signed,
                float(dbc_signal.scale),
            )
            expected_signal = (start, length, byte_order, is_signed, scale)
            if actual != expected_signal:
                fail(
                    f"{path.name} 帧 0x{frame_id:X} 字段 {signal_name} 编码不符："
                    f"需要 {expected_signal}，实际 {actual}"
                )
        print(f"OK: {path.relative_to(ROOT)}，{len(database.messages)} 条报文")


def validate_proto() -> None:
    if not PROTO_FILE.is_file() or not OPTIONS_FILE.is_file():
        fail("缺少正式 Proto 或 Nanopb options")

    with tempfile.TemporaryDirectory(prefix="vehicle-interfaces-") as output_dir:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={PROTO_FILE.parent}",
                f"--descriptor_set_out={Path(output_dir) / 'interfaces.pb'}",
                str(PROTO_FILE),
            ],
            check=False,
        )
        if result.returncode != 0:
            fail("Proto 编译失败")

    option_pattern = re.compile(r"^[A-Za-z_][\w.]*(?:\[[^]]+\])?\s+\w+\s*:\s*\S+")
    for number, raw_line in enumerate(OPTIONS_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if line and not line.startswith("#") and not option_pattern.fullmatch(line):
            fail(f"{OPTIONS_FILE.relative_to(ROOT)}:{number} 格式无法识别")
    print("OK: Proto 与 Nanopb options")


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            clean_target = target.split("#", 1)[0].strip()
            if not clean_target or "://" in clean_target or clean_target.startswith("mailto:"):
                continue
            if not (path.parent / clean_target).resolve().exists():
                fail(f"{path.relative_to(ROOT)} 中链接不存在：{target}")
    print("OK: Markdown 相对链接")


def validate_public_boundary() -> None:
    forbidden_suffixes = {".key", ".p12", ".pfx", ".pem"}
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
    ipv4_pattern = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
    scan_suffixes = {".md", ".yml", ".yaml", ".proto", ".options", ".json", ".toml"}

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in forbidden_suffixes or path.name == ".env":
            fail(f"公开仓库中不允许提交凭据文件：{path.relative_to(ROOT)}")
        if path.suffix.lower() not in scan_suffixes:
            continue
        text = path.read_text(encoding="utf-8")
        if private_key_marker in text:
            fail(f"发现私钥内容：{path.relative_to(ROOT)}")
        if ipv4_pattern.search(text):
            fail(f"发现可能的生产 IPv4 地址：{path.relative_to(ROOT)}")
    print("OK: 未发现凭据文件、私钥或 IPv4 地址")


def main() -> None:
    validate_dbc()
    validate_proto()
    validate_markdown_links()
    validate_public_boundary()
    print("所有接口检查通过")


if __name__ == "__main__":
    main()
