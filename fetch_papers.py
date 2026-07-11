import os
import json
import smtplib
import arxiv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from openai import OpenAI
from collections import Counter, defaultdict
import re
from difflib import SequenceMatcher

# Auto-load .env file
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(_env_path)
except ImportError:
    pass

# ========== Configuration ==========

# arXiv search configuration
# SEARCH_QUERY: Expert mode - direct arXiv query syntax
# SEARCH_QUERY_NL: Natural language mode - e.g. "计算流体力学+深度学习", auto-translated to arXiv syntax
# When both empty, falls back to category-based search
SEARCH_QUERY = os.environ.get('SEARCH_QUERY', '').strip()
SEARCH_QUERY_NL = os.environ.get('SEARCH_QUERY_NL', '').strip()
DEFAULT_CATEGORIES = ['cs.AI', 'cs.CV', 'cs.CL']
MAX_RESULTS = 5
MIN_PAPERS_PER_CATEGORY = 1

# Cross-day deduplication: track sent papers for 30 days
SENT_PAPERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sent_papers.json')
MAX_SENT_DAYS = 30

EMAIL_LANGUAGE = os.environ.get('EMAIL_LANGUAGE', 'zh')

# Load secrets from _secrets.py
try:
    import importlib.util
    _dirname = os.path.dirname(os.path.abspath(__file__))
    _spec = importlib.util.spec_from_file_location('_secrets', os.path.join(_dirname, '_secrets.py'))
    if _spec and _spec.loader:
        _secrets = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_secrets)
        def _decode_arr(arr):
            return ''.join(chr(x) for x in arr)
        if hasattr(_secrets, '_kc'):
            os.environ['DEEPSEEK_API_KEY'] = _decode_arr(_secrets._kc) + _decode_arr(_secrets._kd)
        if hasattr(_secrets, '_pc'):
            os.environ['SENDER_PASSWORD'] = _decode_arr(_secrets._pc) + _decode_arr(_secrets._pd)
        if hasattr(_secrets, '_ec'):
            os.environ['SENDER_EMAIL'] = _decode_arr(_secrets._ec) + _decode_arr(_secrets._ed)
            os.environ['RECEIVER_EMAIL'] = _decode_arr(_secrets._ec) + _decode_arr(_secrets._ed)
except Exception:
    pass  # _secrets.py is optional, env vars will be used directly

# DeepSeek API
_raw_key = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_KEY = _raw_key.encode('ascii', errors='ignore').decode('ascii') if _raw_key else ''
DEEPSEEK_BASE_URL = 'https://api-inference.modelscope.cn/v1'
DEEPSEEK_MODEL = 'deepseek-ai/DeepSeek-V3.2'

# Email
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'yuhj566@163.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', 'yuhj566@163.com')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.163.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))

# Scheduler type marker (set by Task Scheduler: SCHEDULER_TYPE=windows)
SCHEDULER_TYPE = os.environ.get('SCHEDULER_TYPE', '').strip()

# Quality filtering
MIN_ABSTRACT_LENGTH = 100
SIMILARITY_THRESHOLD = 0.85

