#!/usr/bin/env bash
# md2html — 课程 Markdown → 交互式 HTML Slide 转换器
# 用法: md2html "1. 计算机实践基础.md" [--course 课程名] [--title 页面标题] [--ref 参考模板.html]
#       md2html --dir ./课程目录/   （批量转换）
#
# 安装: 将此脚本所在目录加入 PATH，或创建 alias:
#       alias md2html='python ~/.qoder/skills/md2html/convert_md_to_html.py'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python "$SCRIPT_DIR/convert_md_to_html.py" "$@"
