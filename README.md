# arXiv 每日论文推送

🤖 每天自动从 arXiv 获取你**指定研究方向**的最新论文，使用 DeepSeek AI 生成结构化摘要、类型标注、关联分析，并推送到你的邮箱。

[English](./README_EN.md)

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🗣️ **自然语言搜索** | 用中文描述研究方向，AI 自动翻译为 arXiv 查询语法 |
| 🏗️ **结构化摘要** | 领域 → 现有不足 → 分步骤方法 → 约100字创新点 |
| 🏷️ **论文类型标注** | AI 自动识别：方法 / 应用 / 综述 / 基准 / 理论 |
| 📊 **本期综述** | 读完所有论文后，生成一段趋势分析：共同主题、方法演进、论文间关联 |
| ✅ **跨天去重** | 推过的论文不再重复推送 |
| 👍 **反馈机制** | 邮件中可点击"感兴趣/不感兴趣"，逐步优化推送质量 |
| 🎯 **领域感知评分** | 根据不同研究方向自动调整关键词权重 |
| 🔗 **双链接** | 每篇论文同时提供 PDF 和 arXiv 摘要页链接 |
| ⏰ **全自动** | GitHub Actions 每天定时运行 |
| 🆓 **完全免费** | ModelScope API + GitHub Actions 免费额度 |

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/RunRiotComeOn/arXiv-Daily-Summarizer.git
cd arXiv-Daily-Summarizer
pip install -r requirements.txt
```

### 2. 配置

复制 `.env.example` 为 `.env`，填入你的 API Key 和邮箱信息：

```bash
cp .env.example .env
```

```env
# 研究方向（自然语言，推荐）
SEARCH_QUERY_NL=你想研究的方向

# ModelScope API Key（免费申请：https://www.modelscope.cn/）
DEEPSEEK_API_KEY=***

# 邮箱（开启 SMTP 服务后获取授权码）
SENDER_EMAIL=***
SENDER_PASSWORD=***
RECEIVER_EMAIL=***
SMTP_SERVER=你的SMTP服务器
SMTP_PORT=465
```

### 3. 运行

```bash
python fetch_papers.py
```

脚本自动从 `.env` 加载配置，无需手动设置环境变量。

### 4. 部署到 GitHub Actions（可选）

1. 推送到 GitHub 仓库
2. 在 **Settings → Secrets and variables → Actions** 中添加同样名称的 Secrets
3. 每天自动运行（默认北京时间 08:00）

## 🔑 研究方向配置

### 方式一：自然语言（推荐）

直接把研究方向写进 `.env`，AI 自动翻译为 arXiv 查询：

```env
SEARCH_QUERY_NL=你想研究的方向
```

例如输入"计算流体力学方向的深度学习方法"，AI 会自动匹配 arXiv 分类和英文关键词。

### 方式二：专家模式

直接用 arXiv 查询语法精确控制：

```env
SEARCH_QUERY=cat:physics.flu-dyn AND (all:"deep learning" OR all:"neural network")
```

`SEARCH_QUERY` 优先级高于 `SEARCH_QUERY_NL`。查询语法支持 `cat:` / `all:` / `ti:` / `abs:` 和布尔逻辑 `AND` / `OR`。

常用分类：[arXiv Category Taxonomy](https://arxiv.org/category_taxonomy)

### 方式三：默认分类

两个都留空，自动搜索 cs.AI、cs.CV、cs.CL。

## 🤖 邮件内容结构

```
📚 标题 + 日期
─────────────────
📊 本期推送综述  ← AI 跨论文趋势分析
─────────────────
论文 1: 标题 [今日新发布] [方法] [⭐高质量]
  👥 作者  📅 日期  🏷️ 分类  📊 质量分
  🤖 AI 摘要（领域 → 不足 → 步骤 → 创新）
  📄 查看PDF  🔗 arXiv摘要页
  👍 感兴趣  👎 不感兴趣
```

## 🛠️ 自定义

| 需求 | 位置 | 默认值 |
|------|------|--------|
| 每天推送篇数 | `fetch_papers.py` 中 `MAX_RESULTS` | 5 |
| 推送时间 | `.github/workflows/daily_arxiv.yml` cron | 08:00 北京时间 |
| 摘要语言 | `.env` 中 `EMAIL_LANGUAGE` | `zh` |
| AI 模型 | `fetch_papers.py` 中 `DEEPSEEK_MODEL` | `deepseek-ai/DeepSeek-V3.2` |
| 最小摘要长度 | `fetch_papers.py` 中 `MIN_ABSTRACT_LENGTH` | 100 |
| 去重阈值 | `fetch_papers.py` 中 `SIMILARITY_THRESHOLD` | 0.85 |

## 📁 项目结构

```
arxiv-daily-summarizer/
├── .github/workflows/
│   └── daily_arxiv.yml     # GitHub Actions 工作流
├── fetch_papers.py         # 主程序
├── requirements.txt        # Python 依赖
├── .env.example            # 配置模板
├── README.md
└── README_EN.md
```

## 📊 质量评分系统

基于领域感知的多维度评分：摘要长度、作者数量、领域关键词、时效性、标题质量。评分 ≥ 5.0 显示 ⭐ 高质量徽章。

## ❓ 常见问题

**Q: 论文方向和我的研究不匹配？**
- 确保研究方向描述足够具体，或者切换到专家模式手写 arXiv 查询语法

**Q: 邮箱发送失败？**
- 确认 SMTP 端口正确（SSL 用 465，STARTTLS 用 587），密码是授权码而非登录密码

**Q: 想自定义某个功能？**
- 大部分参数都在 `fetch_papers.py` 顶部，直接修改即可

## 📝 许可证

MIT License

## 🙏 致谢

- [arXiv](https://arxiv.org/) — 开放学术论文库
- [DeepSeek](https://www.deepseek.com/) / [ModelScope](https://www.modelscope.cn/) — AI 模型与免费 API
- [GitHub Actions](https://github.com/features/actions) — 免费 CI/CD

---

⭐ 好用的话，给个 Star！
