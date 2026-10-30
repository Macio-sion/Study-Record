import sys
import json
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm/agent）都要在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.graph import parse_engine

pdf = Path(__file__).resolve().parent / "datas" / "文竣昶的简历.pdf"
data = pdf.read_bytes()

print("正在运行解析引擎子图（五节点串行链）...")
result = parse_engine.invoke({"file_source": data, "file_name": pdf.name})

print("=" * 70)
print("=== 关键结果 ===")
print("file_valid:", result.get("file_valid"))
print("file_type:", result.get("file_type"))
print("page_count:", result.get("page_count"))
print("layout_processed:", result.get("layout_processed"))
print("reading_text 前 80 字:", result.get("reading_text", "")[:80])

fields = result.get("fields", {})
print("name:", fields.get("personal", {}).get("name", {}).get("value"))
print("phone:", fields.get("personal", {}).get("phone", {}).get("value"))
print("school:", fields.get("education", [{}])[0].get("school", {}).get("value"))

print("=" * 70)
print("pending:", json.dumps(result.get("pending", []), ensure_ascii=False))
print("validation_report:", json.dumps(result.get("validation_report", {}), ensure_ascii=False))

# 错误流程：空字节流触发文件校验失败，验证「失败即中断」
print()
print("=" * 70)
print("=== 错误流程：空 file_source ===")
err_result = parse_engine.invoke({"file_source": b""})
print("error_data:", json.dumps(err_result.get("error_data", {}), ensure_ascii=False))
print("file_valid:", err_result.get("file_valid"))
print("fields 是否存在（应为 False，表示已中断）:", "fields" in err_result)
