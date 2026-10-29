import torch
from torch import nn

from layers import DecoderLayer


class Decoder(nn.Module):
    """
    Transformer 解码器。

    由 num_layers 个 DecoderLayer 堆叠而成。

    Parameters
    ----------
    d_model : int
        词向量 / 模型隐藏层维度。
    num_heads : int
        多头注意力头数。
    d_ff : int
        前馈网络中间层维度。
    num_layers : int
        解码器层数。
    dropout : float
        Dropout 比率，默认 0.1。
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int,
        num_layers: int,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        self.layers = nn.ModuleList([
            DecoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

    def forward(
        self,
        y: torch.Tensor,
        encoder_outputs: torch.Tensor,
        src_mask: torch.Tensor = None,
        tgt_mask: torch.Tensor = None,
        tgt_subsequent_mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        解码器前向传播。

        Args:
            y: (B, tgt_len, d_model) 目标端输入。
            encoder_outputs: (B, src_len, d_model) 编码器输出。
            src_mask: (B, src_len) 源端 padding mask，True=忽略。
            tgt_mask: (B, tgt_len) 目标端 padding mask，True=忽略。
            tgt_subsequent_mask: (tgt_len, tgt_len) subsequent mask。

        Returns:
            (B, tgt_len, d_model)
        """
        for layer in self.layers:
            y = layer(y, encoder_outputs, src_mask, tgt_mask, tgt_subsequent_mask)
        return y


if __name__ == "__main__":
    x = torch.randn(2, 10, 512)
    y = torch.randn(2, 15, 512)
    decoder = Decoder(512, 8, 2048, 2)
    result = decoder(y, x)
    print(result.shape)  # (2, 15, 512)
