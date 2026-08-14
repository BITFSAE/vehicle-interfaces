# SilverShark CANA/CANB 通信协议

本文档整理整车 CANA 与 CANB 两个通道的通信协议。协议来源以当前工程中的 DBC 文件为准：

- `Vehicle_CanA.dbc`
- `Vehicle_CanB.dbc`

说明：

- CAN ID 均为 11-bit 标准帧 ID。
- DBC 中 `@1` 表示 Intel/Little Endian 字节序。
- DBC 中 `+` 表示无符号信号，`-` 表示有符号信号。
- 物理值计算公式：`physical = raw * factor + offset`。
- AMK 电机编号：AMK1=RL 左后，AMK2=RR 右后，AMK3=FL 左前，AMK4=FR 右前。

## 1. 总线分工

| 总线 | DBC 文件 | 主要节点 | 用途 |
| --- | --- | --- | --- |
| CANA | `Vehicle_CanA.dbc` | VCU、AMKmotor_1 | 四轮 AMK 逆变器控制指令与反馈 |
| CANB | `Vehicle_CanB.dbc` | VCU/ECU、外部记录或调试节点 | 整车数据记录、AMK 状态调试与诊断转发 |

## 2. CANA 通信协议

### 2.1 CANA 报文总览

| CAN ID (Hex) | CAN ID (Dec) | DLC | 报文名 | 发送方 | 接收方 | 说明 |
| --- | ---: | ---: | --- | --- | --- | --- |
| 0x184 | 388 | 8 | `FR_AMKsetpoint` | ECU/VCU | AMKmotor_1 | 右前电机控制指令 |
| 0x185 | 389 | 8 | `FL_AMKsetpoint` | ECU/VCU | AMKmotor_1 | 左前电机控制指令 |
| 0x188 | 392 | 8 | `RL_AMKsetpoint` | ECU/VCU | AMKmotor_1 | 左后电机控制指令 |
| 0x189 | 393 | 8 | `RR_AMKsetpoint` | ECU/VCU | AMKmotor_1 | 右后电机控制指令 |
| 0x283 | 643 | 8 | `FR_ActualValue1` | AMKmotor_1 | ECU/VCU | 右前状态、转速、扭矩、电流 |
| 0x284 | 644 | 8 | `FL_ActualValue1` | AMKmotor_1 | ECU/VCU | 左前状态、转速、扭矩、电流 |
| 0x285 | 645 | 8 | `FR_ActualValue2` | AMKmotor_1 | ECU/VCU | 右前诊断信息 |
| 0x286 | 646 | 8 | `FL_ActualValue2` | AMKmotor_1 | ECU/VCU | 左前诊断信息 |
| 0x287 | 647 | 8 | `RR_ActualValue1` | AMKmotor_1 | ECU/VCU | 右后状态、转速、扭矩、电流 |
| 0x288 | 648 | 8 | `RL_ActualValue1` | AMKmotor_1 | ECU/VCU | 左后状态、转速、扭矩、电流 |
| 0x289 | 649 | 8 | `RR_ActualValue2` | AMKmotor_1 | ECU/VCU | 右后诊断信息 |
| 0x28A | 650 | 8 | `RL_ActualValue2` | AMKmotor_1 | ECU/VCU | 左后诊断信息 |
| 0x28B | 651 | 8 | `FR_ActualValue3` | AMKmotor_1 | ECU/VCU | 右前温度与母线电压 |
| 0x28C | 652 | 8 | `FL_ActualValue3` | AMKmotor_1 | ECU/VCU | 左前温度与母线电压 |
| 0x28D | 653 | 8 | `RR_ActualValue3` | AMKmotor_1 | ECU/VCU | 右后温度与母线电压 |
| 0x28E | 654 | 8 | `RL_ActualValue3` | AMKmotor_1 | ECU/VCU | 左后温度与母线电压 |
| 0x28F | 655 | 8 | `FR_ActualValue4` | AMKmotor_1 | ECU/VCU | 右前力矩电流、扭矩限制、计数器 |
| 0x290 | 656 | 8 | `FL_ActualValue4` | AMKmotor_1 | ECU/VCU | 左前力矩电流、扭矩限制、计数器 |
| 0x291 | 657 | 8 | `RR_ActualValue4` | AMKmotor_1 | ECU/VCU | 右后力矩电流、扭矩限制、计数器 |
| 0x292 | 658 | 8 | `RL_ActualValue4` | AMKmotor_1 | ECU/VCU | 左后力矩电流、扭矩限制、计数器 |

