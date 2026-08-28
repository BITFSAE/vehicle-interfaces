# Grafana 监控与云端遥测指南

> 本指南汇总车载遥测数据在云端接收（Telegraf）、时序数据库存储（InfluxDB 1.x）及 Grafana 仪表盘监控的完整架构、全量字段清单、单位换算公式、常用 InfluxQL 查询语句与故障排查方法。
>
> **事实来源与副本规范**：
> - 机器可读协议以 `vehicle-interfaces/telemetry/fsae_telemetry.proto` 与 `telegraf.conf` 为权威源。
> - 本文件在 `vehicle-interfaces/docs/Grafana监控指南.md` 与 `CANRS485_G473/REFERENCE/protobuf-master/GRAFANA_GUIDE.md` 保持**完全一致的双仓库同步副本**。

---

## 1. 遥测全链路与云端数据源

### 1.1 数据链路架构

```
[车载 STM32 G473 网关]
         │ (Nanopb 序列化 TelemetryFrame)
         ▼
[DTU 4G 透传终端] (RS485 半双工, 115200 8N1)
         │ (MQTT 单 Topic: fsae/telemetry)
         ▼
[云服务器 Mosquitto Broker] (<MQTT_BROKER>:1883)
         │ (内部消费)
         ▼
[Telegraf xpath_protobuf 插件] (按 XPath 提取并存入 Measurement)
         │ (批量写入)
         ▼
[InfluxDB 1.x (fsae_db)] (保留策略存储)
         │ (InfluxQL 查询)
         ▼
[Grafana 可视化仪表盘] (https://<GRAFANA_HOST>/monitor/)
```

### 1.2 数据源配置信息

| 配置项 | 参数值 | 说明 |
| :--- | :--- | :--- |
| **数据源类型** | InfluxDB 1.x | 时序数据库 |
| **HTTP URL** | `http://influxdb:8086` | Docker 内部网络通信 |
| **Database** | `fsae_db` | 遥测主数据库 |
| **Query Language** | `InfluxQL` | 标准 SQL-like 时序查询语法 |
| **Min Time Interval** | `100ms` | 与车载网关 10 Hz 基础帧匹配 |
| **Default Retention** | `autogen` | 默认保留策略 |

---

## 2. InfluxDB 5 大 Measurements 全量字段矩阵

Telegraf 根据 `fsae_telemetry.proto` 的 XPath 配置，将单条 `TelemetryFrame` 解析并写入以下 5 个独立的 Measurement：

### 2.1 `telemetry` 表（整车主遥测与单值摘要，10 Hz）

