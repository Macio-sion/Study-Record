import torch
from torch import nn

from components.rms_norm import RmsNorm
from components.qwen_feed_forward import QwenFeedForward
from components.gqa_multi_head_attention import GroupedQueryAttention

class DecoderLayer(nn.Module):
    """
    解码器层
    """
    def __init__(self, d_model, num_heads, hidden_dim, num_groups, max_seq_len, theta=10000.0, dropout=0.1):
        super().__init__()

        self.attention = GroupedQueryAttention(d_model, num_heads, num_groups, max_seq_len, theta)
        self.feed_forward = QwenFeedForward(d_model, hidden_dim, dropout)

        self.norm1 = RmsNorm(d_model)
        self.norm2 = RmsNorm(d_model)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None, sub_mask=None):
        """
        前向传播
        """
        residual = x
        x = self.norm1(x) 
        x = self.attention(x, x, x, mask, sub_mask)
        x = self.dropout1(x) + residual
        t = self.norm2(x)
        x = self.dropout2(self.feed_forward(t)) + x
        return x
