# 给助手的说明

这台电脑上的 `boss` 是招聘助手的命令行。程序装在 `%LOCALAPPDATA%\HRAssistant`，该目录已加入当前用户的 PATH。新开的终端才能看到 `boss`。

需要机器可读结果时加上 `--json`，并且必须写在子命令前面，例如 `boss --json status`。stdout 是一行 JSON，先看 `ok`。失败时读 `error.code`、`error.recoverable` 和 `error.recovery_action`。

## 登录

1. 先运行 `boss status`。
2. 还没有登录就运行 `boss login`。
3. `boss login` 会先读取本机 Chrome 或 Edge 里已经登录的招聘网站状态。读不到时，会打开窗口让 HR 扫码。不要跳过这一步，也不要自己填写账号或密码。
4. 登录信息在用户主目录的 `.boss-agent`。再次安装不会删除它。

Windows 上较新的 Chrome 和 Edge 可能因为浏览器自己的加密而读不到已有登录。这时弹出扫码窗口是正常退路，不是安装失败。登录步骤保持原样，不要为了读 Cookie 去改它。

## 常用命令

- `boss hr whoami`：看当前是不是招聘者身份
- `boss hr candidates 关键词`：找候选人
- `boss hr recommendations --job-id <职位加密 ID>`：看推荐候选人
- `boss hr greet ... --dry-run`：先预览招呼。HR 明确同意后，才把 `--dry-run` 换成 `--yes`
- `boss hr location <friend_id> --dry-run`：先预览工作地点卡片。HR 明确同意后，才改成 `--yes`

## 必须遵守

- 任何会发出消息、打招呼或发送工作地点的操作，必须先得到 HR 本人的确认。
- 不要自动加上 `--yes`。预览不算同意。
- 同一位候选人不要重复发送工作地点。
- 需要立刻停下自动操作时，运行 `boss agent stop`。
- 不要读取、拷贝或外发 `.boss-agent` 里的登录文件。