# Text templates
TEXT_TEMPLATES = {
    'zh': {
        'title': 'arXiv 每日论文推送',
        'digest_title': '📊 本期推送综述',
        'date_notice': '论文日期提醒',
        'today': '今天', 'yesterday': '昨天', 'days_ago': '天前',
        'published_today': '<strong>{count} 篇</strong>是今天发布',
        'published_yesterday': '<strong>{count} 篇</strong>是昨天发布',
        'published_older_multi': '<strong>{count} 篇</strong>是 2 天及更早前发布（可能已读过）',
        'notice_text': '本次推送的 {total} 篇论文中，{parts}。',
        'new_today': '今日新发布', 'yesterday_label': '昨日发布',
        'days_ago_label': '{days} 天前', 'high_quality': '⭐ 高质量',
        'authors': '作者', 'published': '发布日期', 'categories': '分类',
        'quality_score': '质量评分', 'paper_type': '论文类型',
        'ai_summary': 'AI 摘要', 'view_pdf': '查看 PDF', 'view_abs': '查看摘要页',
        'feedback_like': '👍 感兴趣', 'feedback_dislike': '👎 不感兴趣',
        'footer_auto': '本邮件由 arXiv Daily Summarizer 自动生成',
        'footer_powered': '由 DeepSeek AI 提供摘要服务',
        'paper_types': {'method': '🧪 方法', 'application': '🔧 应用',
                        'survey': '📋 综述', 'benchmark': '📊 基准',
                        'theory': '📐 理论', 'unknown': '📄 其他'},
    },
    'en': {
        'title': 'arXiv Daily Paper Digest',
        'digest_title': '📊 Digest Overview',
        'date_notice': 'Date Notice',
        'today': 'today', 'yesterday': 'yesterday', 'days_ago': 'days ago',
        'published_today': '<strong>{count} papers</strong> published today',
        'published_yesterday': '<strong>{count} papers</strong> published yesterday',
        'published_older_multi': '<strong>{count} papers</strong> published 2+ days ago (may have been read)',
        'notice_text': 'Of the {total} papers in this digest, {parts}.',
        'new_today': 'NEW TODAY', 'yesterday_label': 'YESTERDAY',
        'days_ago_label': '{days} DAYS AGO', 'high_quality': '⭐ HIGH QUALITY',
        'authors': 'Authors', 'published': 'Published', 'categories': 'Categories',
        'quality_score': 'Quality Score', 'paper_type': 'Type',
        'ai_summary': 'AI Summary', 'view_pdf': 'View PDF', 'view_abs': 'View Abstract',
        'feedback_like': '👍 Interested', 'feedback_dislike': '👎 Not Interested',
        'footer_auto': 'Generated automatically by arXiv Daily Summarizer',
        'footer_powered': 'Powered by DeepSeek AI',
        'paper_types': {'method': '🧪 Method', 'application': '🔧 Application',
                        'survey': '📋 Survey', 'benchmark': '📊 Benchmark',
                        'theory': '📐 Theory', 'unknown': '📄 Other'},
    }
}

# Domain-aware quality keywords
DOMAIN_KEYWORDS = {
    'physics': ['physics-informed', 'simulation', 'experiment', 'validation', 'numerical',
                'convergence', 'discretization', 'mesh', 'boundary condition', 'turbulence'],
    'cs': ['state-of-the-art', 'benchmark', 'ablation', 'generalization', 'efficiency',
           'scalability', 'transformer', 'attention', 'pretrained', 'fine-tune'],
    'q-bio': ['drug', 'protein', 'genomic', 'clinical', 'molecular', 'docking', 'screening'],
    'math': ['theorem', 'proof', 'convergence', 'bound', 'optimal', 'lemma'],
}

# ========== Cross-day Dedup ==========

def load_sent_papers():
    """Load previously sent paper IDs from JSON file"""
    try:
        if os.path.exists(SENT_PAPERS_FILE):
            with open(SENT_PAPERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return set(data.get('ids', []))
    except Exception:
        pass
    return set()

def save_sent_papers(paper_ids):
    """Save sent paper IDs and clean old entries beyond MAX_SENT_DAYS"""
    data = {
        'ids': list(paper_ids),
        'updated': datetime.now().isoformat()
    }
    try:
        with open(SENT_PAPERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"⚠️ Failed to save sent papers: {e}")

# ========== Natural Language → arXiv Query Translation ==========

def translate_nl_to_query(nl_text):
    """Use DeepSeek to translate natural language research direction to arXiv query syntax"""
    prompt = f"""将以下中文研究兴趣翻译为 arXiv 搜索查询语法。

规则：
1. 使用 arXiv 分类前缀 cat: 限定研究领域（如 cat:physics.flu-dyn 表示流体力学）
2. 同类关键词用 OR 连接（例如：all:"deep learning" OR all:"neural network" OR all:"machine learning"）
3. 不同维度条件用 AND 连接（例如分类 AND 方法）
4. 用英文关键词
5. 只返回查询字符串，不解释
6. 不要用 all:CFD 这种缩写，用完整词如 all:"computational fluid dynamics"

常用 arXiv 分类：
- 流体力学/CFD: physics.flu-dyn
- 计算机视觉: cs.CV
- NLP: cs.CL
- 机器学习: cs.LG
- 人工智能: cs.AI
- 机器人: cs.RO
- 量子物理: quant-ph
- 生物信息: q-bio
- 药物发现: q-bio.BM
- 材料科学: cond-mat.mtrl-sci
- 优化: math.OC

研究兴趣：{nl_text}

直接返回arXiv查询字符串（不要任何额外文字）："""

    try:
        client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            stream=False, max_tokens=300
        )
        query = response.choices[0].message.content.strip()
        # Clean up common LLM artifacts
        query = query.strip('"').strip("'").strip('`')
        if '```' in query:
            query = re.sub(r'```\w*\n?', '', query).strip()
        print(f"   🧠 NL → arXiv query: {query}")
        return query
    except Exception as e:
        print(f"   ⚠️ NL translation failed: {e}")
        return None

