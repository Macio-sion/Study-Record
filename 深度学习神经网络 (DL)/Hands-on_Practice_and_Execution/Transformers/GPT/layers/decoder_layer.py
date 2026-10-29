import torch
from torch import nn
from component.multi_head_attention import MultiHeadAttention
from component.feed_forward import FeedForward

class DecoderLayer(nn.Module):
    """
    解码器层
    """
    def __init__(self, d_model, num_heads, hidden_dim, dropout=0.1):
        super().__init__()

        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, hidden_dim, dropout)

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None, sub_mask=None):
        """
        前向传播
        """
        x = self.norm1(x)
        x = x + self.dropout1(self.attention(x, x, x, mask, sub_mask))
        x = self.norm2(x)
        x = x + self.dropout2(self.feed_forward(x))
        return x