### 2.2 AMK Setpoint 控制指令

适用报文：`FR_AMKsetpoint`、`FL_AMKsetpoint`、`RL_AMKsetpoint`、`RR_AMKsetpoint`。四个报文结构相同。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `AMK_bInverterOn` | 8 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 逆变器开机请求 |
| `AMK_bDcOn` | 9 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 高压 DC 上电请求 |
| `AMK_bEnable` | 10 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 电机使能请求 |
| `AMK_bErrorReset` | 11 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 故障复位请求 |
| `AMK_TargetTorque` | 16 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 目标扭矩指令，DBC 原始系数为 1 |
| `AMK_TorqueLimitPositiv` | 32 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 正向扭矩限制 |
| `AMK_TorqueLimitNegativ` | 48 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 负向扭矩限制 |

### 2.3 AMK ActualValue1 状态反馈

适用报文：`FR_ActualValue1`、`FL_ActualValue1`、`RR_ActualValue1`、`RL_ActualValue1`。四个报文结构相同。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `AMK_bReserve` | 0 | 8 | Intel | uint | 1 | 0 | 0..255 | - | 保留字节 |
| `AMK_bSystemReady` | 8 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 系统就绪 |
| `AMK_bError` | 9 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 故障标志 |
| `AMK_bWarn` | 10 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 警告标志 |
| `AMK_bQuitDcOn` | 11 | 1 | Intel | uint | 1 | 0 | 0..1 | - | DC 上电确认 |
| `AMK_bDcOn` | 12 | 1 | Intel | uint | 1 | 0 | 0..1 | - | DC 已上电 |
| `AMK_bQuitInverterOn` | 13 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 逆变器开机确认 |
| `AMK_bInverterOn` | 14 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 逆变器已开机 |
| `AMK_bDerating` | 15 | 1 | Intel | uint | 1 | 0 | 0..1 | - | 降额标志 |
| `AMK_ActualVelocity` | 16 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 实际转速 |
| `AMK_ActualTorque` | 32 | 16 | Intel | int | 1 | 0 | -32768..32767 | 0.1%Mn | 实际扭矩 |
| `AMK_MagnetizingCurrent` | 48 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 励磁电流 |

### 2.4 AMK ActualValue2 诊断反馈

适用报文：`FR_ActualValue2`、`FL_ActualValue2`、`RR_ActualValue2`、`RL_ActualValue2`。四个报文结构相同。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `Diagnostic_number_1` | 0 | 32 | Intel | uint | 1 | 0 | 0..4294967295 | - | 诊断码 |
| `Error_info1` | 32 | 32 | Intel | uint | 1 | 0 | 0..4294967295 | - | 故障详细信息 |

### 2.5 AMK ActualValue3 温度与母线电压

适用报文：`FR_ActualValue3`、`FL_ActualValue3`、`RR_ActualValue3`、`RL_ActualValue3`。四个报文结构相同。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `Motor_temperature` | 0 | 16 | Intel | int | 0.1 | 0 | -3276.8..3276.7 | degC | 电机温度 |
| `Inverter_coldplate_temperature` | 16 | 16 | Intel | int | 0.1 | 0 | -3276.8..3276.7 | degC | 逆变器冷板温度 |
| `IGBT_temperature` | 32 | 16 | Intel | int | 0.1 | 0 | -3276.8..3276.7 | degC | IGBT 温度 |
| `DCbus_Voltage` | 48 | 16 | Intel | uint | 1 | 0 | 0..65535 | V | 直流母线电压 |

### 2.6 AMK ActualValue4 电流、限制与计数器

适用报文：`FR_ActualValue4`、`FL_ActualValue4`、`RR_ActualValue4`、`RL_ActualValue4`。四个报文结构相同。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `AMK_TorqueCurrent` | 0 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 力矩电流 |
| `AMK_TorqueLimitPositiv` | 16 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 正向扭矩限制反馈 |
| `AMK_TorqueLimitNegativ` | 32 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 负向扭矩限制反馈 |
| `Message_Counter` | 48 | 16 | Intel | uint | 1 | 0 | 0..65535 | - | 报文计数器 |

