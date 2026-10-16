# 通用邮件 HTTP 服务

各项目后端 → 本服务 HTTP API → 腾讯云 SES SMTP（TLS 465）→ 收件邮箱。

SMTP 密码集中配置；每个项目分配独立 API Key，调用方无法更换发信人。
当前默认发信人 token@scor.vip；收件人由各项目后端指定。
仅用于已授权的业务通知，不直接供浏览器调用。

## 配置

复制 `.env.example` 为 `.env`，填入既有 SMTP 密码。每个项目分别生成随机密钥，例如
`python -c "import secrets; print(secrets.token_urlsafe(32))"`。
将密钥填入 `MAIL_API_KEYS` JSON（项目名到密钥的映射）。不要提交 `.env`。

`MAIL_DAILY_LIMIT` 默认 100，为全项目合计的 UTC 日尝试次数上限，包含失败尝试。
这是本服务的独立限制，不能代替腾讯云额度；其他直接使用该腾讯账号的发信也会消耗云额度。
首次启动缺少 SMTP 密码或有效 API Key 会直接报错。

## 接口

`POST /v1/emails`

请求头：

```text
Authorization: Bearer <该项目的 API Key>
Idempotency-Key: contact:<业务记录ID>
Content-Type: application/json
```

```json
{
  "to": "chenjiwei@moorechipsea.com",
  "subject": "scor.vip 新留言",
  "text": "留言内容",
  "reply_to": "visitor@example.com"
}
```

必填 `to`、`subject`、`text`，可选 `html` 和 `reply_to`。每次只接受一个收件人；
不支持附件、批量群发、自定义发信地址。正文不保存到数据库。

响应示例：

```json
{"id":"邮件ID","status":"accepted","created":"UTC时间","error":null}
```

`GET /v1/emails/<邮件ID>` 使用相同 Authorization，只能查询本项目记录。
`GET /health` 检查进程和本地数据库，不验证 SMTP 可用性。

| 状态 | 含义 |
|---|---|
| accepted | SMTP 已接收，不代表进入收件箱 |
| sending | 已登记，正在发送；若进程中断，需要人工核查 |
| failed | SMTP 明确拒绝 |
| unknown | 网络异常等造成结果不明，可能已被接收 |

首次 SMTP 失败返回 HTTP 502，参数错误 400，认证错误 401，幂等键冲突 409，日上限 429。
同项目同幂等键同内容重复请求只返回已保存记录（HTTP 200），不会再次发送；调用方必须读取 `status`。
同键不同内容被拒绝。SQLite 事务确保多个工作进程或并发请求不会重复发送。
发送记录仅保存 ID、项目名、幂等键、请求哈希、状态、时间、通用错误码。

服务采取同步发送，无自动重试或后台队列。客户端超时后，应使用原幂等键重查；
`unknown` / 长期 `sending` 先查腾讯云记录，不要换键盲目重发。明确失败并修复后，可用新的业务重试键发起。
应用与远端 SMTP 之间不能保证严格的“恰好一次”投递，因此保留不确定状态，避免静默重复。

## 本地验证与部署边界

```powershell
python -m pip install -r requirements.txt
python -m unittest -v
```

Flask 本地运行需要先将配置载入进程环境：
`python -m flask --app app:create_app run --host 127.0.0.1 --port 5080`。
Flask 不保证自动读取此目录 `.env`，Docker Compose 通过 env_file 明确加载。

Dockerfile / compose.yaml 是待部署配置，当前尚未在生产执行。
需要走既有服务器发布流程，使用 `docker compose up -d --build` 前核验配置、端口和数据卷。
默认仅监听服务器 127.0.0.1:5080。其他容器不能用自己的 localhost 访问此端口；
正式接入时需按现有反向代理/容器网络配置内部地址，跨主机使用 HTTPS。
API Key 只放在各项目后端，禁止嵌入前端代码。

数据库在 Docker 命名卷中持久保存。不要删除数据卷，否则发送记录和防重复状态会丢失。
本版本未实现收件回执、退信回调或多机共享数据库；部署一份实例即可。

## SMTP 核验

2026-10-16：从本机使用本地凭据库中已有密码连接 smtp.qcloudmail.com:465，
TLS 与认证通过（235）。凭据原值未复制到此项目或文档。
腾讯云地址说明：https://cloud.tencent.com/document/product/1288/65750

同日通过 Flask HTTP 测试客户端调用真实发信接口，向 chenjiwei@moorechipsea.com 发送一封测试邮件。
SMTP 接收成功，接口返回 HTTP 200 / accepted；邮件 ID：
`5b886234-2cae-4fca-b1b6-fd899c391662`。收件箱实际到达尚待接收方确认。
本地自动测试 8 项通过；Docker 构建与生产部署尚未验证。
