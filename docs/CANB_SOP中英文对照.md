# CANB SOP 中英文对照与命名规则

本文依据 `docs/CANB接口.md` 生成，配套文件为 `CANB_SOP_0x4A0_0x4A3_0x4A4.dbc`。正式源文件未被修改。

## 1. 通用规则

| 项目 | 规则 |
| --- | --- |
| 总线位率 | 500 kbit/s |
| 帧格式 | 经典 CAN 标准数据帧，不使用 CAN FD 或远程帧 |
| DLC | 三帧均为 8 |
| 字节序 | Intel 小端，DBC 表示为 `@1` |
| 数值类型 | 本接口字段均为无符号，DBC 表示为 `+` |
| 无效值 | 没有专用无效原始值；结合版本、计数、CRC、有效位和超时判断 |
| 协议版本 | 当前为 1 |

DBC 名称使用 ASCII `PascalCase`。缩写保留大写，例如 `BMS`、`ECU`、`SOP`、`CRC8`。`Charge*Limit` 同时表示充电和制动能量回收方向；`RegenAllowed` 专指允许制动能量回收。

## 2. 报文对照

| ID | 十进制 ID | DBC 报文名 | 中文名称 | 方向 | 周期或触发 |
| --- | ---: | --- | --- | --- | --- |
| `0x4A0` | 1184 | `BMS_SOPLimits` | BMS SOP 限值 | BMS → ECU | 非充电模式每 50 ms |
| `0x4A3` | 1187 | `BMS_SOPStatus` | BMS SOP 状态 | BMS → ECU | 紧跟同组 `0x4A0` |
| `0x4A4` | 1188 | `ECU_SOPAcknowledgement` | ECU SOP 确认 | ECU → BMS | ECU 周期发送或采用新限值后 |

## 3. 0x4A0 字段

| 字节 | DBC 信号名 | 中文名称 | 类型 | 比例/单位 | 范围 | 0 的含义 |
| --- | --- | --- | --- | --- | --- | --- |
| 0..1 | `DischargeCurrentLimit` | 放电电流上限 | `uint16` 小端 | 0.1 A/bit | 0..6553.5 A | 禁止放电方向动力 |
| 2..3 | `ChargeCurrentLimit` | 充电/回收电流上限 | `uint16` 小端 | 0.1 A/bit | 0..6553.5 A | 禁止充电/回收方向动力 |
| 4..5 | `DischargePowerLimit` | 放电功率上限 | `uint16` 小端 | 0.1 kW/bit | 0..6553.5 kW | 禁止放电方向动力 |
| 6..7 | `ChargePowerLimit` | 充电/回收功率上限 | `uint16` 小端 | 0.1 kW/bit | 0..6553.5 kW | 禁止充电/回收方向动力 |

## 4. 0x4A3 字段

| 位位置 | DBC 信号名 | 中文名称 | 范围或值 1 的含义 |
| --- | --- | --- | --- |
| Byte0 bit3..0 | `SOPSequence` | SOP 会话计数 | 0..15 循环，与同组 `0x4A0` 配对 |
| Byte0 bit7..4 | `SOPProtocolVersion` | SOP 协议版本 | 当前为 1 |
| Byte1 bit0 | `LimitsValid` | 限值有效 | 本组限值有效 |
| Byte1 bit1 | `DriveAllowed` | 允许驱动 | BMS 允许驱动 |
| Byte1 bit2 | `RegenAllowed` | 允许回收 | BMS 允许制动能量回收 |
| Byte1 bit3 | `OvercurrentLimitZero` | 过流限值归零 | 至少一个方向因过流归零 |
| Byte1 bit4 | `BMSFaultHold` | BMS 故障保持 | BMS 处于故障保持 |
| Byte1 bit5 | `SOPAckRequired` | 要求 SOP 确认 | 要求 ECU 发送 `0x4A4`，当前为 1 |
| Byte1 bit6 | `LimitsReduced` | 限值降低 | 本组限值降低或变为 0 |
| Byte1 bit7 | 未定义 | 保留 | 发送方置 0，接收方忽略 |
| Byte2 | `BatteryState` | BMS 状态 | 2 自检；3 待机；4 预充；5 高压接通；7 故障保持 |
| Byte3..4 | `LimitReason` | 限制原因 | `uint16` 小端位图，见下表 |
| Byte5 | `InputHealth` | 输入健康状态 | `uint8` 位图，见下表 |
| Byte6 bit1..0 | `InterventionLevel` | 干预等级 | 0 正常；1 降额；2 过流归零；3 故障或准备下高压 |
| Byte6 bit2 | `DischargeOvercurrentZero` | 放电过流归零 | 放电限值因过流归零 |
| Byte6 bit3 | `ChargeOvercurrentZero` | 回充过流归零 | 回充限值因过流归零 |
| Byte6 bit4 | `AckMissing` | 确认缺失 | 尚未收到新鲜 ECU 确认 |
| Byte6 bit5 | `AckFresh` | 确认新鲜 | ECU 确认在 500 ms 内 |
| Byte6 bit6 | `CurrentBelowClearThreshold` | 电流低于退出阈值 | 实测电流低于过流退出值 |
| Byte6 bit7 | 未定义 | 保留 | 发送方置 0，接收方忽略 |
| Byte7 | `SOPCRC8` | SOP CRC-8 | CRC-8/SAE-J1850 |

