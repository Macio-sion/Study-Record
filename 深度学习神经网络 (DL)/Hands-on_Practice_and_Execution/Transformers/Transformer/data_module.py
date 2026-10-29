"""
Transformer 数据模块（位置编码以前的全流程）。

本模块在位置编码之前完成以下工作：
    1. 提供内置中英文样例语料
    2. 分词（Tokenizer）
    3. 构建词表（Vocabulary / 词袋）
    4. 将词索引映射为稠密词向量（nn.Embedding）

通过 TransformerDataModule 统一对外暴露一个便捷接口，
可直接获取 (batch_token_ids, batch_embeddings, padding_mask) 三元组，
供给后续的 PositionalEncoding 与 MultiHeadAttention 等模块使用。

使用示例
--------
>>> dm = TransformerDataModule(d_model=512, max_seq_len=128)
>>> token_ids, embeddings, pad_mask = dm.get_batch(batch_size=4)
>>> print(token_ids.shape)      # (4, 128)
>>> print(embeddings.shape)     # (4, 128, 512)
>>> print(pad_mask.shape)       # (4, 128)
"""

from __future__ import annotations

import re
import random
from typing import Dict, List, Optional, Tuple, Union

import torch
from torch import nn


# ============================================================================
# 1. 内置样例语料
# ============================================================================

BUILTIN_CORPUS_ZH: List[str] = [
    "深度学习是机器学习的一个分支，它使用多层神经网络来学习数据的表示。",
    "Transformer 模型由 Vaswani 等人在 2017 年提出，完全基于注意力机制。",
    "自注意力机制允许模型在序列中的任意位置之间建立直接的依赖关系。",
    "词嵌入是一种将离散词语映射到连续向量空间的技术。",
    "多头注意力通过并行运行多个注意力头来捕获不同子空间的信息。",
    "位置编码为 Transformer 注入了序列中 token 的位置信息。",
    "残差连接和层归一化是 Transformer 架构中稳定训练的关键组件。",
    "前馈网络在每个位置上独立地对特征进行非线性变换。",
    "BERT 是基于 Transformer 编码器的预训练语言模型。",
    "GPT 系列模型使用 Transformer 解码器进行自回归语言建模。",
]

BUILTIN_CORPUS_EN: List[str] = [
    "Deep learning is a subset of machine learning that uses neural networks with many layers.",
    "The Transformer model was proposed by Vaswani et al. in 2017 and relies entirely on attention.",
    "Self-attention allows the model to establish direct dependencies between any two positions in a sequence.",
    "Word embeddings map discrete tokens into a continuous vector space.",
    "Multi-head attention captures information from different representation subspaces in parallel.",
    "Positional encoding injects information about the position of tokens into the Transformer.",
    "Residual connections and layer normalization are crucial for stable training of deep Transformers.",
    "The feed-forward network applies a non-linear transformation independently at each position.",
    "BERT is a pretrained language model based on the Transformer encoder.",
    "The GPT series uses a Transformer decoder for autoregressive language modeling.",
]


# ============================================================================
# 2. 分词器
# ============================================================================

class Tokenizer:
    """
    简易分词器，支持中英文混合文本。

    英文：按空格和标点进行规则分词。
    中文：按字符级分词（每个汉字 / 标点作为一个 token）。

    Methods
    -------
    tokenize(text: str) -> List[str]
        对输入文本进行分词，返回 token 列表。
    """

    # 英文标点和特殊符号（tokenize 时与单词分离）
    _EN_PUNCTUATION: str = r'[.,!?;:\'"()\[\]{}]'

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """
        对输入文本进行分词。

        Args:
            text: 原始文本字符串。

        Returns:
            分词后的 token 列表。
        """
        tokens: List[str] = []
        # 按空白字符初次切分
        for chunk in re.split(r'\s+', text.strip()):
            if not chunk:
                continue
            # 判断是否为纯中文片段（不含 ASCII 字母）
            if cls._is_chinese_chunk(chunk):
                # 中文：逐字符切分
                tokens.extend(list(chunk))
            else:
                # 英文 / 混合：分离标点后作为独立 token
                tokens.extend(cls._split_english_chunk(chunk))
        return tokens

    @staticmethod
    def _is_chinese_chunk(chunk: str) -> bool:
        """判断一个片段是否主要由 CJK 字符组成（无 ASCII 字母）。"""
        return not bool(re.search(r'[a-zA-Z]', chunk))

    @classmethod
    def _split_english_chunk(cls, chunk: str) -> List[str]:
        """对英文片段做标点分离处理。"""
        # 去除首尾标点并单独记录
        result: List[str] = []
        # 对 chunk 中的标点前后加空格切分
        processed = re.sub(cls._EN_PUNCTUATION, r' \g<0> ', chunk)
        for sub in processed.split():
            sub = sub.strip()
            if sub:
                result.append(sub)
        return result


