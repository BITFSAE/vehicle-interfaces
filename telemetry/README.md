# 遥测协议维护

本次接口审计已将 CANRS485_G473/REFERENCE/protobuf-master 的服务器 Proto/Options 与车端副本逐字节核对，当前中央副本无需改动；生成的 Nanopb/Python 文件仍不属于本仓库的手工编辑源。

`fsae_telemetry.proto` 是遥测消息的唯一协议源，`fsae_telemetry.options` 只负责 Nanopb 的静态容量限制。生成的 `.pb.c/.pb.h` 应在使用方通过固定版本的 Protobuf、Nanopb 重新生成，不在这里手工维护。

能量计保持两个独立消息：`ivt_telemetry` 是一般始终安装的车队自有 IVT-S，U1 为电池侧总压、U2 为电池外侧/逆变器侧（Pre）总压；`energy_meter` 是只在比赛安装的赛会 IVT 或 FS Datalogger，U1 为逆变器侧总压。功率和 Wh 是 `optional`，设备未发对应 CAN 帧时发送端不得补算或写入零值。

## 新增域（2026-08-14）

- `bms_telemetry`：BMS 状态机、告警等级、继电器/充电状态与最近预充结果；预充电压即 `ivt_telemetry.voltage_u2_mv`，不重复上报。
- `imd_telemetry`、`sop_limits`、`charger_telemetry`、`pdm_telemetry`、`fan_telemetry`：分别对应 CAN1 IMD/HV 状态、CANB SOP、Chroma、PDM、FanController。
- `thermal_summary` 用于轮胎红外温度（CANB `0x071..0x074`），帧→轮位映射待实物确认。
- legacy 规则：`vcu_status`/`ready_to_drive` 无真实 ECU/VCU 源时保持 0，禁止用 BMS 状态代填。

## 兼容规则

- 已发布字段号不可改变或复用；删除字段使用 `reserved`；
- 新字段优先追加，不依赖字段声明顺序作为线上顺序；
- 字段名或注释必须明确单位和比例；
- `repeated`、字符串和字节字段同步设置可接受的 Nanopb 上限；
- 修改后至少验证 STM32 编解码、服务器接收和历史数据兼容性。

## MQTT 与部署配置

Proto 定义 Payload，不负责保存 Broker 地址、Topic 权限或认证秘密。MQTT 关闭匿名连接后：

- 仓库可以提供变量名、Topic 约定和脱敏示例；
- 用户名、密码、证书私钥和生产地址通过部署环境、设备安全配置或 GitHub Secrets 注入；
- 凭据轮换不应要求修改 Proto 或提交新的协议版本；
- 如果认证方式或 Topic 结构影响客户端兼容性，应记录到 `CHANGELOG.md` 并提供迁移顺序。
