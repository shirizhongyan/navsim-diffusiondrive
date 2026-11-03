# 自驾实验归档、复核与重跑

## 归档解决了哪些缺口

2026-11-03 对照实际运行目录审查，原仓库尚不能完整承载 README 的加权微调结论：
缺少 `run_training_weighted.py`、`proxy_features.py`、v1/v2 逐场景评测、训练事件与实际环境记录。
这些材料现已补齐；修正了 PyTorch 2.8 学习率调度器调用、机器硬编码路径以及根目录训练入口的 Hydra 配置路径。

实际执行过的原始工具、上游源码补丁保留于 `results/training/runtime_tools/`、
`results/training/executed-source.patch`；便携入口不冒充逐字相同的历史脚本。
DiffusionDrive 上游提交为 `9b52ed0ec06b073d82d6f392ab084c7b301c8681`。

## 无 GPU 复核

```bash
python3 verify_archive.py
```

脚本从原始逐场景 CSV 重算 7 组完整 navtest（每组 12,146 场景），检查场景 token、
valid 状态、PDMS、修复／新增碰撞，以及归档文件 SHA-256。
不需要原始传感器、模型、Python 科学计算库或 SSH。

| 权重 | PDMS | NC<1 场景 | 修复基线碰撞扣分 | 新增碰撞扣分 |
| --- | ---: | ---: | ---: | ---: |
| 官方基线 | 88.0685 | 224 | 0 | 0 |
| 同管线人类轨迹 | 94.5514 | 0 | 224 | 0 |
| v1，epoch09 | 87.5205 | 234 | 15 | 25 |
| v2，epoch00 | 88.0127 | 223 | 8 | 7 |
| v2，epoch01 | 87.8845 | 229 | 8 | 13 |
| v2，epoch02 | 87.8995 | 218 | 16 | 10 |
| v2，epoch03 | 87.9573 | 218 | 13 | 7 |

全部排除 `average` 行。NC 是评分子项，不是事故类型标签；`NC=0.5` 也是扣分，
只数 `NC=0` 会漏掉 14 个基线场景。旧博客、图表保留为历史记录，涉及旧
225/458/636 计数与“16/225、无新增代价”的说法，以本页和重算 JSON 为准。
一组权重的一次完整评测不是多随机种子统计，也没有证实“噪声带内持平”。

## 环境与数据

Linux / Python 3.10，实测环境见 `results/training/environment-freeze.txt`。
这份 freeze 是实际环境快照而非跨平台已验证锁文件；安装首先遵循
`DiffusionDrive/README.md`、`DiffusionDrive/docs/install.md`，RTX 50 系使用 CUDA 12.8
构建的 PyTorch 2.8，而不是直接让旧 requirements 降级 torch。

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128
# 按上游说明安装其余依赖，并安装本仓库的本地源码：
python -m pip install -e ./DiffusionDrive --no-deps
source env.sh
export PYTHONPATH="$NAVSIM_DEVKIT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
```

数据下载遵循 OpenScene / NAVSIM / nuPlan 条款，下载脚本不替代其许可。
脚本会实际下载数百 GB，先检查空间、下载来源与目标路径：

```bash
bash download_all.sh
# 原始 navtrain 在清理前已经不存在；需要训练时重新下载：
bash download_navtrain_local.sh
```

navtest 传感器约 219 GiB，测试日志约 983 MiB，地图约 1.4 GiB。
navtrain 历史估计约 302 GB，不作为当前仍存在的数据。`download_all.sh` 同时获取
官方 NAVSIM 权重、轨迹锚点和 ResNet34 初始化权重；网络镜像失败时可改用官方来源。

## 权重归档

上游基础权重从 Hugging Face `hustvl/DiffusionDrive` 获取。
独有的 6 份训练 checkpoint（v1 最后一次、v2 四个 epoch、10 步 smoke）保存在
`research-archive-2026-11-03` GitHub Release。文件名与 SHA-256 见
`results/training/checkpoints.json`；smoke 仅为完整留档，不是推荐模型。

```bash
mkdir -p ckpt/research
gh release download research-archive-2026-11-03 \
  -R shirizhongyan/navsim-diffusiondrive -D ckpt/research
sha256sum -c ckpt/research/SHA256SUMS
```

Lightning checkpoint 使用 pickle 格式，只加载自己信任来源且通过哈希校验的文件。
本项目 v2 epoch02 对应“修复 16 个、也新增 10 个”的结果，不能把其他 epoch 权重与该成绩混用。

## 评测

```bash
source env.sh
bash run_eval.sh caching
bash run_eval.sh eval
CHECKPOINT="$PWD/ckpt/research/finetune_v2_epoch02.ckpt" bash run_eval.sh eval
NSCENES=1200 bash scan_steps.sh
```

步数扫描是子集，不是 12,146 场景完整评测。实际 Hydra 配置与逐场景 CSV 均在
`results/` 对应实验目录下；`results/archive_summary.json` 指明每组证据文件。
未在空机器重新下载全部数据并重训，因此这里只声称“源代码／证据／启动参数已验证”，
不声称完成了一次新的全流程数百 GB 复现。

## 加权微调

训练只使用 navtrain 代理特征和训练缓存，不使用 navtest 的失败标签直接采样。
TTC 是基于当前帧距离和相对纵向速度的代理量，不是实际未来碰撞时间。
转角特征来自示教未来轨迹，作为训练集采样依据，不是部署时可观测输入。

```bash
source env.sh
export PYTHONPATH="$NAVSIM_DEVKIT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
python proxy_features.py
# 或使用已经归档的 103,288 条代理特征：
mkdir -p exp
cp results/navtrain_proxy_features.csv exp/
python DiffusionDrive/navsim/planning/script/run_dataset_caching.py \
  train_test_split=navtrain agent=diffusiondrive_agent \
  experiment_name=training_cache worker=ray_distributed worker.threads_per_node=6
RECIPE=v2 bash train_weighted.sh
```

缓存命令采用上游独立 `run_dataset_caching.py` 入口；具体配置以所固定源码和历史 Hydra 配置为准，
需要完整 navtrain 和足够缓存空间。v1 学习率 `6e-5`、10 epoch；v2 `2e-5`、
4 epoch；batch 32。样本权重最大 5，分档 TTC、起步、转角、前方行人规则见脚本。

## 清理范围

发布和回读验证通过后，清理自驾原始数据、下载中间件、可重建特征／评测缓存、
旧本地 checkpoint 副本和自驾专属环境；先把独有训练权重保存到 Release。
保留本 Git 仓库、论文／学习对话和公开证据。不删除 `openvla/`、LIBERO、
具身模型权重、具身数据、其他项目环境或整个 agent-rl 目录。
实际删除清单与释放空间另存 `results/cleanup_receipt.json`。

2026-11-03 已完成清理：shunyuan3 移除 `dataset/`、`exp/`、`ckpt/`、`.venv/`，
所统计的原目录分配量合计约 238.01 GiB；本机旧归档移除 `exp/`、`ckpt/`、
`download_tmp/`，约 4.79 GiB。原目录分配量与文件系统实际可用空间增量不完全相同，
可能受共享底层文件、其他进程及文件系统记账影响，详见回执中的前后值。
服务器自驾代码与少量日志仍保留约 99 MiB，具身目录保持完整；本 Git 仓库中的
分析证据、可复现脚本和 GitHub Release 独有训练权重未删除。
