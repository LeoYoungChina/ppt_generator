import streamlit as st
import tempfile
import os
from jinja2 import Environment, FileSystemLoader
from moffee.compositor import composite, PageOption
from moffee.markdown import md
from moffee.utils.md_helper import extract_title
import base64


# 定义主题
THEMES = {
    "default": {
        "name": "默认主题",
        "colors": {
            "background": "#ffffff",
            "text": "#333333",
            "heading1": "#333333",
            "heading2": "#555555",
            "heading3": "#666666",
            "accent": "#4CAF50"
        },
        "fonts": {
            "heading": "Arial, sans-serif",
            "body": "Arial, sans-serif"
        }
    },
    "dark": {
        "name": "暗色主题",
        "colors": {
            "background": "#1e1e1e",
            "text": "#e0e0e0",
            "heading1": "#ffffff",
            "heading2": "#cccccc",
            "heading3": "#bbbbbb",
            "accent": "#4CAF50"
        },
        "fonts": {
            "heading": "Arial, sans-serif",
            "body": "Arial, sans-serif"
        }
    },
    "ocean": {
        "name": "海洋主题",
        "colors": {
            "background": "#f0f8ff",
            "text": "#2f4f4f",
            "heading1": "#000080",
            "heading2": "#0000cd",
            "heading3": "#1e90ff",
            "accent": "#4682b4"
        },
        "fonts": {
            "heading": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            "body": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        }
    },
    "sunset": {
        "name": "日落主题",
        "colors": {
            "background": "#fffaf0",
            "text": "#2f4f4f",
            "heading1": "#ff4500",
            "heading2": "#ff6347",
            "heading3": "#ffa500",
            "accent": "#ff6347"
        },
        "fonts": {
            "heading": "'Georgia', serif",
            "body": "'Georgia', serif"
        }
    }
}


def retrieve_structure(pages):
    """从页面中提取结构信息"""
    current_h1 = None
    current_h2 = None
    current_h3 = None
    last_h1_idx = -1
    last_h2_idx = -1
    last_h3_idx = -1
    page_meta = []
    headings = []
    for i, page in enumerate(pages):
        if page.h1 and page.h1 != current_h1:
            current_h1 = page.h1
            current_h2 = None
            current_h3 = None
            last_h1_idx = len(headings)
            headings.append({"level": 1, "content": page.h1, "page_ids": []})

        if page.h2 and page.h2 != current_h2:
            current_h2 = page.h2
            current_h3 = None
            last_h2_idx = len(headings)
            headings.append({"level": 2, "content": page.h2, "page_ids": []})

        if page.h3 and page.h3 != current_h3:
            current_h3 = page.h3
            last_h3_idx = len(headings)
            headings.append({"level": 3, "content": page.h3, "page_ids": []})

        if page.h1 or page.h2 or page.h3:
            headings[last_h1_idx]["page_ids"].append(i)
        if page.h2 or page.h3:
            headings[last_h2_idx]["page_ids"].append(i)
        if page.h3:
            headings[last_h3_idx]["page_ids"].append(i)

        page_meta.append({"h1": current_h1, "h2": current_h2, "h3": current_h3})

    return {"page_meta": page_meta, "headings": headings}