### 2.7 CANA 电机位置与 ID 对照

| 电机 | 位置 | Setpoint ID | ActualValue1 | ActualValue2 | ActualValue3 | ActualValue4 |
| --- | --- | --- | --- | --- | --- | --- |
| AMK1 | RL 左后 | 0x188 | 0x288 | 0x28A | 0x28E | 0x292 |
| AMK2 | RR 右后 | 0x189 | 0x287 | 0x289 | 0x28D | 0x291 |
| AMK3 | FL 左前 | 0x185 | 0x284 | 0x286 | 0x28C | 0x290 |
| AMK4 | FR 右前 | 0x184 | 0x283 | 0x285 | 0x28B | 0x28F |

## 3. CANB 通信协议

### 3.1 CANB 报文总览

| CAN ID (Hex) | CAN ID (Dec) | DLC | 报文名 | 发送方 | 说明 |
| --- | ---: | ---: | --- | --- | --- |
| 0x305 | 773 | 6 | `DataLogger` | ECU/VCU | 方向盘转角、油门开度、油压 |
| 0x502 | 1282 | 8 | `Debug2` | ECU/VCU | 四轮实际扭矩 |
| 0x503 | 1283 | 8 | `Debug3` | ECU/VCU | AMK1/AMK2 诊断码 |
| 0x504 | 1284 | 8 | `Debug4` | ECU/VCU | AMK3/AMK4 诊断码 |
| 0x505 | 1285 | 8 | `Debug5` | ECU/VCU | 四轮实际转速 |
| 0x506 | 1286 | 8 | `Debug6` | ECU/VCU | 四轮电机温度 |
| 0x507 | 1287 | 8 | `Debug7` | ECU/VCU | 四轮逆变器温度 |
| 0x508 | 1288 | 8 | `Debug8` | ECU/VCU | 四轮 IGBT 温度 |
| 0x509 | 1289 | 5 | `Debug9` | ECU/VCU | AMK 状态位、模式与逻辑状态 |

### 3.2 DataLogger

报文：`DataLogger`，ID `0x305`，DLC 6。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `SteeringWheelAngle` | 0 | 16 | Intel | int | 0.1 | 0 | -3276.8..3276.7 | deg | 方向盘转角 |
| `APS_OpenPct` | 16 | 16 | Intel | uint | 0.1 | 0 | 0..6553.5 | % | 油门开度 |
| `OilPressure_Kpa` | 32 | 16 | Intel | uint | 0.001 | 0 | 0..65.535 | Kpa | 油压 |

### 3.3 Debug2 四轮实际扭矩

报文：`Debug2`，ID `0x502`，DLC 8。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `RL_ActualTorque` | 0 | 16 | Intel | int | 1 | 0 | -32768..32767 | 0.1%Mn | 左后实际扭矩 |
| `RR_ActualTorque` | 16 | 16 | Intel | int | 1 | 0 | -32768..32767 | 0.1%Mn | 右后实际扭矩 |
| `FL_ActualTorque` | 32 | 16 | Intel | int | 1 | 0 | -32768..32767 | 0.1%Mn | 左前实际扭矩 |
| `FR_ActualTorque` | 48 | 16 | Intel | int | 1 | 0 | -32768..32767 | 0.1%Mn | 右前实际扭矩 |

### 3.4 Debug3/Debug4 诊断码

| 报文名 | CAN ID | DLC | 信号名 | 起始位 | 长度 | 类型 | 说明 |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| `Debug3` | 0x503 | 8 | `Diagnostic_number_1` | 0 | 32 | uint | AMK1 诊断码 |
| `Debug3` | 0x503 | 8 | `Diagnostic_number_2` | 32 | 32 | uint | AMK2 诊断码 |
| `Debug4` | 0x504 | 8 | `Diagnostic_number_3` | 0 | 32 | uint | AMK3 诊断码 |
| `Debug4` | 0x504 | 8 | `Diagnostic_number_4` | 32 | 32 | uint | AMK4 诊断码 |

