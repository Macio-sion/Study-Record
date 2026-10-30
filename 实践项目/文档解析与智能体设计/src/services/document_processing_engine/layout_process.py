def is_body(block: dict, page_height: float) -> bool:
    """剥离页眉页脚：顶部/底部固定区域（约 8%）"""
    if not page_height:
        return True
    bbox = block.get("bbox")
    if not bbox:
        return True
    _, y0, _, y1 = bbox
    return y0 > page_height * 0.08 and y1 < page_height * 0.92


def concat_text(blocks: list) -> str:
    """按阅读顺序拼接文本块为纯文本"""
    parts = [b["text"] for b in blocks if b.get("type") == "text" and b.get("text")]
    return "\n".join(parts)


def _center_x(block: dict) -> float:
    """文本块水平中心 x 坐标"""
    bbox = block.get("bbox")
    if not bbox:
        return 0.0
    return (bbox[0] + bbox[2]) / 2


def _is_spanning(block: dict, page_width: float) -> bool:
    """判断文本块是否横跨整页（跨栏标题）"""
    if block.get("type") != "text":
        return False
    bbox = block.get("bbox")
    if not bbox or not page_width:
        return False
    x0, _, x1, _ = bbox
    # 宽度占页面 > 60%，且跨越中线
    return (x1 - x0) > page_width * 0.6 and x0 < page_width * 0.5 < x1


def split_columns(blocks: list, page_width: float) -> list:
    """检测页面栏数，返回 [(x_min, x_max), ...] 每栏 x 范围"""
    texts = [b for b in blocks if b.get("type") == "text"]
    if not texts or not page_width:
        return [(0.0, page_width or 9999.0)]

    mid = page_width / 2
    left = [b for b in texts if _center_x(b) < mid]
    right = [b for b in texts if _center_x(b) >= mid]

    # 启发式：右半边文本块占比 > 15% 判为双栏
    if right and len(right) / len(texts) > 0.15:
        return [(0.0, mid), (mid, page_width)]
    return [(0.0, page_width)]


def _cluster_rows(blocks: list, y_tolerance: float = 5.0) -> list:
    """把 y 中心相近的块聚类成行（处理表格单元格），返回 [ [块, ...], ... ]"""
    ordered = sorted(blocks, key=lambda b: b["bbox"][1] if b.get("bbox") else 0)
    rows = []
    for b in ordered:
        bbox = b.get("bbox")
        if not bbox:
            rows.append([b])
            continue
        y_center = (bbox[1] + bbox[3]) / 2
        placed = False
        for row in rows:
            first_bbox = row[0].get("bbox")
            if not first_bbox:
                continue
            row_y = (first_bbox[1] + first_bbox[3]) / 2
            if abs(y_center - row_y) < y_tolerance:
                row.append(b)
                placed = True
                break
        if not placed:
            rows.append([b])
    return rows


def order_column_blocks(blocks: list) -> list:
    """栏内按阅读顺序排序：y 聚类成行（表格），行内按 x 从左到右"""
    rows = _cluster_rows(blocks)
    ordered = []
    for row in rows:
        row.sort(key=lambda b: b["bbox"][0] if b.get("bbox") else 0)
        ordered.extend(row)
    return ordered


def order_page_blocks(blocks: list, page_width: float) -> list:
    """单页内容块按阅读顺序重排：单栏直接排序，双栏先提跨栏标题再分栏"""
    # 线条块不参与阅读顺序（保留在 layout，供后续表格识别用）
    content = [b for b in blocks if b.get("type") != "line"]

    columns = split_columns(content, page_width)

    if len(columns) <= 1:
        # 单栏：直接按阅读顺序排序（含表格行聚类），无跨栏概念
        return order_column_blocks(content)

    # 双栏：先分离跨栏标题（横跨整页的文本块），再分栏排序
    spanning = [b for b in content if _is_spanning(b, page_width)]
    normal = [b for b in content if not _is_spanning(b, page_width)]
    spanning.sort(key=lambda b: b["bbox"][1] if b.get("bbox") else 0)

    ordered = []
    for col_x0, col_x1 in columns:
        col_blocks = [b for b in normal if col_x0 <= _center_x(b) < col_x1]
        ordered.extend(order_column_blocks(col_blocks))

    return spanning + ordered
