"""渲染指定场景的 BEV: 模型轨迹(红) vs 人类驾驶(绿)"""
import os, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import hydra
from hydra.utils import instantiate

ROOT = Path("~/e2e-driving")
TOKEN = sys.argv[1] if len(sys.argv) > 1 else "01d061d9a66451ea"
OUT = ROOT / "exp/failure_analysis"

from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.visualization.plots import plot_bev_with_agent
from navsim.agents.diffusiondrive.transfuser_agent import TransfuserAgent
from navsim.agents.diffusiondrive.transfuser_config import TransfuserConfig

openscene_data_root = Path(os.environ["OPENSCENE_DATA_ROOT"])
scene_filter = SceneFilter(tokens=[TOKEN], num_history_frames=4, num_future_frames=10, frame_interval=1, has_route=True)
scene_loader = SceneLoader(
    openscene_data_root / "navsim_logs/test",
    openscene_data_root / "sensor_blobs/test",
    scene_filter,
    sensor_config=SensorConfig.build_all_sensors(),
)
scene = scene_loader.get_scene_from_token(TOKEN)

agent = TransfuserAgent(config=TransfuserConfig(),
    checkpoint_path=str(ROOT/"ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS"), lr=6e-4)
agent.initialize()

fig, ax = plot_bev_with_agent(scene, agent)
ax.set_title(f"scene {TOKEN}  (red=model, green=human)")
fig.savefig(OUT/f"bev_{TOKEN}.png", dpi=140, bbox_inches="tight")
print("saved:", OUT/f"bev_{TOKEN}.png")
