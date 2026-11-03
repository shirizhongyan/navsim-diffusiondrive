"""实验A: 错题加权微调训练脚本
基于官方 run_training.py, 唯一改动: train DataLoader 用 WeightedRandomSampler。
权重来自 exp/navtrain_proxy_features.csv 的代理特征:
  TTC<1.5s x5 | TTC<3s x3 | 静止起步 x2 | 路口转向>0.5rad x2 | 前方行人 x1.5, 封顶 x5
用法:
  python run_training_weighted.py agent=diffusiondrive_agent experiment_name=finetune_hardmining \
    train_test_split=navtrain split=trainval \
    agent.checkpoint_path=$E2E_ROOT/ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS \
    agent.lr=6e-5 trainer.params.max_epochs=10 dataloader.params.batch_size=32 \
    cache_path=$NAVSIM_EXP_ROOT/training_cache use_cache_without_dataset=True force_cache_computation=False
"""
import os
from pathlib import Path
import logging

import hydra
import pandas as pd
import torch
from hydra.utils import instantiate
from omegaconf import DictConfig
from torch.utils.data import DataLoader, WeightedRandomSampler
import pytorch_lightning as pl

from navsim.agents.abstract_agent import AbstractAgent
from navsim.planning.training.dataset import CacheOnlyDataset
from navsim.planning.training.agent_lightning_module import AgentLightningModule

logger = logging.getLogger(__name__)
CONFIG_PATH = "config/training"
CONFIG_NAME = "default_training"

# ---- 采样权重规则 (2026-09-18 与用户确认) ----
W_TTC_HIGH = 5.0   # min_ttc_proxy < 1.5s
W_TTC_MID  = 3.0   # min_ttc_proxy < 3.0s
W_RESTART  = 2.0   # 静止起步
W_TURN     = 2.0   # 路口转向 (语义确认: 弯道几何是最大失败聚类)
W_PED      = 1.5   # 前方行人
W_CAP      = 5.0


def compute_sample_weights(tokens):
    csv = Path(os.environ["E2E_ROOT"]) / "exp/navtrain_proxy_features.csv"
    df = pd.read_csv(csv).set_index("token")
    weights = []
    n_boost = 0
    for tok in tokens:
        w = 1.0
        if tok in df.index:
            r = df.loc[tok]
            if r["min_ttc_proxy"] < 1.5:
                w = W_TTC_HIGH
            elif r["min_ttc_proxy"] < 3.0:
                w = W_TTC_MID
            if r["stat_restart"] == 1:
                w *= W_RESTART
            if r["turn_angle"] > 0.5:
                w *= W_TURN
            if r["n_ped_15m"] > 0:
                w *= W_PED
            w = min(w, W_CAP)
        if w > 1.0:
            n_boost += 1
        weights.append(w)
    logger.info(f"Weighted sampling: {n_boost}/{len(tokens)} samples boosted "
                f"({n_boost/len(tokens)*100:.1f}%), mean weight {sum(weights)/len(weights):.2f}")
    return weights


@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME, version_base=None)
def main(cfg: DictConfig) -> None:
    pl.seed_everything(cfg.seed, workers=True)
    logger.info(f"Path where all results are stored: {cfg.output_dir}")

    logger.info("Building Agent")
    agent: AbstractAgent = instantiate(cfg.agent)

    logger.info("Building Lightning Module")
    lightning_module = AgentLightningModule(agent=agent)

    assert cfg.use_cache_without_dataset, "本脚本只支持 cache-only 模式"
    train_data = CacheOnlyDataset(
        cache_path=cfg.cache_path,
        feature_builders=agent.get_feature_builders(),
        target_builders=agent.get_target_builders(),
        log_names=cfg.train_logs,
    )
    val_data = CacheOnlyDataset(
        cache_path=cfg.cache_path,
        feature_builders=agent.get_feature_builders(),
        target_builders=agent.get_target_builders(),
        log_names=cfg.val_logs,
    )

    weights = compute_sample_weights(train_data.tokens)
    sampler = WeightedRandomSampler(weights, num_samples=len(train_data), replacement=True)
    train_dataloader = DataLoader(train_data, **cfg.dataloader.params, sampler=sampler)
    val_dataloader = DataLoader(val_data, **cfg.dataloader.params, shuffle=False)
    logger.info("Num training samples: %d | Num validation samples: %d", len(train_data), len(val_data))

    logger.info("Building Trainer")
    trainer = pl.Trainer(**cfg.trainer.params, callbacks=lightning_module.get_training_callbacks())
    if not cfg.train_test_split.scene_filter.has_route:
        raise RuntimeError("has_route 必须为 True")

    logger.info("Starting Training")
    trainer.fit(lightning_module, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)


if __name__ == "__main__":
    main()
