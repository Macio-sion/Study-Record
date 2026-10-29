import torch
from torch import nn


class RmsNorm(nn.Module):
    """
    RMS 归一化层 (Root Mean Square Layer Normalization)

    与 LayerNorm 的区别：
        - 不做去均值（不减去 mean），只做缩放
        - 通常不带 bias，仅保留可学习的缩放参数 weight (γ)

    公式: RMSNorm(x) = x / sqrt(mean(x^2) + ε) * γ

    参考: Qwen / LLaMA 系列模型
    """

    def __init__(self, d_model: int, eps: float = 1e-10):
        """
        Args:
            d_model: 特征维度
            eps: 数值稳定项，防止除零
        """
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量 (..., d_model)

        Returns:
            归一化后的张量，shape 与 x 相同
        """
        # RMS = sqrt(mean(x^2) + eps)，沿最后一维计算
        rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + self.eps)
        return x / rms * self.weight


if __name__ == '__main__':
    d_model = 16
    batch_size, seq_len = 2, 8

    norm = RmsNorm(d_model)
    x = torch.randn(batch_size, seq_len, d_model)

    y = norm(x)
    print("输入 shape:", x.shape)
    print("输出 shape:", y.shape)
    print("shape 一致:", x.shape == y.shape)

    # 验证：归一化后每行的 RMS 应接近 1
    rms_after = torch.sqrt(torch.mean(y ** 2, dim=-1))
    print("\n归一化后每行 RMS（应接近 1）:")
    print(rms_after)
