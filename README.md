# arXiv 每日论文推送

🤖 每天自动从 arXiv 获取你**指定研究方向**的最新论文，使用 DeepSeek AI 生成结构化摘要、类型标注、关联分析，并推送到你的邮箱。

说人话：**用中文告诉它你想看什么方向，它帮你找论文、写摘要、分析趋势、发邮件。**

[English](./README_EN.md)

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🗣️ **自然语言搜索** | 写"计算流体力学+深度学习"即可，AI 自动翻译为 arXiv 查询语法 |
| 🏗️ **结构化摘要** | 领域 → 现有不足 → 分步骤方法 → 约100字创新点 |
| 🏷️ **论文类型标注** | AI 自动识别：🧪方法/🔧应用/📋综述/📊基准/📐理论 |
| 📊 **本期综述** | 读完所有论文后，生成一段趋势分析：共同主题、方法演进、论文间关联 |
| ✅ **跨天去重** | 推过的论文不再重复推送，避免浪费时间 |
| 👍 **反馈机制** | 邮件中可点击"感兴趣/不感兴趣"，逐步优化推送质量 |
| 🎯 **领域感知评分** | 根据研究方向（物理/CS/生物等）自动调整关键词权重 |
| 🔗 **双链接** | 每篇论文同时提供 PDF 和 arXiv 摘要页链接 |
| 📧 **HTML 邮件** | 精美的邮件格式，含日期徽章、类型标签、质量评分 |
| ⏰ **全自动** | GitHub Actions 每天定时运行，无需人工干预 |
| 🆓 **完全免费** | ModelScope API + GitHub Actions 免费额度 |

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/RunRiotComeOn/arXiv-Daily-Summarizer.git
cd arXiv-Daily-Summarizer
pip install -r requirements.txt
```

### 2. 创建配置文件

复制 `.env.example` 为 `.env`，填上你的信息：

```bash
cp .env.example .env
```

最低配置（其他都有默认值）：

```env
# 自然语言描述研究方向（推荐）
SEARCH_QUERY_NL=计算流体力学+深度学习

# ModelScope API Key（免费申请：https://www.modelscope.cn/）
DEEPSEEK_API_KEY=***

# 邮箱（163 用户照此填写即可）
SENDER_EMAIL=***
SENDER_PASSWORD=***
RECEIVER_EMAIL=***
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
```

### 3. 运行

```bash
python fetch_papers.py
```

不需要设置环境变量！脚本自动从 `.env` 加载配置。

### 4. 部署到 GitHub Actions（可选）

1. 推送到 GitHub 仓库
2. 在 **Settings → Secrets and variables → Actions** 中添加同样名称的 Secrets
3. 工作流每天北京时间 08:00 自动运行

> ⚠️ GitHub Actions 中 `.env` 不会被推送（在 `.gitignore` 中），配置完全通过 GitHub Secrets 注入。

## 🔑 研究方向配置

### 方式一：自然语言（推荐）

直接把你想看的方向写进 `.env`：

```env
SEARCH_QUERY_NL=计算流体力学+深度学习
```

AI 会自动翻译为 arXiv 查询语法，例如：
`cat:physics.flu-dyn AND (all:"deep learning" OR all:"neural network" OR all:"machine learning")`

更多示例：

| 输入 | AI 翻译效果 |
|------|-----------|
| `药物发现方向用图神经网络的方法` | 自动匹配 `q-bio.BM` + GNN 关键词 |
| `机器人路径规划中的强化学习` | 自动匹配 `cs.RO` + RL 关键词 |
| `大语言模型的推理能力` | 自动匹配 `cs.CL` + reasoning 关键词 |
| `材料科学的分子动力学模拟` | 自动匹配 `cond-mat` + MD 关键词 |

### 方式二：专家模式（精确控制）

如果自然语言翻译不理想，直接用 arXiv 查询语法：

```env
SEARCH_QUERY=cat:physics.flu-dyn AND (all:"machine learning" OR all:"deep learning")
SEARCH_QUERY_NL=
```

`SEARCH_QUERY` 优先级高于 `SEARCH_QUERY_NL`。

**查询语法**：
- `cat:` 限定 arXiv 分类，`all:` 全文匹配，`ti:` / `abs:` 标题/摘要
- `AND` / `OR` 布尔逻辑，`""` 精确短语

常用分类：[arXiv Category Taxonomy](https://arxiv.org/category_taxonomy)

### 方式三：默认分类

两个都留空，自动搜索 cs.AI、cs.CV、cs.CL 三个经典方向。

## 🤖 邮件内容结构

每封推送邮件从上到下依次是：

```
📚 标题 + 日期
─────────────────
📊 本期推送综述  ← AI 分析5篇论文的共同主题和趋势
─────────────────
论文 1: 标题 [今日新发布] [🧪方法] [⭐高质量]
  👥 作者  📅 日期  🏷️ 分类  📊 质量分
  🤖 AI 摘要
    📌 所属领域
    📌 现有技术不足
    📌 核心方法（步骤1→2→3）
    📌 创新点（约100字）
  📄 查看PDF  🔗 arXiv摘要页
  👍 感兴趣  👎 不感兴趣