def get_theme_css(theme_name):
    """根据主题名称生成CSS"""
    theme = THEMES.get(theme_name, THEMES["default"])
    colors = theme["colors"]
    fonts = theme["fonts"]
    
    css_content = f"""
    :root {{
        --colorscheme: light;
        --color-admonition-bg: hsl(0, 0%, 90%);
        --color-admonition-fg: hsl(0, 0%, 50%);
        --colour-warning-bg: hsl(28.5, 74%, 90%);
        --colour-warning-fg: hsl(28.5, 74%, 50%);
        --colour-note-bg: hsl(219.5, 84%, 90%);
        --colour-note-fg: hsl(219.5, 84%, 50%);
        --colour-success-bg: hsl(150, 36.7%, 90%);
        --colour-success-fg: hsl(150, 36.7%, 50%);
        --colour-error-bg: hsl(0, 37%, 90%);
        --colour-error-fg: hsl(0, 37%, 50%);
        --colour-todo-bg: hsl(266.8, 100%, 90%);
        --colour-todo-fg: hsl(267, 100%, 50%);
        --min-element-height: 100px;
        --min-element-width: 100px;
        --slide-width: 960px;
        --slide-height: 540px;
        /* Theme colors */
        --background-color: {colors["background"]};
        --text-color: {colors["text"]};
        --heading1-color: {colors["heading1"]};
        --heading2-color: {colors["heading2"]};
        --heading3-color: {colors["heading3"]};
        --accent-color: {colors["accent"]};
        /* Theme fonts */
        --heading-font: {fonts["heading"]};
        --body-font: {fonts["body"]};
    }}

    @page {{
        size: var(--slide-width) var(--slide-height);
        margin: 0;
    }}

    /* Force colored printing */
    * {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }}

    body {{
        background-color: #333;
        margin: 0;
        padding: 20px;
        font-family: var(--body-font);
    }}

    /* Basic Layouts */
    .slide-container {{
        width: var(--slide-width);
        height: var(--slide-height);
        margin: 20px auto;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        background-color: var(--background-color);
    }}

    .slide-content {{
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        position: relative;
        padding: 0 20px;
        background-color: var(--background-color);
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}

    .slide-number {{
        position: absolute;
        bottom: 0;
        right: 20px;
        font-size: 16px;
        color: var(--text-color);
        opacity: 0.7;
    }}

    h1 {{
        font-size: 2.5em;
        margin: 20px 0;
        text-align: center;
        color: var(--heading1-color);
        font-family: var(--heading-font);
    }}

    h2 {{
        z-index: 1;
        font-size: 2em;
        position: relative;
        padding: 15px 0;
        text-align: center;
        color: var(--heading2-color);
        font-family: var(--heading-font);
    }}

    h3 {{
        font-size: 1.7em;
        text-align: center;
        color: var(--heading3-color);
        font-family: var(--heading-font);
    }}

    .content {{
        display: flex;
        flex-direction: column;
        flex: 1;
        max-height: var(--slide-height);
        overflow: hidden;
        margin: 0 15px 30px 15px;
    }}

    .auto-sizing {{
        display: flex;
        flex-direction: column;
        transform-origin: top left;
        flex: 1;
    }}

    .chunk {{
        display: flex;
        flex: 1;
        max-width: 100%;
        max-height: 100%;
    }}

    .chunk-vertical {{
        flex-direction: column;
    }}

    .chunk-horizontal {{
        flex-direction: row;
        justify-content: space-between;
        gap: 20px;
    }}

    .chunk-paragraph {{
        flex: 1;
        flex-direction: column;
        text-align: justify;
        text-justify: inter-word;
        line-height: 1.5;
        font-size: 28px;
        hyphens: auto;
        max-width: 100%;
        max-height: 100%;
        color: var(--text-color);
        font-family: var(--body-font);
    }}

    .chunk-paragraph > ul {{
        font-size: 26px;
        padding-left: 30px;
        color: var(--text-color);
    }}

    .chunk-paragraph > p:has(img) {{
        position: relative;
        height: 100%;
        width: 100%;
    }}

    .chunk-paragraph img,
    .chunk-paragraph .mermaid {{
        display: block;
        position: absolute;
        object-fit: contain;
        min-height: var(--min-element-height);
        min-width: var(--min-element-width);
        width: 100%;
        height: 100%;
        margin: auto;
    }}

    /* Admonition Styles */
    div.admonition {{
        font-size: 0.9em;
        border-radius: 10px;
        padding: 1rem 2rem;
        margin: 10px 0;
        background-color: var(--color-admonition-bg);
    }}

    div.admonition>pre {{
        margin: 0.4em 1em;
    }}

    div.admonition>p.admonition-title {{
        position: relative;
        font-weight: 600;
        margin: -0.7rem 0 0 0;
        padding: 0.3rem 1rem 0.3rem 0rem;
        color: var(--color-admonition-fg);
    }}

    div.attention,
    div.danger,
    div.error {{
        background-color: var(--colour-error-bg);
    }}

    div.important,
    div.caution,
    div.warning {{
        background-color: var(--colour-warning-bg);
    }}

    div.note {{
        background-color: var(--colour-note-bg);
    }}

    div.hint,
    div.tip,
    div.seealso {{
        background-color: var(--colour-success-bg);
    }}

    div.admonition-todo {{
        background-color: var(--colour-todo-bg);
    }}

    div.attention>p.admonition-title,
    div.danger>p.admonition-title,
    div.error>p.admonition-title {{
        color: var(--colour-error-fg);
    }}

    div.important>p.admonition-title,
    div.caution>p.admonition-title,
    div.warning>p.admonition-title {{
        color: var(--colour-warning-fg);
    }}

    div.note>p.admonition-title {{
        color: var(--colour-note-fg);
    }}

    div.hint>p.admonition-title,
    div.tip>p.admonition-title,
    div.seealso>p.admonition-title {{
        color: var(--colour-success-fg);
    }}

    div.admonition-todo>p.admonition-title {{
        color: var(--colour-todo-fg);
    }}

    /* Code blocks */
    pre {{
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        font-size: 20px;
    }}

    code {{
        font-family: 'Courier New', Courier, monospace;
    }}

    /* Presentation mode */
    body.presentation-mode .slide-container {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        margin: 0;
        box-shadow: none;
    }}

    body.presentation-mode .slide-container:not(.active) {{
        display: none;
    }}

    body.presentation-mode .slide-container.active {{
        display: block;
    }}

    /* Floating buttons */
    .floating-btn {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }}

    .action-btn {{
        background-color: var(--accent-color);
        border: none;
        color: white;
        padding: 10px 15px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }}

    .action-btn:hover {{
        background-color: color-mix(in srgb, var(--accent-color) 80%, black);
    }}

    /* Centered layout */
    .slide-content.centered {{
        justify-content: center;
        align-items: center;
        text-align: center;
    }}

    .slide-content.centered h1,
    .slide-content.centered h2,
    .slide-content.centered h3 {{
        width: 100%;
    }}

    .slide-content.centered .content {{
        justify-content: center;
        align-items: center;
    }}

    @media print {{
        body {{
            background-color: var(--background-color);
        }}
        
        .slide-container {{
            page-break-after: always;
            box-shadow: none;
            margin: 0;
        }}
        
        .floating-btn {{
            display: none;
        }}
    }}
    """
    
    return css_content


