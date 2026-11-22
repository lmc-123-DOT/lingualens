# 语镜公网部署（GitHub + Render）

> 目标：拿到一个 `https://lingualens-xxxx.onrender.com` 地址，手机在**任何网络**下都能打开，不用和电脑在同一个 Wi-Fi。

GitHub 只负责存代码，实际运行在 Render 的 Docker 容器里。仓库里已经有 `Dockerfile` 和 `render.yaml`，按下面点几下就行。

---

## 0. 准备

- 一个 GitHub 账号（代码已经在 `lmc-123-DOT/lingualens` 的 `deploy` 分支）
- 一个 Render 账号：<https://render.com>，直接用 GitHub 登录
- 首次构建约 3–6 分钟（会顺便下载并生成学习站台词库）

---

## 1. 在 Render 创建 Blueprint

1. 打开 <https://dashboard.render.com>，用 GitHub 登录。
2. 右上角 **New +** → **Blueprint**。
3. 选择仓库 `lmc-123-DOT/lingualens`，分支选 **`deploy`**。
4. Render 会自动读取 `render.yaml`，显示一个叫 `lingualens` 的 Web Service。
5. 点 **Apply / Create**，等构建完成。

> `render.yaml` 里已经配好：Docker 运行、免费实例、新加坡区域、健康检查 `/api/health`、自动部署。
> 第一次创建时 Render 会自动生成一个登录密码，不需要你手填。

## 2. 找到登录密码

1. 进入 Render 的 `lingualens` 服务页。
2. 左侧 **Environment**。
3. 找到 `LINGUALENS_PASSWORD`，点右边的眼睛图标显示，复制下来。
4. 想换成自己的密码，就点 Edit 改掉，保存后服务会自动重启。

## 3. 手机打开

1. 打开服务页顶部的地址，例如 `https://lingualens-abcd.onrender.com`。
2. 浏览器会弹登录框：
   - 用户名：随便填，例如 `lingualens`
   - 密码：上一步复制的 `LINGUALENS_PASSWORD`
3. 登录后就是完整界面，手机尺寸自动使用底部导航布局。
4. **添加到主屏幕**：iPhone 用 Safari 分享 → 添加到主屏幕；安卓 Chrome 菜单 → 添加到主屏幕。
   通过 HTTPS 打开时，语镜已经带 manifest 和 service worker，可以像 App 一样独立窗口运行。

## 4. 免费版要知道的几件事

| 事项 | 说明 |
|---|---|
| 休眠 | 15 分钟没人访问会休眠，下一次打开要等 30–60 秒冷启动 |
| 数据 | 免费实例没有持久磁盘，**重新部署或重启后历史记录、设置会清空** |
| 想长期保存 | Render 升级到 Starter，加一块 1 GB Disk，挂载到 `/data`，并保持 `LINGUALENS_DATA=/data` |
| 翻译引擎 | 免费引擎（MyMemory / Google）可能限流；要稳定就用户在页面「设置」里填自己的 AI Key |
| 学习站台 | Docker 构建时会从上游公开数据源下载并生成 `lexicon.db`；下载失败会自动跳过，其他功能不受影响 |
| 密码 | 单用户 Basic Auth，全站都要密码；这是个人使用的轻量方案 |

## 5. 以后更新

- 代码改动推到 `deploy` 分支，Render 会自动重新部署（`autoDeploy: true`）。
- 如果之后把 `deploy` 合并进 `main`，把 Render 的分支改成 `main` 即可，也可以继续用 `deploy`。

## 6. 常见问题

**构建失败**：进服务页 → **Logs** → Build，把最后 30 行发我。最常见是某一步 pip 超时，点 **Manual Deploy → Clear build cache & deploy** 重试即可。

**打开 502 / 一直转圈**：免费实例在冷启动，等 30–60 秒再刷新。

**登录框一直弹**：确认地址是 `https://`，不是 `http://`；Basic Auth 在每次新的浏览器会话里会再问一次。也可以之后我帮你换成带「记住我」的登录页。

**手机打不开但电脑能开**：先在电脑上试同一个地址；如果电脑也要等很久，是冷启动；如果电脑正常、手机不行，检查手机是否开了代理/VPN，或换浏览器试。

**翻译失败**：免费引擎有额度；在页面右上角「设置 → 翻译引擎」里配置 AI 精准模式（DeepSeek 等 OpenAI 兼容接口）。

## 7. 安全与费用

- Render 免费 Web Service 目前不需要付费；超过免费额度或要持久磁盘才收费。
- 必须保留 `LINGUALENS_REQUIRE_AUTH=1` 和 `LINGUALENS_PASSWORD`，否则公网任何人都能打开你的历史记录。
- 不要把 `.env`、API Key、`data/` 提交到 GitHub；仓库的 `.gitignore` 已经排除。
- 学习站台词库来自第三方公开数据集，许可证见 `THIRD_PARTY_NOTICES.md` 和 `lexicon/SOURCES.md`；仅在个人部署的镜像内构建，不提交到公开仓库。

---

## 附：不用 Render 的替代方案

- **Docker Compose**：`cp .env.example .env`，改强密码，`docker compose up -d --build`，打开 `http://127.0.0.1:8000`。
- **Railway / Fly.io**：同样支持 Docker，把仓库指过去即可。
- **自己的云服务器**：`docker build -t lingualens .`，`docker run -d -p 80:8000 -e LINGUALENS_PASSWORD=... -v /srv/lingualens:/data lingualens`，前面用 Caddy/Nginx 配 HTTPS。
- **Cloudflare Tunnel**：从本机临时映射一个公网地址，电脑必须一直开着，适合临时演示。