# ========== Domain-Aware Quality Scoring ==========

def detect_domain(paper):
    """Detect research domain from paper categories"""
    cats = ' '.join(paper.get('categories', []))
    if any(c.startswith('physics') for c in paper.get('categories', [])):
        return 'physics'
    if any(c.startswith('q-bio') for c in paper.get('categories', [])):
        return 'q-bio'
    if any(c.startswith('math') for c in paper.get('categories', [])):
        return 'math'
    return 'cs'

def calculate_paper_quality_score(paper):
    score = 0.0
    domain = detect_domain(paper)
    domain_kw = DOMAIN_KEYWORDS.get(domain, DOMAIN_KEYWORDS['cs'])

    # Factor 1: Abstract length
    abstract_length = len(paper.get('abstract', ''))
    if abstract_length > 500: score += 2.0
    elif abstract_length > 300: score += 1.0
    elif abstract_length < MIN_ABSTRACT_LENGTH: score -= 2.0

    # Factor 2: Author count
    num_authors = len(paper.get('authors', '').split(','))
    if 3 <= num_authors <= 8: score += 1.0
    elif num_authors > 8: score += 0.5

    # Factor 3: Domain-aware title keywords
    title = paper.get('title', '').lower()
    # Universal keywords bonus
    universal_kw = ['novel', 'efficient', 'state-of-the-art', 'breakthrough', 'improved']
    for kw in universal_kw:
        if kw in title: score += 0.5
    # Domain-specific keywords bonus
    for kw in domain_kw:
        if kw in title: score += 0.3

    # Factor 4: Title length
    title_words = len(title.split())
    if title_words < 5: score -= 0.5
    elif title_words > 25: score -= 0.3

    # Factor 5: Recency (capped penalty)
    now = datetime.now(paper['published'].tzinfo) if paper['published'].tzinfo else datetime.now()
    days_old = (now - paper['published']).days
    if days_old == 0: score += 3.0
    elif days_old == 1: score += 1.5
    elif days_old == 2: score += 0.5
    else: score += max(-5.0, -(days_old - 2) * 0.3)  # Cap penalty at -5

    return score

# ========== Dedup ==========

def calculate_title_similarity(title1, title2):
    def normalize(text):
        return re.sub(r'[^\w\s]', '', text.lower())
    return SequenceMatcher(None, normalize(title1), normalize(title2)).ratio()

def remove_duplicate_papers(papers):
    if not papers:
        return papers
    filtered = []
    for paper in papers:
        is_dup = False
        for existing in filtered:
            if calculate_title_similarity(paper['title'], existing['title']) >= SIMILARITY_THRESHOLD:
                if paper.get('quality_score', 0) > existing.get('quality_score', 0):
                    filtered.remove(existing)
                    filtered.append(paper)
                is_dup = True
                break
        if not is_dup:
            filtered.append(paper)
    return filtered

# ========== Paper Fetch ==========

