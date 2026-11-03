#!/usr/bin/env bash
# navtrain 训练数据下载 (hf-mirror 版, 只要 current 帧, ~300GB → /data 盘)
set -u
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA="${TRAIN_DATA_ROOT:-$ROOT/dataset}"
DL="${TRAIN_DOWNLOAD_ROOT:-$ROOT/download_tmp_navtrain}"
mkdir -p $DL $DATA/navsim_logs $DATA/sensor_blobs/trainval
OS=https://hf-mirror.com/datasets/OpenDriveLab/OpenScene/resolve/main

step(){ echo "==== $(date +%H:%M:%S) $1"; }

# ---- 1. trainval 日志 (~14GB) ----
step "trainval metadata"
if [ ! -d $DATA/navsim_logs/trainval ]; then
  cd $DL
  wget -c -q $OS/openscene-v1.1/openscene_metadata_trainval.tgz -O meta.tgz \
  && tar -xzf meta.tgz \
  && mv openscene-v1.1/meta_datas/trainval $DATA/navsim_logs/trainval \
  && rm -rf meta.tgz openscene-v1.1 && echo META_OK || echo META_FAIL
else
  echo META_SKIP
fi

# ---- 2. navtrain current 传感器 32 分卷 (~300GB, 4 路并行) ----
step "navtrain_current sensors"
dl_one(){
  i=$1; cd $DL
  f=navtrain_current_${i}.tgz
  [ -f "$f.done" ] && return 0
  wget -c -q "$OS/navsim/navtrain_current_${i}.tgz" -O "$f" \
  && tar -xzf "$f" \
  && rsync -rq navtrain_current_${i}/ $DATA/sensor_blobs/trainval/ \
  && rm -rf "$f" navtrain_current_${i} && touch "$f.done" && echo "OK $f"
}
export -f dl_one; export DL DATA OS
seq 1 32 | xargs -P 4 -I{} bash -c 'dl_one "$@"' _ {}
step "ALL FINISHED"