─────────────────
论文 2: ...
...
─────────────────
页脚
```

## 📮 邮箱配置

| 邮箱 | SMTP 服务器 | 端口 | 说明 |
|------|-----------|------|------|
| 163 | `smtp.163.com` | `465` | SSL 连接 |
| QQ | `smtp.qq.com` | `587` | STARTTLS |
| Gmail | `smtp.gmail.com` | `587` | 需应用专用密码 |

> ⚠️ 全部需要使用**授权码**而非登录密码。在邮箱设置中开启 SMTP 服务后获取。

## 🛠️ 自定义

| 需求 | 位置 | 默认值 |
|------|------|--------|
| 每天推送几篇 | `fetch_papers.py` 中 `MAX_RESULTS` | 5 |
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
├── fetch_papers.py         # 主程序（全部功能）
├── requirements.txt        # Python 依赖
├── .env.example            # 配置模板
├── .env                    # 你的配置（不上传 git）
├── _secrets.py             # 本地密钥（不上传 git）
├── _sent_papers.json       # 推送记录（不上传 git，自动跨天去重）
├── README.md               # 中文文档
└── README_EN.md            # 英文文档
```

## 📊 质量评分系统

基于领域感知的多维度评分：

1. **摘要长度**（+0-2）：越长越详细
2. **作者数量**（+0-1）：3-8 人协作加分
3. **领域关键词**（每个 +0.3）：根据论文分类自动选用不同关键词库
4. **通用关键词**（每个 +0.5）：novel、state-of-the-art 等
5. **时效性**（+3 ~ -5 cap）：越新分越高，但惩罚有上限保护
6. **标题质量**（-0.5 ~ -0.3）：过长或过短扣分

评分 ≥ 5.0 在邮件中显示 ⭐ 高质量徽章。

## ❓ 常见问题

**Q: 自然语言搜索翻译不准怎么办？**
切换为专家模式，用 `SEARCH_QUERY` 手写 arXiv 查询语法。

**Q: 论文方向和我的研究不匹配？**
检查 `SEARCH_QUERY_NL` 是否包含了足够具体的领域描述。越具体越好。

**Q: 推过的论文又出现了？**
检查 `_sent_papers.json` 是否被意外删除。这是跨天去重的依据。

**Q: 163 邮箱发送失败？**
确认端口 `465`（SSL），密码是授权码而非登录密码。

**Q: 想换个 AI 模型？**
在 `fetch_papers.py` 改 `DEEPSEEK_MODEL`，ModelScope 免费支持的有 `deepseek-ai/DeepSeek-V3.2` 和 `deepseek-ai/DeepSeek-V4-Flash`。

**Q: 能不能不要综述/类型标注？**
可以，注释掉 `generate_email_content()` 中的对应 HTML 块即可。

## 📝 许可证

MIT License

## 🙏 致谢

- [arXiv](https://arxiv.org/) — 开放学术论文库
- [DeepSeek](https://www.deepseek.com/) / [ModelScope](https://www.modelscope.cn/) — AI 模型与免费 API
- [GitHub Actions](https://github.com/features/actions) — 免费 CI/CD

---

⭐ 好用的话，给个 Star！

## 🔄 更新日志

### v4.0 — 智能推送
- ✅ 自然语言搜索（写中文即可，AI 自动翻译为 arXiv 查询）
- ✅ 论文间关联综述（"本期推送综述"）
- ✅ 论文类型自动标注（方法/应用/综述/基准/理论）
- ✅ 跨天去重（推过的论文不再重复）
- ✅ 反馈机制（邮件中 👍/👎）
- ✅ arXiv 摘要页链接（PDF + Abstract 双链接）
- ✅ 领域感知质量评分（不同领域不同关键词权重）
- ✅ dotenv 自动加载（无需手动设环境变量）
- ✅ DeepSeek V3.2 模型

### v3.0 — 自定义方向 + 结构化摘要
- ✅ 关键词搜索、结构化摘要格式、SMTP SSL 支持

### v2.0 — 质量与智能
- ✅ 质量评分、去重、领域平衡

### v1.0 — 初始版本
- 论文获取、摘要生成、邮件推送
