import sys
import json
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm）都要在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from services.document_processing_engine.structure_extract import (
    extract_structured, calibrate,
)

text = """文竣昶
22岁 男 汉族 辽宁省鞍山市
13804223973
675817401@qq.com
教育背景
沈阳工业大学 软件工程 本科 2022-09 ~ 2026-06
GPA 3.2/4
"""

print("正在调用 LLM 结构化提取（qwen2.5:7b）...")
result = extract_structured(text)

print("=== 提取结果 ===")
print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))

fields, pending = calibrate(result, text)
print("=== pending 待确认 ===")
print(json.dumps(pending, ensure_ascii=False, indent=2))
