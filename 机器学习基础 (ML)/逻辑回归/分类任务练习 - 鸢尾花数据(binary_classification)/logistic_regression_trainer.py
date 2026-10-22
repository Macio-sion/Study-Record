"""
@Author : Administrator
@Company : 
@Date : 2026/8/4 21:44
@Desc :
@Version : 1.0
"""
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from sigmoid_neuron_classifier import SigmoidNeuronClassifier as snc
from iris_data_module import IrisDataModule as idm
from data_split_config import DataSplitConfig as conf


class LogisticRegressionTrainer:

    def __init__(
            self,
            model: nn.Module,
            train_loader: DataLoader,
            test_loader: DataLoader,
            epochs: int,
            learning_rate: float,
            print_interval: int,
            device: torch.device,
            task_name: str
    ) -> None:
        self._device = device
        self._model = model.to(device)
        self._train_loader = train_loader
        self._test_loader = test_loader
        self._epochs = epochs
        self._learning_rate = learning_rate
        self._print_interval = print_interval
        self._task_name = task_name
        self._optimizer = torch.optim.SGD(self._model.parameters(), lr=self._learning_rate)
        self._loss_f = nn.BCELoss()

    def train(self):
        tm = tqdm(range(1, self._epochs + 1), colour='green', desc='Training...')
        losses: list[float] = []
        for epoch in tm:
            self._model.train()
            epoch_losses: list[float] = []

            for features, labels in self._train_loader:
                features = features.to(self._device)
                labels = labels.to(self._device)

                self._optimizer.zero_grad()
                logits = self._model(features)
                loss = self._loss_f(logits, labels)
                loss.backward()
                self._optimizer.step()
                epoch_losses.append(float(loss.item()))

            mean_loss = float(sum(epoch_losses) / max(len(epoch_losses), 1))
            losses.append(mean_loss)

            if epoch % self._print_interval == 0:
                tm.set_postfix({
                    'task_name': self._task_name,
                    'device_type': self._device,
                    'loss': f"{mean_loss:.6f}",
                    'Epoch': f"{epoch:05d}"
                })
                # print(f"[{self._task_name}][{self._device.type}] Epoch {epoch:05d} Loss {mean_loss:.6f}")
        return losses


if __name__ == '__main__':
    device = torch.device("cuda:0")
    dataset = idm(config=conf())
    feature_dim = dataset.feature_dim
    dataset.setup()
    train_loader = dataset.train_dataloader()
    test_loader = dataset.test_dataloader()

    test = LogisticRegressionTrainer(
        task_name="测试",
        model=snc(feature_dim),
        train_loader=train_loader,
        test_loader=test_loader,
        device=device,
        learning_rate=0.001,
        print_interval=1000,
        epochs=10000
    )
    result = test.train()
    print(result)