| 字段名 (Field Key) | 数据类型 | 物理含义 | 原始单位 | InfluxDB 存储单位 | Grafana 显示换算 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `timestamp_ms` | integer | 车载 MCU 启动时戳 | ms | ms | 时戳 |
| `seq` | integer | 报文递增序号 | — | 整数 | 序号计数 |
| `hv_voltage` | float | 高压总压（Fallback 主值） | V | V | Unit `volt` (V) |
| `hv_current` | float | 高压总流（Fallback 主值） | A | A | Unit `ampere` (A) |
| `hv_voltage_dv` | integer | 高压总压（Starlark 衍生） | 0.1 V | 0.1 V | 查询 `/ 10` $\to$ V |
| `hv_current_ma` | integer | 高压总流（Starlark 衍生） | mA | mA | 查询 `/ 1000` $\to$ A |
| `battery_soc` | integer | 电池荷电状态 SOC | % | % | Unit `percent (0-100)` |
| `battery_temp_max` | float | 电池包最高温度 | °C | °C | Unit `celsius` (°C) |
| `battery_temp_max_dc` | integer | 电池最高温度（Starlark 衍生）| 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ °C |
| `battery_fault_code` | integer | BMS 32 位故障字位图 | 32bit | 十进制整数 | 十六进制展示 |
| `max_cell_voltage` | integer | 电池包最高单体电压 | mV | mV | Unit `millivolt` (mV) |
| `min_cell_voltage` | integer | 电池包最低单体电压 | mV | mV | Unit `millivolt` (mV) |
| `max_cell_voltage_no` | integer | 最高单体电压编号 | 1..138 | 整数编号 | 编号 (1..138) |
| `min_cell_voltage_no` | integer | 最低单体电压编号 | 1..138 | 整数编号 | 编号 (1..138) |
| `max_temp` | integer | 电池包最高采样温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ °C |
| `min_temp` | integer | 电池包最低采样温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ °C |
| `max_temp_no` | integer | 最高温度探头编号 | 1..48 | 整数编号 | 探头编号 (1..48) |
| `min_temp_no` | integer | 最低温度探头编号 | 1..48 | 整数编号 | 探头编号 (1..48) |
| `apps_position` | float | 油门踏板开度 | % | % | Unit `percent (0-100)` |
| `brake_pressure` | float | 刹车油路压力 | kPa | kPa | Unit `kPa` |
| `steering_angle` | float | 方向盘物理转角 | deg | deg | Unit `degree` (°) |
| `ready_to_drive` | integer | 整车就绪（legacy；无真实 ECU/VCU 源时保持 0） | 0/1 | 0/1 | 0=未就绪, 1=就绪 |
| `vcu_status` | integer | VCU 状态（legacy；BMS 不再代填，VCU 源接入前保持 0） | 枚举 | 整数 | 0=未知（VCU 源接入前无值） |
| `vehicle_mode` | integer | 整车驾驶模式 | 枚举 | 1..5 | 1=默认, 2=直线, 3=避障, 4=八字, 5=耐久 |
| `fast_vehicle_mode` | integer | 快速遥测驾驶模式 | 枚举 | 1..5 | 同上 |
| `gps_speed_kmh` | integer | GPS 车速 | km/h | km/h | Unit `kmh` (km/h) |
| `accel_x_g` | float | 车身纵向加速度 X | g | g | Unit `g` |
| `accel_y_g` | float | 车身横向加速度 Y | g | g | Unit `g` |
| `accel_z_g` | float | 车身垂直加速度 Z | g | g | Unit `g` |
| `yaw_rate_dps` | float | 车身横摆角速度 | deg/s | deg/s | Unit `deg/s` |
| `yaw_deg` | float | 车身绝对横摆角 | deg | deg | Unit `degree` (°) |
| `ivt_current_ma` | integer | 自有 IVT-S 电流 | mA | mA | 查询 `/ 1000` $\to$ A |
| `ivt_voltage_u1_mv` | integer | 自有 IVT-S U1 电池侧总压 | mV | mV | 查询 `/ 1000` $\to$ V |
| `ivt_voltage_u2_mv` | integer | 自有 IVT-S U2 逆变器侧总压 | mV | mV | 查询 `/ 1000` $\to$ V |
| `ivt_power_w` | integer | 自有 IVT-S 功率 | W | W | Unit `watt` (W) |
| `ivt_energy_wh` | integer | 自有 IVT-S 积分能量 | Wh | Wh | Unit `watt-hour` (Wh) |
| `ivt_current_state` | integer | 自有 IVT-S 电流状态字 | 掩码 | 状态字 | 0=正常, 详见第 4.2 节 |
| `ivt_voltage_u1_state`| integer | 自有 IVT-S U1 状态字 | 掩码 | 状态字 | 0=正常 |
| `ivt_voltage_u2_state`| integer | 自有 IVT-S U2 状态字 | 掩码 | 状态字 | 0=正常 |
| `ivt_power_state` | integer | 自有 IVT-S 功率状态字 | 掩码 | 状态字 | 0=正常 |
| `ivt_energy_state` | integer | 自有 IVT-S 能量状态字 | 掩码 | 状态字 | 0=正常 |
| `energy_meter_source` | integer | 赛会能量计型号来源 | 枚举 | 1 或 2 | 1=默认 IVT 大端, 2=FS 状态帧 |
| `energy_meter_current_ma` | integer | 赛会能量计电流 | mA | mA | 查询 `/ 1000` $\to$ A |
| `energy_meter_voltage_mv` | integer | 赛会能量计电压 | mV | mV | 查询 `/ 1000` $\to$ V |
| `energy_meter_power_w` | integer | 赛会能量计功率 | W | W | Unit `watt` (W) |
| `energy_meter_energy_wh` | integer | 赛会能量计 Wh | Wh | Wh | Unit `watt-hour` (Wh) |
| `energy_meter_status` | integer | FS 能量计状态码 | 整数 | 状态码 | FS 设备返回 |
| `energy_meter_msg_counter`| integer | 赛会能量计报文计数器 | 计数 | 0..15 / 0..255 | 报文翻转计数 |
| `energy_meter_*_state`| integer | 赛会各通道状态字 | 掩码 | 状态字 | 0=正常 |
| `bms_battery_state` | integer | BMS 状态机 | 2..7 | 整数 | 2自检/3待机/4预充/5高压接通/7故障 |
| `bms_battery_alarm_level` | integer | BMS 告警等级 | 0..3 | 整数 | 0正常/1一级故障/2二级告警 |
| `bms_pos_relay_state`/`bms_neg_relay_state`/`bms_pre_relay_state` | integer | 高压继电器状态 | 0..3 | 整数 | 继电器状态码 |
| `bms_charge_state` | integer | 充电状态 | 0..15 | 整数 | 充电状态码 |
| `bms_charge_comm_state` | integer | 充电通信状态 | 0/1 | 整数 | 通信标志 |
| `bms_last_precharge_result` | integer | 最近预充结果 | 0..2 | 整数 | 0无/1成功/2失败 |
| `bms_last_precharge_success_ms`/`bms_last_precharge_failure_ms` | integer | 预充成功/失败耗时 | ms | ms | 最近一次耗时 |
| `imd_resistance_kohm` | integer | 绝缘电阻 | kΩ | kΩ | Unit `kohm` |
| `imd_duty_pct_x10` | integer | IMD PWM 占空比 | 0.1% | 0.1% | 查询 `/ 10` → % |
| `imd_frequency_hz_x100` | integer | IMD PWM 频率 | 0.01 Hz | 0.01 Hz | 查询 `/ 100` → Hz |
| `imd_frequency_class`/`imd_status_code` | integer | IMD 频率分类/状态码 | 0..15 | 整数 | 状态码 |
| `imd_flags` | integer | IMD 标志位图 | 位图 | 整数 | 十六进制展示 |
| `sop_discharge_current_limit_a_x10`/`sop_charge_current_limit_a_x10` | integer | 充/放电流上限 | 0.1 A | 0.1 A | 查询 `/ 10` → A |
| `sop_discharge_power_limit_kw_x10`/`sop_charge_power_limit_kw_x10` | integer | 充/放功率上限 | 0.1 kW | 0.1 kW | 查询 `/ 10` → kW |
| `sop_sequence`/`sop_protocol_version` | integer | SOP 序列/版本 | 0..15 | 整数 | 序号 |
| `sop_bms_flags`/`sop_ecu_flags` | integer | SOP 标志位图 | 位图 | 整数 | 十六进制展示 |
| `charger_voltage_v`/`charger_current_a` | float | Chroma 充电电压/电流 | V/A | V/A | Unit `volt`/`ampere` |
| `charger_protection` | integer | Chroma 保护位图 | 位图 | 整数 | 十六进制展示 |
| `charger_output_state` | integer | Chroma 输出状态 | 0..255 | 整数 | 0=关, 1=开 |
| `pdm_bus_voltage_v`/`pdm_bus_current_a`/`pdm_bus_power_w`/`pdm_bus_energy_wh` | float | 低压母线 V/A/W/Wh | V/A/W/Wh | V/A/W/Wh | 对应 Unit |
| `pdm_battery_voltage_v`/`pdm_battery_current_a`/`pdm_battery_power_w`/`pdm_battery_energy_wh` | float | 低压蓄电池 V/A/W/Wh | V/A/W/Wh | V/A/W/Wh | 对应 Unit |
| `fan1_rpm`/`fan2_rpm`/`fan3_rpm` | integer | 三路风扇转速 | rpm | rpm | Unit `rpm` |
| `fan_pwm1_duty_pct`/`fan_pwm2_duty_pct` | integer | 风扇当前占空比 | % | % | Unit `percent (0-100)` |
| `fan_pwm1_target_pct`/`fan_pwm2_target_pct` | integer | 风扇目标占空比 | % | % | Unit `percent (0-100)` |
| `fan_ack_actual_pwm1_pct`/`fan_ack_actual_pwm2_pct` | integer | 命令应答实测占空比 | % | % | Unit `percent (0-100)` |
| `fan_faults`/`fan_status_flags` | integer | 风扇故障/状态位图 | 位图 | 整数 | 十六进制展示 |
| `fan_max_motor_temp_dc`/`fan_max_controller_temp_dc` | integer | 最高电机/控制器温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` → °C |
| `fan_ack_result`/`fan_ack_mode`/`fan_ack_failsafe` | integer | 风扇命令应答 | 枚举 | 整数 | 状态码 |
| `fan_curve_*` | integer | 风扇曲线参数 | 枚举 | 整数 | °C / % / %/s |
| `fan_failsafe_*`/`fan_control_mode`/`fan_control_lease_remaining_s` | integer | 故障安全与控制模式 | 枚举 | 整数 | 状态码 |

---

### 2.2 `bms_data` 表（138 串电芯电压与 48 路温度，2 Hz）

- **Tags 索引**：`module_id`（从控模块编号，取值 `'1'` ~ `'6'`）。

| 字段名 (Field Key) | 数据类型 | 物理含义 | 原始单位 | InfluxDB 存储单位 | Grafana 显示换算 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `v_01` ~ `v_23` | integer | 当前模组第 01 ~ 23 节电芯电压 | mV | mV | Unit `millivolt` (mV) |
| `t_1` ~ `t_8` | integer | 当前模组第 1 ~ 8 路采样温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ Unit `celsius` (°C) |

---

### 2.3 `motor_state` 表（四轮电机与逆变器运行状态，随 Debug2~9 驱动）

- **Tags 索引**：`position`（轮位枚举：`'1'`=左前 FL, `'2'`=右前 FR, `'3'`=左后 RL, `'4'`=右后 RR）。

| 字段名 (Field Key) | 数据类型 | 物理含义 | 原始单位 | InfluxDB 存储单位 | Grafana 显示换算 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rpm` | integer | 电机实际物理转速 | rpm | rpm | Unit `rpm` |
| `torque_nm` | integer | 电机实际扭矩原始值 | 0.1%Mn | 0.1%Mn | 查询 `* 9.8 / 1000` $\to$ Unit `Nm` |
| `power_w` | integer | 电机单路功率（待接入） | W | W | Unit `watt` (W) |
| `motor_temp_dc` | integer | 电机本体绕组温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ Unit `celsius` (°C) |
| `inverter_temp_dc` | integer | 逆变器水冷板温度 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ Unit `celsius` (°C) |
| `igbt_temp_dc` | integer | IGBT 模块结温 | 0.1 °C | 0.1 °C | 查询 `/ 10` $\to$ Unit `celsius` (°C) |
| `diagnostic_number` | integer | AMK 32 位故障诊断码 | 32bit | 整数 | 十六进制显示 |
| `motor_error` | integer | AMK 诊断码（当前与 diagnostic_number 同值） | 32bit | 整数 | 十六进制诊断码 |
| `logic_state` | integer | AMK 逻辑使能与逆变器状态 | 0..15 | 0..15 | 逻辑状态码 |

