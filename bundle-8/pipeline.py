"""
流程编排: PDF 处理
"""

import json
import os
import time
from pathlib import Path

from pdf2image import convert_from_path
import pypdf

from config import DPI
from core import pil_to_base64, call_vision_api, call_llm_analysis, resolve_placeholders, print_token_stats


# ========== 5. 单页识别 ==========

def recognize_one_page(pdf_file, page_num):
    """
    识别 PDF 的一页，返回(整合后的文本, 本页token消耗)
    """
    # PDF 转图片（使用配置的 DPI）
    images = convert_from_path(
        pdf_file,
        first_page=page_num + 1,
        last_page=page_num + 1,
        dpi=DPI
    )
    img = images[0]

    # 图片转 base64
    img_b64_uri = pil_to_base64(img)

    # 多次 Vision 识别
    raw_results, vision_usage = call_vision_api(img_b64_uri)

    print(f"DEBUG vision: type={type(vision_usage)}, value={vision_usage}")

    # LLM 整合
    analyzed, text_usage = call_llm_analysis(raw_results)
    print(f"DEBUG text: type={type(text_usage)}, value={text_usage}")
    # 替换歧义占位符
    result = resolve_placeholders(analyzed)
    
    print(vision_usage)

    print(text_usage)

    # 统计本页 token
    page_tokens = {
        "vision": vision_usage.get("total_tokens", 0),
        "text": text_usage.get("total_tokens", 0)
    }
    print("page_token_passed")
    return result, page_tokens


# ========== 6. 批量处理（带断点续传）==========

def pdf_to_markdown(pdf_file, md_file=None):
    """
    带断点续传的 PDF 转 Markdown
    """
    pdf_path = Path(pdf_file)

    if not pdf_path.exists():
        print(f"❌ 文件不存在：{pdf_path}")
        return False

    md_path = Path(md_file) if md_file else pdf_path.with_suffix('.md')
    progress_file = pdf_path.with_suffix('.progress.json')

    # 获取总页数
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"📄 总页数: {total_pages}")

    # 加载进度和 token 统计
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        completed_pages = set(progress.get("completed_pages", []))
        token_stats = progress.get("token_stats",{
            "vision": 0,
            "text": 0,
            "total": 0
        })
        
        print(f"✅ 已完成: {len(completed_pages)} 页")
        print(f"📊 文档历史消耗: Vision {token_stats['vision_total']:,} + Text {token_stats['text_total']:,} = {token_stats['total']:,}")
        print(f"📍 继续识别未完成的 {total_pages - len(completed_pages)} 页")
    else:
        completed_pages = set()
        progress = {"completed_pages": [], "results": {}}
        token_stats = {"vision_total": 0, "text_total": 0, "total": 0}
    # 循环处理
    for page_num in range(total_pages):
        if page_num in completed_pages:
            print(f"⏭️  跳过第 {page_num + 1} 页（已完成）")
            continue
        while True:  # 当前页重试循环
            try:
                print(f"\n📖 正在识别第 {page_num + 1}/{total_pages} 页")
                start_time = time.time()

                result, page_tokens = recognize_one_page(str(pdf_path), page_num)

                # 保存进度
                progress["completed_pages"].append(page_num)
                progress["results"][str(page_num)] = result

                # 累加 token
                token_stats["vision_total"] += page_tokens["vision"]
                token_stats["text_total"] += page_tokens["text"]
                token_stats["total"] = token_stats["vision_total"] + token_stats["text_total"]
                progress["token_stats"] = token_stats
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, ensure_ascii=False, indent=2)

                # 写入输出文件
                with open(md_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n## 第 {page_num + 1} 页\n\n")
                    f.write(result)
                    f.write("\n\n---\n")
                    f.flush()

                elapsed = time.time() - start_time
                print(f"✅ 第 {page_num + 1} 页完成 (输出文本长度: {len(result)}, 耗时: {elapsed:.1f})")
                print(f'📊 本次累计: Vision {token_stats["vision_total"]:,} + Text {token_stats["text_total"]:,} = {token_stats["total"]:,}')
                break  # 成功，进入下一页

            except Exception as e:
                print(f"❌ 第 {page_num + 1} 页失败: {e}")
                print(f"⏳ 5秒后重试...")
                time.sleep(5)

    print(f"\n🎉 全部 {total_pages} 页识别完成！")
    print_token_stats()
    return True
