# 更新记录

## 未发布

### 已完成

- 建立整车 CAN 与遥测协议中央仓库结构。
- 迁入 ECU 同学提供的新版 CANA、CANB、CANC DBC；CANA 与原正式副本一致。
- 以新版 CANB 为基础，将 PDM `0x5A0/0x5A1` 和 FanController `0x5A2..0x5A7` 合入正式 CANB DBC。
- 迁入遥测 `fsae_telemetry.proto` 和 Nanopb `.options` 唯一源。
- 增加协作、审核、自动检查和公开仓库安全规则。
- 以 F405 当前协议为准新增 CAN1 正式 DBC，包含 138 串电压、48 路温度、主控周期帧和版本 4 工具协议。
- CANB 合入 BMS `0x4B0..0x4B2`、ECU SOP `0x4A0/0x4A3/0x4A4`、自有 IVT-S、Chroma 和 Legacy 充电接口。
- 新增 CAN1/CANB 使用文档；CANB 文档同时登记现有 ECU、显示、PDM、FanController、方向盘和数采报文入口。
- 验证脚本增加 CAN1/CANB 关键 ID、DLC、帧类型、字节序、符号和缩放回归检查；遥测 Proto/Options 本次无需修改。

### 待办

- 确认并选择本仓库许可证。
- 确认可以公开的第三方 DBC 及其原始授权。
- 由均衡板负责人确认 0x186450F4..0x186650F4 每字节均衡状态含义。
- 用台架原始帧复核 BMS CAN1 扩展 ID、CANB IVT-S 配置后的 ID/字节序、Chroma 和 Legacy 充电接口。
- 创建首个稳定 Release `v1.0.0`。
