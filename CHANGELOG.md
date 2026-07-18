# 更新记录

## 未发布

### 已完成

- 建立整车 CAN 与遥测协议中央仓库结构。
- 迁入 ECU 同学提供的新版 CANA、CANB、CANC DBC；CANA 与原正式副本一致。
- 以新版 CANB 为基础，将 PDM `0x5A0/0x5A1` 和 FanController `0x5A2..0x5A7` 合入正式 CANB DBC。
- 迁入遥测 `fsae_telemetry.proto` 和 Nanopb `.options` 唯一源。
- 增加协作、审核、自动检查和公开仓库安全规则。

### 待办

- 确认并选择本仓库许可证。
- 确认可以公开的第三方 DBC 及其原始授权。
- 创建首个稳定 Release `v1.0.0`。
