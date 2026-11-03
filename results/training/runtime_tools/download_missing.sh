#!/usr/bin/env bash
# 补齐 0-9 分卷 (主脚本 seq -w 生成了 00-09 的 404 URL)
set -u
DL=/home/ps/e2e-driving/download_tmp
OS=https://hf-mirror.com/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1
mkdir -p $DL/sensors
dl_one(){
  url=$1; f=$(basename $url); cd $DL/sensors
  [ -f "$f.done" ] && return 0
  wget -c -q "$url" -O "$f" && tar -xzf "$f" && rm -f "$f" && touch "$f.done" && echo "OK $f"
}
export -f dl_one; export DL
{
  for i in 0 1 2 3 4 5 6 7 8 9; do
    echo "$OS/openscene_sensor_test_camera/openscene_sensor_test_camera_${i}.tgz"
    echo "$OS/openscene_sensor_test_lidar/openscene_sensor_test_lidar_${i}.tgz"
  done
} | xargs -P 4 -I{} bash -c 'dl_one "$@"' _ {}
echo MISSING_DONE