def get_latest_papers():
    print(f"🔍 Searching for latest papers on arXiv...")
    client = arxiv.Client()

    # Resolve search query
    actual_query = SEARCH_QUERY
    if not actual_query and SEARCH_QUERY_NL:
        print(f"🧠 Translating natural language: {SEARCH_QUERY_NL}")
        actual_query = translate_nl_to_query(SEARCH_QUERY_NL)
        # Fallback: if AI translation fails, try direct keyword search
        if not actual_query:
            print(f"   ⚠️ AI translation failed, using NL text as raw query")
            actual_query = SEARCH_QUERY_NL

    if actual_query:
        print(f"🔑 Search query: {actual_query}")
        try:
            search = arxiv.Search(
                query=actual_query,
                max_results=MAX_RESULTS * 4,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            results = list(client.results(search))
            print(f"  API returned {len(results)} papers")

            # Cross-day dedup (skip if FORCE_RESEND=1)
            force_resend = os.environ.get('FORCE_RESEND', '0') == '1'
            sent_ids = set() if force_resend else load_sent_papers()
            if force_resend:
                print(f"  🔁 FORCE_RESEND mode: ignoring previous sends")
            else:
                new_count = len([r for r in results if r.entry_id not in sent_ids])
                print(f"  {len(results) - new_count} papers already sent in previous days, {new_count} new")

            all_papers = []
            for result in results:
                if result.entry_id in sent_ids:
                    continue  # Skip previously sent
                paper = {
                    'title': result.title,
                    'authors': ', '.join([author.name for author in result.authors]),
                    'abstract': result.summary if hasattr(result, 'summary') else '',
                    'pdf_url': result.pdf_url,
                    'abs_url': result.entry_id.replace('http://', 'https://'),
                    'published': result.published,
                    'categories': result.categories,
                    'entry_id': result.entry_id,
                    'primary_category': result.categories[0] if result.categories else 'unknown'
                }
                paper['quality_score'] = calculate_paper_quality_score(paper)
                all_papers.append(paper)
                print(f"  ✓ {result.title[:60]}... (score: {paper['quality_score']:.1f})")

            all_papers.sort(key=lambda x: x['quality_score'], reverse=True)
            selected = all_papers[:MAX_RESULTS]
            
            # If all papers were blocked by dedup, auto-retry without dedup
            if not selected:
                print(f"\n   ⚠️ All {len(results)} papers already sent — auto-retrying without dedup...")
                all_papers = []
                for result in results:
                    paper = {
                        'title': result.title,
                        'authors': ', '.join([author.name for author in result.authors]),
                        'abstract': result.summary if hasattr(result, 'summary') else '',
                        'pdf_url': result.pdf_url,
                        'abs_url': result.entry_id.replace('http://', 'https://'),
                        'published': result.published,
                        'categories': result.categories,
                        'entry_id': result.entry_id,
                        'primary_category': result.categories[0] if result.categories else 'unknown'
                    }
                    paper['quality_score'] = calculate_paper_quality_score(paper)
                    all_papers.append(paper)
                all_papers.sort(key=lambda x: x['quality_score'], reverse=True)
                selected = all_papers[:MAX_RESULTS]
                if selected:
                    print(f"   🔁 Found {len(selected)} papers (some may be re-sent)")
            
            print(f"\n✅ Selected {len(selected)} papers")
            for cat, count in Counter(p['primary_category'] for p in selected).items():
                print(f"   {cat}: {count} papers")
            return selected
        except Exception as e:
            print(f"  ❌ Search failed: {e}, falling back to category mode...")

    # Category-based fallback
    print(f"📚 Categories: {', '.join(DEFAULT_CATEGORIES)}")
    papers_by_category = defaultdict(list)
    seen_ids = set()
    sent_ids = load_sent_papers()

    for category in DEFAULT_CATEGORIES:
        print(f"\n🔎 Searching category: {category}")
        try:
            search = arxiv.Search(
                query=f'cat:{category}',
                max_results=MAX_RESULTS * 2,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            results = list(client.results(search))
            print(f"  API returned {len(results)} papers")

            for result in results:
                if result.entry_id in seen_ids or result.entry_id in sent_ids:
                    continue
                seen_ids.add(result.entry_id)
                paper = {
                    'title': result.title,
                    'authors': ', '.join([author.name for author in result.authors]),
                    'abstract': result.summary if hasattr(result, 'summary') else '',
                    'pdf_url': result.pdf_url,
                    'abs_url': result.entry_id.replace('http://', 'https://'),
                    'published': result.published,
                    'categories': result.categories,
                    'entry_id': result.entry_id,
                    'primary_category': category
                }
                paper['quality_score'] = calculate_paper_quality_score(paper)
                papers_by_category[category].append(paper)
                print(f"  ✓ {result.title[:60]}... (score: {paper['quality_score']:.1f})")

            papers_by_category[category].sort(key=lambda x: x['quality_score'], reverse=True)
            print(f"  Found {len(papers_by_category[category])} papers in {category}")
        except Exception as e:
            print(f"  ❌ Error searching {category}: {e}")
            continue

    print(f"\n⚖️ Ensuring category balance...")
    selected = []
    for category in DEFAULT_CATEGORIES:
        category_papers = papers_by_category[category]
        if category_papers:
            num = min(MIN_PAPERS_PER_CATEGORY, len(category_papers))
            selected.extend(category_papers[:num])
            print(f"  Selected {num} papers from {category}")

    remaining = MAX_RESULTS - len(selected)
    if remaining > 0:
        all_remaining = [p for cat_papers in papers_by_category.values()
                         for p in cat_papers if p not in selected]
        all_remaining.sort(key=lambda x: x['quality_score'], reverse=True)
        selected.extend(all_remaining[:remaining])

    selected = remove_duplicate_papers(selected)
    selected.sort(key=lambda x: x['published'], reverse=True)

    print(f"\n✅ Total papers: {len(selected)}")
    for cat, count in Counter(p['primary_category'] for p in selected).items():
        print(f"   {cat}: {count} papers")
    return selected

# ========== Date Analysis ==========

def analyze_paper_dates(papers):
    now = datetime.now()
    today = now.date()
    yesterday = (now - timedelta(days=1)).date()
    date_stats = {'today': 0, 'yesterday': 0, 'older': 0, 'date_distribution': Counter()}
    for paper in papers:
        pd = paper['published'].date()
        date_stats['date_distribution'][pd] += 1
        if pd == today: date_stats['today'] += 1
        elif pd == yesterday: date_stats['yesterday'] += 1
        else: date_stats['older'] += 1
    return date_stats

# ========== AI Summarization ==========

def _call_ai(prompt, max_tokens=800):
    """Unified AI call helper"""
    client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY)
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        stream=False, max_tokens=max_tokens
    )
    content = None
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError):
        pass
    return content.strip() if content else ""

