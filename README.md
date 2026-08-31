# BITFSAE Vehicle Interfaces

本仓库集中维护 BITFSAE 整车 CAN 和遥测接口。DBC、Proto 和 Nanopb options 是机器可读的正式来源；Markdown 说明总线边界、兼容规则、维护流程和待确认事项。

各固件、HMI/遥测链路、服务器和分析项目应固定使用本仓库的 Release 或 Commit，并记录所用版本。

> 当前尚未发布首个稳定版本 `v1.0.0`。ECU 和其他 CANB 节点的最终确认见 [`docs/迁移与待确认项.md`](docs/迁移与待确认项.md) 和 [`docs/ECU_SOP实现确认.md`](docs/ECU_SOP实现确认.md)。
> **当前周期、触发条件和处理优先级都是暂定值，不代表最终接口参数。** 各节点结合实际模型、接收端需求和 CAN 容量给出最终值；如果现有值不合理，应提出修改方案，而不是沿用。

## 接口与文档

| 路径 | 内容 |
| --- | --- |
| `can/Vehicle_Can1.dbc` | BMS CAN1 |
| `can/Vehicle_CanA.dbc` | 整车 CANA |
| `can/Vehicle_CanB.dbc` | 整车 CANB |
| `can/Vehicle_CanC.dbc` | 整车 CANC |
| `telemetry/fsae_telemetry.proto` | 遥测 Protobuf 唯一源 |
| `telemetry/fsae_telemetry.options` | Nanopb 静态容量配置 |
| `archive/` | 已退出正式接口的历史参考资料，不得据此新增实现 |
| [`docs/CAN1接口.md`](docs/CAN1接口.md) | BMS 从控、自有 IVT-S、主控状态和工具协议 |
| [`docs/CANB接口.md`](docs/CANB接口.md) | CANB 全报文总表、BMS、ECU SOP、赛会能量计和充电接口 |
| [`docs/ECU_SOP实现确认.md`](docs/ECU_SOP实现确认.md) | ECU 最终 SOP 接收、限制、扭矩、周期和确认策略确认模板 |
| [`docs/CAN_ID分配.md`](docs/CAN_ID分配.md) | 各总线 ID 归属和用途索引 |
| [`docs/CAN与遥测对照.md`](docs/CAN与遥测对照.md) | 全链路 CAN 到遥测端到端映射与 Fallback 策略 |
| [`docs/Grafana监控指南.md`](docs/Grafana监控指南.md) | 云端 InfluxDB 全字段矩阵、InfluxQL 查询与仪表盘配置 |
| [`docs/迁移与待确认项.md`](docs/迁移与待确认项.md) | 尚未完成的接口确认、周期/优先级确认、v1.0.0 发布检查表 |
| [`docs/协作与维护方案.md`](docs/协作与维护方案.md) | 节点确认责任、权限、发布和交接规则 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 修改接口时的提交和验证要求 |

CAN1 连接 BMS 从控、自有 IVT-S、F405 主控和调试工具。CANB 承载整车调试、显示、PDM、FanController、ECU SOP、赛会能量计和充电机报文。具体 ID 和字段见对应 DBC 与接口文档。

## 当前状态

**已按代码确认：** BMS 相关接口（CAN1、CANB `0x4B0..0x4B2`、SOP `0x4A0/0x4A3`、自有 IVT-S、Chroma、Legacy）。

**待确认：** ECU 的 `0x4A4` 和 ECU 侧 SOP 策略、ECU `0x305/0x502..0x509`、Display/HMI/遥测 GPS/IMU、胎温 `0x071..0x074`、PDM、FanController、方向盘、赛会能量计。

**确认要求：** 各节点除提交 DBC 外，必须提供对应报文说明文档，明确字段、单位、比例、有效范围、周期、发送/接收节点和异常处理，并说明报文处理优先级是否合理、是否存在误触发风险。

## 使用和验证

使用方固定到已确认的版本，例如：

```bash
git checkout <release-or-commit>
```

首次在本机创建仓库内固定虚拟环境（`.venv/` 已由 `.gitignore` 排除）：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --requirement requirements-dev.txt
```

以后修改接口后直接复用：

```bash
.venv/bin/python tools/validate_interfaces.py
```

依赖版本由 `requirements-dev.txt` 固定；只有依赖文件变化或主动升级环境时才需要重新安装。

校验内容包括 DBC、Proto、Nanopb options、文档链接和公开仓库边界。

## 公开范围

本仓库只保存公开接口和脱敏示例。真实地址、账号、密码、Token、私钥、部署信息和来源授权不明确的厂家资料不得提交；详细要求见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 许可证

当前尚未确定对外授权方式。许可证和第三方资料授权确认前不发布首个稳定版本。
