# 设计系统令牌（Design Tokens）v3.0

> 风格定位：Data Dense 数据密集 · 紧凑高效 · 状态色编码 · 浅色后台工作台
> 适用范围：`frontend/src/styles/tokens.css`、`DESIGN.md`、`pen/ui.pen`
> 更新日期：2026-08-13

---

## 1. 核心变化

| 项 | v2.0（Halo） | v3.0（Data Dense） |
|----|--------------|--------------------|
| 风格定调 | Halo 浅色 · 圆角卡片 · 中央图表叙事 | 数据密集 · 信息密度最大化 · 扫描效率优先 |
| 主色 | Halo 紫蓝 `#5749F4` | 数据蓝 `#3B82F6`（hover `#2563EB`） |
| 中性色 | 暖灰 `#fafafb` 系 | slate 蓝灰 `#f8fafc` 系 |
| 卡片圆角 | 24px 卡片、40px 主面板 | 全系 4px（pill 胶囊禁止） |
| 阴影 | 5 级阴影体系 | 装饰阴影清零，仅保留极浅 xs/sm；focus 用 1px 蓝环 |
| 字号 | 12–40px（KPI 32px） | 10–24px（KPI 20px；正文 12–13px） |
| 间距 | 页面 24px、卡片 20px | 页面 16px、卡片 12px、gap 4/8/12 |
| 大屏构图 | 中央桑基 + 外圈悬浮徽章轨道 | 中央桑基大主图 + KPI 指标行 + 右侧洞察列表 + 2×2 小图网格 |
| 装饰 | 轨道圆环、渐变底、悬浮徽章 | 全部禁止（无渐变/无装饰阴影/无单侧粗边条） |
| 图表主题 | default 一套浅色主题 | 不变，仍 default 一套 |

**绝对禁止（匹配即重写）：** 大间距（卡片 padding 24px 以上）；大圆角（12px 以上）与 pill 胶囊徽章；大字号（表格数据 16px 以上）；装饰性渐变与阴影；单侧粗边框装饰条；渐变文字；把常用操作藏进下拉菜单；大面积空白；Inter / Roboto / Geist 字体；bounce/elastic 缓动。

---

## 2. 色彩令牌

### 2.1 品牌主色 Primary（数据蓝）

| Token | 值 | 用途 |
|-------|----|------|
| `--color-primary-50` | `#eff6ff` | 选中弱底、表格行 hover |
| `--color-primary-100` | `#dbeafe` | 轻提示背景 |
| `--color-primary-200` | `#bfdbfe` | 弱边框、hover 边界 |
| `--color-primary-300` | `#93c5fd` | 输入 hover、辅助线 |
| `--color-primary-400` | `#60a5fa` | hover 强调 |
| `--color-primary-500` | `#3b82f6` | 主色基准（按钮、激活态、桑基主节点） |
| `--color-primary-600` | `#2563eb` | 主按钮 hover、active |
| `--color-primary-700` | `#1d4ed8` | 强文字强调 |

### 2.2 辅助色 Secondary

| Token | 值 | 用途 |
|-------|----|------|
| `--color-secondary-50` | `#f0fdfa` | 青色浅底 |
| `--color-secondary-100` | `#ccfbf1` | 青色标签底 |
| `--color-secondary-400` | `#2dd4bf` | 辅助 hover |
| `--color-secondary-500` | `#14b8a6` | 辅助强调、图表第二色 |
| `--color-secondary-600` | `#0d9488` | 辅助 active |

### 2.3 中性色 Neutral（slate）

