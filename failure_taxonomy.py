"""失败类型学: 按子项扣分签名归类 navtest 失败场景, 输出报告 + 各类代表场景 token"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT/"exp/diffusiondrive_agent_eval/2026.09.14.19.36.40/2026.09.14.19.58.36.csv")
df = df[df["valid"] & (df["token"] != "average")].copy()

NC, DAC, TTC, EP, DDC = ("no_at_fault_collisions","drivable_area_compliance",
    "time_to_collision_within_bound","ego_progress","driving_direction_compliance")

def categorize(r):
    cats = []
    if r[NC] < 1: cats.append("碰撞")
    if r[DAC] < 1: cats.append("驶出路面")
    if r[TTC] < 1 and r[NC] >= 1: cats.append("跟车过近(未撞)")
    if r[TTC] < 1 and r[NC] < 1: cats.append("碰撞前兆(跟车过近)")
    if r[EP] < 0.5: cats.append("停滞/蠕行")
    if r[DDC] < 1: cats.append("逆行方向")
    return cats

df["cats"] = df.apply(categorize, axis=1)
df["n_hard_fail"] = (df[[NC,DAC,TTC]] < 1).sum(axis=1)

report = ["# DiffusionDrive navtest 失败类型学报告", f"总场景 {len(df)}, PDMS {df['score'].mean():.4f}", ""]
report.append("## 一、按扣分签名归类(可重叠)")
sigs = {
    "碰撞 (NC<1)": df[NC] < 1,
    "驶出路面 (DAC<1)": df[DAC] < 1,
    "跟车过近 (TTC<1)": df[TTC] < 1,
    "停滞/蠕行 (EP<0.5)": df[EP] < 0.5,
    "逆行 (DDC<1)": df[DDC] < 1,
    "多项硬失败 (≥2项)": df["n_hard_fail"] >= 2,
    "完全 0 分": df["score"] == 0,
}
for name, mask in sigs.items():
    report.append(f"- {name}: {mask.sum()} 场景 ({mask.sum()/len(df)*100:.2f}%)")

report += ["", "## 二、各类代表场景(供人工看图确认)"]
reps = {}
queries = {
    "collision": df[df[NC] < 1].nsmallest(3, "score"),
    "offroad": df[(df[DAC] < 1) & (df[NC] >= 1)].nsmallest(3, "score"),
    "closefollow": df[(df[TTC] < 1) & (df[NC] >= 1) & (df[DAC] >= 1)].nsmallest(3, "score"),
    "stagnation": df[(df[EP] < 0.3) & (df[NC] >= 1)].nsmallest(3, "score"),
}
for k, sub in queries.items():
    reps[k] = sub["token"].tolist()
    report.append(f"### {k}")
    for _, r in sub.iterrows():
        report.append(f"- {r['token']}  score={r['score']:.3f} NC={r[NC]:.2f} DAC={r[DAC]:.2f} TTC={r[TTC]:.2f} EP={r[EP]:.2f}")

out = ROOT/"exp/failure_analysis/taxonomy.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(report))
print("\n".join(report[:20]))
import json; json.dump(reps, open(ROOT/"exp/failure_analysis/taxonomy_reps.json","w"))
print("\nreps:", {k: len(v) for k,v in reps.items()})
