#!/usr/bin/env bash
set -u
cd ~/e2e-driving && source env.sh
CKPT_DIR=$(ls -d $E2E_ROOT/exp/finetune_v2_lr2e5/*/lightning_logs/version_0/checkpoints)
for ep in epoch00 epoch01 epoch02 epoch03; do
  ln -sf $CKPT_DIR/$ep.ckpt $E2E_ROOT/ckpt/v2_$ep.pth
  echo "==== eval $ep $(date +%H:%M:%S)"
  python $NAVSIM_DEVKIT_ROOT/navsim/planning/script/run_pdm_score.py train_test_split=navtest \
    agent=diffusiondrive_agent worker=ray_distributed worker.threads_per_node=12 \
    agent.checkpoint_path=$E2E_ROOT/ckpt/v2_$ep.pth \
    experiment_name=finetune_v2_eval_$ep 2>&1 | grep -a "Final average"
done
echo ALL_EVAL_DONE
