# 更新记录

## 未发布

### 已完成

- 由 `DATA_COLLECTION_INTEGRAL` 采集端确认 CANB 胎温 `0x71..0x74`：轮位依次为 FL、FR、RL、RR，每帧记录 MLX90640 图像从上到下四个水平带的平均温度；正式 DBC、CANdb++ 交付副本、接口说明和待确认清单同步更新。
- BMS 告警开关帧 `0x187F50F4` 升为版本7：从控未就绪和从控离线改为全状态动作开关，新增电压/温度采样线断线动作位；单体压差和新增动作位默认开启，单体过压默认值改为4300mV。同步更新 CAN1 DBC、CANdb++ GBK 副本、接口文档和关键字段校验，并把工具协议当前版本说明修正为5。
- 按 FanController 协议 V3 与 F405 电池箱风扇固件复核两套风扇接口：DBC 注释补充 `0x5A3` 温度无效哨兵、`0x08` Action 1..6、`0x5A5` 结果 7、`0x5A9` 供电档位锁定、`0x5AA`/ `0x5AB`/`0x5AC`/`0x5AD`/`0x5AE` 的保存与上下限约束；`CANB接口.md` 补齐 Action 1..6、PDM 四字段离线判定和电池箱风扇中止条件；`CAN1接口.md` 修正 `0x186E50F4` 条件发送周期；接口校验脚本补齐 `0x5A4`/`0x5AA..0x5AE`/`0x186E50F4` 帧回归。
- 现网只读核对确认 `alarm_state` 已有 `severity/alarm_name/message` fields 和 `alarm_id` tag；Grafana 指南补充当前活动告警 Table 的查询、去重、等级配色、时区与时间含义，并标明 G473 包级摘要 ID 超出公共 Proto 约定的问题。
- FanController 风扇子系统报文在 `Vehicle_CanB.dbc` 补齐 `GenMsgCycleTime` 周期属性（`0x5A0/0x5A1/0x5A2/0x5A8/0x5A9` 100 ms、`0x5A3` 500 ms、`0x5AE` 500 ms）；`CANB接口.md` 修正 `0x08` Action 5 的描述为一次提交电池档和 DCDC 档两档上限，并注明 COMPLETED 会话重复停止不丢失提交资格。
- 遥测 `alarms[]` 的 Nanopb 上限由 8 扩展到 32，定义 `alarm_id=0..31` 对应 BMS 故障 bit，一级故障映射 `FATAL`、二级告警映射 `WARNING`；对照表与 Grafana 指南同步 raw/clean MQTT 桥、告警名称和链路健康统计。
- 新增 BMS 电池箱风扇 CANB `0x5AA..0x5AD` 和 CAN1 `0x186E50F4`，并补齐 `0x186250F4` 标定、远程租约和标定会话状态位；正式 DBC 与接口文档同步定义 35 W Chroma/70 W 高压两档限值、控制应答和保存状态。
- FanController 协议升为 V3，新增 `0x5AE` 两档保存限值状态和存储错误应答；电池低压与 DCDC 高压分别标定，未标定上限为 15%。
- 自有 IVT-S `0x512..0x519` 从 CANB 迁到 CAN1/500 kbit/s；八个消息及 `IVT_S` 节点从 `Vehicle_CanB.dbc` 移入 `Vehicle_Can1.dbc`，Chroma/Legacy 的 CANB 位率切换不再影响 IVT。`CAN1接口.md` 补齐八通道布局；`CAN与遥测对照.md` 改为 CAN1 接收自有 IVT，CANB 同 ID 不作为网关输入。
- 清理 CANdb++ DBC 重复交付物：每条总线仅保留 UTF-8/LF 正式源和 GBK/CRLF 交付副本，删除无 BOM UTF-8 及 UTF-8 BOM 副本；archive/ 历史参考资料不变。
- BMS SOP `0x4A0/0x4A3` 保持 10 ms 周期，发送条件收紧为放电模式高压接通后；自检、待机、预充、故障保持和充电模式不发送，避免占用 Chroma 通讯时间。
- Chroma `0x10/0x11/0x13/0x14` 四类反馈周期配置由 100 ms 临时调整为 500 ms，用于降低 CANB 负载；当前 500 ms 新鲜度超时保持不变，待实物确认抖动余量。
- BMS 故障帧格式升为版本4：fault bit22 保留并固定为0，外部安回断开事件改由 CAN1 `0x186950F4` Byte0 bit4 上报；版本3的 bit22 保留为历史兼容说明。
- BMS 固件身份码 3 保留为未知值，不再对应临时测试分支。
- Chroma 节点基准改为 `0x200`，六个 CANB ID 按 `+1/+2/+4/+5/+0x90/+0x91` 派生为 `0x201/0x202/0x204/0x205/0x290/0x291`；已同步固件、can-host、遥测网关、DBC 和地址分配文档。
- CANRS485_G473 对齐 BMS 与 FanController DBC：补齐 BMS 完整位、风扇状态、故障状态/版本、32 项告警等级、八类 IVT-S 结果和 SOP CRC；补齐 FanController `0x5A6..0x5A9` 解码。公共 Proto 尚无对应字段的内容标记为“已解析/未上报”。
- 建立 CANB 接口确认框架：在 `docs/CANB接口.md` 增加完整 CANB 报文总表和各报文确认状态；区分 BMS 已确认、ECU 待确认、节点待确认和赛会待确认。
- 将 CANB 周期、触发条件和优先级明确为“当前暂定值”，允许 ECU/各节点结合实际调整，不把现有值作为最终要求。
- 新增 [`docs/ECU_SOP实现确认.md`](docs/ECU_SOP实现确认.md)，由 ECU 负责人填写最终 SOP 接收、限值、扭矩、`0x4A4`、周期和目标策略；增加了“暂定策略合理性审查”和“误触发/恢复风险”检查。
- 将 [`docs/迁移与待确认项.md`](docs/迁移与待确认项.md) 改为可追踪的确认清单，明确各节点不仅要给 DBC，还要提供报文说明、周期、处理优先级和最终策略。
- 将 [`docs/协作与维护方案.md`](docs/协作与维护方案.md) 和 [`README.md`](README.md) 补充节点确认责任、发布阻断项和当前状态。
- 更新 PDM 低压遥测 `0x5A0/0x5A1` 发送周期为 100 ms，以支持快速闭环功率限制；电池支路电流方向已串口实测确认（正=放电）。
- 在 `Vehicle_CanB.dbc` 与接口文档中新增 FanController 功率仲裁状态帧 `0x5A8`（`FanController_PowerStatus`，100 ms）与标定状态帧 `0x5A9`（`FanController_CalibStatus`，会话非 INACTIVE 时 100 ms）；同步补齐 `0x5A6/0x5A7` 字段、命令/应答枚举和限功率原因。

### 待确认（发布 `v1.0.0` 前必须完成）

- ECU 负责人确认 `0x305`、`0x310`、`0x502..0x509` 和 `0x4A4`；
- ECU 负责人填写 [`docs/ECU_SOP实现确认.md`](docs/ECU_SOP实现确认.md)，并说明策略是否过严、是否高频误触发 0 动力；
- ECU 负责人提交 `0x305`、`0x502..0x509`、`0x4A4` 报文说明文档；
- Display/HMI/遥测负责人确认 GPS `0x067..0x06A`、`0x301` 和 IMU `0x050/0x060..0x066` 的周期和优先级；
- PDM 负责人确认 `0x5A0/0x5A1`；
- FanController 负责人确认 `0x5A2..0x5A9/0x5AE`；
- 方向盘/HMI 负责人确认 `0x700/0x784` 和 `0x310`；
- 赛会设备/遥测负责人确认 `0x430/0x521/0x522/0x526/0x528`；
- 用台架或整车原始帧复核全部正式 DBC 字段；
- 选择并确认仓库许可证和第三方 DBC 授权；
- 创建首个稳定 Tag 和 Release `v1.0.0`，并通知下游固定版本。