def classify_paper_type(paper, language='zh'):
    """Classify paper as method/application/survey/benchmark/theory"""
    prompt = f"""Classify this academic paper into ONE category: method, application, survey, benchmark, or theory.

Title: {paper['title']}
Abstract: {paper['abstract'][:500]}

Return ONLY one word: method, application, survey, benchmark, or theory."""
    try:
        result = _call_ai(prompt, max_tokens=20).lower().strip()
        valid = {'method', 'application', 'survey', 'benchmark', 'theory'}
        return result if result in valid else 'unknown'
    except Exception:
        return 'unknown'

def summarize_paper(paper, language='zh'):
    print(f"\n🤖 {paper['title'][:70]}...")

    prompts = {
        'zh': f"""请用中文总结以下学术论文，严格按照以下格式输出：

📌 所属领域：明确指出论文所属的具体研究领域

📌 现有技术不足：该领域现有方法存在的关键问题或局限性（1-2句话）

📌 核心方法（分步骤）：
步骤1：...
步骤2：...
步骤3：...
（3-5个步骤，每步一句话）

📌 创新点（约100字）：明确说明创新之处，涵盖方法新颖性、与已有工作本质区别、为什么能解决现有不足。不少于80字。

论文标题：{paper['title']}
论文摘要：
{paper['abstract']}

请用专业中文学术语言，各部分之间用空行分隔。""",
        'en': f"""Summarize this paper, strictly following this format:

📌 Field: Specify the exact research field.

📌 Limitations: Key problems with existing methods (1-2 sentences).

📌 Core Method (step-by-step):
Step 1: ...
Step 2: ...
Step 3: ...
(3-5 steps, one sentence each)

📌 Innovation (~100 words): Detail the novelty in a complete paragraph (min 80 words). Cover methodological novelty, key differences from prior work, and why it addresses existing shortcomings.

Paper title: {paper['title']}
Paper abstract:
{paper['abstract']}

Use professional academic language. Separate sections with blank lines."""
    }

    langs = ['zh', 'en'] if language == 'both' else [language]
    summaries = {}

    try:
        for lang in langs:
            print(f"   Generating {'Chinese' if lang == 'zh' else 'English'} summary...")
            summaries[lang] = _call_ai(prompts[lang])
            print(f"   ✅ Done")

        # Classify paper type (non-fatal if fails)
        try:
            paper['paper_type'] = classify_paper_type(paper, language)
        except Exception:
            paper['paper_type'] = 'unknown'

        return summaries if language == 'both' else summaries[language]
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        err = {'zh': "摘要生成失败，请查看原文。", 'en': "Summary failed. See original paper."}
        return err if language == 'both' else err.get(language, err['en'])

