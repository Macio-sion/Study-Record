"""知识库构建命令行工具。

将 ``/knowledge/{type}/`` 下的 PDF 文档清洗、切分、向量化后写入 PGVector。

用法（在项目根目录执行）：
    python build_knowledge.py list                     # 列出知识库类型
    python build_knowledge.py build notes              # 构建指定类型
    python build_knowledge.py build notes --rebuild    # 重建（先删除旧数据）
    python build_knowledge.py build-all                # 构建全部类型
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 确保 src 目录在 sys.path 中
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from infrastructure.config.config_manager import ConfigManager  # noqa: E402
from knowledge.builder import KnowledgeBuilder  # noqa: E402


def _print_result(result: dict) -> None:
    if result.get("success"):
        print(f"[成功] {result['doc_type']}：入库 {result['chunk_count']} 个块 "
              f"(collection={result.get('collection', '')})")
    else:
        print(f"[失败] {result.get('doc_type', '')}：{result.get('message', '')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="构建本地知识库向量数据库")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出知识库类型")

    build_parser = sub.add_parser("build", help="构建指定类型")
    build_parser.add_argument("doc_type", help="文档类型（/knowledge/ 下的子目录名）")
    build_parser.add_argument("--rebuild", action="store_true", help="重建（先删除旧数据）")

    sub.add_parser("build-all", help="构建全部类型")

    args = parser.parse_args()
    builder = KnowledgeBuilder(ConfigManager().load())

    if args.command == "list":
        types = builder.list_types()
        print("知识库类型：", types if types else "（无，请在 /knowledge/ 下创建子目录并放入 PDF）")
    elif args.command == "build":
        _print_result(builder.build(args.doc_type, rebuild=args.rebuild))
    elif args.command == "build-all":
        types = builder.list_types()
        if not types:
            print("无可用类型，请在 /knowledge/ 下创建子目录并放入 PDF。")
            return 0
        for doc_type in types:
            print(f"构建 [{doc_type}] ...")
            _print_result(builder.build(doc_type))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
