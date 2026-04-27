#!/usr/bin/env python3
"""
词元长街 — 条目分类脚本
Phase 4: 基于来源优先 + 关键词的分类，然后按栏目上限裁剪。

用法: python3 scripts/classify.py site/data/raw/2026-04-20/merged.json
修改 merged.json in-place，为每条设置 category + trimmed 字段。
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta

# ─── 栏目上限 ───
CAT_CAPS = {
    "major-release": 20,
    "industry-business": 20,
    "research-frontier": 10,
    "tools-release": 20,
    "policy-regulation": 20,
    "kol-posts": 15,
}

# ─── 来源 → 固定分类映射（优先级最高）───
SOURCE_CATEGORY = {
    # 研究前沿：arxiv 全部
    "arxiv-cs-ai": "research-frontier",
    "arxiv-cs-cl": "research-frontier",
    "arxiv-cs-lg": "research-frontier",
    # 行业动态：融资/商业/科技媒体
    "tencent-news-ai-funding": "industry-business",
    "search-funding": "industry-business",
    "follow-builders": "kol-posts",
    "36kr-ai": "industry-business",
    "search-36kr-ai": "industry-business",
    "tencent-news-hot": "industry-business",
    # 政策监管：政策类
    "tencent-news-ai-policy": "policy-regulation",
    "search-policy": "policy-regulation",
    "search-ai-security": "policy-regulation",
    # 工具发布：工具集/产品
    "ai-bot-daily-news": "tools-release",
    "ai-bot-tools": "tools-release",
    "huggingface-blog": "tools-release",
}

# ─── 关键词匹配（用于没有固定映射的来源）───

# 政策监管关键词（注意：「安全」「safety」太宽泛，会误判产品介绍）
POLICY_KW = re.compile(
    r"监管|政策|法规|法律|合规|伦理|安全审查|安全标准|AI安全|数据安全|审查|治理|立法|禁令|制裁|隐私|版权|"
    r"regulation|policy|compliance|ethics|governance|legislation|ban\b|sanction|"
    r"privacy|copyright|safety\s+(?:standard|framework|policy|regulation|guideline)|"
    r"white\s*house|executive\s+order|EU\s+AI\s+Act|GDPR|出口管制|export\s+control",
    re.IGNORECASE,
)

# 重大发布关键词（需要结合大厂名）
MAJOR_ENTITIES = re.compile(
    r"OpenAI|Google|Anthropic|Meta|Microsoft|Apple|Amazon|Nvidia|字节|ByteDance|"
    r"百度|腾讯|阿里|华为|DeepMind|Mistral|xAI|Stability|Midjourney|Claude|GPT|"
    r"Gemini|Llama|Sora|DALL[·-]?E|Copilot|Siri|Grok",
    re.IGNORECASE,
)
RELEASE_KW = re.compile(
    r"发布|推出|上线|开源|升级|更新|launch|release|announce|ship|introduce|unveil|"
    r"open[\s-]?source|v\d|版本|\d\.\d",
    re.IGNORECASE,
)

# 融资/行业关键词
INDUSTRY_KW = re.compile(
    r"融资|估值|收购|并购|IPO|上市|营收|利润|亏损|裁员|招聘|合作|投资|"
    r"funding|valuation|acquisition|merger|revenue|profit|layoff|partnership|"
    r"invest|raise|billion|million|venture|capital|Series\s+[A-F]|独角兽|unicorn|"
    r"市场|market|竞争|competition|商业|business",
    re.IGNORECASE,
)

# 工具/产品关键词
TOOLS_KW = re.compile(
    r"工具|框架|库|SDK|API|平台|插件|扩展|开发者|教程|指南|入门|"
    r"tool|framework|library|plugin|extension|developer|tutorial|guide|"
    r"getting\s+started|how\s+to|实战|实践|开箱|benchmark|评测|对比",
    re.IGNORECASE,
)

# 研究关键词
RESEARCH_KW = re.compile(
    r"论文|研究|实验|模型架构|训练方法|数据集|基准|消融|"
    r"paper|study|experiment|architecture|training\s+method|dataset|benchmark|ablation|"
    r"transformer|attention|fine[\s-]?tun|pretrain|reinforcement\s+learning|"
    r"RLHF|DPO|GRPO|LoRA|RAG|CoT|chain[\s-]?of[\s-]?thought",
    re.IGNORECASE,
)


def classify_item(item: dict) -> str:
    """对单条 item 分类，返回 category 字符串。"""
    source = item.get("source", "")
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = f"{title} {summary}"

    # 1. 来源固定映射（最高优先级）
    if source in SOURCE_CATEGORY:
        return SOURCE_CATEGORY[source]

    # 2. 来源暗示的默认分类（优先于关键词，因为来源语义比关键词更可靠）
    source_defaults = {
        "openai-blog": "major-release",
        "anthropic-news": "major-release",
        "deepmind-blog": "major-release",
        "google-ai-blog": "major-release",
        "meta-ai-blog": "major-release",
        "microsoft-ai": "major-release",
        "search-major-release": "major-release",
        "techcrunch-ai": "industry-business",
        "theverge-ai": "industry-business",
        "venturebeat-ai": "industry-business",
        "artificial-intelligence-news": "industry-business",
        "mit-tech-review-ai": "industry-business",
        "synced-review": "research-frontier",
        "tencent-news-ai-agent": "tools-release",
        "tencent-news-ai-search": "industry-business",
        "ai-hub-today": "industry-business",
        "gmail-ai-newsletter": "industry-business",
        "search-research": "research-frontier",
        "search-weixin-ai": "industry-business",
        "search-xinhua-ai": "industry-business",
        "weixin-sogou": "industry-business",
    }
    if source in source_defaults:
        return source_defaults[source]

    # 3. 关键词匹配（按优先级）
    # 3a. 政策监管
    if POLICY_KW.search(text):
        return "policy-regulation"

    # 3b. 重大发布 = 大厂名 + 发布动词
    if MAJOR_ENTITIES.search(text) and RELEASE_KW.search(text):
        return "major-release"

    # 3c. 研究前沿
    if RESEARCH_KW.search(text):
        return "research-frontier"

    # 3d. 融资/行业
    if INDUSTRY_KW.search(text):
        return "industry-business"

    # 3e. 工具/产品
    if TOOLS_KW.search(text):
        return "tools-release"

    # 4. 兜底：工具发布
    return "tools-release"


def trim_by_caps(items: list) -> list:
    """按栏目上限裁剪。多源报道优先保留。"""
    # 按 source_count 降序排（多源报道排前面）
    items.sort(key=lambda x: x.get("source_count", 1), reverse=True)

    cat_counts = Counter()
    for item in items:
        cat = item["category"]
        cap = CAT_CAPS.get(cat, 20)
        if cat_counts[cat] < cap:
            item["trimmed"] = False
            cat_counts[cat] += 1
        else:
            item["trimmed"] = True

    return items


# ─── 垃圾/过期数据检测 ───

# Blocked sources — always trimmed
BLOCKED_SOURCES = {
    "tencent-news-hot", "tencent-news-ai-search", "tencent-news-ai-agent",
    "tencent-news-ai-funding", "tencent-news-ai-policy",
}


# Homepage/index URLs that are not real articles
HOMEPAGE_PATTERNS = [
    re.compile(r'https?://[^/]+/?$'),
    re.compile(r'reuters\.com/technology/artificial-intelligence/?$'),
    re.compile(r'aihub\.org/?$'),
    re.compile(r'instagram\.com/popular/'),
    re.compile(r'aiopenminds\.com/ai/news/?$'),
    re.compile(r'apnews\.com/hub/'),
]


def is_garbage(item: dict, run_date: str):
    """Check if item is garbage. Returns reason string or None."""
    url = item.get("url", "")
    title = item.get("title", "")
    summary = item.get("summary", "")

    # 0. Blocked sources
    source = item.get("source", "")
    if source in BLOCKED_SOURCES:
        return f"blocked source: {source}"

    # 1. Homepage URLs
    for pat in HOMEPAGE_PATTERNS:
        if pat.search(url):
            return "homepage URL"

    # 2. URL contains a date older than run_date - 2 days
    #    Handles: /2026/04/13/, april-10-2026, 2026-04-10, etc.
    MONTH_MAP = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    url_date = None
    # Pattern 1: /YYYY/MM/DD/
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if m:
        url_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Pattern 2: month-DD-YYYY (e.g., april-10-2026)
    if not url_date:
        m = re.search(r'(?:^|[/-])(' + '|'.join(MONTH_MAP) + r')[/-](\d{1,2})[/-](\d{4})(?:$|[/-])', url.lower())
        if m:
            url_date = f"{m.group(3)}-{MONTH_MAP[m.group(1)]}-{int(m.group(2)):02d}"
    # Pattern 3: YYYY-MM-DD in URL path
    if not url_date:
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})', url)
        if m:
            url_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    if url_date:
        try:
            ud = datetime.strptime(url_date, "%Y-%m-%d")
            rd = datetime.strptime(run_date, "%Y-%m-%d")
            if ud < rd - timedelta(days=2):
                return f"URL date {url_date} too old"
        except:
            pass

    # 3. Scraping artifacts in summary
    if any(kw in summary.lower() for kw in [
        "enter at least", "cookie policy", "sign up for",
        "page not found", "404", "subscribe to"
    ]):
        return "scraping artifact"

    # 3.5. Aggregation / listicle / roundup pages (not news articles)
    LISTICLE_PATTERNS = [
        r"最全.*(?:工具|AI|应用)",
        r"白皮书",
        r"选型指南",
        r"\d+[款个+].*(?:AI|工具|应用|神器)",
        r"(?:AI|人工智能|机器学习)\s*\d{4}年\d{1,2}月",  # "人工智能 2026年4月" / "机器学习 2026年4月 - stat.ML"
        r"\d{4}年\d{1,2}月.*(?:已经|预期).*(?:发布|上线)",  # "2026年4月已经发布/预期发布的AI大模型"
        r"arXiv\s*(?:上传|合集|论文精选)",
        r"论文精选列表",
        r"(?:每日|每周|本周|本月)AI(?:资讯|新闻|日报|周报)",
    ]
    for pat in LISTICLE_PATTERNS:
        if re.search(pat, title):
            return f"listicle/aggregation: {pat}"

    # 4. Summary is site navigation / too much boilerplate (>800 chars with lots of ####)
    if summary.count("####") >= 3:
        return "site navigation dump"

    return None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/classify.py <merged.json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r") as f:
        items = json.load(f)

    # Infer run date from path (e.g., site/data/raw/2026-04-20/merged.json)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', path)
    run_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    # Garbage detection (before classification) — mark as trimmed permanently
    garbage_ids = set()
    garbage_count = 0
    for item in items:
        reason = is_garbage(item, run_date)
        if reason:
            item["trimmed"] = True
            garbage_ids.add(item.get("id"))
            garbage_count += 1
            print(f"  🗑️ {item.get('id','?')}: {reason} | {item.get('title','')[:50]}")

    if garbage_count:
        print(f"垃圾过滤: {garbage_count} 条\n")

    # 分类 (all items, including garbage — for stats)
    for item in items:
        item["category"] = classify_item(item)

    # 裁剪 (only non-garbage items participate in cap counting)
    non_garbage = [i for i in items if i.get("id") not in garbage_ids]
    non_garbage = trim_by_caps(non_garbage)

    # Re-enforce garbage items stay trimmed
    for item in items:
        if item.get("id") in garbage_ids:
            item["trimmed"] = True

    # 统计
    visible = [i for i in items if not i.get("trimmed", False)]
    trimmed = [i for i in items if i.get("trimmed", False)]
    cats = Counter(i["category"] for i in visible)

    print(f"总条目: {len(items)}")
    print(f"visible: {len(visible)}, trimmed: {len(trimmed)}")
    print("栏目分布 (visible):")
    for cat in ["major-release", "industry-business", "research-frontier", "tools-release", "policy-regulation", "kol-posts"]:
        print(f"  {cat}: {cats.get(cat, 0)}")

    # 写回
    with open(path, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\n已写回 {path}")


if __name__ == "__main__":
    main()
