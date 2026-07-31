# 设计系统令牌（Design Tokens）

> 风格定位：浅色 · 明亮 · 细腻 · 现代
> 适用场景：数据分析平台 / 可视化大屏 / 管理后台前端界面
> 版本：v1.0

---

## 1. 色彩令牌（Color）

### 1.1 品牌主色（Brand / Primary）

以清澈明亮的蓝色为主色，传递专业、可信、数据感。

| 令牌 | 色值 | 用途 |
|---|---|---|
| `color-primary-50` | `#EFF6FF` | 浅底悬浮、选中背景 |
| `color-primary-100` | `#DBEAFE` | 弱强调背景、标签底色 |
| `color-primary-200` | `#BFDBFE` | 禁用态、分割强调 |
| `color-primary-300` | `#93C5FD` | 辅助图形、次级图标 |
| `color-primary-400` | `#60A5FA` | 悬浮态（hover） |
| `color-primary-500` | `#3B82F6` | **主色基准**：主按钮、链接、激活态 |
| `color-primary-600` | `#2563EB` | 按压态（active）、深色强调 |
| `color-primary-700` | `#1D4ED8` | 深色文字强调 |

### 1.2 辅助色（Secondary）

青色系，与主色协调，用于次要操作与信息补充。

| 令牌 | 色值 | 用途 |
|---|---|---|
| `color-secondary-50` | `#F0FDFA` | 浅底背景 |
| `color-secondary-100` | `#CCFBF1` | 弱强调背景 |
| `color-secondary-400` | `#2DD4BF` | 悬浮态 |
| `color-secondary-500` | `#14B8A6` | 辅助色基准 |
| `color-secondary-600` | `#0D9488` | 按压态 |

### 1.3 语义色（Semantic）

| 令牌 | 色值 | 浅色底 | 用途 |
|---|---|---|---|
| `color-success` | `#22C55E` | `#F0FDF4` | 成功、正向指标、上涨 |
| `color-warning` | `#F59E0B` | `#FFFBEB` | 警告、待处理 |
| `color-danger` | `#EF4444` | `#FEF2F2` | 错误、危险操作、下降 |
| `color-info` | `#0EA5E9` | `#F0F9FF` | 信息提示、中性通知 |

### 1.4 中性色（Neutral）

偏冷灰，保证浅色界面干净通透，文字层级清晰。

| 令牌 | 色值 | 用途 |
|---|---|---|
| `color-gray-0` | `#FFFFFF` | 页面卡片、弹窗底色 |
| `color-gray-50` | `#F8FAFC` | **页面主背景** |
| `color-gray-100` | `#F1F5F9` | 次级背景、表头、骨架屏 |
| `color-gray-200` | `#E2E8F0` | 分割线、边框 |
| `color-gray-300` | `#CBD5E1` | 禁用边框、占位图标 |
| `color-gray-400` | `#94A3B8` | 占位文字、辅助图标 |
| `color-gray-500` | `#64748B` | 次级文字、说明文字 |
| `color-gray-700` | `#334155` | 正文文字 |
| `color-gray-900` | `#0F172A` | 标题文字、强强调 |

### 1.5 数据可视化色板（Chart Palette）

8 色循环序列，浅色背景下保证辨识度与和谐度，按序取用。

| 序号 | 令牌 | 色值 |
|---|---|---|
| 1 | `chart-1` | `#3B82F6`（蓝） |
| 2 | `chart-2` | `#14B8A6`（青） |
| 3 | `chart-3` | `#F59E0B`（橙） |
| 4 | `chart-4` | `#8B5CF6`（紫） |
| 5 | `chart-5` | `#EC4899`（粉） |
| 6 | `chart-6` | `#22C55E`（绿） |
| 7 | `chart-7` | `#F97316`（橘红） |
| 8 | `chart-8` | `#06B6D4`（湖蓝） |

- 上涨 / 正向：`#22C55E`；下跌 / 负向：`#EF4444`（遵循国内习惯可互换为红涨绿跌）
- 图表网格线：`color-gray-200`；坐标轴文字：`color-gray-500`

---

## 2. 字体令牌（Typography）

### 2.1 字体族

| 令牌 | 值 | 用途 |
|---|---|---|
| `font-family-base` | `"Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif` | 界面正文 |
| `font-family-number` | `"DIN Alternate", "Roboto Mono", "SF Mono", monospace` | 数字、指标、表格数值 |
| `font-family-code` | `"JetBrains Mono", "Fira Code", Consolas, monospace` | 代码块 |

### 2.2 字号 / 行高

| 令牌 | 字号 | 行高 | 用途 |
|---|---|---|---|
| `font-size-xs` | 12px | 20px | 辅助说明、标签、表格次级信息 |
| `font-size-sm` | 13px | 22px | 表格正文、表单 |
| `font-size-md` | 14px | 24px | **正文基准**、按钮 |
| `font-size-lg` | 16px | 26px | 卡片标题、强调正文 |
| `font-size-xl` | 20px | 30px | 页面标题、模块标题 |
| `font-size-2xl` | 24px | 34px | 大屏模块标题 |
| `font-size-3xl` | 32px | 42px | 核心指标数字 |
| `font-size-4xl` | 40px | 52px | 大屏主指标 |