| Token | 值 | 用途 |
|-------|----|------|
| `--color-white` | `#ffffff` | 卡片底 |
| `--color-gray-50` | `#f8fafc` | 页面底、斑马纹、表头底、交替行 |
| `--color-gray-100` | `#f1f5f9` | tile、骨架、次级容器 |
| `--color-gray-200` | `#e2e8f0` | **默认边框**、图表网格 |
| `--color-gray-300` | `#cbd5e1` | 强边框、分隔线 |
| `--color-gray-400` | `#94a3b8` | **仅占位/装饰/角标**（白底对比度 2.9:1 不达 WCAG AA，禁止用于正文与表格数据） |
| `--color-gray-500` | `#64748b` | 次级文字（白底 4.8:1 达标） |
| `--color-gray-700` | `#1e293b` | 正文（槽位名保留，值即 slate-800） |
| `--color-gray-900` | `#0f172a` | 标题 |

### 2.4 语义色（状态色编码核心，保留不变）

| Token | 主色 | 浅底 | 边框 | 文字 |
|-------|------|------|------|------|
| success | `#22c55e` | `#f0fdf4` | `#bbf7d0` | `#15803d` |
| warning | `#f59e0b` | `#fffbeb` | `#fde68a` | `#b45309` |
| danger | `#ef4444` | `#fef2f2` | `#fecaca` | `#b91c1c` |
| info | `#0ea5e9` | `#f0f9ff` | `#bae6fd` | `#0369a1` |

状态标签统一「浅底 + 文字色 + 4px 方角」徽章模式（示例：`#eff6ff` 底 + `#1d4ed8` 字），禁止胶囊形。

---

## 3. 语义别名

| Token | 值 | 用途 |
|-------|----|------|
| `--bg-page` | `var(--color-gray-50)` | 页面背景（浅灰托白卡） |
| `--bg-card` | `var(--color-white)` | 卡片、弹窗 |
| `--bg-subtle` | `var(--color-gray-50)` | 表头、斑马纹、弱底 |
| `--bg-tile` | `var(--color-gray-100)` | 徽章、指标块 |
| `--text-title` | `var(--color-gray-900)` | 标题 |
| `--text-body` | `var(--color-gray-700)` | 正文 |
| `--text-secondary` | `var(--color-gray-500)` | 辅助文字 |
| `--text-tertiary` | `var(--color-gray-400)` | 占位/角标专用，禁正文 |
| `--text-placeholder` | `var(--color-gray-400)` | 占位文字 |
| `--border-default` | `var(--color-gray-200)` | 默认边框 `#e2e8f0` |
| `--border-hover` | `var(--color-primary-300)` | hover 边框 |
| `--border-focus` | `var(--color-primary-500)` | focus 边框 |
| `--ring-focus` | `0 0 0 1px var(--color-primary-500)` | focus 1px 蓝环 |

---

## 4. 图表色板

| Token | 值 |
|-------|----|
| `--chart-1` | `#3b82f6`（蓝锚） |
| `--chart-2` | `#14b8a6` |
| `--chart-3` | `#f59e0b` |
| `--chart-4` | `#64748b` |
| `--chart-5` | `#0ea5e9` |
| `--chart-6` | `#22c55e` |
| `--chart-7` | `#f97316` |
| `--chart-8` | `#94a3b8` |

**索引语义锁死：** `chart-3`（amber）= 桑基「未转化」节点、`chart-6`（green）=「转化」节点（`ScreenSankeyOrbit` 按索引写死引用），前 6 位禁止重排。图表轴线用 `--chart-grid`，轴文字用 `--chart-axis-text`。`chartTheme.ts` 是运行时唯一取色入口，与本文逐值一致（双写同步）。

---

## 5. 字体

| Token | 值 | 用途 |
|-------|----|------|
| `--font-family-base` | `system-ui, -apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif` | 正文、控件 |
| `--font-family-number` | `ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace` | KPI、概率、run_id、表格数值（配合 `.tabular-nums`） |
| `--font-family-code` | `"JetBrains Mono", "Fira Code", Consolas, monospace` | 代码、日志 |

字号：`10(micro) / 12 / 13 / 14 / 16 / 18 / 20 / 24px`。micro 仅图表刻度与角标；正文 12–13；页标题 18；KPI 20；24 为全场唯一 hero 数字上限（PredictResultCard 概率值）。不要用 viewport 宽度缩放字体。

