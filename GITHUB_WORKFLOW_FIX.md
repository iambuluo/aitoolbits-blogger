# GitHub Actions Schedule 修复

## 问题
GitHub Actions的schedule触发器在某些情况下会被跳过,特别是:
1. 仓库长时间没有新commit
2. GitHub服务器维护或故障
3. 仓库在main分支上长时间没有活动

## 解决方案

### 方案1: 手动触发(立即生效)
访问: https://github.com/iambuluo/aitoolbits-blogger/actions/workflows/publish-article.yml
点击 "Run workflow" 按钮

### 方案2: 推送空commit触发
```bash
git commit --allow-empty -m "trigger: publish workflow"
git push origin main
```

### 方案3: 使用GitHub API触发
```bash
curl -X POST https://api.github.com/repos/iambuluo/aitoolbits-blogger/actions/workflows/282801843/dispatches \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"ref":"main"}'
```

## 建议
- 每天检查一次workflow状态
- 如果连续2天没有自动触发,手动触发一次
- 考虑使用GITHUB_TOKEN环境变量在workflow中发送通知
