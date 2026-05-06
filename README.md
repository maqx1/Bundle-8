
# Bundle-8: PDF 转 Markdown 工具

基于视觉 AI 识别 + LLM 整合的 PDF 处理工具

```
Bundle-8 (PDF 转 Markdown 工具)
├── config.py      → 所有配置
├── core.py        → 核心函数（API 调用）
├── pipeline.py    → 流程编排
├── main.py        → 入口
└── .env           → API Key
```

---
## 1. 功能特点

- 📄 **PDF 解析**：将 PDF 页面转换为图片
- 👁️ **视觉识别**：使用 Qwen3.5-VL 模型识别图片内容
- 🔄 **多次识别**：同一页面识别 3 次，减少识别错误
- 🤖 **智能整合**：使用 DeepSeek-V3 模型整合多次识别结果
- ⚠️ **歧义标记**：自动检测并标记识别歧义点
- 📊 **Token 统计**：记录 API 调用消耗
- 💾 **断点续传**：支持中断后继续处理
- 🔢 **LaTeX 支持**：数学公式自动转换为 LaTeX 格式

---
## 2. 工作流程
PDF 文件
│
▼
PDF → 图片（300 DPI）
│
▼
多次 Vision API 识别（qwen-instruct 模型）
│
▼
LLM 整合（deepseek-v3:671b 模型）
│
▼
歧义检测与标记（AMB-XXX 占位符）
│
▼
Markdown 文件

---

## 3. 安装

### 3.1. 安装 Python 依赖

```bash
pip install requests pdf2image pypdf python-dotenv
```

### 3.2. 安装 Poppler（Linux）

```bash
sudo apt install poppler-utils
```

### 3.3. 配置 API Key

```bash
VISION_API_KEY=你的视觉识别API密钥
TEXT_API_KEY=你的文本整合API密钥
```

---

## 4. 使用方法

### 4.1. 基本使用
```bash
python main.py input.pdf
```
### 4.2. 指定输出文件
```bash
python main.py input.pdf
```
---
## 5. 配置说明

### Vision API（视觉识别）

|配置项|默认值|说明|
|-|-|-|
|VISION_MODEL_NAME|qwen-instruct|视觉识别模型|
|VISION_NUM_OF_CANDIDATES|	3|	同一页面识别次数|
|VISION_TEMPERATURE	|0.2|	生成温度|
|DPI	|300|	PDF 渲染分辨率|
|VISION_INPUT_IMAGE_QUALITY	|85|	输出图片质量|
|VISION_MAX_RETRIES	|2|	最大重试次数|
|VISION_TIMEOUT_SINGLE	|500|	单次请求超时（秒）|

### Text API（文本整合）
|配置项|	默认值|	说明|
|-|-|-|
|TEXT_MODEL_NAME	|deepseek-v3:671b	|文本整合模型|
|TEXT_TEMPERATURE	|0.1	|生成温度|
|TEXT_MAX_RETRIES	|2	|最大重试次数|
|TEXT_COMBINE_TIMEOUT	|500	|请求超时（秒）|

### Vision Prompt（视觉识别提示词）
```python
VISION_PROMPT = r"""请详细描述这张图片的内容，包括所有文字、图表和版面结构。
如果包含数学公式, 请用LaTeX格式输出, 输出数学公式时，使用 $$ 独占一行的写法，不要写在同一行。

注意这是同学的试卷，如果有错误不必强行纠正"""
```

## 6. 输出格式
### 6.1. 歧义标记
识别结果中的歧义点会被标记为：
```markdown
{{AMB-0}}[建议采用的最终值]{{AMB-0}}
```

示例：
```markdown
|x| < √2/2 时，y'' > 0 {{AMB-1}}[上凸（根据学生原文，但可能定义与常规相反）]{{AMB-1}}
```

### 6.2. Token 统计
程序运行时显示：
```text
📖 正在识别第 1/10 页
💰 Vision: 输入 8681, 输出 7679, 总计 16360
💰 Text:   输入 2914, 输出 1410, 总计 4324
✅ 第 1 页完成 (长度: 890, 耗时: 5.2s)
📊 本次累计: Vision 16,360 + Text 4,324 = 20,684
```

### 6.3. 断点续传
```text
📄 总页数: 10
✅ 已完成: 3 页
📊 历史消耗: Vision 49,080 + Text 12,972 = 62,052
📍 继续识别未完成的 7 页
```

## 7. 文件结构
```
Bundle-8/
├── bundle-8/
│   ├── main.py      # 命令行入口
│   ├── config.py        # 所有配置项
│   ├── core.py          # 核心函数（API 调用）
│   └── pipeline.py      # 流程编排
├── .env                 # API 密钥（不提交到 Git）
├── .gitignore           # Git 忽略文件
└── README.md            # 本文档
```

## 8. .gitignore 模板
```Gitignore
__pycache__/
*.pyc
*.pyo
*.progress.json
.env
*.md
```

## 9. License
 
 ```
 GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation.
 ```