def render_jinja2(document: str, theme: str = "default") -> str:
    """使用 Jinja2 模板渲染 HTML"""
    # 创建临时目录和模板
    temp_dir = tempfile.mkdtemp()
    
    # 根据主题获取CSS
    css_content = get_theme_css(theme)
    
    # 创建 index.html 模板
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title|default('Presentation') }}</title>
        <style>{{ css_content }}</style>
    </head>
    <body>
        {% for slide in slides %}
        <div class="slide-container">
            {% set layout = slide.layout|default('content') %}
            <div class="slide-content {{ 'centered' if layout == 'centered' else '' }}" 
                 style="{% for key, value in slide.styles.items() %}{{ key }}: {{ value }}; {% endfor %}">
                {% if slide.h1 %}
                <h1>{{ slide.h1 }}</h1>
                {% endif %}
                {% if slide.h2 %}
                <h2>{{ slide.h2 }}</h2>
                {% endif %}
                {% if slide.h3 %}
                <h3>{{ slide.h3 }}</h3>
                {% endif %}
                <div class="content">
                    <div class="auto-sizing">
                        {% macro render_chunk(chunk) %}
                            {% if chunk.type == 'paragraph' %}
                                <div class="chunk chunk-paragraph">
                                    {{ chunk.paragraph | safe }}
                                </div>
                            {% elif chunk.type == 'node' %}
                                <div class="chunk {% if chunk.direction == 'vertical' %}chunk-vertical{% else %}chunk-horizontal{% endif %}">
                                    {% for child in chunk.children %}
                                        {{ render_chunk(child) }}
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endmacro %}

                        {{ render_chunk(slide.chunk) }}
                    </div>
                    <div class="slide-number">
                        <p>{{ loop.index }}</p>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
        <div class="floating-btn">
            <button class="action-btn" onclick="togglePresentationMode()">
                &#128187; Toggle Slideshow
            </button>
            <button class="action-btn" onclick="window.print()">
                &#128424; Save as PDF
            </button>
        </div>
        <script>
        // Presentation mode
        let isPresentationMode = false;
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide-container');

        function togglePresentationMode() {
            isPresentationMode = !isPresentationMode;
            if (isPresentationMode) {
                enterPresentationMode();
            } else {
                exitPresentationMode();
            }
        }

        function enterPresentationMode() {
            document.body.classList.add('presentation-mode');
            showSlide(currentSlide);
            document.addEventListener('keydown', handleKeydown);
        }

        function exitPresentationMode() {
            document.body.classList.remove('presentation-mode');
            slides.forEach(slide => slide.classList.remove('active'));
            document.removeEventListener('keydown', handleKeydown);
        }

        function handleKeydown(event) {
            switch (event.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                case ' ':
                    showSlide(currentSlide + 1);
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    showSlide(currentSlide - 1);
                    break;
                case 'Escape':
                    togglePresentationMode();
                    break;
            }
        }

        function showSlide(index) {
            if (index < 0) {
                return;
            }
            if (currentSlide < slides.length) {
                slides[currentSlide].classList.remove('active');
            }
            if (index >= slides.length) {
                currentSlide = slides.length - 1;
            } else {
                currentSlide = index
                slides[currentSlide].classList.add('active');
            }
        }

        // 添加 Markdown 渲染函数
        function renderMarkdown(text) {
            // 简单的 Markdown 渲染实现
            let html = text;
            
            // 转换标题
            html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
            html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
            html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
            
            // 转换粗体和斜体
            html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            // 转换列表
            html = html.replace(/^\- (.*$)/gm, '<li>$1</li>');
            html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
            
            // 转换段落
            html = html.replace(/^\s*$(.*?)^\s*$/gm, '<p>$1</p>');
            
            // 处理换行
            html = html.replace(/\n/g, '<br>');
            
            return html;
        }

        // 初始化时渲染 Markdown 内容
        document.addEventListener('DOMContentLoaded', function() {
            const paragraphs = document.querySelectorAll('.chunk-paragraph');
            paragraphs.forEach(function(p) {
                if (p.innerHTML.trim().startsWith('<p>')) {
                    // 已经是 HTML，不需要转换
                    return;
                }
                // 简单处理 Markdown 内容
                p.innerHTML = renderMarkdown(p.innerHTML);
            });
        });
        </script>
    </body>
    </html>
    """
    
    # 将 CSS 和 HTML 模板写入临时文件
    with open(os.path.join(temp_dir, "styles.css"), "w") as f:
        f.write(css_content)
    
    # 创建模板环境
    env = Environment()
    env.filters["safe"] = lambda x: x  # 添加 safe 过滤器
    
    template = env.from_string(html_template)
    
    # 填充模板
    pages = composite(document)
    title = extract_title(document) or "Untitled"
    slide_struct = retrieve_structure(pages)
    _, options = PageOption(), None  # 简化处理
    width, height = 960, 540  # 固定尺寸

    data = {
        "title": title,
        "struct": slide_struct,
        "slide_width": width,
        "slide_height": height,
        "css_content": css_content,
        "slides": [
            {
                "h1": page.h1,
                "h2": page.h2,
                "h3": page.h3,
                "chunk": page.chunk.__dict__,  # 简化处理
                "layout": page.option.layout if hasattr(page.option, 'layout') else 'content',
                "styles": getattr(page.option, 'styles', {}),
            }
            for page in pages
        ],
    }

    return template.render(data)


def generate_presentation_content(topic: str, num_slides: int = 5) -> str:
    """根据主题生成演示文稿内容"""
    # 这里可以集成 AI 模型来生成内容
    # 目前使用示例内容
    if "人工智能" in topic or "AI" in topic:
        markdown_content = """# 人工智能发展趋势

