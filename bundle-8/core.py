"""
核心函数: API 调用、文本处理
"""

import base64
import io
import json
import re
import time
import requests
from config import (
    VISION_API_URL, VISION_API_KEY, VISION_MODEL_NAME,
    VISION_TEMPERATURE, VISION_NUM_OF_CANDIDATES, VISION_PROMPT,
    VISION_TIMEOUT_SINGLE, VISION_MAX_RETRIES,
    VISION_INPUT_IMAGE_QUALITY, VISION_ENABLE_THINKING,
    TEXT_API_URL, TEXT_API_KEY, TEXT_MODEL_NAME,
    TEXT_TEMPERATURE, TEXT_MAX_RETRIES, TEXT_COMBINE_TIMEOUT,
    ANALYSIS_PROMPT, DEBUG_MODE
)

# ========== 1. 图片处理 ==========
def pil_to_base64(img, rec_format="PNG"):
    """将 PIL 图像转为 base64 data URI"""
    with io.BytesIO() as output:
        img.save(output, format=rec_format, quality=VISION_INPUT_IMAGE_QUALITY, optimize=True)
        img_bytes = output.getvalue()
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/{rec_format.lower()};base64,{b64_str}"

# ========== 2. Vision API 调用（带重试）==========
def call_vision_api(image_base64_uri):
    """调用 Vision API 识别图片，返回多次(识别结果的列表,usage字典)"""
    headers = {
        "Authorization": f"Bearer {VISION_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": VISION_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_base64_uri}}
                ]
            }
        ],
        "n": VISION_NUM_OF_CANDIDATES,
        "temperature": VISION_TEMPERATURE,
        #"extra_body": {
        #    "chat_template_kwargs": {"enable_thinking": "False"}
        #}
    }

    last_error = None

    for attempt in range(VISION_MAX_RETRIES):
        try:
            response = requests.post(
                VISION_API_URL,
                headers=headers,
                json=payload,
                timeout=VISION_TIMEOUT_SINGLE
            )
            response.raise_for_status()
            result = response.json()
            
            usage = result.get("usage", {})
            add_token_usage(usage, api_type="vision")
            print(f"   💰 Vision: 输入 {usage.get('prompt_tokens', 0)}, 输出 {usage.get('completion_tokens', 0)}, 总计 {usage.get('total_tokens', 0)}")
  
            if DEBUG_MODE==True:
                print(f"RAW_INFO: {result}")
            contents = [item["message"]["content"] for item in result["choices"]]
            return contents, usage 
        except Exception as e:
            last_error = str(e)
        if attempt < VISION_MAX_RETRIES - 1:
            wait_time = 2 ** attempt
            print(f"⚠️  Vision API {last_error}，{wait_time}秒后重试 ({attempt + 1}/{VISION_MAX_RETRIES})...")
            time.sleep(wait_time)
    raise RuntimeError(f"Vision API 调用失败，已重试 {VISION_MAX_RETRIES} 次：{last_error}")


# ========== 3. LLM 分析整合 ==========

def call_llm_analysis(texts):
    """
    调用 LLM 分析多次识别结果，(返回整合后的 JSON, usage字典)
    """
    text_blocks = "\n\n".join([
        f"【r{i+1}】\n{text}\n" for i, text in enumerate(texts)
    ])

    prompt_filled = ANALYSIS_PROMPT.format(
        TEXT_BLOCKS=text_blocks, 
        NUM=VISION_NUM_OF_CANDIDATES
    )

    headers = {
        "Authorization": f"Bearer {TEXT_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": TEXT_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个专业的文本分析助手，只返回 JSON 格式的结果。"},
            {"role": "user", "content": prompt_filled}
        ],
        "temperature": TEXT_TEMPERATURE,
    }

    last_error = None

    for attempt in range(TEXT_MAX_RETRIES):
        try:
            response = requests.post(
                TEXT_API_URL,
                headers=headers,
                json=payload,
                timeout=TEXT_COMBINE_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

            usage = result.get("usage", {})
            add_token_usage(usage, api_type="text")
            print(f"   💰 Text: 输入 {usage.get('prompt_tokens', 0)}, 输出 {usage.get('completion_tokens', 0)}, 总计 {usage.get('total_tokens', 0)}")
                
            ai_output = result["choices"][0]["message"]["content"]

            # 清理 markdown 代码块
            ai_output = re.sub(r'^```json\s*', '', ai_output)
            ai_output = re.sub(r'\s*```$', '', ai_output)
            print(ai_output)
            return json.loads(ai_output), usage

        except json.JSONDecodeError as e:
            print(f"JSON 解析失败 (尝试 {attempt + 1}/{TEXT_MAX_RETRIES}): {e}")
            if attempt < TEXT_MAX_RETRIES - 1:
                time.sleep(2)

    raise ValueError(f"整合文本时, LLM 输出的JSON不稳定, {TEXT_MAX_RETRIES}次重试无法解析")


# ========== 4. 文本处理 ==========

def resolve_placeholders(output):
    """
    将整合文本中的占位符 {{AMB-0}} 等替换为建议值
    """
    text = output["resolved_text"]
    ambiguities = {amb["id"]: amb for amb in output["ambiguities"]}

    def replace_match(match):
        amb_id = match.group(1)
        if amb_id in ambiguities:
            amb = ambiguities[amb_id]
            suggestion = amb.get("suggested_resolution", "")
            return f"{{{amb_id}}}[{suggestion}]{{{amb_id}}}"
        else: 
            return f"{{{amb_id}}}"
    resolved_text = re.sub(r'{([\w-]+)}', replace_match, text)

    return resolved_text



# ========== Token 统计 ==========
TOKEN_STATS = {
    "vision_prompt_tokens": 0,
    "vision_completion_tokens": 0,
    "text_prompt_tokens": 0,
    "text_completion_tokens": 0,
}

def add_token_usage(usage, api_type="vision"):
    """累加 token 消耗"""
    key_prompt = f"{api_type}_prompt_tokens"
    key_completion = f"{api_type}_completion_tokens"
    TOKEN_STATS[key_prompt] += usage.get("prompt_tokens", 0)
    TOKEN_STATS[key_completion] += usage.get("completion_tokens", 0)

def print_token_stats():
    """打印 token 统计"""
    prompt = TOKEN_STATS["vision_prompt_tokens"] + TOKEN_STATS["text_prompt_tokens"]
    completion = TOKEN_STATS["vision_completion_tokens"] + TOKEN_STATS["text_completion_tokens"]
    total = prompt + completion
    print(f"\n📊 本次Token 消耗统计")
    print(f"   输入 tokens:  {prompt:,}")
    print(f"   输出 tokens:  {completion:,}")
    print(f"   总计 tokens:  {total:,}")
