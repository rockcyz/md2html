#!/usr/bin/env python3
"""
课程 Markdown → 交互式 HTML Slide 转换器

将课程 Markdown 文件转换为带侧边栏导航、全屏演示模式的交互式 HTML 页面。
样式参考: 3.2-数据存储与管理-让数据井井有条.html

用法:
    # 转换单个文件（自动在同目录下找参考模板，或用 --ref 指定）
    python convert_md_to_html.py "1. 计算机实践基础.md"

    # 指定参考模板
    python convert_md_to_html.py "1. 计算机实践基础.md" --ref "3.2-xxx.html"

    # 指定输出路径和元数据
    python convert_md_to_html.py "1. 计算机实践基础.md" -o output.html \\
        --course "计算思维概论" --title "计算机实践基础 💻"

    # 批量转换目录下所有 .md 文件
    python convert_md_to_html.py --dir ./课程内容/
"""

import re
import sys
import os
import argparse
from pathlib import Path


# ── Markdown → HTML 核心转换逻辑 ──────────────────────────────

def extract_template_parts(ref_html_path):
    """从参考 HTML 中提取 CSS + JS 模板。"""
    with open(ref_html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    head_end = html.find('</style>') + len('</style>')
    head_part = html[:head_end]

    body_start = html.find('<body>')
    js_start = html.find('<script>\n(function()')
    body_html = html[body_start:js_start]
    js_part = html[js_start:]

    return head_part, body_html, js_part


def generate_id(title):
    """从标题生成 section ID。"""
    clean = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', title)
    clean = clean.strip().lower()

    id_map = {
        '学习目标': 'objectives', '前置知识': 'prerequisites',
        '电脑里的磁盘文件与文件夹': 'sec-1', '磁盘电脑的仓库': 'sec-1-1',
        '文件夹与文件仓库里的抽屉和纸张': 'sec-1-2',
        '文件的命名规则名字后缀名扩展名': 'sec-1-3',
        '常见文件类型速查': 'sec-1-4', '压缩包把一堆东西打包压缩': 'sec-1-5',
        '怎么找到你的文件路径': 'sec-2', '绝对路径从仓库门口开始走': 'sec-2-1',
        '相对路径从你站的地方开始走': 'sec-2-2',
        '为什么实验要求所有文件放在同一个文件夹': 'sec-2-3',
        '小练习规范文件管理': 'sec-2-4',
        '终端入门用文字指令控制电脑': 'sec-3', '什么是终端': 'sec-3-1',
        '打开终端的三种方式': 'sec-3-2', '几个基本命令': 'sec-3-3',
        '终端里的当前位置': 'sec-3-4',
        'windows桌面与系统组件': 'sec-4', '开始菜单': 'sec-4-1',
        '用户账户你的数字身份证': 'sec-4-2', '资源管理器': 'sec-4-3',
        '任务管理器与系统进程': 'sec-4-4', '文本编辑器': 'sec-4-5',
        '压缩与解压工具': 'sec-4-6', '日常及专业软件': 'sec-4-7',
        '动手试一试': 'sec-5', '总结': 'summary', '思考问题': 'questions',
        '与ai-agent协作的五个方法论': 'sec-1', '描述需求是一门手艺': 'sec-1-1',
        'ai不知道你看到了什么': 'sec-1-2', '迭代是正常的不失败': 'sec-1-3',
        '报错信息是你最好的朋友': 'sec-1-4', '让ai看到你的文件': 'sec-1-5',
        'llm大模型api让程序拥有智能': 'sec-2', '从对话ai到程序调用ai': 'sec-2-1',
        '什么是apikey为什么它需要保密': 'sec-2-2', '获取deepseekapikey': 'sec-2-3',
        '获取聚合平台apikey一个key玩转多种模型': 'sec-2-4',
        '实验新闻数据智能增强': 'sec-3', '实验目标': 'sec-3-1',
        '实验步骤': 'sec-3-2', '实验产出将在后续课程中使用': 'sec-3-3',
    }
    return id_map.get(clean, clean.replace(' ', '-')[:30])


def parse_markdown_sections(md_text):
    """按标题层级解析 Markdown 为 section 列表。"""
    lines = md_text.split('\n')
    sections = []
    current = {'level': 0, 'title': '', 'content': [], 'id': ''}

    for line in lines:
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            if current['content'] or current['title']:
                sections.append(current)
            current = {
                'level': len(m.group(1)),
                'title': m.group(2).strip(),
                'content': [],
                'id': generate_id(m.group(2).strip()),
            }
        else:
            current['content'].append(line)

    if current['content'] or current['title']:
        sections.append(current)
    return sections


def convert_inline(text):
    """行内 Markdown → HTML。"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                  r'<img class="content-img" data-src="\2" alt="\1" loading="lazy">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'<img\s+src="([^"]+)"[^>]*>',
                  r'<img class="content-img" data-src="\1" loading="lazy">', text)
    return text


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def convert_blockquote(lines):
    """Blockquote → 带类型的 <blockquote> 或 objectives/prereq card。"""
    text = ' '.join(lines)

    # objectives-card
    if re.search(r'学习目标', text):
        items = re.findall(r'\d+\.\s+(.+?)(?=\s*\d+\.\s|\s*$)', text) or [text]
        li = '\n'.join(f'    <li>{convert_inline(i)}</li>' for i in items)
        return f'''<div class="objectives-card">
  <div class="card-label">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
    学习目标
  </div>
  <ol>\n{li}\n  </ol>\n</div>'''

    # prereq-card
    if re.search(r'前置知识', text):
        items = re.findall(r'[-*]\s+(.+?)(?=\s*[-*]\s|\s*$)', text) or [text]
        li = '\n'.join(f'    <li>{convert_inline(i)}</li>' for i in items)
        return f'''<div class="prereq-card">
  <div class="card-label">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
    前置知识
  </div>
  <ul>\n{li}\n  </ul>\n</div>'''

    text = convert_inline(text)

    # 判断 blockquote 类型
    type_rules = [
        (r'(安全规则|绝不|不能|泄露|⚠)', 'warn', '⚠️ 安全警告'),
        (r'(小提示|小贴士|专业贴士|💡|tips)', 'tip', '💡 小贴士'),
        (r'(备选方案|替代)', 'tip', '💡 备选方案'),
        (r'(思考|想一想|动手试一试|🧠)', 'think', '🧠 思考'),
        (r'(类比|打个比方)', 'did-you-know', '📖 你知道吗'),
        (r'(最重要|认知转变|🌟)', 'did-you-know', '🌟 关键认知'),
        (r'(回顾|🔙)', 'did-you-know', '🔙 回顾'),
        (r'(数据库是什么|为什么叫|📖)', 'did-you-know', '📖 知识拓展'),
        (r'(数据清洗不是什么|✅)', 'tip', '✅ 关键要点'),
    ]
    cls, label = '', ''
    for pat, c, l in type_rules:
        if re.search(pat, text):
            cls, label = c, l
            break

    if label:
        return f'<blockquote class="{cls}">\n  <div class="quote-label">{label}</div>\n  <p>{text}</p>\n</blockquote>'
    return f'<blockquote>\n  <p>{text}</p>\n</blockquote>'


def convert_table(lines):
    """Markdown 表格 → HTML <table>（保留空单元格）。"""
    data_lines = [l for l in lines if not re.match(r'^[\|\s\-:]+$', l.strip())]
    if len(data_lines) < 2:
        return ''

    hdr = [c.strip() for c in data_lines[0].split('|')[1:-1]]
    th = ''.join(f'<th>{convert_inline(c)}</th>' for c in hdr)

    rows = []
    for line in data_lines[1:]:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        td = ''.join(f'<td>{convert_inline(c)}</td>' for c in cells)
        rows.append(f'<tr>{td}</tr>')

    return f'<table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n' + '\n'.join(rows) + '\n</tbody>\n</table>'


def convert_content(lines):
    """逐行解析 Markdown 内容 → HTML。"""
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            out.append(''); i += 1; continue

        if line.strip() == '---':
            out.append('<div class="section-divider"><span>&#9670;</span></div>')
            i += 1; continue

        if line.startswith('>'):
            bq = []
            while i < len(lines) and lines[i].startswith('>'):
                bq.append(lines[i][1:].strip()); i += 1
            out.append(convert_blockquote(bq)); continue

        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i]); i += 1
            i += 1
            code_text = '\n'.join(code_lines)
            if lang == 'mermaid':
                out.append(f'<pre class="mermaid" style="display:flex;justify-content:center;margin:28px 0;">\n{code_text}\n</pre>')
            else:
                out.append(f'<pre>{escape_html(code_text)}</pre>')
            continue

        if '|' in line and line.strip().startswith('|'):
            tbl = []
            while i < len(lines) and '|' in lines[i]:
                tbl.append(lines[i]); i += 1
            out.append(convert_table(tbl)); continue

        if re.match(r'^\d+\.\s', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i]):
                items.append(re.sub(r'^\d+\.\s', '', lines[i])); i += 1
            li = ''.join(f'<li>{convert_inline(it)}</li>' for it in items)
            out.append(f'<ol>\n{li}\n</ol>'); continue

        if re.match(r'^[-*]\s', line):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s', lines[i]):
                items.append(re.sub(r'^[-*]\s', '', lines[i])); i += 1
            li = ''.join(f'<li style="margin-bottom:8px;">{convert_inline(it)}</li>' for it in items)
            out.append(f'<ul>\n{li}\n</ul>'); continue

        out.append(f'<p>{convert_inline(line)}</p>')
        i += 1

    return '\n'.join(out)


def build_sidebar(sections):
    """从 sections 构建侧边栏导航 HTML。"""
    items = []
    for sec in sections:
        if sec['level'] == 0:
            continue
        t, sid = sec['title'], sec['id']

        if sec['level'] == 1:
            if t in ['学习目标', '前置知识']:
                items.append(('category', '概览'))
                items.append(('link', sid, re.sub(r'^[^\w\u4e00-\u9fff]+', '', t), False))
            elif '总结' in t:
                items.append(('category', '总结'))
                items.append(('link', sid, re.sub(r'^[^\w\u4e00-\u9fff]+', '', t), False))
            elif '思考问题' in t:
                items.append(('link', sid, re.sub(r'^[^\w\u4e00-\u9fff]+', '', t), False))
            elif '动手试一试' in t:
                items.append(('category', '动手实践'))
                items.append(('link', sid, re.sub(r'^[^\w\u4e00-\u9fff]+', '', t), False))
        elif sec['level'] == 2:
            st = re.sub(r'^[\d.]+\s*', '', t)
            st = re.sub(r'^[^\w\u4e00-\u9fff]+', '', st)
            items.append(('category', st[:20]))
            items.append(('link', sid, st[:30], False))
        elif sec['level'] == 3:
            st = re.sub(r'^[\d.]+\s*', '', t)
            st = re.sub(r'^[^\w\u4e00-\u9fff]+', '', st)
            items.append(('link', sid, st[:30], True))
        elif sec['level'] == 4:
            st = re.sub(r'^[^\w\u4e00-\u9fff]+', '', t)
            items.append(('link', sid, st[:30], True))

    html, in_sec = '', False
    for item in items:
        if item[0] == 'category':
            if in_sec:
                html += '    </nav>\n  </div>\n'
            html += f'  <div class="nav-section">\n    <div class="nav-section-title">{item[1]}</div>\n    <nav>\n'
            in_sec = True
        else:
            cls = 'sub' if item[3] else ''
            html += f'      <a href="#{item[1]}" class="{cls}"><span class="nav-dot"></span>{item[2]}</a>\n'
    if in_sec:
        html += '    </nav>\n  </div>'
    return html


def build_slide_groups(sections):
    """从 sections 构建演示模式幻灯片分组 JS。"""
    groups, cur = [], []
    for sec in sections:
        if sec['level'] == 0:
            continue
        sid = sec['id']
        if sid in ['objectives', 'prerequisites']:
            if sid == 'objectives':
                cur = [sid]
            else:
                cur.append(sid); groups.append(cur); cur = []
        elif sec['level'] in [1, 2]:
            if cur:
                groups.append(cur)
            cur = [sid]
        else:
            cur.append(sid)
    if cur:
        groups.append(cur)

    lines = ['var slideGroups = [']
    for g in groups:
        lines.append(f"  [{', '.join(f'{x!r}' for x in g)}],")
    lines.append('];')
    return '\n'.join(lines)


# ── 主流程 ────────────────────────────────────────────────────

def convert_one(md_path, ref_html_path, output_path, course_tag, section_title):
    """转换单个 Markdown 文件为 HTML。"""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    head_part, _body_html, js_part = extract_template_parts(ref_html_path)
    sections = parse_markdown_sections(md_text)

    # ── 构建正文 HTML ──
    content = ''
    for sec in sections:
        if sec['level'] == 0:
            continue
        title, sid, level = sec['title'], sec['id'], sec['level']
        body = convert_content(sec['content'])

        if level == 1:
            if sid == 'objectives':
                items = re.findall(r'<li>(.*?)</li>', body, re.DOTALL)
                li = '\n'.join(f'    <li>{it}</li>' for it in items)
                content += f'''<section id="objectives" class="fade-section">
<div class="objectives-card">
  <div class="card-label">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
    学习目标
  </div>
  <ol>\n{li}\n  </ol>\n</div>\n</section>\n'''
            elif sid == 'prerequisites':
                items = re.findall(r'<li>(.*?)</li>', body, re.DOTALL)
                li = '\n'.join(f'    <li>{it}</li>' for it in items)
                content += f'''<section id="prerequisites" class="fade-section">
<div class="prereq-card">
  <div class="card-label">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
    前置知识
  </div>
  <ul>\n{li}\n  </ul>\n</div>\n</section>\n'''
            elif '思考问题' in title:
                items = re.findall(r'<li>(.*?)</li>', body, re.DOTALL)
                li = '\n'.join(f'    <li style="margin-bottom:14px;">{it}</li>' for it in items)
                content += f'<section id="questions" class="fade-section">\n<h2>{title}</h2>\n<div class="objectives-card" style="counter-reset:none;">\n  <ol>\n{li}\n  </ol>\n</div>\n</section>\n'
            else:
                content += f'<section id="{sid}" class="fade-section">\n<h2>{title}</h2>\n{body}\n</section>\n'
        elif level == 2:
            content += f'<section id="{sid}" class="fade-section">\n<h2>{title}</h2>\n{body}\n</section>\n'
        elif level == 3:
            content += f'<section id="{sid}" class="fade-section">\n<h3>{title}</h3>\n{body}\n</section>\n'
        else:
            content += f'<section id="{sid}" class="fade-section">\n<h4>{title}</h4>\n{body}\n</section>\n'

    sidebar_html = build_sidebar(sections)
    slide_js = build_slide_groups(sections)
    js_part_modified = re.sub(r'var slideGroups = \[[\s\S]*?\];', slide_js, js_part)

    # ── 修改 title ──
    head_part = re.sub(
        r'<title>.*?</title>',
        f'<title>{section_title} — 计算思维概论</title>',
        head_part
    )

    # ── 修改 hero slide 标题 ──
    js_part_modified = re.sub(
        r"hero\.innerHTML = '<h1>.*?</h1>",
        f"hero.innerHTML = '<h1>{section_title}</h1>",
        js_part_modified
    )

    final_html = f'''{head_part}
</head>
<body>
<div id="progress-bar"></div>
<header id="top-header">
  <span class="course-tag">{course_tag}</span>
  <span class="section-title">{section_title}</span>
</header>
<button id="sidebar-toggle" aria-label="Toggle navigation">☰</button>
<aside id="sidebar">
{sidebar_html}
</aside>
<main id="main-content">
<div class="content-wrapper">
<h1>{section_title}</h1>
<p class="subtitle">{course_tag} · 适用专业：戏剧文学 / 文艺编导</p>
{content}
</div>
</main>
<button id="back-to-top" aria-label="回到顶部">↑</button>
<button id="preso-toggle" class="preso-toggle-btn" title="全屏演示模式" aria-label="进入全屏演示">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
</button>
<div id="preso-stage"></div>
<div id="preso-nav">
  <button class="preso-nav-btn preso-arrow prev" aria-label="上一页" title="上一页 (←)">◀</button>
  <button class="preso-nav-btn preso-arrow next" aria-label="下一页" title="下一页 (→)">▶</button>
  <span class="preso-counter" id="preso-counter">1 / 1</span>
  <div class="preso-zoom-group">
    <button class="preso-zoom-btn preso-zoom-out" aria-label="缩小" title="缩小 (Ctrl+-)">−</button>
    <span class="preso-zoom-label" id="preso-zoom-label">100%</span>
    <button class="preso-zoom-btn preso-zoom-in" aria-label="放大" title="放大 (Ctrl+=)">+</button>
    <button class="preso-zoom-btn preso-zoom-reset" aria-label="重置缩放" title="重置 (Ctrl+0)" style="font-size:0.75rem;">↺</button>
  </div>
  <button class="preso-nav-btn preso-exit" aria-label="退出演示" title="退出 (Esc)">✕</button>
</div>
{js_part_modified}
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"[OK] {output_path}")


def find_reference_html(md_dir):
    """在 md 所在目录或父目录查找参考 HTML 模板。"""
    # 优先找同目录下的 *数据存储与管理*.html
    for f in sorted(md_dir.iterdir()):
        if f.suffix == '.html' and '数据存储' in f.name:
            return f
    # 其次找同目录下任意 .html
    for f in sorted(md_dir.iterdir()):
        if f.suffix == '.html':
            return f
    return None


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='课程 Markdown → 交互式 HTML Slide 转换器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python convert_md_to_html.py "1. 计算机实践基础.md"
  python convert_md_to_html.py "1. 计算机实践基础.md" --ref template.html
  python convert_md_to_html.py --dir ./课程内容/ --ref template.html
  python convert_md_to_html.py "1. 计算机实践基础.md" --course "计算思维概论" --title "计算机实践基础 💻"
        ''',
    )
    parser.add_argument('markdown', nargs='?', help='Markdown 文件路径')
    parser.add_argument('--dir', help='批量转换目录下所有 .md 文件')
    parser.add_argument('--ref', help='参考 HTML 模板路径（默认自动查找）')
    parser.add_argument('-o', '--output', help='输出 HTML 路径（默认与 md 同目录同名）')
    parser.add_argument('--course', default='计算思维概论', help='课程标签（默认: 计算思维概论）')
    parser.add_argument('--title', help='页面标题（默认从 md 文件名推断）')

    args = parser.parse_args()

    if args.dir:
        md_dir = Path(args.dir)
        md_files = sorted(md_dir.glob('*.md'))
        if not md_files:
            print(f'❌ 目录下没有 .md 文件: {args.dir}')
            sys.exit(1)
        ref = args.ref and Path(args.ref) or find_reference_html(md_dir)
        if not ref:
            print('❌ 未找到参考 HTML 模板，请用 --ref 指定')
            sys.exit(2)
        for md in md_files:
            title = args.title or md.stem
            out = md.with_suffix('.html')
            convert_one(str(md), str(ref), str(out), args.course, title)
        print(f'\n🎉 共转换 {len(md_files)} 个文件')
        return

    if not args.markdown:
        parser.print_help()
        sys.exit(1)

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f'❌ 文件不存在: {args.markdown}')
        sys.exit(1)

    ref = args.ref and Path(args.ref) or find_reference_html(md_path.parent)
    if not ref:
        print('❌ 未找到参考 HTML 模板，请用 --ref 指定')
        sys.exit(2)

    title = args.title or md_path.stem
    out = args.output and Path(args.output) or md_path.with_suffix('.html')
    convert_one(str(md_path), str(ref), str(out), args.course, title)


if __name__ == '__main__':
    main()
