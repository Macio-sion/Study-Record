import torch
from torch import nn

from component import MultiHeadAttention, FeedForward


class EncoderLayer(nn.Module):
    """
    Transformer 编码器层。

    包含两个子层：
        1. 多头自注意力
        2. 前馈网络

    每个子层均采用残差连接 + 层归一化（Post-LN）。

    Parameters
    ----------
    d_model : int
        词向量 / 模型隐藏层维度。
    num_heads : int
        多头注意力头数。
    d_ff : int
        前馈网络中间层维度。
    dropout : float
        Dropout 比率，默认 0.1。
    """

    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1) -> None:
        super().__init__()

        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """
        编码器层前向传播。

        Args:
            x: (B, seq_len, d_model) 输入张量。
            mask: (B, seq_len) padding mask，True=忽略。

        Returns:
            (B, seq_len, d_model)
        """
        # 1. 自注意力
        attn_out = self.self_attn(x, x, x, mask=mask)
        x = self.norm1(x + self.dropout1(attn_out))

        # 2. 前馈网络
        ff_out = self.feed_forward(x)
        x = self.norm2(x + self.dropout2(ff_out))

        return x


if __name__ == "__main__":
    x = torch.randn(2, 10, 512)
    layer = EncoderLayer(512, 8, 1024)
    result = layer(x)
    print(result.shape)  # (2, 10, 512)
