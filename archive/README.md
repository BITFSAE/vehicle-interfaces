# 历史接口归档

本目录保存已退出正式接口、但仍可能用于迁移追溯或比赛设备核对的历史资料。归档文件不是实现依据；当前接口始终以 `can/`、`telemetry/` 和 `docs/` 中的正式文件为准。

`CANRS485_G473_REFERENCE/` 来自 CANRS485_G473 在提交 `c1ed210` 中删除前的 `REFERENCE/`：

- `FS_Datalogger_Status_v0.2.dbc`：赛会 FS Datalogger 厂家/历史定义；正式运行字段已归并到 `can/Vehicle_CanB.dbc`。
- `Vehicle_CanA.dbc`、`Vehicle_CanB*.dbc`：中央仓库建立前的 CANA/CANB 多个副本。
- `cana_canb_protocol.md`：旧工程按当时 DBC 整理的 CANA/CANB 说明。

需要恢复其中内容时，应与当前代码、台架原始帧和正式 DBC 比对，不能直接覆盖现行接口。