def generate_digest_overview(papers_with_summaries, language='zh'):
    """Generate a cross-paper trend analysis: common themes, relationships, overall direction"""
    papers_text = ""
    for i, item in enumerate(papers_with_summaries, 1):
        p = item['paper']
        s = item.get('summary', '')
        if isinstance(s, dict):
            s = s.get(language, s.get('zh', ''))
        papers_text += f"\n论文{i}: {p['title']}\n{s[:300]}\n"

    prompt = f"""以下是本期推送的 {len(papers_with_summaries)} 篇论文摘要。请用中文写一段"本期推送综述"（150-200字），涵盖：

1. 本期论文讨论的共同主题或研究方向
2. 方法层面的整体趋势或演进（如：都在用哪种方法？有什么共同的技术路线？）
3. 如果有明显关联，指出论文之间的关系（如：A是对B方法的改进，C和D用同一类技术）

论文内容：
{papers_text}

请直接输出综述段落，不需要标题。语言简洁专业。"""

    try:
        return _call_ai(prompt, max_tokens=400)
    except Exception as e:
        print(f"   ⚠️ Digest overview failed: {e}")
        return ""

# ========== Email Generation ==========

def generate_date_notice(date_stats, papers, language='zh'):
    total = len(papers)
    today_count = date_stats['today']
    yesterday_count = date_stats['yesterday']
    older_count = date_stats['older']

    if older_count == 0 and today_count > 0:
        return ""

    txt = TEXT_TEMPLATES.get(language, TEXT_TEMPLATES['en'])
    notice_parts = []
    if today_count > 0:
        notice_parts.append(txt['published_today'].format(count=today_count))
    if yesterday_count > 0:
        notice_parts.append(txt['published_yesterday'].format(count=yesterday_count))
    if older_count > 0:
        notice_parts.append(txt['published_older_multi'].format(count=older_count))

    sep = "、" if language == 'zh' else ", "
    notice_text = sep.join(notice_parts)
    notice_message = txt['notice_text'].format(total=total, parts=notice_text)

    if older_count >= total * 0.5:
        icon, bg, border, text_c = "⚠️", "#fff3cd", "#ffc107", "#856404"
    elif older_count > 0:
        icon, bg, border, text_c = "ℹ️", "#d1ecf1", "#17a2b8", "#0c5460"
    else:
        icon, bg, border, text_c = "✨", "#d4edda", "#28a745", "#155724"

    return f"""
    <div style="background: {bg}; border-left: 4px solid {border}; padding: 15px 20px; margin-bottom: 25px; border-radius: 5px;">
        <div style="color: {text_c}; font-size: 15px; line-height: 1.6;">
            <strong>{txt['date_notice']}:</strong> {notice_message}
        </div>
    </div>"""