# ============================================================================
# 3. 词表
# ============================================================================

class Vocabulary:
    """
    词表（词袋），维护 token 与索引之间的双向映射。

    特殊 token：
        <pad>   — 填充符，索引 0
        <unk>   — 未知词，索引 1
        <bos>   — 句子开头，索引 2
        <eos>   — 句子结尾，索引 3

    Attributes
    ----------
    PAD_TOKEN : str
    UNK_TOKEN : str
    BOS_TOKEN : str
    EOS_TOKEN : str

    Methods
    -------
    build(corpus: List[str], tokenizer: Tokenizer) -> None
        从语料库构建词表。
    encode(tokens: List[str], add_special: bool) -> List[int]
        将 token 列表转为索引列表。
    decode(indices: List[int]) -> List[str]
        将索引列表转回 token 列表。
    """

    PAD_TOKEN: str = '<pad>'
    UNK_TOKEN: str = '<unk>'
    BOS_TOKEN: str = '<bos>'
    EOS_TOKEN: str = '<eos>'

    def __init__(self) -> None:
        """初始化空词表，预先注册特殊 token。"""
        self._idx2token: Dict[int, str] = {}
        self._token2idx: Dict[str, int] = {}

        # 注册特殊 token
        for token in [self.PAD_TOKEN, self.UNK_TOKEN, self.BOS_TOKEN, self.EOS_TOKEN]:
            self._add_token(token)

    def _add_token(self, token: str) -> None:
        """内部方法：将 token 加入词表（若已存在则跳过）。"""
        if token not in self._token2idx:
            idx = len(self._token2idx)
            self._token2idx[token] = idx
            self._idx2token[idx] = token

    # ---- 属性 ----

    @property
    def vocab_size(self) -> int:
        """返回词表大小（含特殊 token）。"""
        return len(self._token2idx)

    @property
    def pad_idx(self) -> int:
        """返回 <pad> 对应的索引。"""
        return self._token2idx[self.PAD_TOKEN]

    @property
    def unk_idx(self) -> int:
        """返回 <unk> 对应的索引。"""
        return self._token2idx[self.UNK_TOKEN]

    @property
    def bos_idx(self) -> int:
        """返回 <bos> 对应的索引。"""
        return self._token2idx[self.BOS_TOKEN]

    @property
    def eos_idx(self) -> int:
        """返回 <eos> 对应的索引。"""
        return self._token2idx[self.EOS_TOKEN]

    # ---- 构建 ----

    def build(
        self,
        corpus: List[str],
        tokenizer: Optional[Tokenizer] = None,
        min_freq: int = 1,
    ) -> None:
        """
        从语料库构建词表。

        Args:
            corpus: 原始文本列表，每项为一个句子/段落。
            tokenizer: 分词器实例，默认为 Tokenizer 类方法。
            min_freq: 最小词频阈值，出现次数低于此值的 token 不会被加入词表。
        """
        if tokenizer is None:
            tokenizer = Tokenizer()
        # 统计词频
        freq: Dict[str, int] = {}
        for text in corpus:
            for token in tokenizer.tokenize(text):
                freq[token] = freq.get(token, 0) + 1
        # 按频率阈值加入词表
        for token, count in sorted(freq.items(), key=lambda x: -x[1]):
            if count >= min_freq:
                self._add_token(token)

    # ---- 编解码 ----

    def encode(
        self,
        tokens: Union[str, List[str]],
        add_special: bool = True,
    ) -> List[int]:
        """
        将 token 列表（或原始文本字符串）转为索引列表。

        Args:
            tokens: token 列表或原始文本字符串。若传入字符串，
                    内部会自动调用 Tokenizer.tokenize 进行分词。
            add_special: 是否在首尾添加 <bos> 和 <eos> 索引。

        Returns:
            整数索引列表。

        Raises:
            RuntimeError: 词表未构建（vocab_size <= 4 且 tokens 非特殊 token）。
        """
        if isinstance(tokens, str):
            tokens = Tokenizer.tokenize(tokens)
        indices = [self._token2idx.get(t, self.unk_idx) for t in tokens]
        if add_special:
            indices = [self.bos_idx] + indices + [self.eos_idx]
        return indices

    def decode(
        self,
        indices: List[int],
        remove_special: bool = True,
    ) -> List[str]:
        """
        将索引列表转回 token 列表。

        Args:
            indices: 整数索引列表。
            remove_special: 是否过滤特殊 token（<pad>, <bos>, <eos>）。

        Returns:
            token 字符串列表。
        """
        specials = {self.pad_idx, self.bos_idx, self.eos_idx}
        tokens: List[str] = []
        for idx in indices:
            token = self._idx2token.get(idx, self.UNK_TOKEN)
            if remove_special and idx in specials:
                continue
            tokens.append(token)
        return tokens

    def idx2token(self, idx: int) -> str:
        """返回索引对应的 token，不存在时返回 <unk>。"""
        return self._idx2token.get(idx, self.UNK_TOKEN)

    def token2idx(self, token: str) -> int:
        """返回 token 对应的索引，不存在时返回 <unk> 的索引。"""
        return self._token2idx.get(token, self.unk_idx)


