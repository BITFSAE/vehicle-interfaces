#!/usr/bin/env python3
"""校验正式 DBC、Proto、Nanopb 配置、文档链接和公开仓库边界。"""

from __future__ import annotations

import re
import shutil
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

CANB_DOC = ROOT / "docs/CANB接口.md"
FAN_NODE_DBC = ROOT.parent / "FanController" / "Doc" / "FanController_CANB.dbc"
CANB_CONFIRMED_IDS = (
    "0x401/0x402/0x404/0x405", "0x490", "0x491",
    "0x4A0", "0x4A3", "0x4B0", "0x4B1", "0x4B2", "0x512..0x519",
    "0x1806E5F4", "0x18FF50E5",
)


def repository_files() -> tuple[Path, ...]:
    """返回 Git 已跟踪及未忽略的未跟踪文件，排除 .venv/build 等本地状态。"""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("无法枚举 Git 仓库文件")
    return tuple(ROOT / item for item in result.stdout.split("\0") if item)


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
        (0x430, 6, False), (0x521, 6, False), (0x522, 6, False),
        (0x526, 6, False), (0x528, 6, False),
        (0x71, 8, False), (0x72, 8, False), (0x73, 8, False), (0x74, 8, False),
        (0x5A0, 8, False), (0x5A1, 8, False),
        (0x5A2, 8, False), (0x5A3, 8, False), (0x5A5, 8, False),
        (0x5A6, 8, False), (0x5A7, 8, False),
        (0x5A8, 8, False), (0x5A9, 8, False),
        (0x1806E5F4, 5, True), (0x18FF50E5, 8, True),
    ]
    cana: list[tuple[int, int, bool]] = [
        *((0x184 + index, 8, False) for index in (0, 1, 4, 5)),
        *((0x283 + index, 8, False) for index in range(16)),
    ]
    canc: list[tuple[int, int, bool]] = [
        (0x125, 8, False), (0x132, 2, False), (0x166, 8, False), (0x270, 5, False),
    ]
    return {
        "Vehicle_Can1.dbc": tuple(can1),
        "Vehicle_CanB.dbc": tuple(canb),
        "Vehicle_CanA.dbc": tuple(cana),
        "Vehicle_CanC.dbc": tuple(canc),
    }


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
            (0x186850F4, "IMDDuty", 23, 16, "big_endian", False, 0.1),
            (0x186850F4, "IMDResistance", 39, 16, "big_endian", False, 1.0),
            (0x186850F4, "IMDFrequency", 55, 16, "big_endian", False, 0.01),
            (0x186950F4, "LastPrechargeResult", 2, 2, "little_endian", False, 1.0),
            (0x186950F4, "LastPrechargeSuccessTime", 15, 16, "big_endian", False, 1.0),
            (0x186A50F4, "DischargeCurrentLimit", 7, 16, "big_endian", False, 0.1),
            (0x186A50F4, "DischargePowerLimit", 39, 16, "big_endian", False, 0.1),
        ),
        "Vehicle_CanB.dbc": (
            (0x4A0, "DischargeCurrentLimit", 0, 16, "little_endian", False, 0.1),
            (0x4A0, "DischargePowerLimit", 32, 16, "little_endian", False, 0.1),
            (0x4A3, "LimitsValid", 8, 1, "little_endian", False, 1.0),
            (0x4A3, "BatteryState", 16, 8, "little_endian", False, 1.0),
            (0x4A4, "AcceptedSOPSequence", 0, 4, "little_endian", False, 1.0),
            (0x4A4, "SOPAppliedToTorque", 9, 1, "little_endian", False, 1.0),
            (0x401, "ChromaVoltage", 24, 32, "little_endian", False, 1.0),
            (0x402, "ChromaCurrent", 24, 32, "little_endian", False, 1.0),
            (0x71, "TireTemp01_Integer", 0, 8, "little_endian", False, 1.0),
            (0x71, "TireTemp01_Fraction", 8, 8, "little_endian", False, 0.01),
            (0x5A0, "BusVoltage", 7, 16, "big_endian", True, 0.001),
            (0x5A0, "BusPower", 39, 16, "big_endian", False, 0.1),
            (0x5A1, "BatteryVoltage", 7, 16, "big_endian", True, 0.001),
            (0x5A1, "BatteryPower", 39, 16, "big_endian", False, 0.1),
            (0x5A2, "Fan1_RPM", 7, 16, "big_endian", False, 1.0),
            (0x5A2, "Fan_PWM1_Duty", 55, 8, "big_endian", False, 1.0),
            (0x5A3, "Fan_Faults", 7, 8, "big_endian", False, 1.0),
            (0x5A3, "Fan_PWM1_Target", 55, 8, "big_endian", False, 1.0),
            (0x5A5, "AckPWM1Actual", 32, 8, "little_endian", False, 1.0),
            (0x5A6, "FanTempOn", 8, 8, "little_endian", False, 1.0),
            (0x5A7, "FanFailsafeStrategy", 0, 8, "little_endian", False, 1.0),
            (0x5A8, "PowerSupplyState", 0, 4, "little_endian", False, 1.0),
            (0x5A9, "CalibState", 0, 4, "little_endian", False, 1.0),
            (0x5A6, "FanTempCritical", 40, 8, "little_endian", False, 1.0),
            (0x5A6, "FanStartDuty", 48, 8, "little_endian", False, 1.0),
            (0x5A6, "FanCurveChannel", 56, 8, "little_endian", False, 1.0),
            (0x5A7, "FanProtocolVersion", 56, 8, "little_endian", False, 1.0),
            (0x5A8, "PowerLimitReason", 4, 4, "little_endian", False, 1.0),
            (0x5A8, "ThermalRequest1_Duty", 8, 8, "little_endian", False, 1.0),
            (0x5A8, "ThermalRequest2_Duty", 16, 8, "little_endian", False, 1.0),
            (0x5A8, "PowerLimitedTarget1_Duty", 24, 8, "little_endian", False, 1.0),
            (0x5A8, "PowerLimitedTarget2_Duty", 32, 8, "little_endian", False, 1.0),
            (0x5A8, "CurrentBudget", 40, 8, "little_endian", False, 0.1),
            (0x5A8, "PredictedCurrent", 48, 16, "little_endian", False, 0.1),
            (0x5A9, "CalibAbortReason", 4, 4, "little_endian", False, 1.0),
            (0x5A9, "CalibStep", 8, 8, "little_endian", False, 1.0),
            (0x5A9, "CalibPWM1Target", 16, 8, "little_endian", False, 1.0),
            (0x5A9, "CalibPWM2Target", 24, 8, "little_endian", False, 1.0),
            (0x5A9, "CalibLeaseRemaining", 32, 8, "little_endian", False, 1.0),
            (0x5A9, "CalibParamVersion", 40, 8, "little_endian", False, 1.0),
            (0x5A9, "CalibFlags", 48, 16, "little_endian", False, 1.0),
            (0x4B0, "BatteryCurrent", 23, 16, "big_endian", True, 0.1),
            (0x512, "ResultValue", 16, 32, "little_endian", True, 1.0),
            (0x521, "ResultValue", 23, 32, "big_endian", True, 1.0),
            (0x522, "ResultValue", 23, 32, "big_endian", True, 1.0),
            (0x1806E5F4, "LegacyRequestVoltage", 7, 16, "big_endian", False, 0.1),
        ),
    }


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_canb_confirmation_status() -> None:
    """检查 CANB 正式文档的报文总表是否记录确认状态，并允许以后增加待确认组。"""
    if not CANB_DOC.is_file():
        fail(f"缺少 CANB 接口文档：{CANB_DOC.relative_to(ROOT)}")
    row = re.compile(
        r"^\| `([^`]+)` .*\| (BMS 已确认|ECU 待确认|节点待确认|赛会待确认) \|$"
    )
    seen: set[str] = set()
    pending: set[str] = set()
    for line in CANB_DOC.read_text(encoding="utf-8").splitlines():
        match = row.match(line)
        if not match:
            continue
        identifier, status = match.group(1), match.group(2)
        seen.add(identifier)
        if status != "BMS 已确认":
            pending.add(identifier)
    for identifier in CANB_CONFIRMED_IDS:
        if identifier not in seen:
            fail(f"CANB 接口文档缺少已确认报文行：{identifier}")
    print(f"OK: CANB 确认状态表，{len(seen)} 行，待确认 {len(pending)} 组")
    return pending


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


