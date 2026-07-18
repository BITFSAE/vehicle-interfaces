# CAN ID 分配

本文用于快速查找报文归属和审核新 ID。具体信号布局以 `can/` 下的三个正式 DBC 为准；不要只根据本表编写解析代码。

## CANA

CANA 当前主要承载四个 AMK 电机控制器的 Setpoint 与 Actual Value。完整 ID 和字段见 [Vehicle_CanA.dbc](../can/Vehicle_CanA.dbc)。

| ID 范围 | 方向 | 用途 |
| --- | --- | --- |
| `0x184..0x189` | ECU → AMK | 四轮 Setpoint；具体轮位并非连续排列，以 DBC 为准 |
| `0x283..0x292` | AMK → ECU | 四轮 ActualValue1..4；具体 ID 与轮位以 DBC 为准 |

## CANB

当前报文均为 11 位标准数据帧。

| ID | DBC 名称 | DLC | 发送节点 | 主要用途 |
| --- | --- | ---: | --- | --- |
| `0x050` | `IMU_Raw` | 8 | Display | IMU 原始分包 |
| `0x060..0x066` | `IMU_Time`..`IMU_Magnetic` | 2..6 | Display | IMU 时间、加速度、角速度、姿态和磁场 |
| `0x067..0x06A` | `GPS_Position`..`GPS_LapTiming` | 8 | Display | GPS 位置、运动、状态、里程和圈速 |
| `0x071..0x074` | `MLX90640_TireTemp_*` | 8 | DATA_COLLECTION_INTEGRAL | 四轮共 16 个轮胎温度点 |
| `0x301` | `GPS_Speed` | 2 | Display | GPS 地速，`0.1 km/h/bit` |
| `0x305` | `DataLogger` | 6 | ECU | 转角、油门开度、油压 |
| `0x310` | `DriveMode_Request` | 8 | Display | 驾驶模式请求 |
| `0x502` | `Debug2` | 8 | ECU | 四轮实际扭矩 |
| `0x503` | `Debug3` | 8 | ECU | 诊断号 1、2 |
| `0x504` | `Debug4` | 8 | ECU | 诊断号 3、4 |
| `0x505` | `Debug5` | 8 | ECU | 四轮实际转速 |
| `0x506` | `Debug6` | 8 | ECU | 四轮电机温度 |
| `0x507` | `Debug7` | 8 | ECU | 四轮逆变器温度 |
| `0x508` | `Debug8` | 8 | ECU | 四轮 IGBT 温度 |
| `0x509` | `Debug9` | 5 | ECU | 四轮状态位与模式 |
| `0x5A0` | `PDM_LowVoltageBus` | 8 | PDM | 低压总线电压、电流、功率、能量 |
| `0x5A1` | `PDM_LowVoltageBattery` | 8 | PDM | 低压电池电压、电流、功率、能量 |
| `0x5A2` | `FanController_Status` | 8 | FanController | 风扇转速和实际占空比 |
| `0x5A3` | `FanController_Diagnostic` | 8 | FanController | 故障、温度和目标占空比 |
| `0x5A4` | `FanController_Command` | 8 | ECU | 参数读写、模式和控制命令 |
| `0x5A5` | `FanController_CommandAck` | 8 | FanController | 命令确认和当前控制状态 |
| `0x5A6` | `FanController_CurveStatus` | 8 | FanController | 温控曲线参数回读 |
| `0x5A7` | `FanController_FailsafeStatus` | 8 | FanController | 失效策略、回退占空比和控制租约 |
| `0x700` | `SteeringPanel_0x700` | 8 | SteeringWheel | 记录、清错、驾驶模式和滑移等级 |
| `0x784` | `DriveMode_0x784` | 8 | SteeringWheel | 冗余驾驶模式报文 |

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

- 先在三个 DBC 和本表中检索，不凭记忆分配；
- 在 Issue 中写明总线、发送者、接收者、周期、DLC 和预计带宽；
- 同一功能的状态、命令、确认尽量放在连续区间，但不要为了连续而改动已发布 ID；
- 正式分配通过 PR 完成，口头约定和未合并分支不占用 ID；
- 跨总线使用相同 ID 不一定冲突，但必须明确网关是否转发。

## PDM 与 FanController 编码提示

- `0x5A0`、`0x5A1` 的 16 位量使用 DBC Motorola/大端定义；电压比例 `0.001 V/bit`，电流 `0.01 A/bit`，功率 `0.1 W/bit`，能量 `0.01 Wh/bit`。
- `0x5A2`、`0x5A3` 的多字节温度和转速按 DBC Motorola/大端定义。
- `0x5A4..0x5A7` 的命令及策略字段按 Intel/小端逐字节排列。
- 更详细的命令枚举、故障位和无效值应以 FanController 项目文档与 DBC 注释同步维护；未定义值不得自行解释。
