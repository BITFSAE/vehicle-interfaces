# CAN 与遥测全链路对照手册

> 本手册梳理整车 CAN（CAN1 / CANA / CANB / CANC）、车载网关 G473 固件、遥测协议 `fsae_telemetry.proto`、云端 Telegraf / InfluxDB 及 Grafana 监控的全链路对应关系、接入状态、多源冗余降级链与协议缺口。
>
> **事实来源与副本规范**：
> - 机器可读协议以 `vehicle-interfaces/telemetry/fsae_telemetry.proto` 及 `can/*.dbc` 为权威源。
> - 本文件在 `vehicle-interfaces/docs/` 与 `CANRS485_G473/REFERENCE/protobuf-master/` 保持**完全一致的双仓库同步副本**。

---

## 1. 架构设计与节点职责

### 1.1 节点职责划分（避免概念混淆）

```
                     ┌──────────────────┐
                     │     VCU / ECU    │ (整车控制器)
                     │  (CANB / CANC)   │ 驾驶模式 / 扭矩分配 / 踏板开度 / 电机使能 / R2D
                     └────────┬─────────┘
                              │ CANB
                              ▼
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│       BMS        ├──────►│     CANRS485_G473    ├──────►│     DTU 4G       │
│  (CAN1 / CANB)   │ CAN1  │  (全时多总线监听网关)  │ RS485 │ (MQTT 无线透传)   │
│ 138串压/48路温   │       └──────────────────────┘       └────────┬─────────┘
│ 继电器/IMD/SOC   │                                               │ MQTT
└──────────────────┘                                               ▼
┌──────────────────┐                                      ┌──────────────────┐
│   自有 IVT-S     ├──────► (CAN1)                        │    云端服务器     │
│   赛会能量计     ├──────► (CANB)                        │ Mosquitto Broker │
│   Display/IMU    ├──────► (CANB / CANC)                 │ Telegraf XPath   │
└──────────────────┘                                      │ InfluxDB 1.x     │
                                                          │ Grafana 可视化   │
                                                          └──────────────────┘
```

1. **VCU 即 ECU（整车控制器）**：
   - 负责整车驾驶模式、油门/刹车踏板行程解析、四轮扭矩分配、AMK 电机使能与整车就绪（Ready-to-Drive）控制。
   - 在 CANB 上标识为 `ECU` 节点（发送 `Debug2~9` 调试帧与 `0x305 DataLogger`），在 CANC 上标识为 `VCU` 节点（发送 `0x166 VCU_Status`、`0x171 VCU_MCU_Ctrl` 等）。
2. **BMS（电池管理系统）**：
   - 负责 138 串单体电压与 48 路温度采样、高压继电器与预充控制、绝缘检测（IMD）、充放电保护与 SOC 计算。
   - 主控 F405 发送 CAN1 扩展帧，并在 CANB 冗余广播 `0x4B0`（包状态）、`0x4B1`（故障汇总）、`0x4B2`（告警等级）。
3. **历史遗留代填说明**：
   - G473 固件曾因历史原因用 BMS 的 `battery_state`（来自 CAN1/CANB 包状态 `0x186050F4`/`0x4B0`，故障/告警帧 `0x187650F4`/`0x4B1` 也会刷新）代填 `TelemetryFrame.vcu_status`，并由 `vcu_status == 5` 派生 `ready_to_drive`；现已停止代填（无源不填），BMS 状态改由 `bms_telemetry` 承载，待 VCU 源接入后恢复。
   - 兼容过渡已结束：BMS 状态现由 `bms_telemetry.battery_state/battery_alarm_level` 承载，`vcu_status` 待 CANC `0x166 VCU_Status` 或 CANB ECU 状态帧接入后恢复。

---

## 2. 全链路端到端数据总表 (Master Matrix)

下表记录整车每个遥测信号从 **CAN 报文 $\to$ Protobuf 字段 $\to$ InfluxDB 存储 $\to$ Grafana 可视化** 的全流程定义：

