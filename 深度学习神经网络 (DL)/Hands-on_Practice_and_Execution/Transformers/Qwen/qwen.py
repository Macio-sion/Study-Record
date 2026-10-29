import torch
from torch import nn

from layers.decoder_layer import DecoderLayer
from components.rms_norm import RmsNorm

class Qwen(nn.Module):
    """
    Qwen模型
    """
    def __init__(self, config):
        super().__init__()

        self.vocab_size = config.vocab_size
        self.d_model = config.d_model
        self.hidden_dim = config.hidden_dim
        self.num_heads = config.num_heads
        self.num_groups = config.num_groups
        self.num_layers = config.num_layers
        self.max_seq_len = config.max_seq_len
        self.theta = config.theta
        self.dropout = config.dropout
        self.pad_token_id = config.pad_token_id

        self.embedding = nn.Embedding(self.vocab_size, self.d_model)

        self.layers = nn.ModuleList([
            DecoderLayer(self.d_model, self.num_heads, self.hidden_dim, self.num_groups, self.max_seq_len, self.theta, self.dropout)
            for _ in range(self.num_layers)
        ])

        self.norm = RmsNorm(self.d_model)

        self.out = nn.Linear(self.d_model, self.vocab_size)

    def generate_padding_mask(self, tgt: torch.Tensor) -> torch.Tensor:
        """
        生成 padding mask
        """
        return tgt == self.pad_token_id

    def generate_subsequent_mask(self, tgt: torch.Tensor) -> torch.Tensor:
        """
        生成 subsequent mask（上三角 mask），用于解码器自注意力。
        """
        return torch.triu(torch.ones(tgt.size(1), tgt.size(1), device=tgt.device), diagonal=1).bool()

    def forward(self, x: torch.Tensor):
        """
        前向传播
        """
        padding_mask = self.generate_padding_mask(x)
        subsequent_mask = self.generate_subsequent_mask(x)

        x = self.embedding(x)

        for layer in self.layers:
            x = layer(x, padding_mask, subsequent_mask)
        
        x = self.out(self.norm(x))

        return x
