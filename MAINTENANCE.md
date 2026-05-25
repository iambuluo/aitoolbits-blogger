# aitoolbits-blogger 运维指南

## 🎯 项目概述

| 项目 | 信息 |
|------|------|
| 博客地址 | https://aitoolbits.blogspot.com |
| 内容方向 | AI Tools Reviews & Tutorials（全英文） |
| 发布频率 | 每天 3 篇（北京时间 8:17 / 14:42 / 21:08） |
| AI 引擎 | DeepSeek V3（$0.01/篇，月成本约 $1） |
| 发布方式 | GitHub Actions 自动生成 → Blogger API 自动发布 |

---

## 📌 你需要管什么？

### 日常：什么都不用管！

自动化流水线会：
- ✅ 每天自动从 57 个主题中随机选题
- ✅ DeepSeek API 自动生成 1500-2000 字英文文章
- ✅ Blogger API 自动发布到博客
- ✅ 自动添加标签（Labels）
- ✅ 随机时间偏移，模拟真人发布

---

## 🔑 关键凭据（保密！）

| 凭据 | 位置 | 用途 |
|------|------|------|
| DeepSeek API Key | GitHub Secrets | 生成文章 |
| Google OAuth | GitHub Secrets | 发布到 Blogger |
| Refresh Token | GitHub Secrets | 自动续期 Token |

### 凭据泄露了怎么办？
1. Google Cloud Console → 凭据 → 删除 OAuth 客户端 → 重新创建
2. DeepSeek Platform → 删除旧 Key → 创建新 Key
3. 更新 GitHub Secrets 中的值

---

## 📊 查看自动化运行状态

1. 打开 https://github.com/iambuluo/aitoolbits-blogger/actions
2. 查看 workflow 运行记录
3. 绿色 ✅ = 成功，红色 ❌ = 失败（点击查看日志）

---

## 🔧 手动操作指南

### 手动触发发布（不等到定时）

1. 打开 https://github.com/iambuluo/aitoolbits-blogger/actions
2. 点击左侧 "Publish Article"
3. 点击右侧 "Run workflow"
4. 可选：设置发布篇数（默认 1 篇）

### 本地手动发布

```bash
cd D:\小程序\aitoolbits-blogger
# 设置环境变量（Windows PowerShell）
$env:BLOGGER_CLIENT_ID = "你的Client ID"
$env:BLOGGER_CLIENT_SECRET = "你的Secret"
$env:BLOGGER_REFRESH_TOKEN = "你的Token"
$env:BLOGGER_BLOG_ID = "2759473256907748566"
$env:DEEPSEEK_API_KEY = "你的Key"

# 发布 1 篇
python scripts/publish_to_blogger.py 1

# 发布 5 篇
python scripts/publish_to_blogger.py 5

# 发布草稿（不公开）
python scripts/publish_to_blogger.py 1 --draft
```

---

## 💰 广告变现策略

### 当前阶段：无广告
- 先积累内容，准备申请 AdSense
- AD_PROVIDER = `none`

### 准备申请 AdSense（博客有 30+ 篇文章后）
1. Blogger 后台 → **Earnings（收入）** → 申请 AdSense
2. 确保博客无弹窗/低质量广告
3. 等待审核（通常 1-2 周）

### AdSense 通过后
1. 改 GitHub Secret：`AD_PROVIDER = monetag`
2. 可选：`AD_PROVIDER = adsense`（需填 AD_ZONE_ID）
3. Monetag 和 AdSense 可共存

### 广告配置方式（在 GitHub Secrets 中修改）
```
AD_PROVIDER = none     # 不插广告（当前）
AD_PROVIDER = monetag  # 每篇文章自动插入 2 个 Monetag 广告位
AD_PROVIDER = adsense  # 每篇文章自动插入 AdSense 广告
AD_ZONE_ID = 229646    # Monetag zone ID（或 AdSense ca-pub-XXXX）
```

---

## 📈 Google Search Console 提交

加速收录新文章：
1. 打开 https://search.google.com/search-console
2. 添加属性：`https://aitoolbits.blogspot.com`
3. 验证所有权（Blogger 自动验证）
4. 提交 sitemap：`https://aitoolbits.blogspot.com/sitemap.xml`

---

## ⚠️ 故障排查

### GitHub Actions 不运行了
- 检查：GitHub → Settings → Actions → General → 确保未禁用
- 检查：GitHub Secrets 是否配置完整

### 文章没发出来
- 查看 Actions 运行日志，找具体错误
- 常见原因：DeepSeek 余额不足、Blogger Token 过期

### Blogger Token 过期
- Refresh Token 通常永久有效
- 如果失效，需重新走 OAuth 授权流程（运行 `python scripts/oauth_setup.py`）

### DeepSeek 余额不足
- 登录 https://platform.deepseek.com/top_up
- 最低充值 5 元（够用 5 个月）

---

## 🎯 里程碑规划

| 时间 | 目标 | 操作 |
|------|------|------|
| **现在** | 博客已有 10 篇文章 ✅ | 自动化运行中 |
| **2 周后** | 累积 50+ 篇 | 自动积累 |
| **1 个月后** | 累积 100+ 篇 | 申请 AdSense |
| **3 个月后** | 累积 300+ 篇 | 开始有稳定收入 |

---

## 📁 项目文件说明

```
aitoolbits-blogger/
├── .github/workflows/
│   └── publish-article.yml    # GitHub Actions 定时任务配置
├── scripts/
│   ├── topics.py              # 57 个文章主题池
│   ├── generate_article.py    # DeepSeek 文章生成器
│   ├── publish_to_blogger.py  # Blogger API 发布器（主入口）
│   ├── oauth_setup.py         # OAuth 一键设置向导
│   └── refresh_token.py       # Token 刷新工具
├── articles/                  # 预写文章（备用）
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📞 常用链接

| 链接 | 用途 |
|------|------|
| https://aitoolbits.blogspot.com | 博客首页 |
| https://www.blogger.com | Blogger 后台 |
| https://github.com/iambuluo/aitoolbits-blogger/actions | GitHub Actions |
| https://platform.deepseek.com | DeepSeek 余额/Key |
| https://console.cloud.google.com/apis/credentials | Google OAuth 凭据 |
