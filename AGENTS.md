# AI 代码与文档规范

## 接口修改

- `can/Vehicle_Can1.dbc`、`can/Vehicle_CanA.dbc`、`can/Vehicle_CanB.dbc`、`can/Vehicle_CanC.dbc` 和 `telemetry/fsae_telemetry.proto` 是正式接口源。
- 修改 CAN 或遥测接口时，同步更新对应说明、测试和 `CHANGELOG.md`。
- 不修改已发布 Protobuf 字段号；删除字段时使用 `reserved`。
- 不把生成的 Nanopb C/H 文件当作手工编辑源。
- 不加入真实服务器地址、密码、Token、私钥或生产部署信息。

## 文档与验证

- 使用清楚、直接的中文，写明方向、帧类型、DLC、字节序、类型、比例、单位、范围、无效值和兼容性。
- 未确认的字段、节点或厂家资料放在待确认文档，不写入正式 DBC。
- 修改后运行 `.venv/bin/python tools/validate_interfaces.py`（首次按 README 创建仓库内固定 `.venv`），并检查 Git 差异中没有生成垃圾或秘密。
- README 只做入口和索引；详细接口、协作流程和迁移记录分别由对应文档维护。

DO NOT send optional commentary