### 3.5 Debug5 四轮实际转速

报文：`Debug5`，ID `0x505`，DLC 8。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 单位 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `RL_ActualVelocity` | 0 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 左后实际转速 |
| `RR_ActualVelocity` | 16 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 右后实际转速 |
| `FL_ActualVelocity` | 32 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 左前实际转速 |
| `FR_ActualVelocity` | 48 | 16 | Intel | int | 1 | 0 | -32768..32767 | - | 右前实际转速 |

### 3.6 Debug6/Debug7/Debug8 四轮温度

`Debug6`、`Debug7`、`Debug8` 的信号排布一致，均为 4 个 16-bit 有符号温度信号，Factor 为 0.1。

| 报文名 | CAN ID | 信号前缀 | 起始位排布 | 范围 | 单位 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `Debug6` | 0x506 | `*_Motor_temperature` | RL=0, RR=16, FL=32, FR=48 | -3276.8..3276.7 | degC | 四轮电机温度 |
| `Debug7` | 0x507 | `*_Inverter_temperature` | RL=0, RR=16, FL=32, FR=48 | -3276.8..3276.7 | degC | 四轮逆变器温度 |
| `Debug8` | 0x508 | `*_IGBT_temperature` | RL=0, RR=16, FL=32, FR=48 | -3276.8..3276.7 | degC | 四轮 IGBT 温度 |

展开后的信号名：

| 报文名 | 信号名 |
| --- | --- |
| `Debug6` | `RL_Motor_temperature`, `RR_Motor_temperature`, `FL_Motor_temperature`, `FR_Motor_temperature` |
| `Debug7` | `RL_Inverter_temperature`, `RR_Inverter_temperature`, `FL_Inverter_temperature`, `FR_Inverter_temperature` |
| `Debug8` | `RL_IGBT_temperature`, `RR_IGBT_temperature`, `FL_IGBT_temperature`, `FR_IGBT_temperature` |

### 3.7 Debug9 AMK 状态与模式

报文：`Debug9`，ID `0x509`，DLC 5。

| 信号名 | 起始位 | 长度 | 字节序 | 类型 | Factor | Offset | 范围 | 说明 |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- |
| `FR_AMK_bError` | 0 | 1 | Intel | uint | 1 | 0 | 0..1 | 右前故障 |
| `FL_AMK_bError` | 1 | 1 | Intel | uint | 1 | 0 | 0..1 | 左前故障 |
| `RR_AMK_bError` | 2 | 1 | Intel | uint | 1 | 0 | 0..1 | 右后故障 |
| `RL_AMK_bError` | 3 | 1 | Intel | uint | 1 | 0 | 0..1 | 左后故障 |
| `ModeFlag` | 4 | 4 | Intel | int | 1 | 0 | -8..7 | 当前模式标志 |
| `FR_AMK_bSystemReady` | 8 | 1 | Intel | uint | 1 | 0 | 0..1 | 右前系统就绪 |
| `FL_AMK_bSystemReady` | 9 | 1 | Intel | uint | 1 | 0 | 0..1 | 左前系统就绪 |
| `RR_AMK_bSystemReady` | 10 | 1 | Intel | uint | 1 | 0 | 0..1 | 右后系统就绪 |
| `RL_AMK_bSystemReady` | 11 | 1 | Intel | uint | 1 | 0 | 0..1 | 左后系统就绪 |
| `FR_AMK_bQuitDcOn` | 12 | 1 | Intel | uint | 1 | 0 | 0..1 | 右前 DC 上电确认 |
| `FL_AMK_bQuitDcOn` | 13 | 1 | Intel | uint | 1 | 0 | 0..1 | 左前 DC 上电确认 |
| `RR_AMK_bQuitDcOn` | 14 | 1 | Intel | uint | 1 | 0 | 0..1 | 右后 DC 上电确认 |
| `RL_AMK_bQuitDcOn` | 15 | 1 | Intel | uint | 1 | 0 | 0..1 | 左后 DC 上电确认 |
| `FR_AMK_bQuitInverterOn` | 16 | 1 | Intel | uint | 1 | 0 | 0..1 | 右前逆变器开机确认 |
| `FL_AMK_bQuitInverterOn` | 17 | 1 | Intel | uint | 1 | 0 | 0..1 | 左前逆变器开机确认 |
| `RR_AMK_bQuitInverterOn` | 18 | 1 | Intel | uint | 1 | 0 | 0..1 | 右后逆变器开机确认 |
| `RL_AMK_bQuitInverterOn` | 19 | 1 | Intel | uint | 1 | 0 | 0..1 | 左后逆变器开机确认 |
| `FR_AMK_bEnable` | 20 | 1 | Intel | uint | 1 | 0 | 0..1 | 右前使能状态 |
| `FL_AMK_bEnable` | 21 | 1 | Intel | uint | 1 | 0 | 0..1 | 左前使能状态 |
| `RR_AMK_bEnable` | 22 | 1 | Intel | uint | 1 | 0 | 0..1 | 右后使能状态 |
| `RL_AMK_bEnable` | 23 | 1 | Intel | uint | 1 | 0 | 0..1 | 左后使能状态 |
| `LogicState_RR` | 24 | 4 | Intel | uint | 1 | 0 | 0..15 | 右后逻辑状态 |
| `LogicState_RL` | 28 | 4 | Intel | uint | 1 | 0 | 0..15 | 左后逻辑状态 |
| `LogicState_FR` | 32 | 4 | Intel | uint | 1 | 0 | 0..15 | 右前逻辑状态 |
| `LogicState_FL` | 36 | 4 | Intel | uint | 1 | 0 | 0..15 | 左前逻辑状态 |

