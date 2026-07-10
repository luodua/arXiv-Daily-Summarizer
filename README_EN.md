# arXiv Daily Paper Summarizer

🤖 Automatically fetch the latest papers from your **specified research direction**, generate structured summaries with type classification and cross-paper analysis, and deliver them to your inbox.

**TL;DR: Type your research interest in plain language, and it finds papers, writes summaries, analyzes trends, and emails you.**

[中文文档](./README.md) | English

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language Search** | Type "CFD + deep learning" and AI auto-translates to arXiv query syntax |
| 🏗️ **Structured Summaries** | Field → Limitations → Step-by-step Method → ~100-word Innovation |
| 🏷️ **Paper Type Classification** | Auto-label: 🧪Method / 🔧Application / 📋Survey / 📊Benchmark / 📐Theory |
| 📊 **Digest Overview** | AI reads all papers, generates a trend analysis: common themes, method evolution, paper relationships |
| ✅ **Cross-day Dedup** | Never sends the same paper twice |
| 👍 **Feedback Links** | Click 👍/👎 in emails to train your preferences |
| 🎯 **Domain-aware Scoring** | Different keyword weights for physics, CS, biology, math |
| 🔗 **Dual Links** | PDF + arXiv abstract page for every paper |
| 📧 **Beautiful Emails** | HTML with date badges, type tags, quality scores |
| ⏰ **Fully Automated** | GitHub Actions daily schedule |
| 🆓 **100% Free** | ModelScope API + GitHub Actions free tiers |

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/RunRiotComeOn/arXiv-Daily-Summarizer.git
cd arXiv-Daily-Summarizer
pip install -r requirements.txt
```

### 2. Create `.env` Config

```bash
cp .env.example .env
```

Minimum config (everything else has sensible defaults):

```env
# Natural language research direction (recommended)
SEARCH_QUERY_NL=CFD and deep learning

# ModelScope API Key (free: https://www.modelscope.cn/)
DEEPSEEK_API_KEY=***

# Email
SENDER_EMAIL=***
SENDER_PASSWORD=***
RECEIVER_EMAIL=***
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 3. Run

```bash
python fetch_papers.py
```

No environment variables needed — config auto-loaded from `.env`.

### 4. Deploy to GitHub Actions (Optional)

1. Push to GitHub
2. Add the same variables as Secrets in **Settings → Secrets and variables → Actions**
3. Workflow runs daily at 08:00 Beijing Time (UTC+8)

> ⚠️ `.env` is gitignored. In GitHub Actions, all config comes from GitHub Secrets.

## 🔑 Research Direction

### Mode 1: Natural Language (Recommended)

```env
SEARCH_QUERY_NL=CFD and deep learning
```

AI auto-translates to arXiv query, e.g.:
`cat:physics.flu-dyn AND (all:"deep learning" OR all:"machine learning")`

More examples:

| Input | AI Translation |
|-------|---------------|
| `drug discovery with graph neural networks` | Matches `q-bio.BM` + GNN keywords |
| `reinforcement learning for robot navigation` | Matches `cs.RO` + RL keywords |
| `reasoning in large language models` | Matches `cs.CL` + reasoning keywords |

### Mode 2: Expert (arXiv Query Syntax)

```env
SEARCH_QUERY=cat:physics.flu-dyn AND (all:"machine learning" OR all:"deep learning")
```

`SEARCH_QUERY` takes priority over `SEARCH_QUERY_NL`.

**Query syntax**: `cat:` for category, `all:` for full-text, `AND`/`OR`, `""` for phrases.

Categories: [arXiv Taxonomy](https://arxiv.org/category_taxonomy)

### Mode 3: Default Categories

Leave both empty for classic search across cs.AI, cs.CV, cs.CL.

## 🤖 Email Layout

```
📚 Title + Date
─────────────────
📊 Digest Overview  ← AI trend analysis across all 5 papers
─────────────────
Paper 1: Title [NEW TODAY] [🧪Method] [⭐High Quality]
  👥 Authors  📅 Date  🏷️ Categories  📊 Score
  🤖 AI Summary
    📌 Field
    📌 Limitations
    📌 Core Method (Step 1→2→3)
    📌 Innovation (~100 words)
  📄 View PDF  🔗 View Abstract
  👍 Interested  👎 Not Interested
─────────────────
Paper 2: ...
```

## 📮 Email Setup

| Provider | SMTP Server | Port | Notes |
|----------|------------|------|-------|
| 163 | `smtp.163.com` | `465` | SSL |
| QQ | `smtp.qq.com` | `587` | STARTTLS |
| Gmail | `smtp.gmail.com` | `587` | App password required |

> ⚠️ Always use authorization codes / app passwords, NOT your login password.

## 🛠️ Configuration

| What | Where | Default |
|------|-------|---------|
| Papers per day | `MAX_RESULTS` in `fetch_papers.py` | 5 |
| Schedule time | Cron in `daily_arxiv.yml` | 08:00 Beijing |
| Summary language | `EMAIL_LANGUAGE` in `.env` | `zh` |
| AI model | `DEEPSEEK_MODEL` in `fetch_papers.py` | `deepseek-ai/DeepSeek-V3.2` |
| Dedup threshold | `SIMILARITY_THRESHOLD` | 0.85 |

## 📁 Structure

```
arxiv-daily-summarizer/
├── .github/workflows/daily_arxiv.yml
├── fetch_papers.py
├── requirements.txt
├── .env.example
├── .env                  (gitignored)
├── _secrets.py           (gitignored)
├── _sent_papers.json     (gitignored, auto dedup state)
├── README.md
└── README_EN.md
```

## ❓ FAQ

**Q: Papers don't match my direction?**
Try making your natural language search more specific, or switch to expert mode with `SEARCH_QUERY`.

**Q: Getting duplicate papers?**
Check that `_sent_papers.json` exists and is writable.

**Q: Email fails with 163.com?**
Use port `465` (SSL), not `587`. Make sure you're using the authorization code.

**Q: Want a different AI model?**
Change `DEEPSEEK_MODEL` in `fetch_papers.py`. Free options on ModelScope: `deepseek-ai/DeepSeek-V3.2` or `deepseek-ai/DeepSeek-V4-Flash`.

**Q: Don't want the digest overview or type classification?**
Comment out the corresponding HTML blocks in `generate_email_content()`.

## 📝 License

MIT

## 🙏 Acknowledgments

- [arXiv](https://arxiv.org/) — Open-access papers
- [DeepSeek](https://www.deepseek.com/) / [ModelScope](https://www.modelscope.cn/) — AI & free API
- [GitHub Actions](https://github.com/features/actions) — Free CI/CD

---

⭐ Star this repo!

## 🔄 Changelog

### v4.0 — Smart Digest
- ✅ Natural language search (AI translates to arXiv query)
- ✅ Cross-paper digest overview (trend analysis)
- ✅ Paper type auto-classification
- ✅ Cross-day deduplication
- ✅ Feedback links (👍/👎 in email)
- ✅ Dual links (PDF + arXiv abstract page)
- ✅ Domain-aware quality scoring
- ✅ dotenv auto-load (no manual env vars)
- ✅ DeepSeek V3.2 model

### v3.0 — Custom Direction + Structured Summaries
- ✅ Keyword search, structured summary format, SMTP SSL

### v2.0 — Quality & Intelligence
- ✅ Scoring, dedup, category balance

### v1.0 — Initial Release
- Paper fetching, summarization, email delivery
