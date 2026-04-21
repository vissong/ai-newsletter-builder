# bigmodel-releases

## Fetch

URL: https://docs.bigmodel.cn/cn/update/new-releases

服务端渲染，直接 WebFetch 即可。若返回空，回退 Jina Reader：`https://r.jina.ai/https://docs.bigmodel.cn/cn/update/new-releases`。

## Extract

这是智谱（BigModel / GLM）官方产品发布时间线。每条记录已包含日期、标题、跳转链接和一句话描述，直接结构化抽取即可。

- title: 条目标题（例如「GLM-5.1」「GLM-5V-Turbo」「AutoGLM-Phone」——保留产品名原样）
- url: 绝对 URL。相对路径 `/cn/guide/...` → 拼接 `https://docs.bigmodel.cn`
- published_at: 表格/列表中显示的日期（YYYY-MM-DD → ISO-8601，取当日 00:00 UTC+8）
- summary: 条目右侧的一句话描述原样保留；如果描述过短（< 30 字），不需要 follow 到子页面——此类更新基本就是「产品名 + 一句话能力」，足够支撑站点上的卡片。

**时间过滤**：只保留过去 **24 小时**内发布的条目。智谱节奏大致 **每月 1-3 条**，多数日子为 0 是正常现象。

## Edge Cases

- **分类归属**：
  - 文本基座模型（GLM-5 / 5.1 / 4.7）与旗舰多模态（GLM-5V-Turbo、GLM-4.6V）→ `major-release`
  - 语音 / TTS / ASR / OCR / 视频生成（CogVideoX / Vidu）模型升级 → `major-release`
  - API / 工具全家桶类公告（「AI 搜索工具全家桶」「Web Search API」）→ `tools-release`
  - AutoGLM-Phone 这类端侧助手类发布 → `tools-release`
- 一天内有多条（例如 2025-12-11 TTS-Clone + TTS + ASR 同日）属于正常批次，保留为独立条目，不要合并。
- 内容本身就是中文，language: zh，Phase 3.5 无需翻译；但 Phase 4 打分时仍要走正常流程。
- 表格里某些「多个端点」的整合发布（如 2025-04-14 的 GLM-4/Z1 系列）以标题为准保留单条，避免爆条。