---

### 2.4 `thermal_summary` 表（轮胎红外温度摘要，CANB 0x071~0x074）

- **Tags 索引**：`position`（轮位枚举 `'1'`~`'4'`）。

| 字段名 (Field Key) | 数据类型 | 物理含义 | 原始单位 | InfluxDB 存储单位 | Grafana 显示换算 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `min_temp_centi_c` | integer | 对应轮位轮胎最低温度 | 0.01 °C | 0.01 °C | 查询 `/ 100` $\to$ °C |
| `max_temp_centi_c` | integer | 对应轮位轮胎最高温度 | 0.01 °C | 0.01 °C | 查询 `/ 100` $\to$ °C |
| `avg_temp_centi_c` | integer | 对应轮位轮胎平均温度 | 0.01 °C | 0.01 °C | 查询 `/ 100` $\to$ °C |

---

> 当前帧→轮位映射假设：0x071=FL、0x072=FR、0x073=RL、0x074=RR，待与胎温采集模块/遥测确认。

### 2.5 `alarm_state` 表（整车告警列表）

- **Tags 索引**：`alarm_id`（告警 CAN ID，如 `0x186050F4`）。

| 字段名 (Field Key) | 数据类型 | 物理含义 | 说明 |
| :--- | :--- | :--- | :--- |
| `severity` | integer | 告警严重级别 | 0=UNSPECIFIED, 1=INFO, 2=WARNING, 3=ERROR, 4=FATAL |
| `message` | string | 告警详细描述文本 | 如 `"BMS summary alarm level 1"` |