---

## 6. 间距、圆角、阴影

间距：4px 栅格 `4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48px`；**常用档收敛为 4/8/12**（gap-1/2/3），卡片 padding 上限 16px，禁止 24px 以上内边距。

| Radius | 值 | 用途 |
|--------|----|------|
| `--radius-sm` | `4px` | 小标签、状态徽章、icon 座 |
| `--radius-md` | `4px` | 按钮、输入框 |
| `--radius-lg` | `4px` | 提示、轻容器 |
| `--radius-xl` | `4px` | 弹窗 |
| `--radius-card` | `4px` | 标准卡片 |
| `--radius-panel` | `4px` | 大屏主面板 |
| `--radius-full` | `999px` | **仅限正圆几何元素**（status-dot、live-dot、spinner）；禁止 pill 形徽章/按钮/标签 |

阴影：

- `--shadow-xs`：输入框、小控件、卡片（`0 1px 2px 0 rgb(15 23 42 / 4%)`）。
- `--shadow-sm`：悬浮态上限（`0 1px 2px 0 rgb(15 23 42 / 6%)`）。
- `--shadow-md` / `--shadow-lg`：**deprecated 别名**，指向 `--shadow-sm`，新代码禁用。
- `--shadow-primary`：**deprecated**，值 `none`，新代码禁用。
- focus 反馈用 `--ring-focus`（1px 蓝环），不用阴影光晕。
- 骨架屏 shimmer 渐变是**功能性加载反馈**，为渐变禁令的白名单豁免项（须有 `prefers-reduced-motion` 降级）。

---

## 7. 布局和控件

| Token | 值 | 用途 |
|-------|----|------|
| `--layout-sidebar-width` | `240px` | 展开侧栏 |
| `--layout-sidebar-collapsed` | `64px` | 折叠侧栏 |
| `--layout-header-height` | `56px` | 顶部栏 |
| `--layout-content-max` | `1440px` | 内容最大宽度 |
| `--layout-page-padding` | `16px` | 页面左右留白 |
| `--control-height-sm/md/lg` | `24 / 28 / 34px` | 控件高度（对应 px10 py4 text-xs 按钮渲染高） |
| `--tag-height-sm/md` | `20 / 22px` | 状态徽章 |
| `--chart-height-sm/md/lg/modal` | `220 / 240 / 280 / 480px` | 图表高度 |
| `--chart-height-hero` | `400px` | `/screen` 桑基主图专用 |

---

## 8. `/screen` 兼容 token

旧 `screen-*` token 不再代表暗色主题，只作为兼容别名保留：

| Token | v3.0 指向 |
|-------|-----------|
| `screen-bg-0` | 浅灰页面（gray-50） |
| `screen-bg-1` | `gray-50` |
| `screen-bg-2` | `gray-100` |
| `screen-border` | `gray-200` |
| `screen-text` | `gray-900` |
| `screen-text-2` | `gray-500` |
| `screen-chart-1..8` | `chart-1..8` |

新增代码不得再写 `data-theme="screen"` 或 `chartColors('screen')`。

---

## 9. 验收

```text
□ tokens.css 与本文色值一致
□ DESIGN.md 与本文口径一致
□ pen/ui.pen 三个顶层画布同步 Data Dense v3（本次迁移未同步，见 CHANGE 2026-08-13 欠账声明）
□ /screen 默认浅色且处在 AppLayout 内，为高密度网格构图
□ 中央桑基大主图为首屏视觉中心，KPI 指标行 + 洞察列表 + 2×2 小图网格环绕
□ 无 12px 以上圆角、无 pill 徽章、无装饰渐变/阴影、无单侧粗边条
□ 字体栈不含 Inter / Roboto / Geist
□ 表格斑马纹 #f8fafc、行高紧凑、单元格 12px
□ 所有业务数字来自 API，接口失败只降级不造假
□ npm run build 通过
```
