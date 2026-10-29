"""
频率分割
"""
import torch
from torch import nn

dim_area = 512
num_heads = 8
head_dim = dim_area // num_heads

freq_div = torch.exp( torch.arange(0, head_dim, 2, dtype=torch.float) * (- torch.log(10000)) / head_dim)

def frequency_division(i: torch.Tensor, head_dim: torch.Tensor):
    """
    频率分割
    """
    # i = torch.arange(0, head_dim, 2, dtype=torch.float)
    return torch.exp( 2 * i  * (- torch.log(10000)) / head_dim)
