# arXiv Daily Paper Summarizer

🤖 Automatically fetch the latest papers from your **specified research direction**, generate structured summaries with type classification and cross-paper analysis, and deliver them to your inbox.

[中文文档](./README.md) | English

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language Search** | Describe your interest in plain language, AI translates to arXiv query |
| 🏗️ **Structured Summaries** | Field → Limitations → Step-by-step Method → ~100-word Innovation |
| 🏷️ **Paper Type Classification** | Auto-label: Method / Application / Survey / Benchmark / Theory |
| 📊 **Digest Overview** | AI analyzes all papers for common themes and trends |
| ✅ **Cross-day Dedup** | Never sends the same paper twice |
| 👍 **Feedback Links** | Click 👍/👎 in emails to refine preferences |
| 🎯 **Domain-aware Scoring** | Different quality metrics per research field |
| 🔗 **Dual Links** | PDF + arXiv abstract page for every paper |
| ⏰ **Fully Automated** | GitHub Actions daily schedule |
| 🆓 **100% Free** | ModelScope API + GitHub Actions free tiers |

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/RunRiotComeOn/arXiv-Daily-Summarizer.git
cd arXiv-Daily-Summarizer
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

```env
# Research direction (natural language, recommended)
SEARCH_QUERY_NL=your research interest

# ModelScope API Key (free: https://www.modelscope.cn/)
DEEPSEEK_API_KEY=***

# Email (enable SMTP and get authorization code)
SENDER_EMAIL=***
SENDER_PASSWORD=***
RECEIVER_EMAIL=***
SMTP_SERVER=your-smtp-server
SMTP_PORT=465
```

### 3. Run

```bash
python fetch_papers.py
```

Config auto-loaded from `.env` — no manual env vars needed.

### 4. GitHub Actions (Optional)

Push to GitHub, add the same variables as Secrets, done. Runs daily at 08:00 Beijing Time.

## 🔑 Research Direction

### Mode 1: Natural Language (Recommended)

```env
SEARCH_QUERY_NL=your research interest
```

AI auto-translates to arXiv query syntax with proper categories and keywords.

### Mode 2: Expert (arXiv Query Syntax)

```env
SEARCH_QUERY=cat:cs.CV AND (all:"transformer" OR all:"attention")
```

`SEARCH_QUERY` takes priority. Supports `cat:` / `all:` / `ti:` / `abs:` with `AND` / `OR`.

Categories: [arXiv Taxonomy](https://arxiv.org/category_taxonomy)

### Mode 3: Default

Leave both empty for classic search across cs.AI, cs.CV, cs.CL.

## 🤖 Email Layout

```
📚 Title + Date
─────────────────
📊 Digest Overview  ← AI cross-paper trend analysis
─────────────────
Paper 1: Title [NEW TODAY] [Method] [⭐High Quality]
  👥 Authors  📅 Date  🏷️ Categories  📊 Score
  🤖 AI Summary (Field → Limitations → Steps → Innovation)
  📄 View PDF  🔗 View Abstract
  👍 Interested  👎 Not Interested
```

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
├── README.md
└── README_EN.md
```

## ❓ FAQ

**Q: Papers don't match my direction?**
Make your search more specific, or switch to expert mode with `SEARCH_QUERY`.

**Q: Email fails to send?**
Verify the correct SMTP port (465 for SSL, 587 for STARTTLS) and that you're using an authorization code, not your login password.

**Q: Want to customize something?**
Most parameters are at the top of `fetch_papers.py` — just edit them.

## 📝 License

MIT

## 🙏 Acknowledgments

- [arXiv](https://arxiv.org/) — Open-access papers
- [DeepSeek](https://www.deepseek.com/) / [ModelScope](https://www.modelscope.cn/) — AI & free API
- [GitHub Actions](https://github.com/features/actions) — Free CI/CD

---

⭐ Star this repo!
