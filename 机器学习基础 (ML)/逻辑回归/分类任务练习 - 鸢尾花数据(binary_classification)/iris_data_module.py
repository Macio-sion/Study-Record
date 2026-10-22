"""
@Author : Administrator
@Company : 
@Date : 2026/8/4 21:13
@Desc :
@Version : 1.0
"""
import torch
from sklearn.datasets import load_iris
from torch.utils.data import DataLoader, Subset
from data_split_config import DataSplitConfig
from iris_dataset import IrisDataset

class IrisDataModule:

    def __init__(self, config: DataSplitConfig) -> None:
        self._config = config
        self._dataset = IrisDataset()
        self._train: Subset[tuple[torch.Tensor, torch.Tensor]] | None = None
        self._test: Subset[tuple[torch.Tensor, torch.Tensor]] | None = None

    @property
    def feature_dim(self) -> int:
        sample, _ = self._dataset[0]
        return int(sample.numel())

    @property
    def num_classes(self) -> int:
        _, labels = load_iris(return_X_y=True)
        return len(set(labels.tolist()))

    def setup(self):
        # total = len(self._dataset)
        total = 100
        test_size = int(total * self._config.test_ratio)
        generator = torch.Generator().manual_seed(self._config.seed)
        indices = torch.randperm(total, generator=generator).tolist()
        test_dataset = indices[:test_size]
        train_dataset = indices[test_size:]
        self._train = Subset(self._dataset, train_dataset)
        self._test = Subset(self._dataset, test_dataset)

    def train_dataloader(self) -> DataLoader:
        if self._train is None:
            raise RuntimeError("数据集异常")
        return DataLoader(
            dataset=self._train,
            batch_size=self._config.batch_size,
            shuffle=self._config.shuffle
        )

    def test_dataloader(self) -> DataLoader:
        if self._test is None:
            raise RuntimeError("数据集异常")
        return DataLoader(
            dataset=self._test,
            batch_size=self._config.batch_size,
            shuffle=self._config.shuffle
        )