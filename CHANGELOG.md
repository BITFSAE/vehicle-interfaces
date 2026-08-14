# 更新记录

## 未发布

### 已完成

- 将车队自有 IVT-S 与赛会 IVT/FS 能量计拆分为独立遥测源；增加自有 U2（Pre）总压及各结果状态，功率/Wh 改为可选 presence，并明确 STM32 不补算。
- 遥测协议新增 `bms_telemetry/imd_telemetry/sop_limits/charger_telemetry/pdm_telemetry/fan_telemetry`（字段 34~39）；停止用 BMS 状态代填 legacy `vcu_status/ready_to_drive`，预充电压明确由自有 IVT-S U2 承担。
- CANB 接入轮胎红外温度 `0x071..0x074`（写入 `thermal_summary`，帧→轮位映射待确认）、Chroma `0x401/0x402/0x404/0x405`、SOP `0x4A0/0x4A3/0x4A4`、PDM `0x5A0/0x5A1`、FanController `0x5A2..0x5A7`；CAN1 解析 IMD `0x186850F4`、HV 状态 `0x186950F4`、SOP 镜像 `0x186A50F4`。
- 验证脚本新增 CANA/CANC 与上述新帧的 ID/DLC/信号回归检查。
- 验证环境固定为仓库内 `.venv`；公开边界检查改为只扫描 Git 已跟踪及未忽略文件，避免扫描虚拟环境和构建目录。
- CANB 增加赛会能量计 `0x430/0x521/0x522/0x526/0x528` 正式定义，历史 FS Datalogger DBC 和旧 CANA/CANB 资料移入 `archive/`。
- 建立整车 CAN 与遥测协议中央仓库结构。
- 迁入 ECU 同学提供的新版 CANA、CANB、CANC DBC；CANA 与原正式副本一致。
- 以新版 CANB 为基础，将 PDM `0x5A0/0x5A1` 和 FanController `0x5A2..0x5A7` 合入正式 CANB DBC。
- 迁入遥测 `fsae_telemetry.proto` 和 Nanopb `.options` 唯一源。
- 增加协作、审核、自动检查和公开仓库安全规则。
- 以 F405 当前协议为准新增 CAN1 正式 DBC，包含 138 串电压、48 路温度、主控周期帧和版本 4 工具协议。
- CANB 合入 BMS `0x4B0..0x4B2`、ECU SOP `0x4A0/0x4A3/0x4A4`、自有 IVT-S、Chroma 和 Legacy 充电接口。
- 新增 CAN1/CANB 使用文档；CANB 文档同时登记现有 ECU、显示、PDM、FanController、方向盘和数采报文入口。
- 验证脚本增加 CAN1/CANB 关键 ID、DLC、帧类型、字节序、符号和缩放回归检查；遥测 Proto/Options 本次无需修改。
- 调整文档分工：CAN ID 只在总线索引集中登记，CANB 文档引用 CAN1 的共用 BMS 状态字段，README 和维护文档删除重复流程与历史说明。
- 补齐 CAN1/CANB 使用文档的字段缺口：告警等级与开关全表、IMD 位映射、阈值与 SOP 字节布局、SOP 发送与确认的模式限制、IVT 结果状态位；不含接口行为变更。

### 待办

- 确认并选择本仓库许可证。
- 确认可以公开的第三方 DBC 及其原始授权。
- 由均衡板负责人确认 0x186450F4..0x186650F4 每字节均衡状态含义。
- 用台架原始帧复核 BMS CAN1 扩展 ID、CANB IVT-S 配置后的 ID/字节序、Chroma 和 Legacy 充电接口。
- 创建首个稳定 Release `v1.0.0`。
