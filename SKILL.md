---
name: md2html-slides
description: Convert Markdown files to interactive HTML slides with sidebar navigation, fullscreen presentation mode, and smart blockquote styling. Use when the user wants to turn Markdown documents into self-contained, presentable web pages.
---

# Markdown → Interactive HTML Slides

Convert a Markdown file into a self-contained HTML page featuring auto-generated sidebar navigation, fullscreen presentation mode, and styled content blocks — all in a single file you can double-click to open.

## When to use

- User asks to convert Markdown to HTML slides or web pages
- User wants a presentation-ready HTML from their Markdown notes
- User needs batch conversion of Markdown files in a directory
- User mentions "md2html", "markdown to slides", or "presentation mode"

## What it produces

| Feature | Description |
|---------|-------------|
| Sidebar navigation | Auto-built from `#`, `##`, `###` heading hierarchy |
| Presentation mode | Fullscreen slides with keyboard (← → Esc), touch, and zoom controls |
| Objectives card | Styled numbered card from `> **学习目标**` blockquote |
| Prerequisites card | Styled bullet card from `> **前置知识**` blockquote |
| Smart blockquotes | Auto-detects warning (red), tip (green), think (amber), did-you-know (blue) |
| Tables | Markdown tables → responsive HTML `<table>` |
| Code blocks | `<pre>` with escape handling; Mermaid diagram support |
| Scroll animations | Content fades in as you scroll |
| Responsive layout | Desktop sidebar + mobile hamburger toggle |

## How it works

The script needs a **reference HTML template** to borrow CSS styles and JavaScript from. It extracts the `<style>` and `<script>` blocks, replaces the content with the parsed Markdown, and writes a complete self-contained HTML file.

```
Markdown + Reference HTML template ──▶ Interactive HTML page
```

## Usage

### Basic — convert one file

```bash
python {baseDir}/scripts/convert_md_to_html.py "document.md" --title "Page Title"
```

### Specify a reference template

```bash
python {baseDir}/scripts/convert_md_to_html.py "document.md" \
    --ref "path/to/template.html" \
    --title "Page Title"
```

### Batch — convert all .md files in a directory

```bash
python {baseDir}/scripts/convert_md_to_html.py \
    --dir ./docs/ \
    --ref "path/to/template.html"
```

### Full options

```
python {baseDir}/scripts/convert_md_to_html.py [markdown] [options]

Arguments:
  markdown              Path to a .md file
  --dir PATH            Convert all .md files in a directory
  --ref PATH            Reference HTML template (auto-searched if omitted)
  -o, --output PATH     Output HTML path
  --course TEXT         Course/project label displayed in the header
  --title TEXT          Page title (defaults to the Markdown filename)
```

## Reference template requirements

The template HTML must contain these CSS classes so the converter can style content correctly:

| CSS class | Purpose |
|-----------|---------|
| `.objectives-card` | Numbered card with teal left border |
| `.prereq-card` | Bullet card with teal left border |
| `blockquote.warn` | Red-tinted warning block |
| `blockquote.tip` | Green-tinted tip block |
| `blockquote.think` | Amber-tinted reflection block |
| `blockquote.did-you-know` | Blue-tinted knowledge block |
| `#sidebar`, `.nav-section`, `.nav-dot` | Sidebar navigation structure |
| `#preso-stage`, `#preso-nav` | Presentation mode elements |
| `var slideGroups = [...]` | JavaScript array mapping slide numbers to section IDs |

The template can be any HTML page — the converter extracts CSS + JS, discards the body, and fills in the Markdown content.

## Markdown conventions

**Objectives / Prerequisites** — detected by keywords in blockquotes:

```markdown
> **学习目标**
>
> 1. First goal
> 2. Second goal

> **前置知识**
>
> - Required skill A
> - Required skill B
```

**Styled blockquotes** — auto-classified by content keywords:

| Keyword pattern | Renders as |
|-----------------|------------|
| 安全规则, 绝不, 泄露, ⚠ | Red warning block |
| 小贴士, 小提示, tips, 💡 | Green tip block |
| 思考, 想一想 | Amber think block |
| 你知道吗, 类比, 最重要, 认知转变 | Blue knowledge block |

**Tables with empty first-cell headers** — preserved correctly:

```markdown
| | Column A | Column B |
|---|----------|----------|
| Row 1 | A1 | B1 |
```

## Implementation notes

- Zero dependencies — uses Python stdlib only (`re`, `argparse`, `pathlib`)
- The script auto-searches the Markdown file's directory for a reference HTML template if `--ref` is not provided
- Output is a single self-contained HTML file — no web server needed
- Section IDs are generated deterministically from heading text so sidebar links and presentation slides always match
