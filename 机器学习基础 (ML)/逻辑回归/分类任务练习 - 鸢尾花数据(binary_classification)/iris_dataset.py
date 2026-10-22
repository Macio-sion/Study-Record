"""
@Author : Administrator
@Company : 
@Date : 2026/8/4 21:07
@Desc :
@Version : 1.0
"""
import torch
from torch.utils.data import Dataset
from sklearn.datasets import load_iris

class IrisDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):

    def __init__(self):
        features, targets = load_iris(return_X_y=True)
        self._features = torch.tensor(features, dtype=torch.float32)
        self._targets = torch.tensor(targets, dtype=torch.float32)

    def __len__(self) -> int:
        # return int(self._features.shape[0])
        return len(self._features)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self._features[index], self._targets[index]