#!/usr/bin/env bash
# NAVSIM navtest + maps + ckpt downloader (hf-mirror 版)
set -u
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DL=$ROOT/download_tmp
mkdir -p "$DL/sensors" "$ROOT/ckpt" "$ROOT/dataset/navsim_logs" "$ROOT/dataset/sensor_blobs"
HF=https://hf-mirror.com
OS=$HF/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1
cd $DL

step(){ echo "==== $(date +%H:%M:%S) $1"; }

# ---- 1. ckpt (小,优先) ----
step "ckpt (skip, done)"
true #
export HF_ENDPOINT=$HF HF_HUB_ENABLE_HF_TRANSFER=0
if [ -s $ROOT/ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS ]; then echo CKPT_OK; else \
$ROOT/.venv/bin/hf download hustvl/DiffusionDrive --include diffusiondrive_navsim_88p1_PDMS --local-dir $ROOT/ckpt/hf_diffusiondrive \
  && echo CKPT_OK || echo CKPT_FAIL; fi

# ---- 2. anchors (github release) ----
step "anchors (skip, done)"
true #
if [ -s $ROOT/ckpt/kmeans_navsim_traj_20.npy ]; then echo ANCHOR_OK; else \
  wget -c -q https://github.com/hustvl/DiffusionDrive/releases/download/DiffusionDrive_88p1_PDMS_Eval_file/kmeans_navsim_traj_20.npy \
  -O $ROOT/ckpt/kmeans_navsim_traj_20.npy && echo ANCHOR_OK || echo ANCHOR_FAIL; fi

# ---- 3. maps ----
step "maps"
if [ ! -f $ROOT/dataset/maps/nuplan-maps-v1.0.json ]; then
  wget -c -q $HF/datasets/pengxiang/nuplan_maps/resolve/main/nuplan-maps-v1.1.zip -O nuplan-maps-v1.1.zip \
  && unzip -q -o nuplan-maps-v1.1.zip \
  && mkdir -p $ROOT/dataset/maps && cp -r nuplan-maps-v1.0/. $ROOT/dataset/maps/ \
  && rm -rf nuplan-maps-v1.0 nuplan-maps-v1.1.zip && echo MAPS_OK || echo MAPS_FAIL
else
  echo MAPS_SKIP
fi
if [ ! -s "$ROOT/ckpt/resnet34.a1_in1k/pytorch_model.bin" ]; then
  "$ROOT/.venv/bin/hf" download timm/resnet34.a1_in1k \
    --include pytorch_model.bin --local-dir "$ROOT/ckpt/resnet34.a1_in1k" || exit 1
fi

# ---- 4. navtest metadata (logs, ~1GB) ----
step "metadata"
if [ ! -d $ROOT/dataset/navsim_logs/test ]; then
  wget -c -q $OS/openscene_metadata_test.tgz -O openscene_metadata_test.tgz \
  && tar -xzf openscene_metadata_test.tgz \
  && mv openscene-v1.1/meta_datas $ROOT/dataset/navsim_logs/test \
  && rm -rf openscene_metadata_test.tgz openscene-v1.1 && echo META_OK || echo META_FAIL
else
  echo META_SKIP
fi

# ---- 5. sensor blobs (相机+激光雷达, ~220GB, 6路并行) ----
step "sensors"
dl_one(){
  url=$1; f=$(basename $url); cd $DL/sensors
  [ -f "$f.done" ] && return 0
  wget -c -q "$url" -O "$f" && tar -xzf "$f" && rm -f "$f" && touch "$f.done" && echo "OK $f"
}
export -f dl_one; export DL
{
  for i in $(seq -w 0 31); do
    echo "$OS/openscene_sensor_test_camera/openscene_sensor_test_camera_${i}.tgz"
  done
  for i in $(seq -w 0 31); do
    echo "$OS/openscene_sensor_test_lidar/openscene_sensor_test_lidar_${i}.tgz"
  done
} | xargs -P 6 -I{} bash -c 'dl_one "$@"' _ {}
mv $DL/sensors/openscene-v1.1/sensor_blobs $ROOT/dataset/sensor_blobs/test 2>/dev/null || \
  cp -r $DL/sensors/openscene-v1.1/sensor_blobs $ROOT/dataset/sensor_blobs/test
echo SENSORS_DONE
step "ALL FINISHED"
