import math
import torch
from torch import nn


class PositionEncoding(nn.Module):
    """
    正弦-余弦位置编码层。

    将序列中每个 token 的位置信息以正弦/余弦波的形式注入到词向量中，
    公式源自 "Attention Is All You Need" (Vaswani et al., 2017)。

    Parameters
    ----------
    d_model : int
        词向量 / 模型隐藏层维度。
    max_len : int
        支持的最大序列长度，默认 5000。

    Notes
    -----
    - pe 通过 register_buffer 注册，不参与梯度更新，但会随模型保存/加载。
    - pe 形状为 (1, max_len, d_model)，支持与 batch 输入直接广播相加。
    """

    def __init__(self, d_model: int, max_len: int = 5000) -> None:
        super().__init__()

        # pe: (max_len, d_model)
        pe = torch.zeros(max_len, d_model)

        # position: (max_len, 1)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)

        # div_term: (d_model // 2,)  — 1 / (10000^(2i/d_model))
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )

        # 偶数维度用 sin，奇数维度用 cos
        pe[:, 0::2] = torch.sin(position * div_term)   # (max_len, d_model//2)
        pe[:, 1::2] = torch.cos(position * div_term)   # (max_len, d_model//2)

        # 增加 batch 维度以支持广播: (1, max_len, d_model)
        pe = pe.unsqueeze(0)

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        将位置编码加到输入张量上。

        Args:
            x: (batch_size, seq_len, d_model) 输入张量（通常是词向量）。

        Returns:
            (batch_size, seq_len, d_model) 加上位置编码后的张量。
        """
        return x + self.pe[:, :x.size(1), :]


if __name__ == "__main__":
    x = torch.randn(2, 10, 512)
    pe = PositionEncoding(512)
    out = pe(x)
    print(out.shape)  # torch.Size([2, 10, 512])