def validate_fan_enum_sync() -> None:
    """核对中央 DBC 与 FanController 节点 DBC 的关键枚举值。"""
    if not FAN_NODE_DBC.is_file():
        fail(f"缺少 FanController 节点 DBC：{FAN_NODE_DBC.relative_to(ROOT.parent)}")
    central = (ROOT / "can/Vehicle_CanB.dbc").read_text(encoding="utf-8")
    node = FAN_NODE_DBC.read_text(encoding="utf-8")
    required_lines = (
        'VAL_ 1444 CommandOpcode 1 "SetControl" 2 "SetCurveCH1" '
        '3 "SetFailsafe" 4 "RestoreDefaults" 5 "Query" 6 "SetCurveCH2" 8 "SetCalib";',
        'VAL_ 1445 AckResult 0 "OK" 1 "BadCRC" 2 "BadLength" 3 "BadValue" '
        '4 "Unsupported" 5 "LeaseExpired" 6 "SafetyAbort";',
        'VAL_ 1448 PowerLimitReason 0 "None" 1 "BusLimit" 2 "BatteryLimit" '
        '3 "PdmTimeout" 4 "TransitionHold" 5 "StallHold" 6 "OverTemperature" 7 "SafetyAbort";',
    )
    for line in required_lines:
        if line not in central:
            fail(f"中央 DBC 缺失枚举行：{line}")
        if line not in node:
            fail(f"FanController 节点 DBC 缺失枚举行：{line}")
    print("OK: FanController 命令/应答/限功率枚举中央与节点一致")


