# NAVSIM / DiffusionDrive environment — source this before running anything
export E2E_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
export NUPLAN_MAP_VERSION="nuplan-maps-v1.0"
export NUPLAN_MAPS_ROOT="$E2E_ROOT/dataset/maps"
export NAVSIM_EXP_ROOT="$E2E_ROOT/exp"
export NAVSIM_DEVKIT_ROOT="$E2E_ROOT/DiffusionDrive"
export OPENSCENE_DATA_ROOT="$E2E_ROOT/dataset"
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
export PATH="$E2E_ROOT/.venv/bin:$PATH"
