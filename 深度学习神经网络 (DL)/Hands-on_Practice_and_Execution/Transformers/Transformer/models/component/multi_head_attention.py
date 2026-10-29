import torch
from torch import nn
from torch.nn import functional as F


class MultiHeadAttention(nn.Module):
    """
    多头注意力层。

    将 d_model 维的 Q/K/V 拆分为 num_heads 个头并行计算缩放点积注意力，
    最后拼接并通过线性层投影回 d_model。

    Parameters
    ----------
    d_model : int
        词向量 / 模型隐藏层维度。
    num_heads : int
        多头拆分的头数。d_model 必须能被 num_heads 整除。
    dropout : float
        Attention 权重上的 dropout 比率，默认 0.1。

    Notes
    -----
    - mask 语义：BoolTensor，True = 需要忽略的位置（会被置为 -inf）。
    - 若同时传入 mask 和 subsequent_mask，内部自动广播合并。
    - d_k = d_model // num_heads。
    """

    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1) -> None:
        super().__init__()
        assert d_model % num_heads == 0, (
            f"d_model ({d_model}) 必须能被 num_heads ({num_heads}) 整除"
        )

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    # ------------------------------------------------------------------
    # Mask 合并
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_masks(
        padding_mask: torch.Tensor,
        subsequent_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        将 padding mask 和 subsequent mask 合并。

        padding_mask   : (B, seq_len) 或 (B, 1, 1, seq_len)
        subsequent_mask: (seq_len, seq_len) 或 (1, 1, seq_len, seq_len)

        Returns:
            (B, 1, seq_len, seq_len) BoolTensor，True = 忽略。
        """
        # 统一升维到 (B, 1, seq_len, seq_len)
        while padding_mask.dim() < 4:
            padding_mask = padding_mask.unsqueeze(1)       # (B, 1, 1, seq_len)
        while subsequent_mask.dim() < 4:
            subsequent_mask = subsequent_mask.unsqueeze(0) # (1, 1, seq_len, seq_len)
        return padding_mask | subsequent_mask

    # ------------------------------------------------------------------
    # 前向传播
    # ------------------------------------------------------------------

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: torch.Tensor = None,
        subsequent_mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        多头注意力前向传播。

        Args:
            query: (batch_size, q_len, d_model)
            key:   (batch_size, kv_len, d_model)
            value: (batch_size, kv_len, d_model)
            mask:  (B, kv_len) 或 (B, 1, 1, kv_len) padding mask，True=忽略。
            subsequent_mask: (kv_len, kv_len) subsequent mask，True=忽略。

        Returns:
            (batch_size, q_len, d_model) 注意力输出。
        """
        batch_size, q_len, _ = query.size()
        kv_len = key.size(1)

        # 线性投影
        Q = self.W_q(query)   # (B, q_len, d_model)
        K = self.W_k(key)     # (B, kv_len, d_model)
        V = self.W_v(value)   # (B, kv_len, d_model)

        # 拆分为多头: (B, num_heads, len, d_k)
        Q = Q.view(batch_size, q_len, self.num_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, kv_len, self.num_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, kv_len, self.num_heads, self.d_k).transpose(1, 2)

        # 缩放点积注意力
        scale = self.d_k ** 0.5
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale  # (B, nH, q_len, kv_len)

        # 合并 mask 并应用
        if mask is not None or subsequent_mask is not None:
            if mask is None:
                mask = torch.zeros(batch_size, kv_len, dtype=torch.bool, device=scores.device)
            if subsequent_mask is not None:
                combined_mask = self._merge_masks(mask, subsequent_mask)
            else:
                while mask.dim() < 4:
                    mask = mask.unsqueeze(1)
                combined_mask = mask
            scores = scores.masked_fill(combined_mask, float('-inf'))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 加权聚合
        context = torch.matmul(attn_weights, V)  # (B, nH, q_len, d_k)

        # 拼接多头并投影
        context = context.transpose(1, 2).contiguous().view(batch_size, q_len, self.d_model)
        outputs = self.W_o(context)

        return outputs


if __name__ == "__main__":
    # 基础测试
    x = torch.randn(2, 10, 512)
    mha = MultiHeadAttention(512, 8)
    result = mha(x, x, x)
    print(f"无 mask: {result.shape}")  # (2, 10, 512)

    # padding mask 测试
    pad_mask = torch.zeros(2, 10, dtype=torch.bool)
    pad_mask[:, -3:] = True  # 最后 3 个位置为 pad
    result = mha(x, x, x, mask=pad_mask)
    print(f"有 padding mask: {result.shape}")

    # padding + subsequent mask 测试
    sub_mask = torch.triu(torch.ones(10, 10, dtype=torch.bool), diagonal=1)
    result = mha(x, x, x, mask=pad_mask, subsequent_mask=sub_mask)
    print(f"有 padding + subsequent mask: {result.shape}")
