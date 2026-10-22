"""
@Author : Administrator
@Company : 
@Date : 2026/8/4 21:05
@Desc :
@Version : 1.0
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class DataSplitConfig:

    batch_size: int = 20
    test_ratio: float = 0.2
    seed: int = 22
    shuffle: bool = True