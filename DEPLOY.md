# 语镜公网部署（Render · 不连 GitHub 也能做）

> 目标：拿到 `https://lingualens-xxxx.onrender.com`，手机在**任何网络**下都能打开。
>
> 代码已经在 GitHub 的 `deploy` 分支：<https://github.com/lmc-123-DOT/lingualens/tree/deploy>
> 仓库是公开的，所以 Render 可以直接用「Public Git Repository」拉取，**不需要授权 GitHub 账号**。

---

## 0. 先关代理

Render 直连能打开；开着代理时 Edge 可能白屏（证书校验状态被打断）。
如果页面白屏：把代理关掉，**完全退出 Edge 再重开**。

## 1. 注册 Render（用邮箱）

1. 打开 <https://dashboard.render.com/signup>
2. 填邮箱 + 密码，点 **Sign in / Sign up**
3. 去邮箱点验证链接
4. 不需要点「Continue with GitHub」

## 2. 创建 Web Service

1. 右上角 **New +** → **Web Service**
2. 选 **Public Git Repository** 标签（不是 GitHub）
3. 填仓库地址：

   ```
   https://github.com/lmc-123-DOT/lingualens
   ```

4. Branch 填 **`deploy`**
5. 其它配置：

   | 项目 | 填什么 |
   |---|---|
   | Name | `lingualens` |
   | Region | `Singapore`（不行就选 Oregon） |
   | Runtime | **Docker**（会自动识别） |
   | Plan | **Free** |
   | Health Check Path | `/api/health` |

6. 展开 **Environment Variables**，加三条：

   | Key | Value |
   |---|---|
   | `LINGUALENS_PASSWORD` | 自己设一个强密码，记下来 |
   | `LINGUALENS_REQUIRE_AUTH` | `1` |
   | `LINGUALENS_DATA` | `/data` |

7. 点 **Create Web Service**，等构建 3–6 分钟（会下载学习站台词库）。

## 3. 打开和登录

1. 构建完成后，服务页顶部就是地址：`https://lingualens-xxxx.onrender.com`
2. 浏览器会弹登录框：
   - 用户名：随便填，例如 `lingualens`
   - 密码：第 2 步设置的 `LINGUALENS_PASSWORD`
3. 登录后就是完整界面，手机尺寸自动使用底部导航。

## 4. 手机 / 平板

1. 手机在 4G / 5G / 任何 Wi-Fi 下打开上面的 HTTPS 地址。
2. 第一次会要求登录，用户名随便填，密码同上。
3. **添加到主屏幕**：
   - iPhone：Safari 分享 → 添加到主屏幕
   - 安卓：Chrome 菜单 → 添加到主屏幕
4. HTTPS 下语镜自带 manifest 和 service worker，可以像 App 一样独立窗口运行。

## 5. 免费版要知道的

| 事项 | 说明 |
|---|---|
| 休眠 | 15 分钟没人访问会休眠，下一次打开等 30–60 秒冷启动 |
| 数据 | 免费实例没有持久磁盘，**重新部署或重启后历史会清空** |
| 长期保存 | 升级 Starter，加 1 GB Disk 挂 `/data`，保持 `LINGUALENS_DATA=/data` |
| 更新代码 | Public Git Repository 没有自动部署；改完推 `deploy` 后，在服务页点 **Manual Deploy → Deploy latest commit** |
| 学习站台 | Docker 构建时从上游公开数据源下载并生成，下载失败会自动跳过，其它功能不受影响 |
| 密码 | 单用户 Basic Auth；个人使用够用 |

## 6. 常见问题

**页面白屏 / 打不开**：先关代理并完全重启浏览器；再确认打开的是 `https://`。

**构建失败**：服务页 → Logs → Build，看最后 30 行。多半是网络超时，点 **Manual Deploy → Clear build cache & deploy** 重试。

**502 / 一直转圈**：免费实例冷启动，等 30–60 秒。

**登录框反复弹**：确认是 HTTPS；Basic Auth 每个新的浏览器会话会再问一次。需要「记住我」的登录页可以再改。

**翻译失败**：免费引擎有限额；在页面「设置 → 翻译引擎」里配置 AI Key。

## 7. 安全

- 必须保留 `LINGUALENS_REQUIRE_AUTH=1` 和 `LINGUALENS_PASSWORD`。
- 不要把 `.env`、API Key、`data/` 提交到 GitHub。
- 学习站台数据来自第三方公开数据集，许可证见 `THIRD_PARTY_NOTICES.md`；只在个人部署的镜像里构建，不提交到仓库。

---

## 附：以后接了 GitHub，可以用 Blueprint

如果之后网络方便、愿意把 GitHub 授权给 Render，可以直接用仓库里的 `render.yaml`：

1. Render → **New +** → **Blueprint**
2. 选 `lmc-123-DOT/lingualens`，分支 `deploy`
3. Apply；密码会自动生成，在 Environment 里查看
4. 之后推 `deploy` 分支会自动部署

## 附：不用 Render 的替代方案

- **Docker Compose**：`cp .env.example .env`，改强密码，`docker compose up -d --build`，打开 `http://127.0.0.1:8000`。
- **Railway / Fly.io**：支持 Docker，把仓库指过去即可。
- **自己的云服务器**：`docker build -t lingualens .`，`docker run -d -p 80:8000 -e LINGUALENS_PASSWORD=... -v /srv/lingualens:/data lingualens`，前面用 Caddy/Nginx 配 HTTPS。
- **Cloudflare Tunnel**：从本机临时映射公网地址，电脑必须一直开着。