---

## 3. 单位与换算公式速查表

| 数据类型 | 数据库存储字段 | InfluxQL 换算表达式 | Grafana Panel Unit 设置 |
| :--- | :--- | :--- | :--- |
| **电压 (V)** | `hv_voltage` | 无需换算（直接查询） | `Misc / volt (V)` |
| **电压 (mV)** | `ivt_voltage_u1_mv`, `energy_meter_voltage_mv` | `"field" / 1000.0` | `Misc / volt (V)` |
| **电芯电压 (mV)** | `v_01` ~ `v_23`, `max_cell_voltage` | 无需换算（直接查询） | `Misc / millivolt (mV)` |
| **电流 (A)** | `hv_current` | 无需换算（直接查询） | `Misc / ampere (A)` |
| **电流 (mA)** | `ivt_current_ma`, `energy_meter_current_ma` | `"field" / 1000.0` | `Misc / ampere (A)` |
| **功率 (W)** | `ivt_power_w`, `energy_meter_power_w` | 无需换算 / 1000 $\to$ kW | `Misc / watt (W)` 或 `kilowatt (kW)` |
| **能量 (Wh)** | `ivt_energy_wh`, `energy_meter_energy_wh` | 无需换算 / 1000 $\to$ kWh | `Misc / watt-hour (Wh)` 或 `kilowatt-hour` |
| **温度 (°C)** | `battery_temp_max` | 无需换算（直接查询） | `Temperature / Celsius (°C)` |
| **0.1°C 温度** | `t_1`~`t_8`, `max_temp`, `*_temp_dc` | `"field" / 10.0` | `Temperature / Celsius (°C)` |
| **0.01°C 温度** | `*_temp_centi_c` | `"field" / 100.0` | `Temperature / Celsius (°C)` |
| **AMK 扭矩 (Nm)** | `torque_nm` | `"torque_nm" * 9.8 / 1000.0` | `Force / Newton-meter (Nm)` |
| **百分比 (%)** | `battery_soc`, `apps_position` | 无需换算（直接查询） | `Misc / percent (0-100)` |
| **车速 (km/h)** | `gps_speed_kmh` | 无需换算（直接查询） | `Velocity / km/h` |
| **压力 (kPa)** | `brake_pressure` | 无需换算（直接查询） | `Pressure / kilopascal (kPa)` |
| **转角 (deg)** | `steering_angle`, `yaw_deg` | 无需换算（直接查询） | `Angle / Degrees (°)` |
| **角速度 (deg/s)**| `yaw_rate_dps` | 无需换算（直接查询） | `Angle / Degrees/second (°/s)` |
| **加速度 (g)** | `accel_x_g`, `accel_y_g`, `accel_z_g` | 无需换算（直接查询） | `Acceleration / G` (自定义 `g`) |

