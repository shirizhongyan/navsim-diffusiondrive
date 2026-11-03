#!/usr/bin/env bash
# 用法: bash run_eval.sh [caching|eval]
set -e
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh
CKPT="${CHECKPOINT:-$E2E_ROOT/ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS}"

if [ "${1:-all}" = "caching" ] || [ "${1:-all}" = "all" ]; then
  python $NAVSIM_DEVKIT_ROOT/navsim/planning/script/run_metric_caching.py \
    train_test_split=navtest cache.cache_path=$NAVSIM_EXP_ROOT/metric_cache
fi
if [ "${1:-all}" = "eval" ] || [ "${1:-all}" = "all" ]; then
  python $NAVSIM_DEVKIT_ROOT/navsim/planning/script/run_pdm_score.py \
    train_test_split=navtest \
    agent=diffusiondrive_agent \
    worker=ray_distributed \
    worker.threads_per_node=6 \
    agent.checkpoint_path=$CKPT \
    experiment_name=diffusiondrive_agent_eval
fi
