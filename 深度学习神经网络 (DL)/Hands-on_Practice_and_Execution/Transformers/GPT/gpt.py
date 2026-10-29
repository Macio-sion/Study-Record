import torch
from torch import nn

from components.position_encoding import PositionalEncoding
from layers.decoder_layer import DecoderLayer

class GPTModel(nn.Module):
    """
    GPT 模型
    """
    def __init__(self, config):
        super().__init__()

        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.hidden_dim = config.hidden_dim
        self.max_len = config.max_len
        self.n_layers = config.n_layers
        self.vocab_size = config.vocab_size
        self.dropout = config.dropout
        
        self.embedding = nn.Embedding(self.vocab_size, self.d_model)
        self.pos_embed = PositionalEncoding(self.max_len, self.d_model)

        self.layers = nn.ModuleList([
            DecoderLayer(self.d_model, self.n_heads, self.hidden_dim, self.dropout) 
            for _ in range(self.n_layers)
            ]
        )

        self.dropout = nn.Dropout(self.dropout)
        self.norm = nn.LayerNorm(self.d_model)

        self.output_proj = nn.Linear(self.d_model, self.vocab_size)

        

    def generate_padding_mask(self, tgt: torch.Tensor, pad_token_id: int) -> torch.Tensor:
        """
        生成 padding mask
        """
        return tgt == pad_token_id

    def generate_subsequent_mask(self, tgt: torch.Tensor, device: torch.device) -> torch.Tensor:
        """
        生成 subsequent mask（上三角 mask），用于解码器自注意力。
        """
        return torch.triu(torch.ones(tgt.size(1), tgt.size(1), device=device), diagonal=1).bool()

    def forward(self, x, pad_token_id):
        """
        前向传播
        """
        padding_mask = self.generate_padding_mask(x, pad_token_id)
        subsequent_mask = self.generate_subsequent_mask(x, x.device)

        x = self.embedding(x)
        x = self.dropout(self.pos_embed(x))

        for layer in self.layers:
            x = layer(x, padding_mask, subsequent_mask)

        x = self.norm(x)
        x = self.output_proj(x)
        return x
        
        
        
   