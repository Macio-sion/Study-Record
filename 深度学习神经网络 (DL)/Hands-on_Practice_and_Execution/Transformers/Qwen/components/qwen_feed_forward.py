import torch
from torch import nn


class QwenFeedForward(nn.Module):
    """
    Qwen 前馈网络
    """
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()

        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_model, d_ff)
        self.linear3 = nn.Linear(d_ff, d_model)

        self.silu = nn.SiLU()

    def forward(self, x):
        """
        前向传播
        """
        return self.linear3(self.silu(self.linear1(x)) * self.linear2(x))