`ModeFlag` 取值：`-1` 默认模式（每个电机限功率 12.3 kW），`0` 直线（18.5 kW），`1` 高速避障（17.5 kW），`2` 八字绕环（17.5 kW），`3` 耐久（15 kW）。每次重新上低压后 ECU 车辆模式回到默认模式。

云端下发驾驶模式配置时，MCU 应在 CANB 上发送标准帧 `0x310`，小端 `bit0` 起始的命令值：`48` 切换直线，`49` 切换高速避障，`50` 切换八字绕环，`51` 切换耐久。

当前 `CAN2RS485` 下行链路为：MQTT `fsae/command` -> DTU 订阅透传 -> USART2/RS485 -> MCU -> CANB `0x310`。MCU 接受以下 payload：

| 目标模式 | CANB `0x310` DLC=1 `data[0]` | MQTT payload 可用写法 |
| --- | ---: | --- |
| 直线 | 48 | 二进制单字节 `0x30`、ASCII `0`、ASCII `48`、`straight` |
| 高速避障 | 49 | 二进制单字节 `0x31`、ASCII `1`、ASCII `49`、`autocross`、`avoidance` |
| 八字绕环 | 50 | 二进制单字节 `0x32`、ASCII `2`、ASCII `50`、`skidpad` |
| 耐久 | 51 | 二进制单字节 `0x33`、ASCII `3`、ASCII `51`、`endurance` |

调试串口：本板 USART1 `115200 8N1` 提供文本 CLI。常用命令：

| 命令 | 用途 |
| --- | --- |
| `help` | 显示命令列表 |
| `status` | 显示系统 tick、遥测帧计数、CAN1/CAN2 是否收到数据、当前 `ModeFlag` 与故障字 |
| `can` | 显示最近收到的 CAN 帧 |
| `ids` | 显示最近统计到的 CAN ID、接收次数和最近更新时间 |
| `cmd` | 显示最近一次 DTU 下行 payload、解析结果、`0x310` 发送结果 |
| `clear` | 清空调试统计 |

## 4. 使用注意

- CANA 是控制闭环中的关键总线，AMK setpoint 与 actual value 的轮位映射必须按 `AMK1=RL, AMK2=RR, AMK3=FL, AMK4=FR` 保持一致。
- CANB 当前 DBC 主要承载 VCU 对外调试和数据记录信息，不包含 AMK setpoint 控制指令。
- 文档中的周期未从 DBC 解析得到；若 R2018b 模型中 CAN 发送块配置了固定周期，应以模型块参数为准补充到本文件。
- DBC 注释区存在部分历史乱码，本文件只使用 DBC 报文、信号、位域、缩放和模型可识别命名进行整理。
