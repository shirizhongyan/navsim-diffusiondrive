"""渲染指定场景的相机图像(当前帧)"""
import os, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parent
TOKEN = sys.argv[1]
OUT = ROOT / "exp/failure_analysis"
OUT.mkdir(parents=True, exist_ok=True)

from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.visualization.plots import plot_cameras_frame

openscene_data_root = Path(os.environ["OPENSCENE_DATA_ROOT"])
sf = SceneFilter(tokens=[TOKEN], num_history_frames=4, num_future_frames=10, frame_interval=1, has_route=True)
loader = SceneLoader(openscene_data_root / "navsim_logs/test",
                     openscene_data_root / "sensor_blobs/test",
                     sf, sensor_config=SensorConfig.build_all_sensors())
scene = loader.get_scene_from_token(TOKEN)
fig, axes = plot_cameras_frame(scene, frame_idx=3)  # 3 = 当前帧
fig.savefig(OUT / f"cameras_{TOKEN}.png", dpi=130, bbox_inches="tight")
print("saved:", OUT / f"cameras_{TOKEN}.png")
