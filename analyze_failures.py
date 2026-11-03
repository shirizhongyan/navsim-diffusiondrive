"""失败 case 挖掘 + 可视化: 对 navtest 评测结果按子项归因, 渲染最差场景的 BEV 图"""
import os, sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import hydra
from hydra.utils import instantiate

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "exp/diffusiondrive_agent_eval/2026.09.14.19.36.40/2026.09.14.19.58.36.csv"
OUT = ROOT / "exp/failure_analysis"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV)
df = df[df["valid"] & (df["token"] != "average")].copy()
SUB = ["no_at_fault_collisions","drivable_area_compliance","time_to_collision_within_bound",
       "ego_progress","comfort","driving_direction_compliance"]

# ---- 1. 文本归因报告 ----
print(f"总场景 {len(df)}, 均分 {df['score'].mean():.4f}")
for c in SUB:
    n_bad = (df[c] < 1.0).sum()
    print(f"  {c:38s} 扣分场景 {n_bad:5d} ({n_bad/len(df)*100:4.1f}%)  均值 {df[c].mean():.4f}")

worst = df.nsmallest(10, "score")[["token","score"]+SUB]
worst.to_csv(OUT/"worst10.csv", index=False)
print("\n最差 10 个场景已写入", OUT/"worst10.csv")
print(worst[["token","score","no_at_fault_collisions","ego_progress"]].to_string(index=False))

# 各子项联合分布直方图(图形报告)
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, c in zip(axes.flat, SUB):
    ax.hist(df[c], bins=40, color="#59a14f", edgecolor="white")
    ax.set_title(c, fontsize=9); ax.set_xlim(0, 1.02)
fig.suptitle(f"DiffusionDrive navtest subscore distributions (PDMS={df['score'].mean():.4f})")
fig.tight_layout(); fig.savefig(OUT/"subscore_hist.png", dpi=120)
print("直方图:", OUT/"subscore_hist.png")