---

## 4. InfluxQL 核心查询语句全集

### 4.1 Overview 整车核心概览

```sql
-- 1. 实时时序曲线（必须带 $timeFilter）
SELECT "hv_voltage" AS "Total Voltage (V)", "hv_current" AS "Total Current (A)"
FROM "telemetry" WHERE $timeFilter;

SELECT "battery_soc" AS "SOC (%)", "battery_temp_max" AS "Max Temp (°C)"
FROM "telemetry" WHERE $timeFilter;

-- 2. 最新快照（不带 $timeFilter，避免时间窗口过小返回空）
SELECT "hv_voltage", "hv_current", "battery_soc", "battery_temp_max", "battery_fault_code", "vehicle_mode", "ready_to_drive", "gps_speed_kmh"
FROM "telemetry" ORDER BY time DESC LIMIT 1;
```

### 4.2 Energy Meter 能量与功率对比（自有 IVT-S vs 赛会能量计）

```sql
-- 1. 电池侧总压与逆变器侧总压对比
SELECT "ivt_voltage_u1_mv" / 1000.0 AS "Own IVT Battery Side (U1)",
       "ivt_voltage_u2_mv" / 1000.0 AS "Own IVT Inverter Side (U2)",
       "energy_meter_voltage_mv" / 1000.0 AS "Competition Meter (U1)"
FROM "telemetry" WHERE $timeFilter;

-- 2. 总流对比
SELECT "ivt_current_ma" / 1000.0 AS "Own IVT Current",
       "energy_meter_current_ma" / 1000.0 AS "Competition Current"
FROM "telemetry" WHERE $timeFilter;

-- 3. 功率与 Wh 对比
SELECT "ivt_power_w" AS "Own Power (W)", "energy_meter_power_w" AS "Competition Power (W)"
FROM "telemetry" WHERE $timeFilter;

SELECT "ivt_energy_wh" AS "Own Energy (Wh)", "energy_meter_energy_wh" AS "Competition Energy (Wh)"
FROM "telemetry" WHERE $timeFilter;

-- 4. 自有 IVT-S 状态字监控 (0=正常)
SELECT "ivt_current_state", "ivt_voltage_u1_state", "ivt_voltage_u2_state", "ivt_power_state", "ivt_energy_state"
FROM "telemetry" ORDER BY time DESC LIMIT 1;
```

