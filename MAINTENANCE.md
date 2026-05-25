# aitoolbits-blogger 运维指南

## 项目概述

| 项目 | 信息 |
|------|------|
| 博客地址 | https://aitoolbits.blogspot.com |
| GitHub 仓库 | https://github.com/iambuluo/aitoolbits-blogger |
| 内容方向 | AI Tools Reviews & Tutorials（全英文） |
| 发布频率 | 每天 3 篇（北京时间 08:17 / 14:42 / 21:08） |
| AI 引擎 | DeepSeek V3（~$0.01/篇，月成本约 $1） |
| 发布方式 | GitHub Actions 自动生成 + Blogger API 自动发布 |
| 运行环境 | GitHub 云端（**不需要电脑开机，不消耗 WorkBuddy tokens**） |
| 主题池 | 89 个主题，10 个分类 |
| 文章字数 | 1800-2500 词/篇 |
| 广告策略 | 当前无广告（AD_PROVIDER=none），积累内容后申请 AdSense |

---

## 你需要管什么？

### 日常：什么都不用管！

自动化流水线完全在 GitHub 云端运行，每天自动完成：

1. **选题** - 从 89 个主题中随机选题
2. **生成** - DeepSeek API 生成 1800-2500 字英文文章
3. **SEO 优化** - 自动添加产品链接、LSI 关键词、E-E-A-T 内容
4. **发布** - Blogger API 自动发布，附带智能 Labels 和 Search Description
5. **去重** - 自动避免重复标题

你的电脑关机、WorkBuddy 不开，照样每天自动发文章。GitHub Actions 公共仓库每月免费 2000 分钟，实际每月只用约 180 分钟。

---

## 项目文件说明

```
aitoolbits-blogger/
├── .github/workflows/
│   └── publish-article.yml    # GitHub Actions 定时任务（每天3次）
├── scripts/
│   ├── topics.py              # 89 个文章主题池（10个分类）
│   ├── generate_article.py    # DeepSeek 文章生成器（含SEO/GEO优化）
│   ├── publish_to_blogger.py  # Blogger API 发布器（主入口）
│   ├── setup_oauth.py         # OAuth 一键设置向导
│   └── oauth_setup.py         # OAuth 授权流程工具
├── articles/                  # 已生成的文章存档（10篇预写文章）
├── .gitignore                 # 排除所有 JSON（保护密钥安全）
├── requirements.txt           # Python 依赖
├── README.md                  # 项目英文说明
└── MAINTENANCE.md             # 本文档（运维指南）
```

---

## 自动化运行流程详解

### 完整流水线

```
GitHub Actions 触发（定时或手动）
    │
    ├─ 1. 读取环境变量（从 GitHub Secrets 注入，加密存储）
    │     BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET,
    │     BLOGGER_REFRESH_TOKEN, BLOGGER_BLOG_ID,
    │     DEEPSEEK_API_KEY, AD_PROVIDER, AD_ZONE_ID
    │
    ├─ 2. 刷新 Access Token（refresh_token → access_token）
    │     OAuth 2.0 自动续期，无需人工干预
    │
    ├─ 3. 随机选题（topics.py）
    │     从 89 个主题中随机选取，填充 {year} 等动态参数
    │     10 次重试机制避免重复标题
    │
    ├─ 4. 生成文章（generate_article.py → DeepSeek API）
    │     System Prompt 包含 5 大核心规则：
    │     ├─ 强制产品链接（首次提及必带官网URL，20+产品URL映射）
    │     ├─ E-E-A-T（具体数据、定价、真实案例）
    │     ├─ 原创性分析（非泛泛而谈）
    │     ├─ 可读性（短段落、项目符号、H2/H3层级）
    │     └─ 博客身份（aitoolbits.blogspot.com 独立评测者）
    │
    │     Article Prompt 包含 12 条 SEO/GEO 指令：
    │     ├─ 1800-2500 词
    │     ├─ 纯 HTML 格式（无 Markdown）
    │     ├─ 前 100 字包含主关键词
    │     ├─ H2/H3 清晰层级
    │     ├─ LSI 关键词自然融入
    │     ├─ 结尾 Call-to-Action
    │     └─ 按文章类型（comparison/review/tutorial/list）生成专属内容
    │
    ├─ 5. SEO 后处理（generate_article.py）
    │     ├─ clean_html()：移除 Markdown 残留和 H1 标签
    │     ├─ _generate_labels()：智能标签（分类 + 关键词 + 文章类型，5-6个/篇）
    │     ├─ _generate_search_description()：SEO meta description（150-160字符）
    │     └─ insert_ads()：广告插入（当前 none，可切换 monetag/adsense，3个广告位）
    │
    ├─ 6. 发布到 Blogger（publish_to_blogger.py → Blogger API v3）
    │     POST /blogger/v3/blogs/{blog_id}/posts
    │     包含：title, content, labels, searchDescription
    │     多篇文章间隔 10-30 秒随机延迟
    │
    └─ 7. 输出结果日志
          成功：发布 URL
          失败：错误信息（查看 Actions 日志排查）
```

