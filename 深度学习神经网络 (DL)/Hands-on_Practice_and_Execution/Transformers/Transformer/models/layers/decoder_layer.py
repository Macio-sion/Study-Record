import torch
from torch import nn

from component import MultiHeadAttention, FeedForward


class DecoderLayer(nn.Module):
    """
    Transformer 解码器层。

    包含三个子层：
        1. Masked 多头自注意力（含 subsequent mask + padding mask）
        2. 交叉注意力（Q 来自 Decoder，K/V 来自 Encoder）
        3. 前馈网络

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
        self.cross_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        encoder_output: torch.Tensor,
        src_mask: torch.Tensor = None,
        tgt_mask: torch.Tensor = None,
        tgt_subsequent_mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        解码器层前向传播。

        Args:
            x: (B, tgt_len, d_model) 目标端输入。
            encoder_output: (B, src_len, d_model) 编码器输出。
            src_mask: (B, src_len) padding mask，True=忽略。
            tgt_mask: (B, tgt_len) 目标端 padding mask，True=忽略。
            tgt_subsequent_mask: (tgt_len, tgt_len) subsequent mask，True=忽略。

        Returns:
            (B, tgt_len, d_model)
        """
        # 1. Masked 自注意力（含 subsequent + padding mask）
        attn_out = self.self_attn(x, x, x, mask=tgt_mask, subsequent_mask=tgt_subsequent_mask)
        x = self.norm1(x + self.dropout1(attn_out))

        # 2. 交叉注意力：Q=x(Decoder), K=V=encoder_output(Encoder)
        cross_out = self.cross_attn(x, encoder_output, encoder_output, mask=src_mask)
        x = self.norm2(x + self.dropout2(cross_out))

        # 3. 前馈网络
        ff_out = self.feed_forward(x)
        x = self.norm3(x + self.dropout3(ff_out))

        return x


if __name__ == "__main__":
    x = torch.randn(2, 10, 512)
    enc_out = torch.randn(2, 15, 512)
    dl = DecoderLayer(512, 8, 1024)
    result = dl(x, enc_out)
    print(result.shape)  # (2, 10, 512)
