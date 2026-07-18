# BITFSAE Vehicle Interfaces

BITFSAE 整车通信接口的公共仓库。这里统一维护 CANA、CANB、CANC 的 DBC，以及车载遥测使用的 Protobuf/Nanopb 配置。

`main` 只保存已经校验和审核的接口。各 MCU、遥测和分析项目应固定使用某个 Release 或 Commit，不应继续在各自仓库中独立维护另一份“正式协议”。

## 当前内容

| 路径 | 内容 | 权威性 |
| --- | --- | --- |
| `can/Vehicle_CanA.dbc` | 整车 CANA 定义 | 当前正式来源 |
| `can/Vehicle_CanB.dbc` | ECU 新版 CANB，已合入 PDM 和 FanController | 当前正式来源 |
| `can/Vehicle_CanC.dbc` | ECU 提供的 CANC 定义 | 当前正式来源 |
| `telemetry/fsae_telemetry.proto` | 遥测 Protobuf | 唯一协议源 |
| `telemetry/fsae_telemetry.options` | Nanopb 静态容量配置 | 与 Proto 同步维护 |
| `docs/CAN_ID分配.md` | CAN ID、节点和用途索引 | 便于人工审核，DBC 仍是字段权威来源 |
| `docs/协作与维护方案.md` | 权限、分支、审核、发布和交接流程 | 仓库维护规则 |
| `docs/迁移与待确认项.md` | 从旧工程迁入时尚未确认的内容 | 不属于已发布接口 |

## 使用方式

```bash
git clone https://github.com/BITFSAE/vehicle-interfaces.git
cd vehicle-interfaces
```

正式使用时固定到 Release，例如：

```bash
git checkout v1.0.0
```

固件仓库应在 README、构建配置或接口版本文件中记录所使用的 `vehicle-interfaces` 版本。

## 修改接口

1. 先提交 Issue，说明节点、总线、方向、周期、字段、单位、范围和兼容性。
2. 创建功能分支修改 DBC/Proto、对应文档和 `CHANGELOG.md`。
3. 提交 Pull Request，等待自动检查和 CODEOWNERS 审核。
4. 合并后由维护者在稳定节点创建 Tag/Release。

完整要求见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [协作与维护方案](docs/协作与维护方案.md)。

## 公开仓库边界

本仓库只保存接口定义和脱敏示例，不保存：

- MQTT、服务器、数据库的真实密码或 Token；
- TLS 私钥、证书私钥、SSH 私钥；
- 生产服务器 IP、SSH 命令和部署账号；
- GitHub Actions Secret 的实际值；
- 无权再次发布的厂家文档或协议文件。

MQTT 后续关闭匿名连接后，用户名、密码和证书保存在服务器环境变量、设备安全配置或 GitHub Secrets 中。本仓库最多提供不含真实值的 `.example` 配置。

## 许可证

当前尚未确定对外授权方式。在车队确认许可证及第三方文件再发布权限前，请不要向本仓库加入来源和授权不明确的厂家材料。
