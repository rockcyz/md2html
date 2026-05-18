# md2html — Markdown to Interactive HTML Slides

> 一行命令，把 Markdown 文档变成带侧边栏导航、全屏演示模式的精美网页。

## 效果展示

从一个普通的 `.md` 文件，自动生成：

| 功能 | 说明 |
|------|------|
| 🧭 侧边栏导航 | 根据标题层级自动生成，滚动高亮当前章节 |
| 📽️ 全屏演示模式 | 自动分组幻灯片，支持键盘翻页、触屏滑动、缩放 |
| 📊 表格 | Markdown 表格 → 响应式 HTML 表格 |
| 💬 四类提示框 | 自动识别警告/小贴士/思考/知识拓展 |
| 🎯 学习目标卡片 | `> **学习目标**` 自动渲染为编号卡片 |
| 📋 前置知识卡片 | `> **前置知识**` 自动渲染为列表卡片 |
| 🎨 代码块 | 语法高亮风格深色代码块 |
| 📱 响应式 | 桌面/平板/手机全适配 |
| ⏳ 滚动动画 | 内容块进入视口时淡入 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/md2html.git
cd md2html

# 2. 准备一个参考 HTML 模板（提供 CSS/JS 样式）
#    见下方"模板说明"

# 3. 转换你的 Markdown
python convert_md_to_html.py "你的文档.md" --ref template.html --title "页面标题"
```

### 前置条件

- Python 3.7+
- 无需安装任何第三方库（仅使用标准库）

## 用法

### 基本用法

```bash
# 转换单个文件（自动在同目录查找参考模板）
python convert_md_to_html.py "文档.md"

# 指定页面标题
python convert_md_to_html.py "文档.md" --title "我的文档"

# 指定课程/项目标签（显示在页面顶部）
python convert_md_to_html.py "文档.md" --course "项目名" --title "第一章"

# 指定输出路径
python convert_md_to_html.py "文档.md" -o output.html
```

### 批量转换

```bash
# 转换目录下所有 .md 文件
python convert_md_to_html.py --dir ./docs/ --ref template.html
```

### 完整参数

```
python convert_md_to_html.py [markdown文件] [选项]

参数:
  markdown               Markdown 文件路径
  --dir PATH             批量转换目录下所有 .md 文件
  --ref PATH             参考 HTML 模板（提供样式和脚本）
  -o, --output PATH      输出文件路径
  --course TEXT          顶部课程/项目标签（默认: "文档"）
  --title TEXT           页面标题（默认从文件名推断）
```

## 模板说明

工具需要一个**参考 HTML 模板**来提供 CSS 样式和 JavaScript 交互逻辑。模板应包含：

- 完整的 CSS 变量系统和样式定义
- 侧边栏导航、演示模式的 JavaScript 代码
- 响应式布局和动画效果

工具会提取模板中的 CSS 和 JS，然后填入你的 Markdown 内容。

<details>
<summary>模板的 CSS 类名约定（点击展开）</summary>

| CSS 类 | 用途 |
|--------|------|
| `.objectives-card` | 学习目标卡片 |
| `.prereq-card` | 前置知识卡片 |
| `blockquote.warn` | 警告提示框（红） |
| `blockquote.tip` | 小贴士提示框（绿） |
| `blockquote.think` | 思考提示框（黄） |
| `blockquote.did-you-know` | 知识拓展提示框（蓝） |
| `.content-img` | 懒加载图片 |
| `.fade-section` | 滚动淡入动画 |
| `.highlight-box` | 高亮信息框 |
| `.section-divider` | 章节分隔线 |

侧边栏导航结构：

```html
<aside id="sidebar">
  <div class="nav-section">
    <div class="nav-section-title">分类名</div>
    <nav>
      <a href="#section-id" class="sub">
        <span class="nav-dot"></span>链接文字
      </a>
    </nav>
  </div>
</aside>
```

演示模式需要以下元素：

```html
<div id="preso-stage"></div>
<div id="preso-nav">
  <button class="preso-nav-btn preso-arrow prev">◀</button>
  <button class="preso-nav-btn preso-arrow next">▶</button>
  <span class="preso-counter"></span>
  <button class="preso-nav-btn preso-exit">✕</button>
</div>
```

`var slideGroups = [...]` 数组定义了每张幻灯片包含哪些 section ID。
</details>

## Markdown 编写约定

工具会识别以下 Markdown 模式并自动美化：

### 学习目标 & 前置知识

```markdown
> **学习目标**
>
> 1. 掌握基本概念
> 2. 能够独立操作

> **前置知识**
>
> - 已了解 HTML 基础
> - 有命令行使用经验
```

### 提示框

工具根据关键词自动判断提示框类型：

```markdown
> **小贴士**：这是一个绿色提示框。

> **安全规则**：Key 不能泄露。—— 自动识别为红色警告框。

> **思考一下**：为什么这样设计？—— 自动识别为黄色思考框。

> **你知道吗**：这个技术诞生于 1972 年。—— 自动识别为蓝色拓展框。
```

### 表格

```markdown
| 特性 | 说明 |
|------|------|
| CSV | 纯文本表格格式 |
| JSON | 支持嵌套结构 |
```

### 代码块 & Mermaid 图表

````markdown
```python
print("hello")
```

```mermaid
flowchart LR
    A[开始] --> B[结束]
```
````

## 工作原理

```
你的 Markdown
    │
    ▼
┌─────────────────────────────┐
│ 1. 解析标题 → 侧边栏导航     │
│ 2. 解析内容 → HTML 正文      │
│ 3. 识别特殊块 → 美化卡片     │
│ 4. 替换模板中的内容          │
│ 5. 输出完整单文件 HTML       │
└─────────────────────────────┘
    │
    ▼
可演示的交互式网页
```

转换结果是一个**完全自包含的 HTML 文件**——无需 Web 服务器，双击即可在浏览器中打开，侧边栏导航、全屏演示、响应式布局全部就绪。

## 许可

MIT
