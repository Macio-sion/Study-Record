"""
@Author : Administrator
@Company : 
@Date : 2026/8/4 21:40
@Desc :
@Version : 1.0
"""
import torch
from torch import nn

class SigmoidNeuronClassifier(nn.Module):

    def __init__(self, feature_dim: int) -> None:
        super().__init__()
        self.linear = nn.Linear(feature_dim, 1)
        self.activation = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.linear(x)
        return self.activation(logits).reshape(-1)