| 物理量 / 业务域 | CAN 来源 (ID / 节点 / 周期) | Protobuf 字段 (`TelemetryFrame.*`) | 固件取数逻辑 / Fallback 链 | InfluxDB Measurement & Field | 原始单位 $\to$ 存储 $\to$ 显示 | 接入状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **报文时间戳** | MCU SysTick (内部) | `timestamp_ms` (#1)<br>`header.timestamp_ms` (#26.1) | `HAL_GetTick()` | `telemetry.timestamp_ms` | ms | 已接入 |
| **报文序号** | G473 计数器 (内部) | `frame_id` (#2)<br>`header.seq` (#26.2) | 递增序列号 `++g_frame_counter` | `telemetry.seq` | 无符号整数 | 已接入 |
| **油门开度** | CANB `0x305` (ECU, 50ms) | `apps_position` (#3)<br>`vehicle_state.throttle_position` (#28.3) | `APS_OpenPct` (0.1%) $\div 10.0$ | `telemetry.apps_position` | 0.1% $\to$ % $\to$ `%` | 已接入 |
| **刹车油压** | CANB `0x305` (ECU, 50ms) | `brake_pressure` (#4) | `OilPressure_Kpa` (milli-kPa) $\div 1000.0$ | `telemetry.brake_pressure` | milli-kPa $\to$ kPa $\to$ `kPa` | 已接入 (语义为油压) |
| **转向角** | CANB `0x305` (ECU, 50ms) | `steering_angle` (#5) | `SteeringWheelAngle` (0.1 deg) $\div 10.0$ | `telemetry.steering_angle` | 0.1 deg $\to$ deg $\to$ `deg` | 已接入 |
| **高压总压** | CAN1 `0x513` (IVT-S)<br>CAN1 `0x186050F4` / CANB `0x4B0`<br>CAN1 `0x186750F4` (累加和)<br>CAN1 `0x180050F3+` (138串) | `hv_voltage` (#6)<br>`fast_telemetry.hv_voltage_dv` (#27.1) | **Fallback 链**：<br>1. IVT-S U1 (`0x513`)<br>2. BMS 包状态 (`0x186050F4/0x4B0`)<br>3. 累加和 (`0x186750F4`)<br>4. 138 串单体累加 | `telemetry.hv_voltage`<br>`telemetry.hv_voltage_dv` | mV / 0.1V $\to$ V / 0.1V $\to$ `V` | 已接入 (多源自适应) |
| **高压总流** | CAN1 `0x512` (IVT-S)<br>CANB `0x18FF50E5` (Legacy充电机)<br>CAN1 `0x186050F4` / CANB `0x4B0` | `hv_current` (#7)<br>`fast_telemetry.hv_current_ma` (#27.2) | **Fallback 链**：<br>1. IVT-S 电流 (`0x512`)<br>2. 充电反馈 (`0x18FF50E5`)<br>3. BMS 包状态 (`0x186050F4/0x4B0`) | `telemetry.hv_current`<br>`telemetry.hv_current_ma` | mA / 0.1A $\to$ A / mA $\to$ `A` | 已接入 (多源自适应) |
| **电池最高温度** | CAN1 `0x186250F4` (BMS 极值帧)<br>CAN1 `0x184050F3+` (48路温度数组) | `battery_temp_max` (#8)<br>`fast_telemetry.battery_temp_max_dc` (#27.3) | **Fallback 链**：<br>1. BMS 温度极值帧 (`0x186250F4`)<br>2. 48 路温度数组本地遍历计算 | `telemetry.battery_temp_max`<br>`telemetry.battery_temp_max_dc` | 0.1 °C $\to$ °C / 0.1°C $\to$ `°C` | 已接入 (含备用算法) |
| **故障字** | CAN1 `0x187650F4` (BMS)<br>CANB `0x4B1` (BMS 冗余) | `fault_code` (#9)<br>`battery_fault_code` (#25) | `App_FaultCompute()` 提取 32 位故障掩码 | `telemetry.battery_fault_code` | 32位位图 $\to$ 十六进制显示 | 已接入 (双源互备) |
| **左后电机转速 (旧)** | CANB `0x505` (Debug5, 10ms) | `motor_rpm` (#10) | 取 `Debug5` 中 RL 电机转速 (兼容旧表) | `telemetry` (保留) | rpm $\to$ `rpm` | 已接入 (兼容字段) |
| **左后电机温度 (旧)** | CANB `0x506` (Debug6, 10ms) | `motor_temp` (#11) | 取 `Debug6` 中 RL 电机温度 $\div 10.0$ | `telemetry` (保留) | 0.1 °C $\to$ °C $\to$ `°C` | 已接入 (兼容字段) |
| **左后控制器温度 (旧)** | CANB `0x507` (Debug7, 10ms) | `inverter_temp` (#12) | 取 `Debug7` 中 RL 控制器温度 $\div 10.0$ | `telemetry` (保留) | 0.1 °C $\to$ °C $\to$ `°C` | 已接入 (兼容字段) |
| **就绪驱动标志** | 暂无真实 ECU/VCU 源；候选 CANC `0x166` | `ready_to_drive` (#13) | 当前固定 0，禁止由 BMS 状态派生；接入 VCU 源后再填充 | `telemetry.ready_to_drive` | 0 / 1 标志位 | 未接入（等待 VCU 源） |
| **VCU 状态字段** | 暂无真实 ECU/VCU 源；候选 CANC `0x166` 或 CANB ECU 状态帧 | `vcu_status` (#14)<br>`vehicle_state.vcu_status` (#28.6) | 当前保持 0；BMS 状态只写入 `bms_telemetry.battery_state` | `telemetry.vcu_status` | VCU 枚举；当前 0=未知 | 未接入（等待 VCU 源） |
| **138 串单体电压** | CAN1 `0x180050F3 + (n << 16)` (36 帧) | `modules[].v01..v23` (#15) | 6 从控 $\times$ 23 串；`2101..5399 mV` 有效，`≤2100 mV`、`≥5400 mV`、`0xFFFF` 无效；任一电压帧无效时省略整个模组 | `bms_data.v_01` ~ `v_23` (Tag: `module_id`) | mV $\to$ `mV` (Bar chart / 压差) | 已接入 (2 Hz 上报) |
| **48 路采样温度** | CAN1 `0x184050F3 + (n << 16)` (6 帧) | `modules[].t1..t8` (#15) | 6 从控 $\times$ 8 路，原始值减 30 °C | `bms_data.t_1` ~ `t_8` (Tag: `module_id`) | 0.1 °C $\to$ 0.1°C $\to$ `°C` (/10) | 已接入 (2 Hz 上报) |
| **电池 SOC** | CAN1 `0x186050F4` / CANB `0x4B0` | `battery_soc` (#16) | `BatterySOC` (0..100%)，结合有效位使用 | `telemetry.battery_soc` | % $\to$ `%` | 已接入 (双源互备) |
| **单体极值及编号** | CAN1 `0x186150F4` (单体极值帧)<br>或 138 串单体本地遍历 | `max_cell_voltage` (#17)<br>`min_cell_voltage` (#18)<br>`max_cell_voltage_no` (#19)<br>`min_cell_voltage_no` (#20) | 优先解码 `0x186150F4`；无数据时本地遍历 138 串数组计算 | `telemetry.max_cell_voltage`<br>`telemetry.min_cell_voltage`<br>`telemetry.max_cell_voltage_no`<br>`telemetry.min_cell_voltage_no` | mV / 编号 (1..138) | 已接入 (含备用算法) |
| **温度极值及编号** | CAN1 `0x186250F4` (温度极值帧)<br>或 48 路温度本地遍历 | `max_temp` (#21)<br>`min_temp` (#22)<br>`max_temp_no` (#23)<br>`min_temp_no` (#24) | 优先解码 `0x186250F4`；无数据时本地遍历 48 路数组计算 | `telemetry.max_temp`<br>`telemetry.min_temp`<br>`telemetry.max_temp_no`<br>`telemetry.min_temp_no` | 0.1 °C / 编号 (1..48) $\to$ `°C` (/10) | 已接入 (含备用算法) |
| **车速** | CANB `0x301` (Display, 50ms) | `fast_telemetry.speed_kmh` (#27.5)<br>`vehicle_state.speed_kmh` (#28.1)<br>`motion.gps_speed_kmh` (#33.1) | `GroundSpeed` (0.1 km/h) 四舍五入为整数 km/h | `telemetry.gps_speed_kmh` | 0.1 km/h $\to$ km/h $\to$ `km/h` | 已接入 (三处同值) |
| **驾驶模式** | CANB `0x509` (ECU ModeFlag) | `driving_mode` (#27.4 / #28.2) | `ModeFlag` 映射为 `fsae_DrivingMode` 枚举 | `telemetry.vehicle_mode` | 枚举 (1默认/2直线/3避障/4八字/5耐久) | 已接入 |
| **四轮电机扭矩** | CANB `0x502` (Debug2, 10ms) | `vehicle_state.motors[].torque_nm` (#28.7) | 四轮实际扭矩原始值 (0.1%Mn) | `motor_state.torque_nm` (Tag: `position`) | 0.1%Mn $\to$ `Nm` ($\times 9.8 / 1000$) | 已接入 |
| **四轮电机转速** | CANB `0x505` (Debug5, 10ms) | `vehicle_state.motors[].rpm` (#28.7) | 四轮电机实际转速 | `motor_state.rpm` (Tag: `position`) | rpm $\to$ `rpm` | 已接入 |
| **四轮电机温度** | CANB `0x506` (Debug6, 10ms) | `vehicle_state.motors[].motor_temp_dc` | 四轮电机温度 (0.1 °C) | `motor_state.motor_temp_dc` | 0.1 °C $\to$ `°C` (/10) | 已接入 |
| **四轮逆变器温度** | CANB `0x507` (Debug7, 10ms) | `vehicle_state.motors[].inverter_temp_dc` | 四轮控制器冷板温度 (0.1 °C) | `motor_state.inverter_temp_dc` | 0.1 °C $\to$ `°C` (/10) | 已接入 |
| **四轮 IGBT 温度** | CANB `0x508` (Debug8, 10ms) | `vehicle_state.motors[].igbt_temp_dc` | 四轮 IGBT 结温 (0.1 °C) | `motor_state.igbt_temp_dc` | 0.1 °C $\to$ `°C` (/10) | 已接入 |
| **四轮 AMK 诊断码** | CANB `0x503/0x504` (Debug3/4) | `vehicle_state.motors[].diagnostic_number`<br>`vehicle_state.motors[].motor_error` | 四轮 AMK 32 位故障诊断字 | `motor_state.diagnostic_number`<br>`motor_state.motor_error` | 十六进制诊断码 | 已接入 |
| **四轮使能逻辑状态** | CANB `0x509` (Debug9) | `vehicle_state.motors[].logic_state` | 四轮 `LogicState` (0..15) | `motor_state.logic_state` | 0..15 状态位 | 已接入 |
| **自有 IVT-S 数据** | CAN1 `0x512/0x513/0x514/0x517/0x519` | `ivt_telemetry.*` (#31) | 小端解码电流(mA)、U1(mV)、U2(mV)、功率(W)、能量(Wh) 及各通道状态字 | `telemetry.ivt_*` | mA, mV, W, Wh 及状态掩码 | 已完全接入 (5 通道) |
| **赛会能量计数据** | CANB `0x521/0x522/0x526/0x528`<br>CANB `0x430` (FS 状态) | `energy_meter.*` (#32) | 大端解码或 FS 格式识别，记录 source (1=IVT, 2=FS)、电流、电压、功率、Wh、MsgCnt | `telemetry.energy_meter_*` | mA, mV, W, Wh 及计数器 | 已接入 (赛会专用) |
| **IMU 三轴加速度** | CANB `0x061` (IMU_Accel, 源自 `0x050`) | `motion.accel_x/y/z_g` (#33.2~4) | 小端解码 raw $\times 0.00048828125\text{ g}$ | `telemetry.accel_x/y/z_g` | g $\to$ `g` | 已接入 |
| **IMU 角速度与横摆角** | CANB `0x062/0x065` (源自 `0x050`) | `motion.yaw_rate_dps` (#33.5)<br>`motion.yaw_deg` (#33.6) | 陀螺仪 Z 轴 (raw $\times 0.0610352$)、横摆角 (raw $\times 0.005493$) | `telemetry.yaw_rate_dps`<br>`telemetry.yaw_deg` | deg/s, deg | 已接入 |
| **BMS 活动告警明细** | 故障字：CAN1 `0x187650F4` / CANB `0x4B1`<br>等级：CAN1 `0x187850F4` / CANB `0x4B2` | `battery_fault_code` (#25)<br>`alarms[]` (#30) | 故障字是权威活动位图；按置位 bit 展开最多 32 条。公共接口约定 `alarm_id=bit 0..31`，等级 1 映射 `FATAL`，等级 2 映射 `WARNING`。等级明细超过 3 s 未更新时，当前 G473 兼容路径改发 `alarm_id=0x186050F4` 的包级摘要；该 ID 超出公共接口约定，待统一处理 | `telemetry.battery_fault_code`<br>`alarm_state.alarm_id/severity/alarm_name/message` | 32 位位图 + 告警名称 | 已接入；摘要 ID 待统一 |

---

## 3. 逐总线 CAN 报文接入与解析详表

### 3.1 CAN1（BMS 内部总线，500 kbit/s）

- **机器可读来源**：`vehicle-interfaces/can/Vehicle_Can1.dbc`。从控、主控和工具报文为 29 位扩展帧；自有 IVT-S `0x512..0x519` 为 11 位标准帧。

| CAN ID | 帧名 | 周期 | 接入状态 | 字段说明与固件处理 |
| :--- | :--- | :--- | :--- | :--- |
| `0x180050F3 + (n << 16)` (n=0..35) | 从控单体电压帧 | 周期 | **已接入** | 6 个从控模块各 6 帧，共 138 串电芯电压（mV，小端 uint16）。`2101..5399 mV` 按原值上报；`≤2100 mV`、`≥5400 mV`、`0xFFFF` 使当前电压帧无效，任一帧无效时该模组不进入 `modules[]`。 |
| `0x184050F3 + (n << 16)` (n=0..5) | 从控温度采样帧 | 周期 | **已接入** | 6 个从控模块各 1 帧，共 48 路温度。原始值减 30 得到摄氏度 (0.1 °C 存储，0xFF 无效)。编码入 `modules[].t1..t8`。 |
| `0x512` | IVT 电流 | 周期 | **已接入** | 自有 IVT-S 电流 (mA, 小端 int32) 及状态位。**`hv_current` 第一优先级主源**。CANB 同 ID 不解析。 |
| `0x513` | IVT U1 | 周期 | **已接入** | 自有 IVT-S 电池侧总压 (mV, 小端 int32) 及状态位。**`hv_voltage` 第一优先级主源**。 |
| `0x514` | IVT U2 | 周期 | **已接入** | 自有 IVT-S 逆变器侧 (Pre) 总压 (mV, 小端 int32)。写入 `ivt_telemetry.voltage_u2_mv`。 |
| `0x517` | IVT 功率 | 周期 | **已接入** | 自有 IVT-S 功率 (W, 小端 int32)。写入 `ivt_telemetry.power_w`。 |
| `0x519` | IVT 能量 | 周期 | **已接入** | 自有 IVT-S 积分能量 (Wh, 小端 int32)。写入 `ivt_telemetry.energy_wh`。 |
| `0x515/0x516/0x518` | IVT U3/温度/As | 周期 | **已解析/未上报** | MUX、消息计数、状态和数值已保存；当前公共 Proto 仅定义 I/U1/U2/W/Wh。 |
| `0x186050F4` | BMS 电池包状态 | 500 ms | **已接入** | 包总压、总流、SOC、有效位 (Byte5)、BMS 状态机与告警等级。作为 `battery_soc` 主源及 `hv_voltage`/`hv_current` 备用源，并刷新 `bms_telemetry.battery_state/battery_alarm_level`。 |
| `0x186150F4` | 单体电压极值 | 500 ms | **已接入** | 最高/最低单体电压 (大端 mV) 及单体编号 (0..137，上报时 +1 转为 1..138)。编码入 `max/min_cell_voltage(_no)`。 |
| `0x186250F4` | 温度极值与风扇 | 500 ms | **部分上报** | 温度极值和编号进入遥测；风扇目标占空比、转速和八个状态位可供本地工具使用，公共 Proto 暂无对应字段。 |
| `0x186E50F4` | 电池箱风扇详细状态 | 500 ms | 待网关接入 | 转速、实际占空比、当前上限、模式、供电来源和八个状态位已进入正式 DBC。 |
| `0x186350F4` | 继电器与工作状态 | 500 ms | **已接入** | 正/负/预充继电器命令、Byte1 bit4 充电状态和 bit3 反馈有效位进入 `bms_telemetry`；预充电压使用自有 IVT-S U2 上报。 |
| `0x186750F4` | 单体电压累加和 | 1 s | **已接入** | 138 串单体累加总压 (大端 0.1 V)。作为 `hv_voltage` 第 3 优先级备用源。 |
| `0x187650F4` | 故障汇总 | 500 ms/变发 | **部分上报** | 32 位故障字进入 `fault_code` 与 `battery_fault_code`；Byte5 状态、从控离线掩码和版本已解析到本地状态。 |
| `0x186850F4` | IMD 绝缘诊断 | 500 ms | **已接入** | 解析阻值 (kΩ)、PWM 占空比 (0.1%)、频率 (0.01 Hz)、频率分类、状态码与标志位，编码入 `imd_telemetry`。 |
| `0x186450F4..0x186650F4` | 三帧均衡位图 | 250 ms (条件) | 未接入 | 均衡开启时发送，Proto 无字段。 |
| `0x186950F4` | 高压请求与预充结果 | 500 ms | **已接入** | HV/充电请求、最近预充结果与成功/失败耗时，编码入 `bms_telemetry`；预充电压即自有 IVT-S U2，不重复上报。 |
| `0x186A50F4` | SOP 限值镜像 | 1 s | **已接入** | 充放电电流/功率上限镜像（大端，与 CANB `0x4A0` 冗余），编码入 `sop_limits`。 |
| `0x186B50F4` | 运行配置与充电机 | 1 s | 未接入 | 运维配置回读与充电机状态。 |
| `0x186C50F4/51F4` | 固件身份与构建日期 | 5 s | 未接入 | Git commit 与构建日期，运维类。 |
| `0x186D50F4` | IVT 诊断与 SOC 来源 | 1 s | 未接入 | IVT 诊断与零漂偏移量，运维类。 |
| `0x187850F4` | 32 项告警等级表 | 2 s/变发 | **已接入** | 32 项两位等级与故障字组合后展开到 `alarms[]`，与 CANB `0x4B2` 冗余。 |

---

### 3.2 CANB（整车主总线，500 kbit/s）

- **机器可读来源**：`vehicle-interfaces/can/Vehicle_CanB.dbc`。

| CAN ID | 帧名 | 发送节点 | 周期 | 接入状态 | 字段说明与固件处理 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x301` | GPS_Speed | Display | 50 ms | **已接入** | 车速 (小端 uint16, 0.1 km/h)，写入 `fast_telemetry/vehicle_state/motion` 的车速字段。 |
| `0x305` | DataLogger | ECU | 50 ms | **已接入** | 方向盘转角 (0.1 deg)、油门开度 (0.1%)、油压信号 (0.001 kPa)。 |
| `0x502` | Debug2 | ECU | 10 ms | **已接入** | 四轮 AMK 实际扭矩 (小端有符号, 0.1%Mn)。写入 `motors[].torque_nm`。 |
| `0x503/0x504` | Debug3/4 | ECU | 10 ms | **已接入** | 四轮 AMK 32 位故障诊断码。写入 `motors[].diagnostic_number` 与 `motor_error`。 |
| `0x505` | Debug5 | ECU | 10 ms | **已接入** | 四轮 AMK 电机实际转速 (小端有符号, rpm)。写入 `motors[].rpm` 及顶层 `motor_rpm` (RL)。 |
| `0x506` | Debug6 | ECU | 10 ms | **已接入** | 四轮 AMK 电机温度 (0.1 °C)。写入 `motors[].motor_temp_dc` 及顶层 `motor_temp` (RL)。 |
| `0x507` | Debug7 | ECU | 10 ms | **已接入** | 四轮 AMK 控制器冷板温度 (0.1 °C)。写入 `motors[].inverter_temp_dc`。 |
| `0x508` | Debug8 | ECU | 10 ms | **已接入** | 四轮 AMK IGBT 结温 (0.1 °C)。写入 `motors[].igbt_temp_dc`。 |
| `0x509` | Debug9 | ECU | 10 ms | **已接入** | 车辆驾驶模式 `ModeFlag`（写入 `driving_mode`）及四轮使能逻辑状态 `LogicState`。 |
| `0x521/522/526/528` | 赛会能量计结果 | 赛会设备 | 周期 | **已接入** | 赛会能量计电流、U1 总压、功率、Wh（大端 int32）。写入 `energy_meter.*`。 |
| `0x430` | FS Datalogger 状态 | 赛会设备 | 周期 | **已接入** | FS 型号能量计状态、16 mV / 64 mA 低分辨率采样与 MsgCnt。写入 `energy_meter`。 |
| `0x4B0` | BMS 包状态冗余 | BMS | 500 ms | **已接入** | 与 CAN1 `0x186050F4` 同格式。提供总压/总流/SOC 跨总线冗余。 |
| `0x4B1` | BMS 故障汇总冗余 | BMS | 500 ms | **已接入** | 与 CAN1 `0x187650F4` 同格式。提供故障字跨总线冗余。 |
| `0x18FF50E5` | 充电机反馈 | 充电机 | 周期 | **已接入** | Legacy 充电机输出电流，作为 `hv_current` 第 2 优先级备用源。 |
| `0x050` | IMU 原始帧 | Display | 周期 | **部分接入** | 固件拆解为 `0x060..0x066` 转发到 CANB；其中加速度 (`0x061`)、陀螺仪 Z (`0x062`)、横摆角 (`0x065`) 进入遥测。 |
| `0x071..0x074` | 轮胎红外温度 | 采集模块 | 周期 | **已接入** | 四轮各 4 点红外温度（0.01 °C），按帧顺序映射 FL/FR/RL/RR 写入 `thermal_summary`（映射待实物确认）。 |
| `0x201/202/204/205` | Chroma 充电机反馈 | Chroma | 周期 | **已接入** | Chroma 充电电压/电流（LE float32）、保护位图与输出状态，编码入 `charger_telemetry`。 |
| `0x4A0/0x4A3/0x4A4` | BMS/ECU SOP 限值 | BMS/ECU | 放电模式高压接通后 10 ms | **部分上报** | `0x4A0/0x4A3` 通过成组 CRC 和 100 ms 配对检查后才更新限值；`0x4A4` 独立验 CRC。完整状态保存在本地，Proto 已定义的限值和汇总标志进入 `sop_limits`。 |
| `0x4B2` | BMS 告警等级冗余 | BMS | 2 s | **已接入** | 32 项两位等级与故障字组合后展开到 `alarms[]`，与 CAN1 `0x187850F4` 共用数据。 |
| `0x5A0/0x5A1` | 低压配电 PDM | PDM | 周期 | **已接入** | 低压母线/蓄电池电压、电流、功率、能量，编码入 `pdm_telemetry`。 |
| `0x5A2..0x5A9/0x5AE` | 整车风扇控制器 | 风扇板 | 周期/事件 | **部分上报** | `0x5A2..0x5A9` 已解析；`0x5AE` 两档保存限值待网关接入。现有 `fan_telemetry` 字段继续上报，新增字段在公共 Proto 扩展前只保存在本地状态。 |
| `0x5AA..0x5AD` | BMS 电池箱风扇 | BMS/工具 | 请求窗口内周期/事件 | 待网关接入 | 状态、远程控制、命令应答及 Chroma 35 W/高压 70 W 两档标定已进入正式 DBC。 |

---

### 3.3 CANA 与 CANC（底盘与电机总线）

- **CANA (AMK 电机总线)**：当前 G473 硬件接收但不解码，四轮电机运行遥测由 ECU 在 CANB 上的 `Debug2~Debug9` 转发提供。
  - *待接入*：四轮电机单路功率 (`AMK_PowerValue`，CANA ActualValue4，0.001 kW，原始值即 W) 与单路母线电压 (`DCbus_Voltage`，ActualValue3) 已确认存在，暂不解码（功率非当前重点）。
- **CANC (底盘总线，MCP2518FD)**：当前硬件接收记录原始帧。
  - *高价值候选源*：`0x125 ABS_Status`（轮速车速真值）、`0x132 ESC_Status`（主缸刹车压力真值）、`0x166 VCU_Status`（**权威 VCU 状态来源**）、`0x270 IBS_Info`（踏板行程真值）。

---

## 4. 多源冗余与固件 Fallback 降级策略

### 4.1 自动降级与单总线自适应取数

固件内部采用 **全局状态池 + 独立新鲜度时戳（`App_IsFresh`，默认 2000 ms 超时）** 机制。无论网关是全接还是只接任一路 CAN，都能自动选取有效数据并平滑降级：

```
【高压总压 hv_voltage 取数优先级】
┌────────────────────────────────────────────────────────┐
│ 优先级 1: CAN1 自有 IVT-S U1 (0x513) (新鲜且状态字正常) │
└───────────────────────────┬────────────────────────────┘
                            │ 超时 / 错误
                            ▼
┌────────────────────────────────────────────────────────┐
│ 优先级 2: BMS 包状态 (CAN1 0x186050F4 / CANB 0x4B0)     │
└───────────────────────────┬────────────────────────────┘
                            │ 超时 / 无效位
                            ▼
┌────────────────────────────────────────────────────────┐
│ 优先级 3: CAN1 电压累加和 (0x186750F4) (新鲜)           │
└───────────────────────────┬────────────────────────────┘
                            │ 超时
                            ▼
┌────────────────────────────────────────────────────────┐
│ 优先级 4: CAN1 138 串单体电压逐帧累加 (6 模块均有效)     │
└───────────────────────────┬────────────────────────────┘
                            │ 缺帧 / 超时
                            ▼
                       输出 0.0 V
```

```
【高压总流 hv_current 取数优先级】
┌────────────────────────────────────────────────────────┐
│ 优先级 1: CAN1 自有 IVT-S 电流 (0x512) (新鲜且状态字正常)│
└───────────────────────────┬────────────────────────────┘
                            │ 超时 / 错误
                            ▼
┌────────────────────────────────────────────────────────┐
│ 优先级 2: CANB Legacy 充电反馈 (0x18FF50E5) (新鲜)     │
└───────────────────────────┬────────────────────────────┘
                            │ 超时
                            ▼
┌────────────────────────────────────────────────────────┐
│ 优先级 3: BMS 包状态 (CAN1 0x186050F4 / CANB 0x4B0)     │
└───────────────────────────┬────────────────────────────┘
                            │ 超时 / 无效位
                            ▼
                       输出 0.0 A
```

### 4.2 单路 CAN 接入表现速查

| 接入场景 | 高压总压 / 总流 / SOC / 故障码 | 138 串电压 / 48 路温度明细 | 车速 / 踏板 / 四电机 / 驾驶模式 / IMU |
| :--- | :--- | :--- | :--- |
| **只接 CAN1**（BMS 专线） | **最优**（CAN1 自有 IVT-S 供数，并可降级到 BMS `0x186050F4`） | **正常**（CAN1 从控采样帧完整供数） | 无数据（置 0 / 空） |
| **只接 CANB**（整车总线） | **正常**（BMS 冗余 `0x4B0` 供数；自有 IVT-S 不在 CANB） | 无数据（从控采样帧不走 CANB） | **正常**（ECU、Display、IMU 供数） |
| **双路全接**（推荐） | **最优**（CAN1 高精度 IVT-S 供数） | **正常**（CAN1 供数） | **正常**（CANB 供数） |

---

## 5. 协议演进缺口与待确认项

1. **VCU 与 BMS 状态彻底解耦（BMS 侧已完成）**：
   - `TelemetryFrame.vcu_status` 与 `ready_to_drive` 已停止用 BMS 状态代填，无真实 ECU/VCU 源前保持 0。
   - BMS 状态机与告警等级改由新增 `bms_telemetry.battery_state/battery_alarm_level` 承载（继电器、充电状态与预充结果同消息）。
   - *待办*：接入 CANC `0x166 VCU_Status` 或 CANB ECU 状态帧后，再恢复 `vcu_status` 与 `ready_to_drive`。
2. **刹车开度真值与刹车压力**：
   - 当前 `brake_pressure` 实际为 CANB `0x305` 的机油压力（kPa）。真正的刹车主缸压力在 CANC `0x132`，踏板开度在 CANC `0x270`，需结合底盘总线规划接入。
3. **四轮电机单路功率**：
   - `motors[].power_w` 字段保留；CANA ActualValue4 `AMK_PowerValue` 已确认存在（0.001 kW），但暂未解码，非当前重点，后续按需接入。
4. **轮胎温度轮位映射**：
   - CANB `0x071..0x074` 16 点已接入 `thermal_summary`，当前按 0x071=FL、0x072=FR、0x073=RL、0x074=RR 假设，待与胎温采集模块/遥测确认。
