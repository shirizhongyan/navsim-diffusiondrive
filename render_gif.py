"""渲染场景 GIF: BEV 动画(车流动起来 + 模型/人类轨迹) 和 相机标注动画
用法: python render_gif.py <token>
"""
import os, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parent
TOKEN = sys.argv[1]
OUT = ROOT / "exp/failure_analysis"
OUT.mkdir(parents=True, exist_ok=True)

from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.visualization.plots import (
    plot_bev_frame, plot_cameras_frame_with_annotations, frame_plot_to_gif,
)
from navsim.visualization.config import TRAJECTORY_CONFIG
from navsim.agents.diffusiondrive.transfuser_agent import TransfuserAgent
from navsim.agents.diffusiondrive.transfuser_config import TransfuserConfig

root = Path(os.environ["OPENSCENE_DATA_ROOT"])
sf = SceneFilter(tokens=[TOKEN], num_history_frames=4, num_future_frames=10, frame_interval=1, has_route=True)
loader = SceneLoader(root / "navsim_logs/test", root / "sensor_blobs/test", sf,
                     sensor_config=SensorConfig.build_all_sensors())
scene = loader.get_scene_from_token(TOKEN)

agent = TransfuserAgent(config=TransfuserConfig(),
    checkpoint_path=str(ROOT / "ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS"), lr=6e-4)
agent.initialize()

cur = scene.scene_metadata.num_history_frames - 1  # 当前帧 idx
human = scene.get_future_trajectory().poses[:, :2]
model = agent.compute_trajectory(scene.get_agent_input()).poses[:, :2]

# 轨迹是"当前帧 ego 坐标系"下的, 转到全局再转到各帧 ego 系
def to_global(xy, pose):
    c, s = np.cos(pose[2]), np.sin(pose[2])
    R = np.array([[c, -s], [s, c]])
    return xy @ R.T + np.array([pose[0], pose[1]])

def to_local(xy_global, pose):
    c, s = np.cos(pose[2]), np.sin(pose[2])
    R = np.array([[c, s], [-s, c]])
    return (xy_global - np.array([pose[0], pose[1]])) @ R.T

pose_cur = scene.frames[cur].ego_status.ego_pose
human_g, model_g = to_global(human, pose_cur), to_global(model, pose_cur)

def bev_with_traj(scene, frame_idx):
    fig, ax = plot_bev_frame(scene, frame_idx)
    p = scene.frames[frame_idx].ego_status.ego_pose
    for traj_g, key in ((human_g, "human"), (model_g, "agent")):
        xy = to_local(traj_g, p)
        xy = np.concatenate([np.array([[0, 0]]), xy])
        cfg = TRAJECTORY_CONFIG[key]
        ax.plot(xy[:, 1], xy[:, 0], color=cfg["line_color"], alpha=cfg["line_color_alpha"],
                linewidth=cfg["line_width"], linestyle=cfg["line_style"])
    return fig, ax

indices = list(range(len(scene.frames)))
frame_plot_to_gif(str(OUT / f"bev_anim_{TOKEN}.gif"), bev_with_traj, scene, indices, duration=400)
print("saved:", OUT / f"bev_anim_{TOKEN}.gif")
frame_plot_to_gif(str(OUT / f"cam_anim_{TOKEN}.gif"), plot_cameras_frame_with_annotations, scene, indices, duration=400)
print("saved:", OUT / f"cam_anim_{TOKEN}.gif")
