# Google Indexing API Service Account 设置指南

> **一次性设置，约 5 分钟**。设置完成后，GitHub Actions 会每天自动提交所有文章 URL 到 Google 索引。

## 为什么需要这个？

Blogger 的 `sitemap.xml` 自带 `X-Robots-Tag: noindex` 头，导致 GSC 显示"无法抓取"。
通过 Google Indexing API 可以绕过 sitemap，直接告诉 Google "这些 URL 有更新，请抓取"。
Indexing API 需要一个 Service Account 来认证。

---

## 设置步骤

### 第 1 步：打开 Google Cloud Console

1. 访问 https://console.cloud.google.com/
2. 登录你的 Google 账号（和 Blogger 同一个账号）

### 第 2 步：创建项目（如果已有项目可跳过）

1. 点击顶部导航栏的项目下拉
2. 点击「新建项目」
3. 项目名：`aitoolbits-indexing`
4. 点击「创建」

### 第 3 步：启用 Indexing API

1. 左侧菜单 →「API 和服务」→「信息中心」
2. 点击「+ 启用 API 和服务」
3. 搜索 `Web Search Indexing API`
4. 点击它 →「启用」

### 第 4 步：创建 Service Account

1. 左侧菜单 →「API 和服务」→「凭据」
2. 点击「+ 创建凭据」→「服务账号」
3. 服务账号名称：`indexing-bot`
4. 点击「创建并继续」
5. 角色选择：跳过（不需要）
6. 点击「完成」

### 第 5 步：下载 JSON 密钥

1. 在「凭据」页面，点击刚创建的服务账号邮箱
2. 切换到「密钥」标签
3. 点击「添加密钥」→「创建新密钥」
4. 密钥类型选择：**JSON**
5. 点击「创建」→ 文件会自动下载

### 第 6 步：在 GSC 中添加为所有者

> **关键步骤！** 不做这步 Indexing API 会返回 403。

1. 打开 https://search.google.com/search-console
2. 选择你的 `aitoolbits.blogspot.com` 站点
3. 左侧菜单底部 →「设置」→「用户和权限」
4. 点击「添加用户」
5. 邮箱填入 Service Account 的邮箱（在 JSON 文件里的 `client_email` 字段）
6. 权限选择：**拥有者** (Owner)
7. 点击「添加」

### 第 7 步：添加到 GitHub Secrets

1. 打开你的 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 点击「New repository secret」
3. Name: `GOOGLE_SERVICE_ACCOUNT_JSON`
4. Secret: 把下载的 JSON 文件的**全部内容**粘贴进去
5. 点击「Add secret」

---

## 验证

设置完成后，可以手动触发 GitHub Action 验证：

1. 打开仓库 → Actions 标签
2. 左侧选择「Google Indexing Auto-Submit (Daily)」
3. 点击「Run workflow」→「Run workflow」
4. 等待执行完成，查看日志

如果看到类似输出：
```
[OK] (1/57) https://aitoolbits.blogspot.com/2026/06/...
[OK] (2/57) https://aitoolbits.blogspot.com/2026/06/...
...
提交完成: 成功 57, 失败 0
```

说明 Indexing API 已经正常工作！

---

## FAQ

**Q: 不设置 Service Account 会怎样？**
A: 脚本仍然会运行，但只做 PubSubHubbub ping（效果较弱）。Indexing API 是最有效的自动索引提交方式。

**Q: 这个脚本多久运行一次？**
A: 每天北京时间 09:00 自动运行。也可以随时手动触发。

**Q: 会消耗 Google API 配额吗？**
A: Indexing API 免费配额：每天 200 次请求。你的博客约 57 篇文章，完全够用。

**Q: 已经提交过的 URL 重复提交有问题吗？**
A: 没有。Google 会智能判断 URL 是否有更新，重复提交不会受罚。
