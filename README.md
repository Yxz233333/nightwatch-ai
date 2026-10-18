# 夜行 AI 观察站

主站：https://ai.zmh.icu

公开 AI 阅读站：https://jiankong.ai.zmh.icu

## 网站与账号

主站为本机 Node.js + SQLite 服务，监听 127.0.0.1:8791，经独立 Cloudflare Tunnel 对外提供 HTTPS。首次可直接在网站创建个人账号，密码至少8位。账号创建后关闭首次创建入口，后续通过相同账号登录。密码采用带随机盐的 scrypt 散列，浏览器使用 HttpOnly 会话。数据文件 data/nightwatch.sqlite 不提交 GitHub。

ChatGPT 与 Codex 分功能更新/功能预告；AI资讯分今日推荐/其他内容，其他内容保留行业新闻、模型动态、工具动态；OpenAI论文单列。板块和分类使用独立路径，支持刷新和浏览器前进后退。论文保留英文原题、原始摘要、原文及独立审查状态说明，后续中文解读由每日整理逐步补充。首轮导入不是全部历史资讯的穷尽回溯。

## GPT 阅读入口

公开站由 GitHub Pages 托管，不要求登录。它包括完整内容库，也精准保留用户主动标记。用户同意公开喜欢和想深入了解的标记，不公开账号、密码、会话和监控日志。

- /content.json：全部内容，interest 数组给出标记类型及时间。
- /interests.json：所有已标记条目。
- /likes.json：喜欢。
- /learn.json：想深入了解。
- /chatgpt.json、/codex.json、/news.json、/papers.json：按板块读取。
- /articles/固定编号/：单条 HTML；该路径下 content.json 为单条结构化内容。
- /llms.txt：AI 读取说明。

点赞和取消标记后，后端运行 publish-public.mjs 导出、提交及推送公开快照；每分钟重试同步。GitHub Pages 构建通常需要额外时间，公开页顶部显示最后快照同步时间，不能误称零延迟。电脑关机时主站登录/标记不可用，公开站保留最近已发布快照。

## 更新和维护

每日北京时间08:00由本聊天的“夜行 AI 网站每日更新”自动化负责检索、核实、中文整理及发布。GitHub 不执行资讯采编。仅可信、已核实的未来计划进入功能预告；没有可核实预告时允许为空，不能填充推测。更新 public/content.json 时保留稳定ID和历史条目，原子替换；不要覆盖用户数据库。之后执行 `node publish-public.mjs` 并回读公开站。

不要用 build-initial.py 覆盖已经编辑的内容库；该脚本仅用于首次导入。数学材料来自 OpenAI math 仓库，保留 Apache-2.0 许可证及出处。

start-local.ps1 启动本项目的服务、隧道和独立转接进程；stop-local.ps1 仅停止本项目。reconnect.ps1 只重启本项目的隧道与转接，不停止数据库后端。隧道凭据保留在本机 .cloudflared 目录，ai-tunnel.yml 本机配置已忽略，绝不提交凭据。

## 夜行监控

桌面快捷方式“夜行监控”统一管理荐书与AI服务器。两个服务器独立在后台每5秒检查，公网入口每60秒检查；窗口隐藏也继续监控。点击顶部服务器仅显示已缓存状态，不启动新的检查、不重置计时和日志。荐书的自动重连设置在切换时保留。启停与重连分别按所属服务器执行。

监控源码位于 H:\shichangdiaoyan\sites\reading-preferences\monitor，夜行监控.exe 为正式程序。

## 验证

`node verify-backend.mjs` 使用临时隔离数据库，验证8位密码/7位拒绝、登录权限、标记保存与取消、完整库及兴趣导出、凭据不公开。实际账号由用户自行创建，测试不能使用用户真实账号。