### 4.3 BMS 电芯矩阵监控（138 串电芯）

```sql
-- 1. 单模组 23 节电芯最新电压柱状图（使用变量 $module_id）
SELECT "v_01", "v_02", "v_03", "v_04", "v_05", "v_06", "v_07", "v_08", "v_09", "v_10",
       "v_11", "v_12", "v_13", "v_14", "v_15", "v_16", "v_17", "v_18", "v_19", "v_20",
       "v_21", "v_22", "v_23"
FROM "bms_data" WHERE "module_id" = '$module_id' ORDER BY time DESC LIMIT 1;

-- 2. 包级单体最高压、最低压与实时最大压差
SELECT "max_cell_voltage" AS "Max Cell (mV)",
       "min_cell_voltage" AS "Min Cell (mV)",
       ("max_cell_voltage" - "min_cell_voltage") AS "Delta V (mV)"
FROM "telemetry" WHERE $timeFilter;

-- 3. 极值单体编号查询
SELECT "max_cell_voltage_no" AS "Max Cell ID", "min_cell_voltage_no" AS "Min Cell ID"
FROM "telemetry" ORDER BY time DESC LIMIT 1;
```

### 4.4 BMS 采样温度监控（48 路温度）

```sql
-- 1. 单模组 8 路温度最新柱状图（使用变量 $module_id）
SELECT "t_1" / 10.0 AS "Temp 1", "t_2" / 10.0 AS "Temp 2", "t_3" / 10.0 AS "Temp 3", "t_4" / 10.0 AS "Temp 4",
       "t_5" / 10.0 AS "Temp 5", "t_6" / 10.0 AS "Temp 6", "t_7" / 10.0 AS "Temp 7", "t_8" / 10.0 AS "Temp 8"
FROM "bms_data" WHERE "module_id" = '$module_id' ORDER BY time DESC LIMIT 1;

-- 2. 包级最高温、最低温与最大温差
SELECT "max_temp" / 10.0 AS "Max Temp (°C)",
       "min_temp" / 10.0 AS "Min Temp (°C)",
       ("max_temp" - "min_temp") / 10.0 AS "Delta Temp (°C)"
FROM "telemetry" WHERE $timeFilter;

-- 3. 极值温度探头编号查询
SELECT "max_temp_no" AS "Max Temp Probe ID", "min_temp_no" AS "Min Temp Probe ID"
FROM "telemetry" ORDER BY time DESC LIMIT 1;
```