### GitHub Actions 定时计划

| 时间（UTC） | 时间（北京时间） | 说明 |
|-------------|-----------------|------|
| 00:17 | 08:17 | 早间文章 |
| 06:42 | 14:42 | 午后文章 |
| 13:08 | 21:08 | 晚间文章 |

分钟偏移量故意设置得"不整"，模拟真人发布习惯，对 SEO 更友好。

---

## SEO/GEO 优化策略

### 已实施的优化

| 优化项 | 具体措施 |
|--------|---------|
| 产品链接 | 每个 AI 产品首次提及必带官网链接（`<a href="..." rel="nofollow noopener">`），预置 20+ 产品 URL |
| E-E-A-T | 强制具体数据、版本号、定价细节、真实案例 |
| Labels | 智能标签：分类名 + 关键词 Title 化 + 文章类型（5-6 个/篇） |
| Search Description | 自动生成 150-160 字符 SEO meta description，通过 Blogger API 发布 |
| LSI 关键词 | Prompt 要求自然融入同义词和相关词 |
| 文章结构 | 强制 H2/H3 层级、短段落（2-3 句）、项目符号 |
| 文章类型 | 4 种类型（comparison/review/tutorial/list），每种有专属指令 |
| 文章字数 | 1800-2500 词（长文 SEO 加权更高） |
| 标题优化 | 含年份 {year}、明确关键词 |
| 去重机制 | 同批生成最多 10 次重试避免重复 |

### 广告位策略（3 个/篇）

```
文章结构示例：

[H2] Introduction      ← 无广告
[H2] Topic Overview    ← 无广告
[H2] Detailed Review   ← 📢 广告位 1（第 2 个 H2 后）
[H2] Feature Analysis
[H2] Pricing           ← 📢 广告位 2（第 4 个 H2 后）
[H2] Pros and Cons
[H2] Conclusion
                     ← 📢 广告位 3（页脚）
```

广告配置在 GitHub Secrets 中切换：
```
AD_PROVIDER = none      ← 当前（不插广告，先积累内容）
AD_PROVIDER = monetag   ← Monetag 广告（3个位）
AD_PROVIDER = adsense   ← Google AdSense（需填 ca-pub-XXXX）
AD_ZONE_ID = 229646     ← Monetag zone ID 或 AdSense client ID
```

---

## 安全说明

### 密钥安全

| 敏感信息 | 存储位置 | 代码中引用方式 |
|---------|---------|---------------|
| DeepSeek API Key | GitHub Secrets | `os.environ.get("DEEPSEEK_API_KEY")` |
| Google Client Secret | GitHub Secrets | `os.environ.get("BLOGGER_CLIENT_SECRET")` |
| Google Client ID | GitHub Secrets | `os.environ.get("BLOGGER_CLIENT_ID")` |
| Blogger Refresh Token | GitHub Secrets | `os.environ.get("BLOGGER_REFRESH_TOKEN")` |
| Blog ID | GitHub Secrets | `os.environ.get("BLOGGER_BLOG_ID")` |

**所有密钥均通过环境变量读取，代码中无硬编码。** GitHub Secrets 即使在公开仓库中也加密存储，别人无法查看。

### .gitignore 保护

```
*.json          ← 排除所有 JSON 文件（包括 blogger_tokens.json）
.env*           ← 排除环境变量文件
token.json      ← 排除 OAuth token
credentials.json← 排除 Google 凭据
```

### 凭据泄露应急

1. Google Cloud Console → 凭据 → 删除 OAuth 客户端 → 重新创建
2. DeepSeek Platform → 删除旧 Key → 创建新 Key
3. 更新 GitHub Secrets 中的值

---

## 常用链接

| 链接 | 用途 |
|------|------|
| https://aitoolbits.blogspot.com | 博客首页 |
| https://www.blogger.com | Blogger 后台管理 |
| https://github.com/iambuluo/aitoolbits-blogger/actions | GitHub Actions 运行日志 |
| https://github.com/iambuluo/aitoolbits-blogger/settings/secrets/actions | GitHub Secrets 配置 |
| https://platform.deepseek.com | DeepSeek 余额/Key 管理 |
| https://console.cloud.google.com/apis/credentials | Google OAuth 凭据管理 |
| https://search.google.com/search-console | Google Search Console（加速收录） |

---

## 手动操作指南

### 手动触发发布

