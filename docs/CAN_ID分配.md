# CAN ID 分配

本文只用于查找报文归属和审核新 ID。字段布局、字节序和缩放以 `can/` 下的正式 DBC 为准。

## CANA

CANA 当前主要承载四个 AMK 电机控制器的 Setpoint 与 Actual Value。完整 ID 和字段见 [Vehicle_CanA.dbc](../can/Vehicle_CanA.dbc)。

| ID 范围 | 方向 | 用途 |
| --- | --- | --- |
| `0x184..0x189` | ECU → AMK | 四轮 Setpoint；具体轮位并非连续排列，以 DBC 为准 |
| `0x283..0x292` | AMK → ECU | 四轮 ActualValue1..4；具体 ID 与轮位以 DBC 为准 |

## CAN1（BMS 内部总线）

详细字段见 [CAN1 接口](CAN1接口.md)，机器可读来源为 [Vehicle_Can1.dbc](../can/Vehicle_Can1.dbc)。

| ID 范围 | 帧类型 | 方向 | 用途 |
| --- | --- | --- | --- |
| `0x180050F3 + (n << 16)`，n=0..35 | 扩展 | 从控 → 主控 | 6 个从控的 138 串电压 |
| `0x184050F3 + (n << 16)`，n=0..5 | 扩展 | 从控 → 主控 | 6 个从控的 48 路温度 |
| `0x512..0x519` | 标准 | IVT_S → 主控 | 自有 IVT-S 电流、电压、温度、功率、电荷和能量 |
| `0x186050F4..0x187F50F4` | 扩展 | 主控 → 显示/工具 | BMS 状态、告警、均衡、IMD、SOP 镜像、固件身份和电池箱风扇详细状态 |
| `0x18A050F5` | 扩展 | 工具 → 主控 | 统一工具请求 |
| `0x18A450F4/0x18A650F4/0x18A750F4` | 扩展 | 主控 → 工具 | RTC 应答、统一应答和日志数据 |

## CANB

CANB 主要使用 11 位标准数据帧；Legacy 充电接口使用两个 29 位扩展 ID。

| ID | 帧类型 | 发送节点 | 主要用途 |
| --- | --- | --- | --- |
| `0x050`、`0x060..0x066` | 标准 | Display | IMU 原始包、时间、加速度、角速度、姿态和磁场 |
| `0x067..0x06A`、`0x301` | 标准 | Display | GPS 位置、速度、航向、信号、里程和圈速 |
| `0x071..0x074` | 标准 | DATA_COLLECTION_INTEGRAL | 四轮胎温 |
| `0x305` | 标准 | ECU | 转角、油门开度和油压 |
| `0x310` | 标准 | Display | 驾驶模式请求 |
| `0x201/0x202/0x204/0x205` | 标准 | Chroma | 充电电压、电流、保护和输出状态 |
| `0x290` | 标准 | BMS_Master | Chroma 设置命令 |
| `0x291` | 标准 | Chroma | Chroma 命令应答 |
| `0x4A0/0x4A3` | 标准 | BMS_Master | ECU SOP 限值、状态和 CRC |
| `0x4A4` | 标准 | ECU | ECU SOP 确认 |
| `0x4B0..0x4B2` | 标准 | BMS_Master | BMS 包状态、故障和告警等级 |
| `0x502..0x509` | 标准 | ECU | 扭矩、转速、温度、状态和诊断数据 |
| `0x521/0x522/0x526/0x528` | 标准 | Competition_IVT 或 FS_Datalogger | 赛会能量计大端结果帧 |
| `0x430` | 标准 | FS_Datalogger | FS 赛会能量计状态、电压和电流 |
| `0x5A0..0x5A1` | 标准 | PDM | 低压母线和低压电池支路（100 ms 周期） |
| `0x5A2..0x5A9/0x5AE` | 标准 | FanController、ECU | 整车风扇状态、诊断、命令、参数、功率仲裁、标定和两档保存限值 |
| `0x5AA..0x5AD` | 标准 | BMS_Master、工具 | 电池箱风扇状态、控制、应答和功率标定 |
| `0x700/0x784` | 标准 | SteeringWheel | 方向盘面板和冗余驾驶模式 |
| `0x1806E5F4` | 扩展 | BMS_Master | Legacy 充电请求 |
| `0x18FF50E5` | 扩展 | LegacyCharger | Legacy 充电反馈 |

Chroma 当前节点基准为 `0x200`，上述六个 ID 分别按 `+1/+2/+4/+5/+0x90/+0x91` 派生。改面板基准前须检查所有派生 ID；例如基准 `0x300` 会碰撞 `0x301` 和 `0x305`，当前不能使用。

## CANC

| ID | DBC 名称 | DLC | 发送节点 | 主要用途 |
| --- | --- | ---: | --- | --- |
| `0x0AB` | `VCU_MCU_Ctrl` | 7 | VCU | 驱动力与扭矩请求 |
| `0x125` | `ABS_Status` | 8 | WCBS | 车速及有效位 |
| `0x132` | `ESC_Status_0x132` | 2 | WCBS | 主缸压力与 ESC/TCS 状态 |
| `0x166` | `VCU_Status` | 8 | VCU | 驾驶模式与 EOL 偏置 |
| `0x17E` | `SAS_Sensor_0x17E` | 5 | VCU | 转角和转速 |
| `0x270` | `IBS_Info` | 5 | WCBS | 加速、制动踏板状态 |
| `0x301` | `CDC_Info` | 8 | SUM | CDC 模式、状态与四轮高度 |
| `0x302` | `CDC_IMUAccelerationSignals` | 6 | SUM | 三轴加速度及有效位 |
| `0x303` | `CDC_IMURotationSignals` | 7 | SUM | 横摆、俯仰、侧倾角速度及有效位 |
| `0x304` | `CDC_Curr` | 8 | SUM | 四轮压缩/回弹阀电流 |
| `0x522` | `VddmChas2NMFr` | 8 | VDDM | 网络管理 |
| `0x525` | `SumChas2NMFr` | 8 | SUM | 网络管理 |
| `0x614` | `SumToVddmChas2DiagResFrame` | 8 | SUM | 诊断响应 |
| `0x714` | `VddmToSumChas2DiagReqFrame` | 8 | VDDM | 定向诊断请求 |
| `0x7FF` | `VddmToAllFuncChas2DiagReqFrame` | 8 | VDDM | 功能寻址诊断请求 |

## 新 ID 分配规则

- 先在全部正式 DBC 和本表中检索占用情况。
- 在 Issue 中写明总线、发送者、接收者、周期、DLC 和预计带宽。
- 跨总线复用 ID 时，说明网关是否转发。
