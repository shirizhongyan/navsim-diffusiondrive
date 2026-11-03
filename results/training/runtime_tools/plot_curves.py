import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from pathlib import Path

log = Path.home()/"e2e-driving/exp/finetune_hardmining_v1/2026.09.18.05.57.49/lightning_logs/version_0"
ea = EventAccumulator(str(log)); ea.Reload()
tags = ea.Tags()["scalars"]
print("可用 tag:", [t for t in tags if "epoch" in t])

def series(tag):
    if tag not in tags: return None
    ev = ea.Scalars(tag)
    return np.array([e.step for e in ev]), np.array([e.value for e in ev])

fig, axes = plt.subplots(2, 3, figsize=(16, 8))
panels = ["train/loss_epoch", "val/loss_epoch", "train/trajectory_loss_epoch",
          "val/trajectory_loss_epoch", "train/bev_semantic_loss_epoch", "val/agent_class_loss_epoch"]
for ax, tag in zip(axes.flat, panels):
    s = series(tag)
    if s is None:
        ax.set_title(f"{tag} (无数据)"); continue
    x, y = s
    ax.plot(x, y, "o-", color="#59a14f", lw=2)
    ax.set_title(tag.replace("_epoch",""), fontsize=10)
    ax.set_xlabel("epoch"); ax.grid(alpha=0.3)
fig.suptitle("finetune_hardmining_v1 (lr=6e-5, 10ep, weighted sampler)", fontsize=13)
fig.tight_layout()
out = Path.home()/"e2e-driving/exp/finetune_hardmining_v1/training_curves.png"
fig.savefig(out, dpi=130)
print("saved:", out)

# 逐 epoch 数值表
for tag in ["train/loss_epoch","val/loss_epoch","train/trajectory_loss_epoch","val/trajectory_loss_epoch"]:
    s = series(tag)
    if s: print(tag, np.round(s[1], 3).tolist())
