"""数据导出工具 — CSV格式"""
import csv
import io
from typing import Optional


def export_csv(data: list[dict], filename: str, columns: Optional[list[str]] = None) -> bytes:
    """将列表数据导出为CSV字节流"""
    output = io.StringIO()
    if not data:
        output.write("no data\n")
        return output.getvalue().encode("utf-8-sig")
    
    if columns is None:
        columns = list(data[0].keys())
    
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    
    return output.getvalue().encode("utf-8-sig")