1. 打开 https://github.com/iambuluo/aitoolbits-blogger/actions
2. 点击左侧 "Auto Publish Blog Articles"
3. 点击右侧 "Run workflow"
4. 可选：设置 `article_count`（发布篇数）、`is_draft`（是否草稿）

### 本地手动发布（需要 Python 3.12）

```bash
cd D:\小程序\aitoolbits-blogger

# Windows PowerShell 设置环境变量
$env:BLOGGER_CLIENT_ID = "你的Client ID"
$env:BLOGGER_CLIENT_SECRET = "你的Secret"
$env:BLOGGER_REFRESH_TOKEN = "你的Refresh Token"
$env:BLOGGER_BLOG_ID = "2759473256907748566"
$env:DEEPSEEK_API_KEY = "你的DeepSeek Key"
$env:AD_PROVIDER = "none"

# 发布 1 篇
python scripts/publish_to_blogger.py 1

# 发布 5 篇
python scripts/publish_to_blogger.py 5

# 发布草稿（不公开）
python scripts/publish_to_blogger.py 1 --draft

# 仅生成文章（不发布）
python scripts/generate_article.py 3
```

---

## 广告变现策略

### 三阶段规划

| 阶段 | 条件 | 操作 | 预期收入 |
|------|------|------|---------|
| **阶段一（当前）** | 0-30 篇 | AD_PROVIDER=none，不插广告 | $0 |
| **阶段二** | 30+ 篇 | Blogger 后台申请 AdSense | $0（审核中） |
| **阶段三** | AdSense 通过 | AD_PROVIDER=adsense，填入 ca-pub-XXXX | 开始有收入 |

### 申请 AdSense 步骤

1. 确保 AD_PROVIDER=none（无 Monetag 弹窗，避免影响审核）
2. Blogger 后台 → **Earnings（收入）** → 申请 AdSense
3. Blogger 平台的 AdSense 审核比独立网站更宽松
4. 等待审核（通常 1-2 周）
5. 通过后，改 GitHub Secret：AD_PROVIDER=adsense，AD_ZONE_ID=你的ca-pub-XXXX

### 加速收录

1. 打开 https://search.google.com/search-console
2. 添加属性：`https://aitoolbits.blogspot.com`
3. Blogger 自动验证所有权
4. 提交 sitemap：`https://aitoolbits.blogspot.com/sitemap.xml`

---

## 故障排查

### GitHub Actions 不运行

- 检查：GitHub → Settings → Actions → General → 确保未禁用
- 检查：GitHub Secrets 是否配置完整（7 个 Secret）
- 注意：GitHub Actions 的 cron 有 5-15 分钟延迟是正常的

### 文章没发出来

- 查看 Actions 运行日志，找具体错误
- 常见原因：DeepSeek 余额不足、Blogger Token 过期、网络超时

### Blogger Token 过期

- Refresh Token 通常永久有效（除非用户在 Google 账号中撤销授权）
- 如果失效：重新运行 `python scripts/setup_oauth.py` 获取新 Token
- 更新 GitHub Secret 中的 BLOGGER_REFRESH_TOKEN

### DeepSeek 余额不足

- 登录 https://platform.deepseek.com/top_up
- 最低充值 5 元（够用约 5 个月）

---

## 里程碑规划

| 时间 | 文章数 | 目标 | 操作 |
|------|--------|------|------|
| 2026-05-25 | 10 篇 | 博客启动 | 已完成 ✅ |
| 2 周后 | ~50 篇 | 自动积累 | 无需操作 |
| 1 个月后 | ~100 篇 | 申请 AdSense | Blogger 后台申请 |
| 2 个月后 | ~180 篇 | AdSense 审核 | 等待通过 |
| 3 个月后 | ~270 篇 | 稳定收入 | 开启 AdSense 广告 |

---

## 更新日志

### 2026-05-25 - v2.0 SEO/GEO 全面优化

- **主题池**: 57 → 89 个（新增 32 个长尾关键词主题）
- **产品链接**: System Prompt 强制每个 AI 产品首次提及必带官网链接（预置 20+ 产品 URL）
- **E-E-A-T**: Prompt 强制具体数据、版本号、定价、真实案例
- **Labels**: 从粗暴取首词改为完整关键词 Title 化 + 文章类型标签（5-6 个/篇）
- **Search Description**: 新增自动生成 SEO meta description（150-160 字符）
- **文章字数**: 1500-2000 → 1800-2500 词
- **广告位**: 2 个 → 3 个（第2个H2后 + 第4个H2后 + 页脚）
- **Prompt 增强**: 4 种文章类型各有专属详细指令（对比表、评分、FAQ 等）

### 2026-05-25 - v1.0 初始版本

- 基础自动化流水线：选题 → 生成 → 发布
- 57 个主题，10 个分类
- 2 个广告位
- OAuth 2.0 + Blogger API v3
- GitHub Actions 每日 3 次定时发布
