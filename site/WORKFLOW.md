# 词元长街 — 日报更新工作流

本文档面向 AI agent 或协作者，描述如何在此仓库中执行日常的期刊内容更新。

> **核心规则：更新日报内容时，禁止修改任何 HTML 文件（`index.html`、`issues/index.html`）和 CSS 文件（`assets/style.css`）。** 网站使用客户端渲染（SPA），页面 JS 从 JSON 数据文件动态加载内容。日报更新只需产出 JSON，不需要也不应该碰 HTML/CSS。仅在明确要求修改网站样式或布局时才允许编辑这些文件。

---

## 前置依赖

### Skill

本站依赖 `ai-newsletter-builder` skill（位于 `~/.claude/skills/ai-newsletter-builder/`）。Skill 中的 `SKILL.md` 包含完整的管道定义（数据源管理、采集、去重、分类、翻译、上限裁剪、Manifest 生成、RSS 构建等），是所有阶段的权威参考。执行更新前应先读取 SKILL.md 确认最新流程。

### CLI 工具

| 工具 | 用途 | 安装 | 依赖它的数据源 |
|---|---|---|---|
| `python3` | 运行 22 个 script 类数据源的 fetch.py | 系统自带或 `brew install python` | 大多数 script 类源 |
| `tvly` (Tavily CLI) | 搜索类数据源的 web search | `curl -fsSL https://cli.tavily.com/install.sh \| bash && tvly login` | `search-*`（6 个） |
| `tencent-news-cli` | 腾讯新闻 AI 频道 | 见 source.yaml 中的 `install_hint` | `tencent-news-*`（5 个） |
| `git` | follow-builders 源（拉取 GitHub 仓库） | 系统自带 | `follow-builders` |
| `gog` | Gmail AI Newsletter 源 | [gogcli.sh](https://gogcli.sh)，装好后 `gog auth login` | `gmail-ai-newsletter` |
| `~/.browser-use-env/bin/python3` | 需要 headless 浏览器的源（反爬/JS 渲染） | 见下方安装命令 | `36kr-ai`, `venturebeat-ai`, `theverge-ai` |

browser-use 安装：
```bash
uv venv ~/.browser-use-env --python 3.13
uv pip install --python ~/.browser-use-env/bin/python3 browser-use playwright
~/.browser-use-env/bin/python3 -m playwright install chromium
```

### 站点配置

`config/site.yaml`：
```yaml
title: "词元长街"
subtitle: "每日 AI 资讯精选"
output_language: zh        # 所有内容翻译为中文
timezone: Asia/Shanghai
design: ciyuan-jie
base_url: "https://token-street.pages.dev"
```

---

## 目录结构（仅与日报更新相关的部分）

```
site/
├── data/
│   ├── issues.json              # 期刊清单（首页读取）    ← 每次更新写入
│   └── raw/
│       └── <YYYY-MM-DD>/
│           ├── <source>.json    # 每个数据源的原始采集    ← Phase 2 产出
│           ├── collect.log      # 采集日志               ← Phase 2 产出
│           └── merged.json      # 去重+分类+翻译后的合并  ← Phase 3-4 产出
├── feed.xml                     # RSS 2.0 feed           ← Phase 6.5 产出
├── config/
│   └── sources/                 # 34 个数据源配置（自动发现）
│       └── <name>/
│           ├── source.yaml      # 元数据：type, enabled, priority, ...
│           ├── fetch.py         # script 类：固定抓取脚本
│           └── prompt.md        # prompt 类：LLM 抓取指令
├── index.html                   # ⛔ 禁止修改（除非改样式）
├── issues/index.html            # ⛔ 禁止修改（除非改样式）
└── assets/style.css             # ⛔ 禁止修改（除非改样式）
```

---

## 更新流程

执行顺序严格按以下阶段进行。日期默认为当天（ISO 格式 `YYYY-MM-DD`）。

### Phase 2: 并发采集

1. 创建 `data/raw/<date>/` 目录。
2. 扫描 `config/sources/` 下所有含 `source.yaml` 的子目录，跳过 `enabled: false` 的。
3. 按 `type` 分发：

   **`type: script`** — 执行抓取脚本：
   ```bash
   # 示例
   python3 config/sources/techcrunch-ai/fetch.py --date 2026-04-20 --recent-hours 36
   ```
   - 先检查 `check.binary`（如 `tencent-news-cli`），缺失则报错不静默跳过
   - 解析 `args` 中的模板变量（`{{date}}`、`{{recent_hours}}` 等）
   - stdout 必须是 JSON 数组
   - 写入 `data/raw/<date>/<name>.json`

   **`type: prompt`** — LLM 驱动抓取：
   - 读取 `prompt.md` 中的抓取+提取指令
   - 遵循 RSS-first 策略和分层回退链（real browser → WebFetch → Jina Reader → WebSearch）
   - 写入 `data/raw/<date>/<name>.json`

4. **并发执行**，每个源 30 秒超时（可通过 `timeout_seconds` 覆盖）。
5. 后处理：注入 `source`、`fetched_at`，按 `time_window_hours` 过滤。
6. 写入 `data/raw/<date>/collect.log`。

### Phase 3: 合并去重

读取所有 `<source>.json`，合并为 `data/raw/<date>/merged.json`。

去重规则（按顺序）：
1. 相同 URL（去除追踪参数）
2. 标题近似（edit distance ≤ 3）
3. 相同实体 + 相同事件类型（48h 窗口内）

合并时：保留最详细的 summary，合并 sources 数组，取最早 published_at，选最权威 URL 为主。

### Phase 3.5: 翻译

`output_language: zh` → 将所有英文条目的 `title` 和 `summary` 翻译为中文。原标题存入 `title_original`。保留专有名词原文（Claude、OpenAI、GPT-5 等）。

### Phase 4: 分类 + 裁剪

分配到 5 个固定分类（slug 不可更改）：

| Slug | 名称 | 上限 |
|---|---|---|
| `major-release` | 重大发布 | 20 |
| `industry-business` | 行业动态及商业价值 | 20 |
| `research-frontier` | 研究前沿 | **10** |
| `tools-release` | 工具发布 | 20 |
| `policy-regulation` | 政策监管 | 20 |

超出上限的条目标记 `"trimmed": true`（不删除），仅非 trimmed 条目计入可见数。

### Phase 5: 更新期刊清单

更新 `data/issues.json`，追加或覆盖当天的条目。关键字段：

- **`title`**：编辑标题，不含日期和站点名，≤30 字，概括 1-2 件最大新闻
- **`headlines`**：2 条编辑头条（覆盖不同分类，15-30 字完整短句，非 top_items 复制）
- **`top_items`**：3-5 条，含 `id` 用于锚点跳转
- **`n`**：期号（1-based，递增）
- **`dow`**：星期缩写（`SUN`..`SAT`）

### Phase 6.5: 重建 RSS

```bash
python scripts/build_feed.py --site site --base-url https://token-street.pages.dev
```

---

## 快速执行（一条命令总结）

对于已经熟悉流程的 agent，按顺序执行：

```
Phase 2  → 并发抓取所有源，写入 data/raw/<date>/<source>.json + collect.log
Phase 3  → 合并去重 → data/raw/<date>/merged.json
Phase 3.5 → 翻译英文条目为中文
Phase 4  → 分类 + 裁剪（research ≤10, 其余 ≤20）→ 回写 merged.json
Phase 5  → 更新 data/issues.json（编辑标题 + 2 条 headlines + top_items）
Phase 6.5 → python scripts/build_feed.py --site site --base-url https://token-street.pages.dev
```

产出文件清单（仅这些文件应被修改）：
- `data/raw/<date>/*.json`
- `data/raw/<date>/collect.log`
- `data/raw/<date>/merged.json`
- `data/issues.json`
- `feed.xml`

---

## 不应该做的事

- **禁止修改 `index.html`、`issues/index.html`、`assets/style.css`** — 除非明确要求修改网站样式/布局
- 不要发明新的分类 slug — 下游模板依赖这 5 个固定值
- 不要删除 trimmed 条目 — 保留在 merged.json 中供审查
- 不要手动编辑 `feed.xml` — 它是 `build_feed.py` 的构建产物
- 不要在 issues.json 的 `title` 中使用模板化格式（如 `站点名 · 日期`）

## 发布

```bash
bash scripts/publish.sh "feat: issue <date>"
```

该脚本会同步 skill 文件到 `skill/` 目录、commit、push 到 GitHub。Cloudflare Pages 自动部署。