### 2.3 字重

| 令牌 | 值 | 用途 |
|---|---|---|
| `font-weight-regular` | 400 | 正文 |
| `font-weight-medium` | 500 | 表格头、强调正文 |
| `font-weight-semibold` | 600 | 卡片/模块标题、指标数字 |
| `font-weight-bold` | 700 | 页面主标题 |

---

## 3. 间距令牌（Spacing）

基于 4px 栅格系统。

| 令牌 | 值 | 典型用途 |
|---|---|---|
| `space-1` | 4px | 图标与文字间距 |
| `space-2` | 8px | 紧凑元素内边距 |
| `space-3` | 12px | 表单项间距 |
| `space-4` | 16px | **基准间距**：卡片内边距 |
| `space-5` | 20px | 卡片标题与内容间距 |
| `space-6` | 24px | 卡片之间、模块间距 |
| `space-8` | 32px | 大区块间距 |
| `space-10` | 40px | 页面区块间距 |
| `space-12` | 48px | 页面顶部留白 |

---

## 4. 圆角令牌（Radius）

| 令牌 | 值 | 用途 |
|---|---|---|
| `radius-sm` | 4px | 标签、小徽章 |
| `radius-md` | 6px | 按钮、输入框 |
| `radius-lg` | 8px | **卡片基准** |
| `radius-xl` | 12px | 弹窗、大型面板 |
| `radius-full` | 9999px | 胶囊按钮、头像、状态点 |

---

## 5. 阴影令牌（Shadow）

浅色界面使用低透明度、偏蓝的柔和阴影，避免脏感。

| 令牌 | 值 | 用途 |
|---|---|---|
| `shadow-xs` | `0 1px 2px 0 rgba(15, 23, 42, 0.04)` | 输入框、小控件 |
| `shadow-sm` | `0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)` | **卡片基准** |
| `shadow-md` | `0 4px 12px -2px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)` | 悬浮卡片、下拉菜单 |
| `shadow-lg` | `0 12px 32px -8px rgba(15, 23, 42, 0.12), 0 4px 8px -4px rgba(15, 23, 42, 0.06)` | 弹窗、抽屉 |
| `shadow-primary` | `0 4px 12px -2px rgba(59, 130, 246, 0.32)` | 主按钮悬浮态 |

---

## 6. 边框令牌（Border）

| 令牌 | 值 | 用途 |
|---|---|---|
| `border-width-default` | 1px | 常规边框 |
| `border-color-default` | `#E2E8F0` | 卡片、表格、输入框边框 |
| `border-color-hover` | `#93C5FD` | 输入框悬浮 |
| `border-color-focus` | `#3B82F6` | 输入框聚焦 |

---

## 7. 动效令牌（Motion）

