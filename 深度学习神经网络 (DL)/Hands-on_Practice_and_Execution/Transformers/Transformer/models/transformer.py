import torch
from torch import nn

from component.position_encoding import PositionEncoding
import encoder
import decoder


class Transformer(nn.Module):
    """
    Transformer 完整模型 (Encoder-Decoder)。

    完整流程:
        token_ids → Embedding → PositionalEncoding → Encoder → Decoder → Linear

    Parameters
    ----------
    vocab_size : int
        词表大小。
    pad_idx : int
        词表中 <pad> 的索引，用于生成 padding_mask。
    d_model : int
        词向量 / 模型隐藏层维度，默认 512。
    num_heads : int
        多头注意力头数，默认 8。
    d_ff : int
        前馈网络中间层维度，默认 2048。
    num_layers : int
        Encoder 和 Decoder 的层数，默认 6。
    max_seq_len : int
        位置编码支持的最大序列长度，默认 5000。
    dropout : float
        Dropout 比率，默认 0.1。

    Notes
    -----
    - mask 语义：BoolTensor，True = 需要忽略的位置。
    - padding_mask 由 token_ids 与 pad_idx 比较自动生成。
    - subsequent_mask 为上三角矩阵，防止解码器看到未来 token。
    """

    def __init__(
        self,
        vocab_size: int,
        pad_idx: int,
        d_model: int = 512,
        num_heads: int = 8,
        d_ff: int = 2048,
        num_layers: int = 6,
        max_seq_len: int = 5000,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.pad_idx = pad_idx
        self.d_model = d_model

        # 词嵌入 + 位置编码（Encoder / Decoder 共享）
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=pad_idx)
        self.position_encoding = PositionEncoding(d_model, max_seq_len)
        self.dropout_emb = nn.Dropout(dropout)

        # Encoder & Decoder
        self.encoder = encoder.Encoder(d_model, num_heads, d_ff, num_layers, dropout)
        self.decoder = decoder.Decoder(d_model, num_heads, d_ff, num_layers, dropout)

        # 输出投影（可选，将 d_model 映射回 vocab_size 用于 loss 计算）
        self.output_proj = nn.Linear(d_model, vocab_size)

    # ========================================================================
    # Mask 生成
    # ========================================================================

    def generate_padding_mask(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        根据 token_ids 生成 padding mask。

        Args:
            token_ids: (batch_size, seq_len) LongTensor。

        Returns:
            (batch_size, seq_len) BoolTensor。True = 该位置是 <pad>，需忽略。
        """
        return token_ids == self.pad_idx

    @staticmethod
    def generate_subsequent_mask(seq_len: int, device: torch.device) -> torch.Tensor:
        """
        生成 subsequent mask（上三角 mask），用于解码器自注意力。

        Args:
            seq_len: 序列长度。
            device: 张量所在设备。

        Returns:
            (seq_len, seq_len) BoolTensor。True = 不可见（未来 token），需忽略。
        """
        return torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()

    # ========================================================================
    # 前向传播
    # ========================================================================

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
    ) -> torch.Tensor:
        """
        Transformer 前向传播。

        Args:
            src: (batch_size, src_len) 源端 token 索引。
            tgt: (batch_size, tgt_len) 目标端 token 索引。

        Returns:
            (batch_size, tgt_len, vocab_size) logits（经 output_proj 投影）。
        """
        # 生成各种 mask（True = 忽略）
        src_pad_mask = self.generate_padding_mask(src)                      # (B, src_len)
        tgt_pad_mask = self.generate_padding_mask(tgt)                      # (B, tgt_len)
        tgt_sub_mask = self.generate_subsequent_mask(tgt.size(1), tgt.device)  # (tgt_len, tgt_len)

        # Embedding + PositionalEncoding
        src_emb = self.dropout_emb(self.position_encoding(self.embedding(src)))  # (B, src_len, d_model)
        tgt_emb = self.dropout_emb(self.position_encoding(self.embedding(tgt)))  # (B, tgt_len, d_model)

        # Encoder
        enc_out = self.encoder(src_emb, mask=src_pad_mask)

        # Decoder
        dec_out = self.decoder(
            tgt_emb,
            enc_out,
            src_mask=src_pad_mask,
            tgt_mask=tgt_pad_mask,
            tgt_subsequent_mask=tgt_sub_mask,
        )

        # 输出投影 → logits
        return self.output_proj(dec_out)


if __name__ == "__main__":
    src_ids = torch.randint(1, 200, (2, 10))   # 避免 0 = pad_idx
    tgt_ids = torch.randint(1, 200, (2, 15))

    model = Transformer(vocab_size=300, pad_idx=0, d_model=512, num_heads=8, num_layers=2)
    output = model(src_ids, tgt_ids)
    print(f"Transformer 输出: {output.shape}")  # (2, 15, 300)
