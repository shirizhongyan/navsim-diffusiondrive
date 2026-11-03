"""② 扩散步数-延迟基准: steps ∈ {1,2,3,5,10,20} × 单场景推理耗时"""
import os, time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
(ROOT / "exp/step_scan").mkdir(parents=True, exist_ok=True)
from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.agents.diffusiondrive.transfuser_agent import TransfuserAgent
from navsim.agents.diffusiondrive.transfuser_config import TransfuserConfig

root = Path(os.environ["OPENSCENE_DATA_ROOT"])
sf = SceneFilter(num_history_frames=4, num_future_frames=10, frame_interval=1,
                 has_route=True, max_scenes=60)
loader = SceneLoader(root / "navsim_logs/test", root / "sensor_blobs/test", sf,
                     sensor_config=SensorConfig.build_all_sensors())
tokens = loader.tokens
print(f"{len(tokens)} 个场景用于测速")

agent = TransfuserAgent(config=TransfuserConfig(),
    checkpoint_path=str(ROOT / "ckpt/hf_diffusiondrive/diffusiondrive_navsim_88p1_PDMS"), lr=6e-4)
agent.initialize()
model = agent._transfuser_model.cuda().eval()

results = {}
for steps in [1, 2, 3, 5, 10, 20]:
    os.environ["DD_STEP_NUM"] = str(steps)
    times = []
    builders = agent.get_feature_builders()
    with torch.no_grad():
        for i, tok in enumerate(tokens):
            agent_input = loader.get_agent_input_from_token(tok)
            features = {}
            for b in builders:
                features.update(b.compute_features(agent_input))
            features = {k: v.unsqueeze(0).cuda() for k, v in features.items()}
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            agent.forward(features)
            torch.cuda.synchronize()
            dt = (time.perf_counter() - t0) * 1000
            if i >= 10:  # 前 10 个预热不计
                times.append(dt)
    arr = np.array(times)
    results[steps] = (arr.mean(), np.median(arr))
    print(f"steps={steps:>2}: mean {arr.mean():6.1f} ms  median {np.median(arr):6.1f} ms  ≈ {1000/arr.mean():4.1f} FPS")

import json
json.dump({str(k): {"mean_ms": v[0], "median_ms": v[1]} for k, v in results.items()},
          open(ROOT / "exp/step_scan/latency.json", "w"), indent=2)
print("已存 exp/step_scan/latency.json")
