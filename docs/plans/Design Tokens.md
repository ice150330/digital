# 设计系统令牌（Design Tokens）v2.0

> 风格定位：Halo 浅色 · 圆角卡片 · 现代数据工作台
> 适用范围：`frontend/src/styles/tokens.css`、`DESIGN.md`、`pen/ui.pen`
> 更新日期：2026-08-02

---

## 1. 核心变化

| 项 | v1.0 | v2.0 |
|----|------|------|
| 默认主题 | 浅色 + `/screen` 独立暗色 | 全站默认浅色，`/screen` 并入 AppLayout |
| 主色 | 清澈蓝 `#3B82F6` | Halo 紫蓝 `#5749F4` |
| 卡片圆角 | 8px 基准 | 24px 卡片、40px 主面板 |
| 大屏构图 | 多小图表拼版 | 中央转化星图 + 外圈业务徽章 |
| 图表主题 | default/screen 两套 | default 一套浅色主题 |

---

## 2. 色彩令牌

### 2.1 品牌主色 Primary

| Token | 值 | 用途 |
|-------|----|------|
| `--color-primary-50` | `#f3f1ff` | 选中弱底、图标底 |
| `--color-primary-100` | `#e7e3ff` | 轻提示背景 |
| `--color-primary-200` | `#cbc4ff` | 弱边框、hover 边界 |
| `--color-primary-300` | `#a99dff` | 输入 hover、辅助线 |
| `--color-primary-400` | `#7e70fb` | hover 强调 |
| `--color-primary-500` | `#5749f4` | 主色基准 |
| `--color-primary-600` | `#4639d8` | active、深强调 |
| `--color-primary-700` | `#352bb0` | 强文字强调 |

### 2.2 辅助色 Secondary

| Token | 值 | 用途 |
|-------|----|------|
| `--color-secondary-50` | `#f0fdfa` | 青色浅底 |
| `--color-secondary-100` | `#ccfbf1` | 青色标签底 |
| `--color-secondary-400` | `#2dd4bf` | 辅助 hover |
| `--color-secondary-500` | `#14b8a6` | 辅助强调、图表第二色 |
| `--color-secondary-600` | `#0d9488` | 辅助 active |

### 2.3 中性色 Neutral

| Token | 值 | 用途 |
|-------|----|------|
| `--color-white` | `#ffffff` | 页面和卡片底 |
| `--color-gray-50` | `#fafafb` | 弱背景 |
| `--color-gray-100` | `#f5f5f5` | tile、表头、骨架 |
| `--color-gray-200` | `#e1e2e5` | 图表网格、弱线 |
| `--color-gray-300` | `#c5c5cb` | 默认边框 |
| `--color-gray-400` | `#939399` | 占位文字 |
| `--color-gray-500` | `#616167` | 次级文字 |
| `--color-gray-700` | `#403f51` | 正文 |
| `--color-gray-900` | `#2a2933` | 标题 |

### 2.4 语义色

| Token | 主色 | 浅底 | 边框 | 文字 |
|-------|------|------|------|------|
| success | `#22c55e` | `#f0fdf4` | `#bbf7d0` | `#15803d` |
| warning | `#f59e0b` | `#fffbeb` | `#fde68a` | `#b45309` |
| danger | `#ef4444` | `#fef2f2` | `#fecaca` | `#b91c1c` |
| info | `#0ea5e9` | `#f0f9ff` | `#bae6fd` | `#0369a1` |

---

## 3. 语义别名

| Token | 值 | 用途 |
|-------|----|------|
| `--bg-page` | `var(--color-white)` | 页面背景 |
| `--bg-card` | `var(--color-white)` | 卡片、弹窗 |
| `--bg-subtle` | `var(--color-gray-100)` | 弱底 |
| `--bg-tile` | `var(--color-gray-100)` | 徽章、指标块 |
| `--text-title` | `var(--color-gray-900)` | 标题 |
| `--text-body` | `var(--color-gray-700)` | 正文 |
| `--text-secondary` | `var(--color-gray-500)` | 辅助文字 |
| `--text-placeholder` | `var(--color-gray-400)` | 占位文字 |
| `--border-default` | `var(--color-gray-300)` | 默认边框 |
| `--border-hover` | `var(--color-primary-300)` | hover 边框 |
| `--border-focus` | `var(--color-primary-500)` | focus 边框 |

