# bigmodel-features

## Fetch

URL: https://docs.bigmodel.cn/cn/update/feature-updates

服务端渲染，直接 WebFetch 即可。若返回空，回退 Jina Reader：`https://r.jina.ai/https://docs.bigmodel.cn/cn/update/feature-updates`。

**与 `bigmodel-releases` 的区别**：那是模型发布线（GLM-5.1、GLM-5V-Turbo 等新模型），这是**平台/工具/API 侧的功能变更**（微调新增 DPO、Web Search API 增加参数等）。两者都抓，不要合并。

## Extract

页面是长页滚动的变更日志，每条记录包括：
- date: 条目前的日期标签（YYYY-MM-DD → ISO-8601，取当日 00:00 UTC+8）
- title: 方括号标签 + 简述的组合（示例：「【AI搜索工具】新增多项实用参数」「【模型微调】新增支持 DPO 训练能力」）——**保留中文方括号**
- url: 条目通常不带独立 permalink，使用页面 URL + 简单的 `#date-slug` 锚点：
  `https://docs.bigmodel.cn/cn/update/feature-updates#<YYYY-MM-DD>-<slug>`
  如果条目内有「使用指南 / 接口文档」子链接，把**第一个**子链接作为 canonical `url`，把页面锚点放 `alt_urls`。
- summary: 条目下方的描述段落，通常 1-3 句。

**时间过滤**：只保留过去 **24 小时**内的条目。智谱这类平台功能更新频率约每月 1-2 次，**绝大多数日子为 0 是正常现象**。

## Edge Cases

- **分类归属**：几乎全部归为 `tools-release`——API 参数扩展、微调新能力、控制台升级、计费/额度规则变化等都算「开发者侧工具变更」。只有极少数「发布新产品线」才会冒到 `major-release`。
- 同一天多条更新（例如一次版本上线同时覆盖 API + 控制台 + 文档）应拆成独立条目，不要合并——读者关心的是具体能力点。
- 内容本身是中文，language: zh，Phase 3.5 无需翻译。
- 页面没有 RSS，也没有单条文章页。如果想带读者到原始位置，锚点 URL 至少能跳到同一页；避免生成看起来像独立文章实则 404 的 URL。