### 4.5 四轮电机与驱动系统监控

```sql
-- 1. 四轮电机转速（按 position 分组）
SELECT "rpm" FROM "motor_state" WHERE $timeFilter GROUP BY "position";

-- 2. 四轮电机实际输出扭矩（转换为 Nm）
SELECT "torque_nm" * 9.8 / 1000.0 AS "Torque (Nm)"
FROM "motor_state" WHERE $timeFilter GROUP BY "position";

-- 3. 四轮电机绕组温度、逆变器冷板温度、IGBT 结温
SELECT "motor_temp_dc" / 10.0 AS "Motor Temp (°C)" FROM "motor_state" WHERE $timeFilter GROUP BY "position";
SELECT "inverter_temp_dc" / 10.0 AS "Inverter Temp (°C)" FROM "motor_state" WHERE $timeFilter GROUP BY "position";
SELECT "igbt_temp_dc" / 10.0 AS "IGBT Temp (°C)" FROM "motor_state" WHERE $timeFilter GROUP BY "position";

-- 4. 指定轮位最新诊断码与使能逻辑状态（使用变量 $position）
SELECT "diagnostic_number", "motor_error", "logic_state"
FROM "motor_state" WHERE "position" = '$position' ORDER BY time DESC LIMIT 1;
```

### 4.6 踏板、转向与整车运动姿态

```sql
-- 1. 油门开度、刹车油压、方向盘转角
SELECT "apps_position" AS "Throttle (%)",
       "brake_pressure" AS "Brake Oil Press (kPa)",
       "steering_angle" AS "Steering Angle (deg)"
FROM "telemetry" WHERE $timeFilter;

-- 2. GPS 车速与 IMU 三轴加速度
SELECT "gps_speed_kmh" AS "Speed (km/h)",
       "accel_x_g" AS "Accel X (g)",
       "accel_y_g" AS "Accel Y (g)",
       "accel_z_g" AS "Accel Z (g)"
FROM "telemetry" WHERE $timeFilter;

-- 3. IMU 横摆角速度与车身姿态角
SELECT "yaw_rate_dps" AS "Yaw Rate (deg/s)", "yaw_deg" AS "Yaw Angle (deg)"
FROM "telemetry" WHERE $timeFilter;
```

### 4.7 故障诊断与报警列表

