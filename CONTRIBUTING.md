# 参与维护

## 权限与基本原则

- 队员可以创建功能分支并提交 Pull Request。
- 不直接向 `main` 推送，不强制推送，不改写已发布 Tag。
- 普通接口改动至少需要 1 名维护者审核。
- 不兼容修改、安全相关控制报文或同时影响多个系统的改动应由 2 人复核。
- DBC、Proto、说明文档、测试和更新记录在同一个 PR 中同步修改。

## 分支命名

```text
can/add-pdm-status
can/update-fan-diagnostic
telemetry/add-energy-field
docs/correct-canb-byte-order
```

## 提交接口变更

1. 创建或关联 Issue。
2. 从最新 `main` 创建分支。
3. 只修改一个清楚的接口主题。
4. 执行 `.venv/bin/python tools/validate_interfaces.py`；首次使用先按 README 创建仓库内 `.venv`。
5. 更新 `CHANGELOG.md`。
6. 提交 PR，并写明受影响项目、兼容性和验证结果。

## CAN 修改要求

- 新 ID 先查 `docs/CAN_ID分配.md` 和对应总线的正式 DBC。
- 写明发送节点、接收节点、标准/扩展帧、DLC、周期或触发条件。
- 每个字段写明字节序、符号、比例、偏移、单位、范围和无效值。
- 已发布报文的 ID、DLC、字节序或比例变化属于高风险修改，必须提供迁移方案。

## Protobuf 修改要求

- `telemetry/fsae_telemetry.proto` 是唯一协议源。
- 已发布字段号不得修改或分配给其他字段。
- 删除字段时使用 `reserved` 保留字段号，必要时同时保留字段名。
- `repeated` 和字符串字段同步检查 `fsae_telemetry.options` 的 Nanopb 上限。
- 生成的 `.pb.c/.h` 不作为手工编辑源；由固定版本的协议重新生成。

## 安全要求

- 不提交真实 Broker 地址、密码、Token、证书私钥或服务器部署信息。
- 示例配置使用 `${MQTT_HOST}`、`${MQTT_USERNAME}`、`${MQTT_PASSWORD}` 等占位符。
- 如果秘密已经进入 Git 历史，不能只删除当前文件；必须立即轮换秘密并清理历史。