## 什么是人工智能

- 人工智能是计算机科学的一个分支
- 旨在创建能够执行通常需要人类智能的任务的系统
- 包括机器学习、自然语言处理、计算机视觉等领域

---

## 人工智能的历史发展

### 早期发展 (1950s-1970s)
- 1950年：图灵测试提出
- 1956年：达特茅斯会议，AI概念正式确立

### 知识工程时代 (1980s)
- 专家系统的兴起
- 基于规则的AI系统

### 机器学习时代 (1990s-2000s)
- 统计学习方法的发展
- 支持向量机等算法的提出

---

## 当前AI技术热点

### 深度学习
- 神经网络的复兴
- 在图像识别、语音识别等领域取得突破

### 自然语言处理
- 大语言模型的出现
- 机器翻译、文本生成能力大幅提升

### 计算机视觉
- 图像识别准确率超越人类
- 自动驾驶技术快速发展

---

## 人工智能的应用领域

- **医疗健康**：辅助诊断、药物研发
- **金融服务**：风险评估、算法交易
- **智能制造**：工业机器人、质量控制
- **教育领域**：个性化学习、智能辅导
- **交通出行**：自动驾驶、智能交通系统

---

## 未来展望与挑战

### 发展趋势
- 更强大的通用人工智能
- AI与其他技术的深度融合
- 边缘计算与AI的结合