# ============================================================================
# 4. 统一数据模块
# ============================================================================

class TransformerDataModule:
    """
    Transformer 位置编码前的统一数据模块。

    职责：
        1. 管理内置 / 自定义语料
        2. 自动完成分词与词表构建
        3. 提供 nn.Embedding 词向量层
        4. 提供 get_batch() 便捷接口，直接输出 (token_ids, embeddings, pad_mask)

    Parameters
    ----------
    d_model : int
        词向量维度（即 embedding_dim）。
    max_seq_len : int
        最大序列长度，超过则截断，不足则 <pad> 填充。
    vocab : Vocabulary, optional
        外部传入的词表；若为 None，则使用内置语料自动构建。
    embedding : nn.Embedding, optional
        外部传入的嵌入层；若为 None，则根据 vocab_size 和 d_model 自动创建。

    Attributes
    ----------
    vocab : Vocabulary
        词表实例。
    embedding : nn.Embedding
        词向量嵌入层。
    d_model : int
        词向量维度。
    max_seq_len : int
        最大序列长度。

    Notes
    -----
    - 若未传入 vocab，内部会使用 BUILTIN_CORPUS_ZH + BUILTIN_CORPUS_EN 自动构建词表。
    - 若未传入 embedding，内部会自动创建一个参数可训练的 nn.Embedding 层。
    """

    def __init__(
        self,
        d_model: int = 512,
        max_seq_len: int = 128,
        vocab: Optional[Vocabulary] = None,
        embedding: Optional[nn.Embedding] = None,
    ) -> None:
        """初始化数据模块。"""
        self.d_model: int = d_model
        self.max_seq_len: int = max_seq_len

        # 词表
        if vocab is not None:
            self.vocab: Vocabulary = vocab
        else:
            self.vocab = Vocabulary()
            self.vocab.build(BUILTIN_CORPUS_ZH + BUILTIN_CORPUS_EN)

        # 词向量嵌入层
        if embedding is not None:
            self.embedding: nn.Embedding = embedding
        else:
            self.embedding = nn.Embedding(
                num_embeddings=self.vocab.vocab_size,
                embedding_dim=d_model,
                padding_idx=self.vocab.pad_idx,
            )

        # 内置语料（用于随机采样生成 batch）
        self._corpus: List[str] = BUILTIN_CORPUS_ZH + BUILTIN_CORPUS_EN

    # ========================================================================
    # 核心接口
    # ========================================================================

    def encode_single(self, text: str) -> torch.Tensor:
        """
        将单条文本编码为定长索引张量（含 <bos>/<eos>，自动截断/填充）。

        Args:
            text: 原始文本字符串。

        Returns:
            shape = (max_seq_len,) 的 LongTensor。
        """
        indices = self.vocab.encode(text, add_special=True)
        return self._pad_to_length(indices)

    def encode_batch(self, texts: List[str]) -> torch.Tensor:
        """
        将多条文本批量编码为定长索引张量。

        Args:
            texts: 原始文本字符串列表。

        Returns:
            shape = (batch_size, max_seq_len) 的 LongTensor。
        """
        batch: List[List[int]] = []
        for text in texts:
            batch.append(self.vocab.encode(text, add_special=True))
        return self._pad_batch(batch)

    def get_batch(
        self,
        batch_size: int = 4,
        texts: Optional[List[str]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        获取一个 batch 的 (token_ids, embeddings, padding_mask)。

        若未指定 texts，则从内置语料中随机采样 batch_size 条文本。

        Args:
            batch_size: 批大小，仅在 texts 为 None 时生效。
            texts: 可选的自定义文本列表；若提供则忽略 batch_size。

        Returns:
            token_ids  : (batch_size, max_seq_len)      LongTensor
            embeddings : (batch_size, max_seq_len, d_model)  FloatTensor
            pad_mask   : (batch_size, max_seq_len)      BoolTensor
                         True 表示实际 token，False 表示 <pad> 填充位置。

        Notes
        -----
        - pad_mask 中 True=有效token, False=pad, 适用于后续 attention 的 mask 计算。
        - 若需适配 PyTorch 官方 MultiheadAttention 的 key_padding_mask 参数
          （True=忽略），可取 ~pad_mask。
        """
        if texts is None:
            texts = random.choices(self._corpus, k=batch_size)

        token_ids = self.encode_batch(texts)          # (B, L)
        embeddings = self.embedding(token_ids)        # (B, L, D)
        pad_mask = self._make_pad_mask(token_ids)     # (B, L)

        return token_ids, embeddings, pad_mask

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _pad_to_length(self, indices: List[int]) -> torch.Tensor:
        """将索引列表填充 / 截断至 max_seq_len。"""
        if len(indices) >= self.max_seq_len:
            return torch.tensor(indices[:self.max_seq_len], dtype=torch.long)
        padded = indices + [self.vocab.pad_idx] * (self.max_seq_len - len(indices))
        return torch.tensor(padded, dtype=torch.long)

    def _pad_batch(self, batch: List[List[int]]) -> torch.Tensor:
        """将变长索引列表批量填充为 (batch_size, max_seq_len) 张量。"""
        return torch.stack([self._pad_to_length(seq) for seq in batch])

    def _make_pad_mask(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        根据 token_ids 生成 padding mask。

        Args:
            token_ids: (batch_size, max_seq_len) LongTensor。

        Returns:
            (batch_size, max_seq_len) BoolTensor。
            True = 有效 token，False = <pad>。
        """
        return token_ids != self.vocab.pad_idx

    # ========================================================================
    # 工具方法
    # ========================================================================

    def add_corpus(self, texts: List[str], rebuild_vocab: bool = False) -> None:
        """
        向内部语料库追加文本。

        Args:
            texts: 要追加的文本列表。
            rebuild_vocab: 是否基于全部语料重建词表（以包含新增 token）。
        """
        self._corpus.extend(texts)
        if rebuild_vocab:
            self.vocab = Vocabulary()
            self.vocab.build(self._corpus)

    def summary(self) -> str:
        """返回数据模块的摘要信息字符串。"""
        lines = [
            "=" * 50,
            "TransformerDataModule 摘要",
            "=" * 50,
            f"  词向量维度 (d_model)  : {self.d_model}",
            f"  最大序列长度           : {self.max_seq_len}",
            f"  词表大小               : {self.vocab.vocab_size}",
            f"  内置语料条数           : {len(self._corpus)}",
            f"  嵌入层参数量           : {sum(p.numel() for p in self.embedding.parameters()):,}",
            "=" * 50,
        ]
        return "\n".join(lines)