| 令牌 | 值 | 用途 |
|---|---|---|
| `motion-duration-fast` | 150ms | hover 变色、图标反馈 |
| `motion-duration-base` | 250ms | **基准**：展开收起、状态切换 |
| `motion-duration-slow` | 400ms | 弹窗、抽屉、页面转场 |
| `motion-easing-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | 通用缓动 |
| `motion-easing-out` | `cubic-bezier(0, 0, 0.2, 1)` | 进入动画 |
| `motion-easing-in` | `cubic-bezier(0.4, 0, 1, 1)` | 退出动画 |

---

## 8. 层级令牌（Z-Index）

| 令牌 | 值 | 用途 |
|---|---|---|
| `z-base` | 0 | 常规内容 |
| `z-sticky` | 100 | 吸顶表头、吸顶导航 |
| `z-dropdown` | 1000 | 下拉菜单 |
| `z-overlay` | 1300 | 遮罩层 |
| `z-modal` | 1400 | 弹窗 |
| `z-toast` | 1600 | 全局消息提示 |
| `z-tooltip` | 1700 | 气泡提示 |

---

## 9. 布局令牌（Layout）

| 令牌 | 值 | 用途 |
|---|---|---|
| `layout-sidebar-width` | 240px | 侧边栏展开宽度 |
| `layout-sidebar-collapsed` | 64px | 侧边栏收起宽度 |
| `layout-header-height` | 64px | 顶部导航高度 |
| `layout-content-max` | 1440px | 内容区最大宽度 |
| `layout-page-padding` | 24px | 页面内容左右留白 |

### 断点（Breakpoints）

| 令牌 | 值 | 说明 |
|---|---|---|
| `breakpoint-sm` | 640px | 大屏手机 |
| `breakpoint-md` | 768px | 平板 |
| `breakpoint-lg` | 1024px | 小屏笔记本 |
| `breakpoint-xl` | 1280px | 桌面端（设计基准） |
| `breakpoint-2xl` | 1920px | 大屏 / 可视化大屏 |

---

## 10. CSS 变量（可直接粘贴）

```css
:root {
  /* ===== 品牌主色 ===== */
  --color-primary-50: #EFF6FF;
  --color-primary-100: #DBEAFE;
  --color-primary-200: #BFDBFE;
  --color-primary-300: #93C5FD;
  --color-primary-400: #60A5FA;
  --color-primary-500: #3B82F6;
  --color-primary-600: #2563EB;
  --color-primary-700: #1D4ED8;

  /* ===== 辅助色 ===== */
  --color-secondary-50: #F0FDFA;
  --color-secondary-100: #CCFBF1;
  --color-secondary-400: #2DD4BF;
  --color-secondary-500: #14B8A6;
  --color-secondary-600: #0D9488;

  /* ===== 语义色 ===== */
  --color-success: #22C55E;
  --color-success-bg: #F0FDF4;
  --color-warning: #F59E0B;
  --color-warning-bg: #FFFBEB;
  --color-danger: #EF4444;
  --color-danger-bg: #FEF2F2;
  --color-info: #0EA5E9;
  --color-info-bg: #F0F9FF;

  /* ===== 中性色 ===== */
  --color-white: #FFFFFF;
  --color-gray-50: #F8FAFC;
  --color-gray-100: #F1F5F9;
  --color-gray-200: #E2E8F0;
  --color-gray-300: #CBD5E1;
  --color-gray-400: #94A3B8;
  --color-gray-500: #64748B;
  --color-gray-700: #334155;
  --color-gray-900: #0F172A;

  /* ===== 语义化别名（推荐业务代码使用） ===== */
  --bg-page: var(--color-gray-50);
  --bg-card: var(--color-white);
  --bg-subtle: var(--color-gray-100);
  --text-title: var(--color-gray-900);
  --text-body: var(--color-gray-700);
  --text-secondary: var(--color-gray-500);
  --text-placeholder: var(--color-gray-400);
  --border-default: var(--color-gray-200);
  --border-hover: var(--color-primary-300);
  --border-focus: var(--color-primary-500);

  /* ===== 数据可视化色板 ===== */
  --chart-1: #3B82F6;
  --chart-2: #14B8A6;
  --chart-3: #F59E0B;
  --chart-4: #8B5CF6;
  --chart-5: #EC4899;
  --chart-6: #22C55E;
  --chart-7: #F97316;
  --chart-8: #06B6D4;
  --chart-grid: var(--color-gray-200);
  --chart-axis-text: var(--color-gray-500);

  /* ===== 字体 ===== */
  --font-family-base: "Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
  --font-family-number: "DIN Alternate", "Roboto Mono", "SF Mono", monospace;
  --font-family-code: "JetBrains Mono", "Fira Code", Consolas, monospace;

  --font-size-xs: 12px;
  --font-size-sm: 13px;
  --font-size-md: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;
  --font-size-4xl: 40px;

  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* ===== 间距（4px 栅格） ===== */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* ===== 圆角 ===== */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-full: 9999px;

  /* ===== 阴影 ===== */
  --shadow-xs: 0 1px 2px 0 rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px -2px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04);
  --shadow-lg: 0 12px 32px -8px rgba(15, 23, 42, 0.12), 0 4px 8px -4px rgba(15, 23, 42, 0.06);
  --shadow-primary: 0 4px 12px -2px rgba(59, 130, 246, 0.32);

  /* ===== 动效 ===== */
  --motion-duration-fast: 150ms;
  --motion-duration-base: 250ms;
  --motion-duration-slow: 400ms;
  --motion-easing-default: cubic-bezier(0.4, 0, 0.2, 1);
  --motion-easing-out: cubic-bezier(0, 0, 0.2, 1);
  --motion-easing-in: cubic-bezier(0.4, 0, 1, 1);

  /* ===== 层级 ===== */
  --z-sticky: 100;
  --z-dropdown: 1000;
  --z-overlay: 1300;
  --z-modal: 1400;
  --z-toast: 1600;
  --z-tooltip: 1700;

  /* ===== 布局 ===== */
  --layout-sidebar-width: 240px;
  --layout-sidebar-collapsed: 64px;
  --layout-header-height: 64px;
  --layout-content-max: 1440px;
  --layout-page-padding: 24px;
}
```

---

## 11. 使用建议

1. **业务代码优先使用语义化别名**（`--bg-page`、`--text-body` 等），避免直接引用基础色值，便于后续换肤与暗色模式扩展。
2. **数字类指标统一使用 `font-family-number`**，保证数据跳动时宽度稳定（等宽数字）。
3. **图表配色按 `chart-1 → chart-8` 顺序循环**，单图类目超过 8 个时考虑合并为"其他"。
4. **阴影克制使用**：常规卡片用 `shadow-sm` 或纯边框即可，悬浮/弹层再升级阴影层级。
5. 后续接入暗色模式时，仅需重写 `:root` 下的语义化别名，组件层无需改动。
