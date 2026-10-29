import torch
from torch import nn


def rotate_half(x: torch.Tensor):
    """
    对相邻维度对 (x0, x1) 执行 90° 旋转 → (-x1, x0)
    """
    x1, x2 = x[..., :: 2], x[..., 1 :: 2]
    return torch.cat([-x2, x1], dim=-1)


def precompute_freqs(head_dim: int, max_seq_len: int, theta: float = 10000.0):
    """
    预计算所有位置的 RoPE cos/sin 表

    Args:
        head_dim: 每个注意力头的维度
        max_seq_len: 最大序列长度
        theta: 频率基数，默认 10000

    Returns:
        cos_v: (max_seq_len, head_dim // 2) 余弦表
        sin_v: (max_seq_len, head_dim // 2) 正弦表
    """
    # 维度对索引: 0, 2, 4, ..., head_dim-2  → 共 head_dim/2 个
    i = torch.arange(0, head_dim, 2, dtype=torch.float32)
    # 频率基: theta_i = theta^(-2i/d) = 1 / (theta^(2i/d))
    freq = 1.0 / (theta ** (i / head_dim))
    # 位置索引: 0, 1, 2, ..., max_seq_len-1
    pos = torch.arange(max_seq_len, dtype=torch.float32)
    # 旋转角: (seq_len, head_dim/2) 每个位置 × 每个维度对的频率
    angles = torch.outer(pos, freq)
    return torch.cos(angles), torch.sin(angles)


def apply_rotary_pos_emb(x: torch.Tensor, cos_v: torch.Tensor, sin_v: torch.Tensor):
    """
    对输入施加旋转位置编码

    Args:
        x: 输入张量 (..., seq_len, head_dim)
        cos_v: 余弦表 (seq_len, head_dim // 2)
        sin_v: 正弦表 (seq_len, head_dim // 2)

    Returns:
        施加 RoPE 后的张量，shape 与 x 相同
    """
    # 每个 cos/sin 值对应一对维度，重复一次以匹配 head_dim
    cos_v = cos_v.repeat_interleave(2, dim=-1)  # (seq_len, head_dim)
    sin_v = sin_v.repeat_interleave(2, dim=-1)
    return x * cos_v + rotate_half(x) * sin_v


if __name__ == '__main__':
    head_dim = 8
    max_seq_len = 4

    # 预计算 cos/sin 表
    cos_v, sin_v = precompute_freqs(head_dim, max_seq_len)
    print("cos_v shape:", cos_v.shape)  # (4, 4)
    print("sin_v shape:", sin_v.shape)

    # 模拟输入: (batch=1, seq_len=4, head_dim=8)
    x = torch.randn(1, max_seq_len, head_dim)
    print("\n原始 x[:2]:", x[0, :2])

    result = apply_rotary_pos_emb(x, cos_v, sin_v)
    print("RoPE 后 x[:2]:", result[0, :2])
    print("shape 不变:", x.shape == result.shape)