### LimitReason 位图

| Bit | 英文名称 | 中文含义 |
| ---: | --- | --- |
| 0 | `MinimumCellLimitsDischarge` | 最低单体限制放电 |
| 1 | `MaximumCellLimitsCharge` | 最高单体限制回充 |
| 2 | `HighTemperatureLimitsDischarge` | 高温限制放电 |
| 3 | `HighTemperatureLimitsCharge` | 高温限制回充 |
| 4 | `LowTemperatureLimitsCharge` | 低温限制回充 |
| 5 | `LowSOCLimitsDischarge` | 低 SOC 限制放电 |
| 6 | `HighSOCLimitsCharge` | 高 SOC 限制回充 |
| 7 | `ConfiguredCurrentOrPowerLimit` | 程序电流/功率上限 |
| 8 | `CellVoltageInvalid` | 单体电压无效 |
| 9 | `TemperatureInvalid` | 温度无效 |
| 10 | `U1Invalid` | U1 无效 |
| 11 | `SOCInvalid` | SOC 无效 |
| 12 | `IVTCurrentInvalid` | IVT 电流无效 |
| 13 | `BMSStateOrFaultBlocksDrive` | BMS 状态或故障禁止动力 |
| 14 | `DischargeOvercurrentZero` | 放电过流归零 |
| 15 | `ChargeOvercurrentZero` | 回充过流归零 |

### InputHealth 位图

| Bit | 英文名称 | 中文含义 |
| ---: | --- | --- |
| 0 | `CellFramesComplete` | 单体帧完整 |
| 1 | `CellExtremaValid` | 单体极值有效 |
| 2 | `TemperatureFramesComplete` | 温度帧完整 |
| 3 | `TemperatureExtremaValid` | 温度极值有效 |
| 4 | `U1Valid` | U1 有效 |
| 5 | `SOCValid` | SOC 有效 |
| 6 | `IVTCurrentValid` | IVT 电流有效 |
| 7 | `AllSOPInputsValid` | 全部 SOP 输入有效 |

## 5. 0x4A4 字段

| 位位置 | DBC 信号名 | 中文名称 | 比例/范围或值 1 的含义 |
| --- | --- | --- | --- |
| Byte0 bit3..0 | `AcceptedSOPSequence` | 已采用的 SOP 会话计数 | 0..15 |
| Byte0 bit7..4 | `SOPProtocolVersion` | SOP 协议版本 | 当前为 1 |
| Byte1 bit0 | `SOPChecksPassed` | SOP 检查通过 | 报文、版本、计数和 CRC 均通过 |
| Byte1 bit1 | `SOPAppliedToTorque` | SOP 已用于扭矩 | 已用于最终扭矩计算 |
| Byte1 bit2 | `PositiveTorqueZero` | 正扭矩归零 | 正扭矩已为 0 |
| Byte1 bit3 | `NegativeTorqueZero` | 负扭矩归零 | 负扭矩已为 0 |
| Byte1 bit4 | `DriveLimitedByBMS` | 驱动受 BMS 限制 | 驱动受 BMS SOP 限制 |
| Byte1 bit5 | `RegenLimitedByBMS` | 回收受 BMS 限制 | 回收受 BMS SOP 限制 |
| Byte1 bit6 | `ECUSOPTimeout` | ECU SOP 超时 | ECU 因 SOP 超时进入零扭矩 |
| Byte1 bit7 | `ECUFaultBlocksDrive` | ECU 故障禁止动力 | ECU 自身故障禁止动力 |
| Byte2..3 | `FinalDischargePowerLimit` | 最终放电功率上限 | 0.1 kW/bit，0..6553.5 kW |
| Byte4..5 | `FinalChargePowerLimit` | 最终充电/回收功率上限 | 0.1 kW/bit，0..6553.5 kW |
| Byte6 | `PrimaryLimitSource` | 主要限制来源 | 0..255；当前未定义枚举 |
| Byte7 | `SOPAckCRC8` | SOP 确认 CRC-8 | CRC-8/SAE-J1850 |

## 6. CRC 与兼容性

CRC-8/SAE-J1850 参数：多项式 `0x1D`，初值 `0xFF`，输入和输出不反射，结果异或 `0xFF`。

- `0x4A3` CRC 输入：`04 A0`、完整 `0x4A0` 8 字节、`04 A3`、`0x4A3` Byte0..6。
- `0x4A4` CRC 输入：`04 A4`、`0x4A4` Byte0..6。
- ID 字节高字节在前。

BMS 只在非充电模式发送 `0x4A0 + 0x4A3`，`0x4A4` 也只在非充电模式接受。BMS 接受最近一组以及最多落后 3 个计数的确认；确认超过 500 ms 未更新即过期。模式切换时会话计数从 0 开始并清除旧确认状态。

接收方必须同时检查协议版本、会话计数、CRC、有效位和报文新鲜度。修改 ID、DLC、位位置、字节序、比例或 CRC 覆盖范围属于不兼容接口变更。
