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
)
PROTO_FILE = ROOT / "telemetry/fsae_telemetry.proto"
OPTIONS_FILE = ROOT / "telemetry/fsae_telemetry.options"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_dbc() -> None:
    for path in DBC_FILES:
        if not path.is_file():
            fail(f"缺少正式 DBC：{path.relative_to(ROOT)}")
        database = cantools.database.load_file(path, strict=True)
        frame_ids: set[int] = set()
        for message in database.messages:
            if message.frame_id in frame_ids:
                fail(f"{path.name} 存在重复 CAN ID 0x{message.frame_id:X}")
            frame_ids.add(message.frame_id)
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