def validate_proto() -> None:
    if not PROTO_FILE.is_file() or not OPTIONS_FILE.is_file():
        fail("缺少正式 Proto 或 Nanopb options")

    with tempfile.TemporaryDirectory(prefix="vehicle-interfaces-") as output_dir:
        protoc = shutil.which("protoc")
        command = (
            [
                protoc,
                f"--proto_path={PROTO_FILE.parent}",
                f"--descriptor_set_out={Path(output_dir) / 'interfaces.pb'}",
                str(PROTO_FILE),
            ]
            if protoc
            else [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={PROTO_FILE.parent}",
                f"--descriptor_set_out={Path(output_dir) / 'interfaces.pb'}",
                str(PROTO_FILE),
            ]
        )
        result = subprocess.run(
            command,
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
    for path in repository_files():
        if path.suffix.lower() != ".md":
            continue
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
    production_markers = ("bitfsae.com", "/home/ubuntu/")
    scan_suffixes = {".md", ".yml", ".yaml", ".proto", ".options", ".json", ".toml"}

    for path in repository_files():
        if not path.is_file():
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
        if any(marker in text for marker in production_markers):
            fail(f"发现可能的生产部署地址：{path.relative_to(ROOT)}")
    print("OK: 未发现凭据文件、私钥或生产部署地址")


def main() -> None:
    validate_canb_confirmation_status()
    validate_dbc()
    validate_fan_enum_sync()
    validate_proto()
    validate_markdown_links()
    validate_public_boundary()
    print("所有接口检查通过")


if __name__ == "__main__":
    main()
