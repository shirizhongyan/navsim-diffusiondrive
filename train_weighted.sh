#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh
export PYTHONPATH="$NAVSIM_DEVKIT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
RECIPE="${RECIPE:-v2}"
case "$RECIPE" in
    v1) learning_rate=6e-5; epochs=10; experiment=finetune_hardmining_v1; export SAVE_EVERY_EPOCH=0 ;;
    v2) learning_rate=2e-5; epochs=4; experiment=finetune_v2_lr2e5; export SAVE_EVERY_EPOCH=1 ;;
    *) echo "RECIPE must be v1 or v2" >&2; exit 1 ;;
esac
checkpoint="${CHECKPOINT:-$E2E_ROOT/ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS}"
[[ -f "$checkpoint" ]]
[[ -f "$NAVSIM_EXP_ROOT/navtrain_proxy_features.csv" ]]
[[ -d "$NAVSIM_EXP_ROOT/training_cache" ]]
python run_training_weighted.py \
    agent=diffusiondrive_agent "experiment_name=$experiment" \
    train_test_split=navtrain split=trainval \
    "agent.checkpoint_path=$checkpoint" "agent.lr=$learning_rate" \
    "trainer.params.max_epochs=$epochs" dataloader.params.batch_size=32 \
    "cache_path=$NAVSIM_EXP_ROOT/training_cache" \
    use_cache_without_dataset=True force_cache_computation=False "$@"
