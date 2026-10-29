import torch
from torch import nn
from torch.nn import functional as F

from layers import EncoderLayer

class Encoder(nn.Module):
    """
    """
    def __init__(self, d_model, num_heads, d_ff, num_layers, dropout=0.1):

        super().__init__()

        self.layers = nn.ModuleList([
            EncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

    def forward(self, x, mask=None):
        for layer in self.layers:
            x = layer(x, mask)
        return x

if __name__ == "__main__":
    x = torch.randn(3, 512).unsqueeze(0)
    encoder = Encoder(512, 8, 1024, 6)
    result = encoder(x)
    print(result.shape)
    pass