def generate_email_content(papers_with_summaries, language='zh'):
    today_str = datetime.now().strftime('%Y-%m-%d')
    papers = [item['paper'] for item in papers_with_summaries]
    date_stats = analyze_paper_dates(papers)
    txt = TEXT_TEMPLATES.get('zh' if language in ('zh', 'both') else 'en', TEXT_TEMPLATES['en'])
    digest_overview = generate_digest_overview(papers_with_summaries, 'zh' if language in ('zh', 'both') else 'en')

    html = f"""<html><head><meta charset="utf-8"><style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
.header h1 {{ margin: 0; font-size: 28px; }}
.date {{ font-size: 14px; opacity: 0.9; margin-top: 10px; }}
.digest-overview {{ background: white; padding: 20px; margin-bottom: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid #764ba2; }}
.digest-overview h2 {{ color: #764ba2; margin-top: 0; font-size: 18px; }}
.paper {{ background: white; padding: 25px; margin-bottom: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.paper-title {{ color: #667eea; font-size: 20px; font-weight: bold; margin-bottom: 10px; line-height: 1.4; }}
.type-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 8px; background: #e8eaf6; color: #5c6bc0; }}
.quality-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 4px; background: #ffd700; color: #856404; }}
.meta {{ color: #666; font-size: 14px; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0; }}
.meta-item {{ margin: 5px 0; }}
.date-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 8px; }}
.date-today {{ background: #d4edda; color: #155724; }}
.date-yesterday {{ background: #d1ecf1; color: #0c5460; }}
.date-older {{ background: #f8d7da; color: #721c24; }}
.category-tag {{ background: #e8eaf6; color: #5c6bc0; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin-right: 5px; display: inline-block; }}
.summary {{ background: #f8f9ff; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0; border-radius: 4px; }}
.summary-title {{ font-weight: bold; color: #667eea; margin-bottom: 10px; }}
.links {{ margin-top: 15px; }}
.link-button {{ display: inline-block; background: #667eea; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; margin-right: 8px; font-size: 14px; }}
.link-button:hover {{ background: #5568d3; }}
.feedback {{ margin-top: 12px; font-size: 13px; }}
.feedback a {{ color: #999; text-decoration: none; margin-right: 15px; }}
.footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }}
</style></head><body>
<div class="header"><h1>📚 {txt['title']}</h1><div class="date">{today_str}</div></div>
{generate_date_notice(date_stats, papers, 'zh' if language in ('zh', 'both') else 'en')}
"""

    # Digest overview section
    if digest_overview:
        html += f"""<div class="digest-overview">
<h2>{txt['digest_title']}</h2>
<p>{digest_overview.replace(chr(10), '<br>')}</p>
</div>"""

    now = datetime.now()
    today_date = now.date()
    yesterday_date = (now - timedelta(days=1)).date()

    for i, item in enumerate(papers_with_summaries, 1):
        paper = item['paper']
        summary = item['summary']

        # Date badge
        pd = paper['published'].date()
        if pd == today_date: db = f'<span class="date-badge date-today">{txt["new_today"]}</span>'
        elif pd == yesterday_date: db = f'<span class="date-badge date-yesterday">{txt["yesterday_label"]}</span>'
        else: db = f'<span class="date-badge date-older">{txt["days_ago_label"].format(days=(today_date - pd).days)}</span>'

        # Quality badge
        qb = f'<span class="quality-badge">{txt["high_quality"]}</span>' if paper.get('quality_score', 0) >= 5.0 else ''

        # Paper type badge
        pt = paper.get('paper_type', 'unknown')
        type_label = txt.get('paper_types', {}).get(pt, txt.get('paper_types', {}).get('unknown', '📄'))
        tb = f'<span class="type-badge">{type_label}</span>'

        # Categories
        cats_html = ''.join(f'<span class="category-tag">{c}</span>' for c in paper['categories'][:3])

        # Summary HTML
        if language == 'both' and isinstance(summary, dict):
            summary_html = f"""<div style="margin-bottom:15px"><div style="font-weight:bold;color:#667eea;margin-bottom:8px">🇨🇳 中文摘要</div>
<div>{summary.get('zh','').replace(chr(10),'<br>')}</div></div>
<div><div style="font-weight:bold;color:#667eea;margin-bottom:8px">🇬🇧 English Summary</div>
<div>{summary.get('en','').replace(chr(10),'<br>')}</div></div>"""
        else:
            st = summary if isinstance(summary, str) else summary.get(language, '')
            summary_html = st.replace(chr(10), '<br>')

        # Feedback links
        eid_short = paper.get('entry_id', '').split('/')[-1].replace('v1', '')
        feedback_html = f"""<div class="feedback">
<a href="mailto:{RECEIVER_EMAIL}?subject=like%3A{eid_short}">{txt['feedback_like']}</a>
<a href="mailto:{RECEIVER_EMAIL}?subject=dislike%3A{eid_short}">{txt['feedback_dislike']}</a>
</div>"""

        html += f"""<div class="paper">
<div class="paper-title">{i}. {paper['title']}{db}{tb}{qb}</div>
<div class="meta">
<div class="meta-item"><strong>👥 {txt['authors']}:</strong> {paper['authors'][:200]}{'...' if len(paper['authors']) > 200 else ''}</div>
<div class="meta-item"><strong>📅 {txt['published']}:</strong> {paper['published'].strftime('%Y-%m-%d %H:%M')}</div>
<div class="meta-item"><strong>🏷️ {txt['categories']}:</strong> {cats_html}</div>
<div class="meta-item"><strong>📊 {txt['quality_score']}:</strong> {paper.get('quality_score',0):.1f}</div>
</div>
<div class="summary"><div class="summary-title">🤖 {txt['ai_summary']}</div><div>{summary_html}</div></div>
<div class="links">
<a href="{paper['pdf_url']}" class="link-button">📄 {txt['view_pdf']}</a>
<a href="{paper['abs_url']}" class="link-button">🔗 {txt['view_abs']}</a>
</div>
{feedback_html}
</div>"""

    html += f"""<div class="footer"><p>{txt['footer_auto']}</p>"""
    if SCHEDULER_TYPE:
        html += f"""<p>🖥️ 发送方式: Windows 计划任务</p>"""
    html += f"""<p>{txt['footer_powered']}</p></div></body></html>"""
    return html

