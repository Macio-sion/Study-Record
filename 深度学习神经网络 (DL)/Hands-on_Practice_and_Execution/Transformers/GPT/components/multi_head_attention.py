import torch
from torch import nn

class MultiHeadAttention(nn.Module):
    """
    多头注意力机制
    """
    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = self.d_model // self.n_heads

        self.linear1 = nn.Linear(d_model, d_model)
        self.linear2 = nn.Linear(d_model, d_model)
        self.linear3 = nn.Linear(d_model, d_model)
        self.linear4 = nn.Linear(d_model, d_model)

        self.softmax = nn.Softmax(dim=-1)
        self.dropout = nn.Dropout(dropout)

    @staticmethod
    def _merge_masks(
        padding_mask: torch.Tensor,
        subsequent_mask: torch.Tensor,
    ):
        """
        合并 padding mask 和 subsequent mask
        """
        padding_mask = padding_mask.unsqueeze(1).unsqueeze(2)
        subsequent_mask = subsequent_mask.unsqueeze(0).unsqueeze(1)
        return padding_mask & subsequent_mask

    def forward(self, Query, Key, Value, mask=None, sub_mask=None):
        """
        前向传播
        """
        batch_size, seq_len, _ = Query.shape
        Query = self.linear1(Query)
        Key = self.linear2(Key)
        Value = self.linear3(Value)

        Query = Query.reshape(batch_size, seq_len, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
        Key = Key.reshape(batch_size, seq_len, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
        Value = Value.reshape(batch_size, seq_len, self.n_heads, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.matmul(Query, Key.transpose(-2, -1)) / torch.sqrt(self.head_dim)

        combined_mask = self._merge_masks(mask, sub_mask)
        scores = scores.masked_fill(combined_mask, float('-inf'))
            
        attn_weights = self.softmax(scores)
        attn_weights = self.dropout(attn_weights)

        context = torch.matmul(attn_weights, Value)
        context = context.transpose(1, 2).reshape(batch_size, seq_len, self.d_model)
        context = self.linear4(context)

        return context


