#!/usr/bin/env bash
# ② 扩散步数-精度权衡扫描: 对 steps ∈ {1,2,3,5,10,20} 在 navtest 子集上测 PDMS
set -u
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh
CKPT=$E2E_ROOT/ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS
NSCENES=${NSCENES:-1200}
OUT=$E2E_ROOT/exp/step_scan
mkdir -p $OUT

for STEPS in 1 2 3 5 10 20; do
  echo "==== steps=$STEPS  $(date +%H:%M:%S)"
  DD_STEP_NUM=$STEPS python $NAVSIM_DEVKIT_ROOT/navsim/planning/script/run_pdm_score.py \
    train_test_split=navtest \
    train_test_split.scene_filter.max_scenes=$NSCENES \
    agent=diffusiondrive_agent \
    worker=ray_distributed \
    worker.threads_per_node=6 \
    agent.checkpoint_path=$CKPT \
    experiment_name=step_scan/steps_$STEPS 2>&1 | tail -3
done
echo "==== ALL DONE, 汇总:"
python - <<'PY'
import pandas as pd, glob, os
rows=[]
for d in sorted(glob.glob("exp/step_scan/steps_*/*"), key=os.path.getmtime):
    csvs=[f for f in glob.glob(d+"/*.csv") if "cache" not in f]
    for c in csvs:
        df=pd.read_csv(c); df=df[df["valid"]]
        steps=d.split("steps_")[1].split("/")[0]
        rows.append((int(steps), len(df), df["score"].mean(),
                     df["no_at_fault_collisions"].mean(), df["time_to_collision_within_bound"].mean(),
                     df["ego_progress"].mean()))
rows=sorted(set(rows))
print(f"{'steps':>5} {'scenes':>7} {'PDMS':>8} {'NC':>7} {'TTC':>7} {'EP':>7}")
for r in rows: print(f"{r[0]:>5} {r[1]:>7} {r[2]:>8.4f} {r[3]:>7.4f} {r[4]:>7.4f} {r[5]:>7.4f}")
pd.DataFrame(rows, columns=["steps","scenes","pdms","nc","ttc","ep"]).to_csv("exp/step_scan/summary.csv", index=False)
PY
