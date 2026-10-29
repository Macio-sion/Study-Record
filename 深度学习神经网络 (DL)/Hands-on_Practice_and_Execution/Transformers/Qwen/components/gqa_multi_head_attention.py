import torch
from torch import nn

from components.rms_norm import RmsNorm

class GroupedQueryAttention(nn.Module):
    """
    分组查询-键值对注意力层
    """
    def __init__(self, d_model, q_num_heads, kv_num_heads, max_seq_len, theta=10000.0):
        super().__init__()
        
        self.d_model = d_model
        self.q_num_heads = q_num_heads
        self.head_dim = self.d_model // q_num_heads
        self.kv_num_heads = kv_num_heads
        self.theta = theta
        self.max_seq_len = max_seq_len
        self.cos_v, self.sin_v = self.precompute_freqs()
        self.register_buffer('cos_v', cos_v)
        self.register_buffer('sin_v', sin_v)
        
        self.linear_q = nn.Linear(d_model, self.d_model)
        self.linear_k = nn.Linear(d_model, kv_num_heads * self.head_dim)
        self.linear_v = nn.Linear(d_model, kv_num_heads * self.head_dim)
        self.out = nn.Linear(d_model, d_model)

        self.norm1 = RmsNorm(self.head_dim)
        self.norm2 = RmsNorm(self.head_dim)

        self.attention = nn.Softmax(dim=-1)
    

    def precompute_freqs(self):
        """
        预计算所有位置的 RoPE cos/sin 表
        """
        i = torch.arange(0, self.head_dim, 2, dtype=torch.float32)
        freq = 1.0 / (self.theta ** (i / self.head_dim))
        pos = torch.arange(self.max_seq_len, dtype=torch.float32)
        angles = torch.outer(pos, freq)

        return torch.cos(angles), torch.sin(angles)

    def rotate_half(self, x: torch.Tensor):
        """
        对相邻维度对 (x0, x1) 执行 90° 旋转 → (-x1, x0)
        """
        x1, x2 = x[..., :: 2], x[..., 1 :: 2]
        return torch.cat([-x2, x1], dim=-1)

    def apply_rotary_pos_emb(self, x):
        """
        对输入施加旋转位置编码
        """
        seq_len = x.size(-2)
        cos_v = self.cos_v[:seq_len].repeat_interleave(2, dim=-1)
        sin_v = self.sin_v[:seq_len].repeat_interleave(2, dim=-1)
        return x * cos_v + self.rotate_half(x) * sin_v

    @staticmethod
    def _merge_masks(
        padding_mask: torch.Tensor,
        subsequent_mask: torch.Tensor,
    ):
        """
        合并 padding mask 和 subsequent mask
        """
        padding_mask = padding_mask.unsqueeze(1).unsqueeze(2).unsqueeze(3)
        subsequent_mask = subsequent_mask.unsqueeze(0).unsqueeze(1).unsqueeze(2)
        return padding_mask & subsequent_mask
        

    def forward(self, x, mask=None, sub_mask=None):
        """
        前向传播
        """
        batch_size, seq_len, _ = x.shape
        kv_len = seq_len 

        q = self.linear_q(x)
        k = self.linear_k(x)
        v = self.linear_v(x)

        q = q.reshape(batch_size, seq_len, self.q_num_heads, self.head_dim).transpose(1, 2)
        k = k.reshape(batch_size, kv_len, self.kv_num_heads, self.head_dim).transpose(1, 2)
        v = v.reshape(batch_size, kv_len, self.kv_num_heads, self.head_dim).transpose(1, 2)

        q = self.apply_rotary_pos_emb(q)
        k = self.apply_rotary_pos_emb(k)

        q = self.norm1(q)
        k = self.norm2(k)

        q = q.reshape(batch_size, self.kv_num_heads, self.q_num_heads // self.kv_num_heads, seq_len, self.head_dim)
        
        scores = torch.matmul(q, k.transpose(-2, -1)) / self.head_dim**0.5

        combined_mask = self._merge_masks(mask, sub_mask)
        scores = scores.masked_fill(combined_mask, float('-inf'))
        
        attn_weights = self.attention(scores)

        output = torch.matmul(attn_weights, v)
        output = output.reshape(batch_size, seq_len, self.q_num_heads, self.head_dim)
        output = output.transpose(1, 2).reshape(batch_size, seq_len, self.d_model)
        output = self.out(output)

        return output
