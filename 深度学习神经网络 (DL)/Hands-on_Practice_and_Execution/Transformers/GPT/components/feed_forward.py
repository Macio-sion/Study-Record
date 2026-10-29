import torch
from torch import nn

class FeedForward(nn.Module):
    """
    前馈网络
    """
    def __init__(self, d_model, hidden_dim, dropout=0.1):
        super().__init__()
        
        self.linear1 = nn.Linear(d_model, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, d_model)
        self.dropout = nn.Dropout(dropout)
        self.gelu = nn.GELU()

    def forward(self, x):
        """
        前向传播
        """
        x = self.gelu(self.linear1(x))
        x = self.dropout(x)
        x = self.linear2(x)
        return x