### 面临挑战
- 数据隐私与安全问题
- AI伦理与责任归属
- 就业结构变化与社会适应
- 技术可控性与可解释性
"""
    elif "机器学习" in topic:
        markdown_content = """# 机器学习基础入门

## 机器学习概述

- 机器学习是人工智能的核心领域之一
- 使计算机能够从数据中学习并做出预测或决策
- 无需明确编程每个具体任务

---

## 机器学习主要类型

### 监督学习
- 使用标记数据进行训练
- 常见算法：线性回归、决策树、支持向量机
- 应用：分类和回归问题

### 无监督学习
- 从未标记数据中发现模式
- 常见算法：K-means聚类、主成分分析
- 应用：数据聚类和降维

### 强化学习
- 通过与环境交互学习最优行为
- 基于奖励和惩罚机制
- 应用：游戏AI、机器人控制

---

## 机器学习工作流程

1. **问题定义**：明确业务目标和评估指标
2. **数据收集**：获取相关数据集
3. **数据预处理**：清洗、转换和标准化数据
4. **特征工程**：提取和选择重要特征
5. **模型选择**：选择合适的算法
6. **模型训练**：使用训练数据训练模型
7. **模型评估**：使用测试数据评估性能
8. **模型部署**：将模型应用到实际场景

---

## 常用算法介绍

### 线性回归
- 用于预测连续数值
- 假设特征与目标变量之间存在线性关系

### 决策树
- 易于理解和解释
- 可处理数值型和类别型数据

### 随机森林
- 由多个决策树组成的集成方法
- 减少过拟合风险，提高预测准确性

### 神经网络
- 模拟人脑神经元结构
- 能够学习复杂的非线性关系

---

## 实践建议

### 数据质量
- 确保数据的准确性和完整性
- 处理缺失值和异常值
- 数据量越大通常效果越好

### 模型选择
- 根据问题类型选择合适算法
- 考虑计算资源和时间成本
- 不要忽视简单模型的效果

### 持续优化
- 定期重新训练模型
- 监控模型性能变化
- 根据反馈调整模型参数
"""
    else:
        # 默认示例内容
        markdown_content = f"""# {topic}

## 简介

这是一个关于"{topic}"的演示文稿。
我们将从多个角度来探讨这个主题。

---

## 主要内容

### 方面一
- 关键点1
- 关键点2
- 关键点3

### 方面二
- 要点1
- 要点2
- 要点3

---

## 总结

- 核心观点1
- 核心观点2
- 核心观点3

## Q&A

感谢您的关注！
欢迎提问。
"""

    return markdown_content


def main():
    st.set_page_config(
        page_title="AI PPT Generator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("AI PPT Generator 📊")
    st.markdown("将自然语言转换为专业的演示文稿")
    
    # 用户输入
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "请输入演示文稿主题和内容要求:",
            height=150,
            placeholder="例如：请为我生成一个关于人工智能发展趋势的PPT，包含5页幻灯片..."
        )
    
    with col2:
        num_slides = st.number_input("幻灯片页数", min_value=3, max_value=20, value=5)
        # 主题选择
        theme_options = {k: v["name"] for k, v in THEMES.items()}
        selected_theme_key = st.selectbox(
            "选择主题", 
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=0
        )
        layout_style = st.selectbox("布局风格", ["默认", "居中"])
    
    # 生成按钮
    if st.button("生成演示文稿", type="primary"):
        if user_input:
            with st.spinner("正在生成演示文稿..."):
                # 生成内容
                markdown_content = generate_presentation_content(user_input, num_slides)
                
                # 渲染为HTML，使用选定的主题
                html_content = render_jinja2(markdown_content, selected_theme_key)
                
                # 显示结果
                st.success("演示文稿生成成功！")
                
                # 使用组件显示HTML
                import streamlit.components.v1 as components
                components.html(html_content, height=700, scrolling=True)
                
                # 提供下载选项
                st.download_button(
                    label="下载HTML文件",
                    data=html_content,
                    file_name="presentation.html",
                    mime="text/html"
                )
                
                # 提供PDF转换提示
                st.info("提示：在演示文稿页面中，您可以点击右下角的“Save as PDF”按钮将演示文稿保存为PDF文件。")
        else:
            st.warning("请输入演示文稿主题和内容要求")


if __name__ == "__main__":
    main()