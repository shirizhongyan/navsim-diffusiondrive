"""实验A: 从 navtrain 场景提取代理特征(无需传感器), 用于错题加权采样
特征定义(全部可从日志/标注计算):
  front_veh_dist : 前方最近车辆距离(m)
  min_ttc_proxy  : 历史帧中(前车距/相对速度)最小 TTC 估计(s), 越大越安全
  n_agents_30m   : 30m 内交通参与者数
  n_ped_15m      : 前方 15m 行人数
  turn_angle     : 人类未来轨迹总转角(rad), 大=转向/路口场景
  stat_restart   : 历史平均速度<0.5m/s 但人类未来前进>5m (静止起步场景)
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from multiprocessing import Pool

os.environ.setdefault('OPENSCENE_DATA_ROOT', str(Path.home()/'e2e-driving/dataset'))
from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig

def feats_of(scene):
    f = scene.frames[scene.scene_metadata.num_history_frames - 1]
    boxes, names = f.annotations.boxes, f.annotations.names
    vel = f.annotations.velocity_3d
    ego_xy = np.array([0.0, 0.0])  # 当前帧 ego 在原点
    out = dict(front_veh_dist=999.0, min_ttc_proxy=99.0, n_agents_30m=0,
               n_ped_15m=0, turn_angle=0.0, stat_restart=0)
    if len(boxes):
        xy = boxes[:, :2]
        dist = np.linalg.norm(xy - ego_xy, axis=1)
        out['n_agents_30m'] = int((dist < 30).sum())
        veh = (names == 'vehicle')
        # 前方扇区(|横向|<3m 纵向>0)最近车辆
        front = veh & (xy[:,0] > 0) & (np.abs(xy[:,1]) < 3.0)
        if front.any():
            d = dist[front].min()
            out['front_veh_dist'] = float(d)
            # TTC 粗估: 距离 / max(ego速度-前车纵向速度, eps)
            ego_v = f.ego_status.ego_velocity[0]
            lead_v = float(vel[front][dist[front].argmin()][0])
            rel = max(ego_v - lead_v, 0.1)
            out['min_ttc_proxy'] = float(d / rel)
        ped = (names == 'pedestrian') & (xy[:,0] > 0) & (np.abs(xy[:,1]) < 5.0) & (dist < 15)
        out['n_ped_15m'] = int(ped.sum())
    fut = scene.get_future_trajectory().poses
    if len(fut) > 1:
        heads = fut[:, 2]
        out['turn_angle'] = float(np.abs(np.unwrap(heads)[-1] - np.unwrap(heads)[0]))
    hist_v = np.linalg.norm([fr.ego_status.ego_velocity for fr in scene.frames[:4]], axis=1).mean()
    prog = np.linalg.norm(fut[-1,:2] - fut[0,:2]) if len(fut)>1 else 0
    out['stat_restart'] = int(hist_v < 0.5 and prog > 5.0)
    return out

def work(tok):
    try:
        scene = loader.get_scene_from_token(tok)
        r = feats_of(scene); r['token'] = tok
        return r
    except Exception:
        return None

if __name__ == '__main__':
    root = Path(os.environ['OPENSCENE_DATA_ROOT'])
    from omegaconf import OmegaConf
    from hydra.utils import instantiate
    _cfg = OmegaConf.load(str(Path.home()/'e2e-driving/DiffusionDrive/navsim/planning/script/config/common/train_test_split/scene_filter/navtrain.yaml'))
    sf = instantiate(_cfg)
    global loader
    loader = SceneLoader(root/'navsim_logs/trainval', root/'sensor_blobs/trainval', sf,
                         sensor_config=SensorConfig.build_no_sensors())
    toks = loader.tokens
    print(f'{len(toks)} scenes', flush=True)
    with Pool(32) as p:
        rows = [r for r in p.map(work, toks, chunksize=64) if r]
    df = pd.DataFrame(rows)
    df.to_csv(Path.home()/'e2e-driving/exp/navtrain_proxy_features.csv', index=False)
    print(df.describe().to_string())