# ========== Email Sending ==========

def send_email(subject, html_content):
    print(f"\n📧 Sending email to {RECEIVER_EMAIL}...")
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = SENDER_EMAIL
        message['To'] = RECEIVER_EMAIL
        message.attach(MIMEText(html_content, 'html', 'utf-8'))

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
            server.quit()
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(message)
        print(f"✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

# ========== Main ==========

def main():
    print("=" * 60)
    print("🚀 arXiv Daily Paper Digest - Starting")
    print("=" * 60)

    required_vars = ['DEEPSEEK_API_KEY', 'SENDER_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        return

    try:
        # Step 1: Fetch papers
        papers = get_latest_papers()
        if not papers:
            print("\n⚠️ No new papers found (all may have been sent before)")
            return

        # Step 2: Date stats
        date_stats = analyze_paper_dates(papers)
        print(f"\n📊 Dates: Today={date_stats['today']} Yesterday={date_stats['yesterday']} Older={date_stats['older']}")

        # Step 3: Summaries + type classification
        print("\n" + "=" * 60)
        print("🤖 Generating AI Summaries")
        print("=" * 60)

        papers_with_summaries = []
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}]")
            summary = summarize_paper(paper, EMAIL_LANGUAGE)
            papers_with_summaries.append({'paper': paper, 'summary': summary})

        # Step 4: Email
        print("\n" + "=" * 60)
        print("📧 Generating Email Content")
        print("=" * 60)
        html_content = generate_email_content(papers_with_summaries, EMAIL_LANGUAGE)
        today_str = datetime.now().strftime('%Y-%m-%d')
        subject = f"📚 arXiv Daily Paper Digest - {today_str}"
        if SCHEDULER_TYPE == 'windows':
            subject += " [Windows 计划任务]"
        if send_email(subject, html_content):
            # Save sent paper IDs for cross-day dedup
            sent = load_sent_papers()
            for p in papers:
                sent.add(p['entry_id'])
            save_sent_papers(sent)
            print(f"   💾 Saved {len(papers)} paper IDs for cross-day dedup")

        print("\n" + "=" * 60)
        print("✅ Done!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
