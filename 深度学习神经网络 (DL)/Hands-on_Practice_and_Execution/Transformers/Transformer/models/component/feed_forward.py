import torch
from torch import nn
from torch.nn import functional as F

class FeedForward(nn.Module):
    """
    编码器的前向网络层
    params:
        d_model: 词向量空间维度
        d_ff: 特征提取转化的维度 (小于d_model是压缩，大于d_model是增大描述关系)
        dropout: Dropout层的丢弃系数
    return:
        x: 词的特征矩阵 -> shape:(batch_size, seq_len, d_model)
    """
    def __init__(self, d_model, d_ff, dropout=0.1):

        super().__init__()

        self.d_model = d_model
        self.d_ff = d_ff
        
        self.linear1 = nn.Linear(self.d_model, self.d_ff)
        self.linear2 = nn.Linear(self.d_ff, self.d_model)
        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):

        x = self.linear1(x) # shape: (batch_size, seq_len, d_ff)
        x = self.activation(x) # shape: (batch_size, seq_len, d_ff)
        x = self.dropout(x) # shape: (batch_size, seq_len, d_ff)
        x = self.linear2(x) # shape: (batch_size, seq_len, d_model)
        
        return x
    
if __name__ == "__main__":
    x = torch.randn(3, 512).unsqueeze(0)
    ff = FeedForward(512, 1024)
    result = ff(x)
    print(result.shape)
