# 遥测协议维护

`fsae_telemetry.proto` 是遥测消息的唯一协议源，`fsae_telemetry.options` 只负责 Nanopb 的静态容量限制。生成的 `.pb.c/.pb.h` 应在使用方通过固定版本的 Protobuf、Nanopb 重新生成，不在这里手工维护。

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
