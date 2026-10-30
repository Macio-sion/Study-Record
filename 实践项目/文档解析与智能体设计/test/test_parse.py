import sys
import json
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm）都要在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.files_parse import validate_file, parse_file, layout_process, structure_extract, validate_result

PDF_PATH = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else Path(__file__).resolve().parent / "datas" / "文竣昶的简历.pdf"
)


def main():
    data = PDF_PATH.read_bytes()
    state = {"file_source": data, "file_name": PDF_PATH.name}

    # 节点一：文件校验
    r1 = validate_file(state)
    state.update(r1)
    print("=" * 70)
    print("[节点一] validate_file 返回:")
    print(json.dumps(r1, ensure_ascii=False, default=str))

    # 节点二：多格式解析
    r2 = parse_file(state)
    state.update(r2)
    print("=" * 70)
    print("[节点二] parse_file 返回:")
    r2_show = dict(r2)
    if "text" in r2_show and isinstance(r2_show["text"], str):
        r2_show["text"] = r2_show["text"][:300] + f"...(总长 {len(r2['text'])})"
    if "layout" in r2_show:
        pages = r2_show["layout"].get("pages", [])
        r2_show["layout"] = {
            "pages_count": len(pages),
            "pages": [
                {
                    "page": p.get("page"),
                    "width": p.get("width"),
                    "height": p.get("height"),
                    "blocks_count": len(p.get("blocks", [])),
                    "blocks_preview": p.get("blocks", [])[:3],
                }
                for p in pages
            ],
        }
    print(json.dumps(r2_show, ensure_ascii=False, default=str, indent=2))

    # 节点三：布局处理
    r3 = layout_process(state)
    state.update(r3)
    print("=" * 70)
    print("[节点三] layout_process 返回（概要）:")
    r3_show = {
        "layout_processed": r3.get("layout_processed"),
        "ordered_blocks_count": len(r3.get("ordered_blocks", [])),
        "reading_text": (r3.get("reading_text", "") or "")[:500]
        + f"...(总长 {len(r3.get('reading_text', '') or '')})",
    }
    print(json.dumps(r3_show, ensure_ascii=False, default=str, indent=2))

    print("=" * 70)
    print("[节点三] reading_text 全文（判断阅读顺序）:")
    print(r3.get("reading_text", ""))

    # 节点四：结构化提取
    r4 = structure_extract(state)
    state.update(r4)
    print("=" * 70)
    print("[节点四] structure_extract 返回:")
    print(json.dumps(r4, ensure_ascii=False, default=str, indent=2))

    # 节点五：结果校验
    r5 = validate_result(state)
    state.update(r5)
    print("=" * 70)
    print("[节点五] validate_result 返回:")
    print(json.dumps(r5, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