```sql
-- 1. BMS 故障字时序变化
SELECT "battery_fault_code" FROM "telemetry" WHERE $timeFilter;

-- 2. 最新告警事件列表
SELECT "severity", "message" FROM "alarm_state" WHERE $timeFilter ORDER BY time DESC LIMIT 50;
```

---

## 5. Dashboard 6 行标准布局规划

推荐在 Grafana 仪表盘中建立以下 6 个 Row：

| Row 编号 | 区域名称 | 包含面板与可视化形式 | 关键阈值 / 配置 |
| :--- | :--- | :--- | :--- |
| **Row 1** | **Overview (核心大屏)** | - 高压总压、总流 Stat/Gauge 卡片<br>- SOC 与最高温 Stat 仪表<br>- 驾驶模式、R2D 就绪状态 Stat 徽标<br>- 故障字与能量计来源 Stat | 电压红线: `<450V` 或 `>580V`<br>最高温报警: `>55°C` (黄), `>60°C` (红)<br>SOC: `<20%` (黄), `<10%` (红) |
| **Row 2** | **Energy & Power (能量对比)** | - 自有 IVT-S vs 赛会能量计双电压曲线<br>- 双总流时序对比曲线<br>- 瞬时总功率 (W) 与积分能耗 (Wh) 对比曲线<br>- IVT 状态字监控表 | 状态字非 0 标红 |
| **Row 3** | **BMS Cells (138 串电芯)** | - 单模组 23 节电芯 Bar Chart 柱状图（带 `$module_id` 下拉）<br>- 包级最大压差曲线 (`max - min`)<br>- 最高/最低电压及电芯编号 Stat 卡片 | 单体电压: `<3.0V` (红), `<3.3V` (黄)<br>最大压差报警: `>100mV` (黄), `>200mV` (红) |
| **Row 4** | **BMS Temps (48 路温度)** | - 单模组 8 路温度 Bar Chart 柱状图<br>- 包级最大温差曲线 (`max - min`)<br>- 最高/最低温度及探头编号 Stat 卡片 | 探头温差报警: `>8°C` (黄), `>12°C` (红) |
| **Row 5** | **Motors & Inverters (四电机)**| - 四轮转速 4 色 Time Series 曲线<br>- 四轮实际扭矩 (Nm) 曲线<br>- 四轮电机/逆变器/IGBT 温度对比<br>- 四轮 AMK 诊断码与 LogicState 状态表 | 电机温度: `>110°C` (黄), `>130°C` (红)<br>IGBT 结温: `>120°C` (红) |
| **Row 6** | **Motion & Diagnostics (底盘与诊断)**| - 油门/刹车/转向三合一曲线<br>- 车速与三轴加速度曲线<br>- 横摆角速度与横摆角<br>- 报警事件列表 Table | 告警等级 3/4 标红高亮 |

---

## 6. 故障排查与数据库诊断常用命令

```bash
# 1. 登录服务器并检查容器状态
ssh bitfsae-com
cd <SERVER_PROJECT_DIR>
sudo docker compose ps

# 2. 查看 Telegraf 数据解析日志（观察是否有 XPath 报错）
sudo docker compose logs --tail=80 telegraf

# 3. 进入 InfluxDB 检查数据写入状态
sudo docker exec -it fsae_influxdb influx -database fsae_db

# 4. InfluxQL 常用自检语句
SHOW MEASUREMENTS;
SHOW FIELD KEYS FROM "telemetry";
SHOW FIELD KEYS FROM "motor_state";
SHOW TAG VALUES FROM "bms_data" WITH KEY = "module_id";
SHOW TAG VALUES FROM "motor_state" WITH KEY = "position";

# 5. 快速查验各表最新一条数据
SELECT * FROM "telemetry" ORDER BY time DESC LIMIT 1;
SELECT * FROM "motor_state" ORDER BY time DESC LIMIT 4;
SELECT * FROM "bms_data" WHERE "module_id"='1' ORDER BY time DESC LIMIT 1;
```
