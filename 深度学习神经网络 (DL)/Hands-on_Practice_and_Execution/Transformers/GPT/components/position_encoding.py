import torch
from torch import nn

class PositionalEncoding(nn.Module):
    """
    位置编码
    """
    def __init__(self, max_len, d_model):
        super().__init__()
        self.max_len = max_len
        self.position_embedding = nn.Embedding(self.max_len, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        """
        前向传播
        """
        position = torch.arange(0, x.shape[1], device=x.device)
        position_embedding = self.position_embedding(position)
        x = x + position_embedding
        return x