---

## 4. 图表色板

| Token | 值 |
|-------|----|
| `--chart-1` | `#5749f4` |
| `--chart-2` | `#14b8a6` |
| `--chart-3` | `#f59e0b` |
| `--chart-4` | `#8b5cf6` |
| `--chart-5` | `#ec4899` |
| `--chart-6` | `#22c55e` |
| `--chart-7` | `#f97316` |
| `--chart-8` | `#06b6d4` |

图表轴线使用 `--chart-grid`，轴文字使用 `--chart-axis-text`。`chartTheme.ts` 是运行时唯一取色入口。

---

## 5. 字体

| Token | 值 | 用途 |
|-------|----|------|
| `--font-family-base` | `"Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif` | 正文、控件 |
| `--font-family-number` | `"DIN Alternate", "Roboto Mono", "SF Mono", monospace` | KPI、概率、run_id |
| `--font-family-code` | `"JetBrains Mono", "Fira Code", Consolas, monospace` | 代码、日志 |

字号：`12 / 13 / 14 / 16 / 20 / 24 / 32 / 40px`。不要用 viewport 宽度缩放字体。

---

## 6. 间距、圆角、阴影

间距：`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48px`。

| Radius | 值 | 用途 |
|--------|----|------|
| `--radius-sm` | `6px` | 小标签 |
| `--radius-md` | `12px` | 按钮、输入框 |
| `--radius-lg` | `18px` | 提示、轻容器 |
| `--radius-xl` | `24px` | 弹窗、大卡片 |
| `--radius-card` | `24px` | 标准卡片 |
| `--radius-panel` | `40px` | 大屏主面板 |
| `--radius-full` | `999px` | 胶囊、状态点 |

阴影：

- `--shadow-xs`：输入框、小控件。
- `--shadow-sm`：默认卡片。
- `--shadow-md`：悬浮卡片、下拉。
- `--shadow-lg`：弹窗、抽屉。
- `--shadow-primary`：主按钮和中央星图强调。

---

## 7. 布局和控件

| Token | 值 | 用途 |
|-------|----|------|
| `--layout-sidebar-width` | `240px` | 展开侧栏 |
| `--layout-sidebar-collapsed` | `64px` | 折叠侧栏 |
| `--layout-header-height` | `64px` | 顶部栏 |
| `--layout-content-max` | `1440px` | 内容最大宽度 |
| `--layout-page-padding` | `24px` | 页面左右留白 |
| `--control-height-sm/md/lg` | `28 / 36 / 44px` | 控件高度 |
| `--chart-height-sm/md/lg/modal` | `260 / 280 / 320 / 520px` | 图表高度 |

---

## 8. `/screen` 兼容 token

旧 `screen-*` token 不再代表暗色主题，只作为兼容别名保留：

| Token | v2.0 指向 |
|-------|-----------|
| `screen-bg-0` | 白色页面 |
| `screen-bg-1` | `gray-50` |
| `screen-bg-2` | `gray-100` |
| `screen-border` | `gray-300` |
| `screen-text` | `gray-900` |
| `screen-text-2` | `gray-500` |
| `screen-chart-1..8` | `chart-1..8` |

新增代码不得再写 `data-theme="screen"` 或 `chartColors('screen')`。

---

## 9. 验收

```text
□ tokens.css 与本文色值一致
□ DESIGN.md 与本文口径一致
□ pen/ui.pen 三个顶层画布同步 Halo v2
□ /screen 默认浅色且处在 AppLayout 内
□ 中央转化星图和外圈小图标为主视觉
□ npm run build 通过
```
