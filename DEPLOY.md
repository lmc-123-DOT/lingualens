# 语镜公网部署（GitHub + Render）

> **GitHub 本身不能跑这个后端。** GitHub 是代码仓库；GitHub Pages 只能放静态网页，跑不了 Python、SQLite、翻译代理和查词接口。正确做法是：**代码放 GitHub，Render 从 GitHub 拉取并运行 Docker 服务**。

部署完成后你会得到类似 `https://lingualens-xxxx.onrender.com` 的 HTTPS 地址，手机浏览器直接打开就能用。

---

## 1. 把代码放到 GitHub

在 GitHub 新建一个 **Private** 仓库，例如 `lingualens`，然后把项目文件推上去。

```bash
cd "D:\大肥鱼\语镜翻译"
git init
git add .
git commit -m "LinguaLens v2.0.0"
git branch -M main
git remote add origin https://github.com/你的用户名/lingualens.git
git push -u origin main
```

不要提交 `.venv`、`data`、`logs`、`dist`，这些已经在 `.gitignore` / `.dockerignore` 里排除。

> **学习站台数据不要提交到公开仓库**：`lexicon/lexicon.db` 由第三方数据集构建，包含 CC BY-NC 和许可证未确认的数据。公开仓库只放代码；需要学习站台时，在部署机器上运行 `python fetch_lexicon_data.py` + `python build_lexicon.py`，或把数据库单独上传到私有服务器/私有镜像。许可证与署名要求见 `THIRD_PARTY_NOTICES.md`。

## 2. 在 Render 创建服务

1. 打开 [render.com](https://render.com)，用 GitHub 登录。
2. **New → Web Service**，选择刚才的仓库。
3. Runtime 选 **Docker**（仓库里有 `Dockerfile`）。
4. Instance 选 **Free**。
5. 在 Environment 里添加：
   - `LINGUALENS_PASSWORD`：设置一个强密码（必须设置，否则公网没有登录保护）。
   - `LINGUALENS_DATA`：`/data`
6. 点 **Create Web Service**，等构建完成。

也可以直接用仓库里的 `render.yaml` 创建 Blueprint，效果一样。

## 3. 手机访问

部署完成后打开 Render 给的 HTTPS 地址：

- 浏览器会弹出登录框：用户名随便填（例如 `lingualens`），密码填 `LINGUALENS_PASSWORD`。
- 登录后就是完整界面，手机尺寸会自动变成单列。
- 对照阅读页支持点词卡片；查词需要服务器能访问有道词典。

## 4. 数据持久化

免费实例的磁盘是临时的，重新部署/休眠重启后 SQLite 历史可能丢失。

要长期保存历史：

1. Render 升级到支持 Persistent Disk 的实例。
2. 添加 Disk，Mount Path 填 `/data`，大小 1 GB 即可。
3. 保持 `LINGUALENS_DATA=/data`。

## 5. 安全与费用

- 必须设置 `LINGUALENS_PASSWORD`；这是单用户 Basic Auth，适合个人使用。
- Render 提供 HTTPS，密码不会明文传输。
- 免费实例一段时间无人访问会休眠，首次打开会慢几十秒。
- 翻译免费引擎（MyMemory / Google）不需要 Key；AI 精准模式需要在页面设置里填自己的 API Key。
- 不要把 `.env`、数据库、API Key 提交到 GitHub。

## 6. 不用 Render 的替代方案

- **Docker Compose**：`cp .env.example .env`，把 `LINGUALENS_PASSWORD` 改成强密码，然后 `docker compose up -d --build`，打开 `http://127.0.0.1:8000`。
- **Railway / Fly.io**：同样支持 Docker，把 `Dockerfile` 指过去即可。
- **自己的云服务器**：`docker build -t lingualens .`，然后 `docker run -d -p 80:8000 -e LINGUALENS_PASSWORD=... -v /srv/lingualens:/data lingualens`，前面用 Caddy/Nginx 配 HTTPS。
- **Cloudflare Tunnel**：不想买服务器时，可以从这台电脑临时映射一个公网地址，但电脑必须一直开着。

> 公开仓库只放代码，不提交 `lexicon/lexicon.db`、`data/` 和 API Key。学习站台数据由使用者自己运行 `fetch_lexicon_data.py` + `build_lexicon.py` 生成，或单独挂载到部署环境；不要把第三方数据打进公开镜像。

---

部署遇到问题，把 Render 的构建日志发我，我按日志改。
