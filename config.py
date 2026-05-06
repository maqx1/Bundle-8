from dotenv import load_dotenv
load_dotenv()

import os


DEBUG_MODE=True

# ========== 视觉识别 API：qwen3.5-vl ============
VISION_API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
VISION_API_KEY = os.getenv("VISION_API_KEY","")
VISION_MODEL_NAME = "qwen-instruct"
VISION_TEMPERATURE = 0.2
VISION_ENABLE_THINKING = False
VISION_NUM_OF_CANDIDATES = 3 # 注意如果比较多，可能需要调整TEXT_COMBINE_TIMEOUT
VISION_PROMPT = r"""请详细描述这张图片的内容，包括所有文字、图表和版面结构。
如果包含数学公式, 请用LaTeX格式输出, 输出数学公式时，使用 $$ 独占一行的写法，不要写在同一行。例如：

$$
D \in \mathbb{R}
$$

而不是：$$D \in \mathbb{R}$$

注意这是同学的试卷，如果有错误不必强行纠正"""
VISION_TIMEOUT_SINGLE = 500 #秒
VISION_MAX_RETRIES = 2
VISION_INPUT_IMAGE_QUALITY = 85
DPI = 300



# ========== 文本整合 API：deepseek-v3 ============
TEXT_API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
TEXT_API_KEY = os.getenv("TEXT_API_KEY","")
TEXT_MODEL_NAME = "deepseek-v3:671b"
TEXT_TEMPERATURE = 0.1
TEXT_MAX_RETRIES = 2
TEXT_COMBINE_TIMEOUT = 500 #秒
# 引用时f-string 将 {{}}转义为单括号，谨慎改动。
ANALYSIS_PROMPT = """你是一个文本分析专家。用户提供了{NUM}次识别的文本（来自同一个源，可能有歧义）。

任务：
1. 分析这{NUM}段文本，找出所有存在歧义/不一致的地方
2. 对于没有歧义的部分，整合成一个连贯的文本
3. 在整合文本中，遇到有歧义的地方，使用占位符 {{AMB-XXX}} 标记，其中 XXX 是自增的数字
4. 为每个歧义点记录详细信息
5. 请以 JSON 格式返回，结构如下：
{{
  "resolved_text": "整合后的文本，歧义处用{{AMB-0}}, {{AMB-1}}等标记",
  "ambiguities": [
    {{
      "id": "AMB-0",
      "description": "歧义描述",
      "variants": [
        {{"source": "r1", "snippet": "第一次识别的内容片段"}},
        {{"source": "r2", "snippet": "第二次识别的内容片段"}},
        {{"source": "r3", "snippet": "第三次识别的内容片段"}}
      ],
      "suggested_resolution": "建议采用的最终值"
    }}
  ]
}}

注意：
- 只返回 JSON, 不要有其他解释文字——不要套在 markdown里的json, 只要json
- 如果没有任何歧义, ambiguities 为空数组
- 整合文本要自然流畅，合并所有一致的信息
- 如果包含数学公式, 请用LaTeX格式输出, 输出数学公式时，使用 $$ 独占一行的写法，不要写在同一行。例如：

$$
D \in \mathbb{{R}}
$$

而不是：$$D \in \mathbb{{R}}$$

以下是{NUM}次识别的文本：{TEXT_BLOCKS}
"""
