# BITFSAE Vehicle Interfaces

本仓库集中维护 BITFSAE 整车 CAN 和遥测接口。DBC、Proto 和 Nanopb options 是机器可读的正式来源；Markdown 说明总线边界、兼容规则、维护流程和待确认事项。

各固件、上位机、服务器和分析项目应固定使用本仓库的 Release 或 Commit，并记录所用版本。

## 接口与文档

| 路径 | 内容 |
| --- | --- |
| `can/Vehicle_Can1.dbc` | BMS CAN1 |
| `can/Vehicle_CanA.dbc` | 整车 CANA |
| `can/Vehicle_CanB.dbc` | 整车 CANB |
| `can/Vehicle_CanC.dbc` | 整车 CANC |
| `telemetry/fsae_telemetry.proto` | 遥测 Protobuf 唯一源 |
| `telemetry/fsae_telemetry.options` | Nanopb 静态容量配置 |
| [`docs/CAN1接口.md`](docs/CAN1接口.md) | BMS 从控、主控状态和工具协议 |
| [`docs/CANB接口.md`](docs/CANB接口.md) | BMS、ECU SOP、IVT-S 和充电接口 |
| [`docs/CAN_ID分配.md`](docs/CAN_ID分配.md) | 各总线 ID 归属和用途索引 |
| [`docs/迁移与待确认项.md`](docs/迁移与待确认项.md) | 尚未完成的接口确认和实物验证 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 修改接口时的提交和验证要求 |
| [`docs/协作与维护方案.md`](docs/协作与维护方案.md) | 权限、发布和交接规则 |

CAN1 连接 BMS 从控、F405 主控和调试工具。IVT-S 位于 CANB；CANB 还承载整车调试、显示、PDM、FanController、ECU SOP 和充电机报文。具体 ID 和字段见对应 DBC 与接口文档。

## 使用和验证

使用方固定到已确认的版本，例如：

```bash
git checkout <release-or-commit>
```

修改接口后运行：

```bash
python3 tools/validate_interfaces.py
```

校验内容包括 DBC、Proto、Nanopb options、文档链接和公开仓库边界。

## 公开范围

本仓库只保存公开接口和脱敏示例。真实地址、账号、密码、Token、私钥、部署信息和来源授权不明确的厂家资料不得提交；详细要求见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 许可证

当前尚未确定对外授权方式。许可证和第三方资料授权确认前不发布首个稳定版本。
