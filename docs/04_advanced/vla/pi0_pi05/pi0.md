---
title: "Pi0"
description: "Pi0 视觉语言动作模型从 LeRobot 训练、OELLM2.0 量化编译到 RDK S600 板端部署运行的完整链路与问题解决方法。"
sidebar_position: 2
---

# Pi0


## 流程概览

```text
训练
   pi0_base  (HF 预训练)
        │  finetune  (v3.0 数据集, 30 fps)
        ▼
   checkpoints/030000/pretrained_model  (bf16, chunk=50, 绝对动作)

        │
        ▼
量化 + 编译(oe_llm_s600/pi0_conver/)
   float_eval  → 浮点基线 / 参考 dump
   calib       → fake-quant 权重 (pi0 无 time-mod LUT)
   calib_eval  → 伪量化精度 (校准集)
   compile     → 3× HBM (w8 nash-p)

        │
        ▼
板端部署与运行
   3× HBM + norm_stats_runtime.json + tokenizer/
   服务端 (vla_sdk_demo) + 客户端 (vla_robot)
```

- 模型：PaliGemma(gemma_2b) + Gemma 动作专家(gemma_300m)，3 路相机 + 14 维 state/action（pad 32），chunk=50，10 步去噪。
- 量化：int8 权重（w8）/ 动作专家 W8A16，编译为 nash-p HBM。
- pi0 模型/流程代码在 pi0_pkg，通过运行时注册 + monkey-patch 接入框架。


## 运行效果

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/pi0-effect.mp4" type="video/mp4" />
 您的浏览器不支持 video 标签。
</video>



## 获取工具包

```shell
wget https://archive.d-robotics.cc/downloads/rdk_demo/rdk_s600_demo/pi0_toolkit.tar.gz
```

## 训练

### 环境准备

| 用途 | conda 环境 | 说明 |
| :--- | :--- | :--- |
| 训练 | lerobot | <ul><li>RTX 5090</li><li>CUDA 13.3</li><li>Python 3.12</li><li>torch 2.11</li><li>lerobot 0.6.2（editable）</li></ul> |

- 基础环境搭建完成之后，下拉 lerobot 代码，安装依赖：

  ```bash
  #下拉 lerobot 代码
  git clone https://github.com/huggingface/lerobot.git

  pip install -e ".[core_scripts]"  # For robot workflows (recording, replaying, calibrate)
  pip install -e ".[training]"      # For training policies
  pip install -e ".[all]"     # Everything (all policies, envs, hardware, dev tools)
  ```

- 数据集格式：训练用 v3.0（`CODEBASE_VERSION=v3.0`），v2.1 需先转 v3.0（`convert_dataset_v21_to_v30.py`）。v2.1/v3.0 的目录结构对照见 [数据集格式说明](#数据集格式说明-v21-vs-v30)。本地数据转换指令如下：

  ```bash
  python lerobot/src/lerobot/scripts/convert_dataset_v21_to_v30.py  \
      --repo-id=xxx \
      --root=待转换数据路径  \
      --push-to-hub=false
  ```
    :::warning 注意

    - 训练依赖两份 Hugging Face 资源：

      - 预训练权重 `lerobot/pi0_base`，以及其 `policy_preprocessor.json` 中 `tokenizer_name` 指向的 tokenizer `google/paligemma-3b-pt-224`。可以访问 Hugging Face、且训练时不设置 `HF_HUB_OFFLINE=1` 时，不必提前下载，`lerobot-train` 会按仓库名自动拉取。下方训练命令带有 `HF_HUB_OFFLINE=1`，需要先完成本地准备。

      - `google/paligemma-3b-pt-224` 是 gated 模型，下载前需要先授权：登录 [Hugging Face](https://huggingface.co)，打开 [google/paligemma-3b-pt-224](https://huggingface.co/google/paligemma-3b-pt-224)，点击 Acknowledge license 同意 Gemma 使用许可（同意后立即生效），再执行 `hf auth login`。

    - 网络较差，或训练命令带有 `HF_HUB_OFFLINE=1`（只读本地文件，不再访问 Hugging Face）时，在 `lerobot` 目录下提前下载。`./pi0_base` 作为 `--policy.pretrained_path`。下载完成后，把 `pi0_base/policy_preprocessor.json` 里的 `tokenizer_name` 改为 `./paligemma-3b-pt-224`。

      ```bash
      cd lerobot
      hf download lerobot/pi0_base --local-dir ./pi0_base
      hf download google/paligemma-3b-pt-224 --local-dir ./paligemma-3b-pt-224
      ```

    :::

- 若训练时欲通过 wandb 查看模型训练情况，可先登录：

  ```bash
  wandb login YOUR_API_KEY
  ```

### 训练命令

```bash
#启动lerobot环境
cd lerobot
conda activate lerobot

#从 pi0_base 微调（数据集若需要重映射则使用rename_map）
HF_HUB_OFFLINE=1 lerobot-train \
    --dataset.repo_id=D-Robotics/fold_the_towel_remap_v3 \
    --dataset.root=<...>/fold_the_towel_remap_v3 \
    --policy.type=pi0 \
    --output_dir=./outputs/pi0_training \
    --job_name=pi0_training \
    --policy.pretrained_path=./pi0_base \
    --policy.compile_model=true \
    --policy.gradient_checkpointing=true \
    --policy.dtype=bfloat16 \
    --policy.freeze_vision_encoder=false \
    --policy.train_expert_only=false \
    --policy.push_to_hub=false \
    --steps=30000 \
    --policy.device=cuda \
    --batch_size=32 \
    --rename_map '{"state":"observation.state","head_cam":"observation.images.head_cam",
"left_cam":"observation.images.left_cam","right_cam":"observation.images.right_cam"}'

# 若需断点重训，可参考一下指令：
HF_HUB_OFFLINE=1 lerobot-train \
  --config_path=outputs/pi0_training/checkpoints/030000/pretrained_model \
  --resume=true --steps=60000 --dataset.eval_split=0.05 --eval_steps=1000
```

**关键配置**

**train_config.json** / **config.json**

| 项 | 值 |
| :--- | :--- |
| policy | pi0（gemma_2b + gemma_300m） |
| batch | 32 |
| steps | 30000 |
| lr | AdamW 2.5e-5<br />cosine + warmup 1000<br />decay 30000 |
| dtype | bfloat16<br />compile_model=true<br />compile_mode=max-autotune |
| freeze | true |
| train_expert_only | true |
| chunk | 50 |
| action / state | 输出 14 维（pad 32）；state 14 维（pad 32） |
| 归一化 | ACTION/STATE=MEAN_STD<br />VISUAL=IDENTITY |
| tokenizer | tokenizer_max_length=48 |
| 部署相关 | type=pi0<br />chunk_size=50<br />n_action_steps=50<br />num_inference_steps=10<br />compile_model=true<br />image_resolution=\[224,224\]<br />use_relative_actions=false<br />control_fps=30 |

**训练资源与耗时**

| 项 | 值 |
| :--- | :--- |
| 机器 | 1× NVIDIA RTX 5090 32GB（32607 MiB，驱动 610.57.04）+ Intel i9-14900KF（32 线程） |
| GPU 显存占用 | ~10.5 GB |
| batch | 32 |
| 精度 | bfloat16 |
| 显存优化 | gradient_checkpointing=true<br />freeze_vision_encoder=true<br />train_expert_only=true<br />compile_model=true（max-autotune） |
| 可学习参数 | 578M（仅 action expert 解冻） |
| 单步耗时 | ~1.92 s/step |
| 含 eval/保存的实测吞吐 | ~2.30 s/step |
| 训练步数 | 30000 |
| 数据时长 | 35s |
| 数据数量 | 300 条 |
| 该段耗时 | ≈ 16.3 h |

### 数据集格式说明 v2.1 vs v3.0

:::info 说明

训练环境 lerobot（0.6.2，CODEBASE_VERSION=v3.0）只能读 v3.0。
:::

**v2.1 — fold_the_towel**

```text
.
├── meta/
│   ├── info.json              codebase_version = "v2.1"
│   ├── tasks.jsonl            {"task_index":0,"task":"Fold the towel from bottom to top twice, then from right to left."}
│   ├── episodes.jsonl         {"episode_index","tasks","length"}
│   ├── episodes_stats.jsonl   {"episode_index","stats":{feature:{min,max,mean,std,count}}}
│   └── modality.json          state/action/endpose/... 的分段索引
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet     ← 一 episode 一文件（共 320 个）
│       └── ...
└── videos/
    └── chunk-000/
        ├── head_cam/episode_000000.mp4
        ├── left_cam/episode_000000.mp4
        └── right_cam/episode_000000.mp4
```

**v3.0 — fold_the_towel_v3**

```text
.
├── meta/
│   ├── info.json              codebase_version = "v3.0"
│   ├── tasks.parquet          task_index | task
│   ├── stats.json             聚合 stats
│   └── episodes/
│       └── chunk-000/
│           └── file-000.parquet      ← 一行一 episode（data/video 索引 + from/to_ts + length + 各 feature 的 stats 列）
├── data/
│   └── chunk-000/
│       ├── file-000.parquet          ← 按 data_files_size_in_mb 聚合
│       └── ...
└── videos/
    ├── head_cam/chunk-000/file-000.mp4     ← video_key 提到 chunk 之前，按 video_files_size_in_mb 聚合
    ├── left_cam/chunk-000/file-000.mp4
    └── right_cam/chunk-000/file-000.mp4
```

**关键差异**

| 项 | v2.1 | v3.0 |
| :--- | :--- | :--- |
| data | 一个 episode 对应一个文件 | 多个 episode 聚合成一个文件 |
| video | 一个 episode 对应一个 video 文件 | 多个 episode 聚合成一个 video 文件 |
| 逐 episode 元数据 | episodes.jsonl + episodes_stats.jsonl | meta/episodes/chunk-XXX/file-XXX.parquet |
| task | tasks.jsonl | tasks.parquet |
| info.json | 无 per-feature fps、有 total_videos/total_chunks | 每个 feature 带 fps、有 data_files_size_in_mb |
| modality.json | 有 | 无 |

:::warning 注意

- 用 v2.1 数据集直接训练时，lerobot 0.6.2 会抛出 `BackwardCompatibilityError`。按 [环境准备](#环境准备) 中的命令先转成 v3.0。
- v2.1 和 v3.0 的特征名都是扁平名（如 `head_cam`、`state`），策略需要的是 `observation.images.*` 和 `observation.state`。训练时加上 `--rename_map`，映射示例见 [训练命令](#训练命令)。
- `info.json.features.*.info.video.codec` 为 `av1` 时，解码依赖 `ffmpeg`。需在训练机安装 `ffmpeg`，并确认它在 `PATH` 中。

:::

## 量化编译

### 环境准备

```bash
conda create -n oellm python=3.10 -y
pip install torch==2.8.0+cu128 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install $SDK/package/host/*.whl          # horizon / hbdk / hbm
pip install -r $SDK/llm_compression/requirements.txt
pip install --force-reinstall setuptools==80.10.2

# 创建 pi0_conver文件夹，量化所需文件以及生成产物都放在 pi0_conver
mkdir oe_llm_s600/pi0_conver
```

量化包 `pi0_toolkit/quantize/pi0_pkg/`

| 文件 | 作用 |
| :--- | :--- |
| model.py | Pi0Config + Pi0GemmaExpert（state_proj / action_time_mlp / 标准 RMSNorm） |
| process_utils.py | 带 state 的去噪循环 + 专家 attention mask/position_ids（_SUFFIX_STATE_TOKENS=1） |
| pi0_model.py | Pi0 QModel（@MODEL_REGISTRY 运行时注册；get_qconfig_setting("action") 定义量化方案） |
| float_model.py | Pi0FloatModel + build_pi0_float_model |
| patch.py | monkey-patch vla_eval（eval dump 传 state、HbmExecutor.\_run_expert state 归一化+fp16、suffix state token 的 mask/pos） |
| run.py | 统一入口：float_eval / calib / calib_eval / compile |

### 数据与模型准备

用 `pi0_toolkit/tool/prep_pi0.py` 一个脚本搞定：模型目录+ 校准数据 + `norm_stats_runtime.json` + 量化用需配置。

```bash
# 使用 lerobot 环境 (lerobot 0.6.2, 读 v3.0)
conda activate lerobot

python3 tool/prep_pi0.py \
  --ckpt-dir     <model_path xxx/checkpoints/xxxx> \
  --dataset-root <lerobot_v3data_path lerobot_dataset/xxx> \
  --output-dir   oe_llm_s600/pi0_conver \
  --num-samples  30
```

<div className="markdown-table-scroll">
<table>
  <thead>
    <tr align="left">
      <th colSpan={2}>产物</th>
      <th>说明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowSpan={3}>模型目录</td>
      <td>`<output-dir>/model_<step>/config.json`</td>
      <td>Pi05Config 架构常量：max_token_len=200、无 uses_state</td>
    </tr>
    <tr>
      <td>`<output-dir>/model_<step>/model.safetensors`</td>
      <td>由原生 ckpt 自动去 model. 前缀生成</td>
    </tr>
    <tr>
      <td>`<output-dir>/model_<step>/paligemma_tokenizer.model`</td>
      <td>tokenizer 软链（默认从 --ckpt-dir 自动定位）</td>
    </tr>
    <tr>
      <td rowSpan={4}>校准数据</td>
      <td>`<output-dir>/pi05_calib_image/{sid}/image_{0,1,2}.jpg`</td>
      <td>head / left / right（640×480，quality 95）</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi05_action_calib_data/{sid}/state.npy`<br />`action.npy`<br />`x_t.npy`</td>
      <td>\[14\] raw + \[50,32\] flow 噪声</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi05_prompt.json`</td>
      <td>\[\{"text": ...\} x N\]（默认读数据集 tasks）</td>
    </tr>
    <tr>
      <td>`<output-dir>/norm_stats.json`</td>
      <td>actions 的 mean/std/q01/q99（全量统计）</td>
    </tr>
    <tr>
      <td>板端 norm</td>
      <td>`<output-dir>/norm_stats_runtime.json`</td>
      <td>state + actions 的 mean/std/q01/q99（板端运行时用）</td>
    </tr>
    <tr>
      <td rowSpan={2}>量化 yml</td>
      <td>`<output-dir>/pi0.yml`</td>
      <td>calib / calib_eval / compile 用</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi0_float.yml`</td>
      <td>float_eval 专用：已去 evaluation.calib_ckpt_load_path（否则 torch_eval 会当成 calib_eval）</td>
    </tr>
  </tbody>
</table>
</div>

- 采样约定：对数据集全局帧等距采集，相机序固定 head→left→right。action/state 存 raw 物理量。
- --ckpt-dir 是输入（原生 lerobot 模型目录）。
- --model-dir 是输出（转换后的 llm_compression 目录，默认 \<output-dir>/model_\<step>）。
- model. 前缀去除在脚本内完成。


### 量化编译

在 `pi0_conver/` 下启动

```bash
#使用 oellm 环境
conda activate oellm

cd oe_llm_s600/pi0_conver

export PYTHONPATH="<D-Robotics_LLM_S600_2.0.0-Beta_SDK_path>:<D-Robotics_LLM_S600_2.0.0-Beta_SDK_path>/llm_compression/lightcompress:oe_llm_s600/pi0_conver"

# 将 run.py和 pi0_pkg 放到 oe_llm_s600/pi0_conver 下，脚本与 pkg 包见 pi0_toolkit
python run.py float_eval  --config_path pi0_float.yml  # 1) 浮点基线 + 参考 dump
python run.py calib   --config_path pi0.yml     # 2) 校准（生成 calib_ckpt/）
python run.py calib_eval   --config_path pi0.yml # 3) 伪量化精度（yml 里 calib_ckpt_load_path=./calib_ckpt）
python run.py compile   --config_path pi0.yml   # 4) 编译 HBM（纯 CPU，lm 约 2~3h）
```

`pi0.yml` 关键项：

```yaml
model:      {model_name: Pi0, model_path: .../model_060000, model_list: [visual,lm,action],
             model_dtype: bfloat16, max_token_len: 48, enable_time_mod_lut: false}
calibration:{dataset_type: vla_dataset, vla_image_path/vla_action_calib_data/vla_prompt_path: ...,
             calibration_step: 30, calib_ckpt_save_path: ./calib_ckpt}
evaluation: {norm_stats_path: .../norm_stats.json, eval_stages: [calib], dump_dir: ./eval_dump}
compile:    {hbm_save_path: ./compile, calib_ckpt_load_path: ./calib_ckpt, opt_level: 2, enable_hpc: true, skip_embed_tokens: true, skip_lm_pd_split: true, lm:   {enable_hpc: false, core_num: 4},          # lm 关 HPC（(256*3+48)%32 问题，见「数据/配置配比」）
action:{enable_hpc: true,  core_num: 4}}         # action 开 HPC
```

量化方案（pi0_model.py::get_qconfig_setting("action")）：

- 默认：Linear qint16 in / qint8 w / fp16 out。qk/sv matmul qint16×qint16。norm/add/cat/gate fp16。
- pi0 独有且默认被量化的模块：state_proj、action_time_mlp_in、action_time_mlp_out。
- model.action_w16=true → action 专家权重用 qint16（W16A16）而非 qint8（W8A16）。

### 产物

| 文件 | 部件 | 大小 |
| :--- | :--- | :--- |
| xxxx_vision_224x224_w8_nash-p_corenum_1.hbm | SigLIP | ~487 MB |
| xxxx_llm_action_horizon_50_w8_nash-p_corenum_4.hbm | Gemma-2B LM | ~3.45 GB |
| xxxx_action_horizon_50_w8_nash-p_corenum_4.hbm | Gemma-300M 动作专家 | ~463 MB |

- 量化精度：模型精度指标参见 [量化精度](#量化精度)，量化模型精度查验与调优见 OELLM2.0 手册「精度评测」章节，此处不展开。
- 编译耗时（Intel Core i9-14900KF）：visual ~23min + lm ~1h58min + action ~24min ≈ 2h46min。


## 板端部署与运行

把 SDK 放到板端，重点关注 `D-Robotics_LLM_S600_2.0.0-Beta_SDK/oellm_runtime/examples/vla_demo/pi0`，运行前需执行以下命令给 `vla_sdk_demo` 赋执行权限：`chmod +x vla_sdk_demo`

### 运行所需文件

```text
pi0/
├── xxxx_{vision,llm,action}_*.hbm             # 阶段二产物，三个模型
├── norm_stats.json                            # 板端运行时 norm stats（含 state+actions，由prep_pi0生成）
├── tokenizer.json / tokenizer_config.json     # 位于paligemma-3b-pt-224下
├── paligemma_tokenizer.model                  # paligemma-3b-pt-224下，tokenizer.model重命名
├── pi0_config.json                            # oellm 模型配置（oellm_runtime/examples/vla_demo/pi0下）
└── demo.json                                  # demo 配置 (network, 127.0.0.1:30005, oellm_runtime/examples/vla_demo/pi0下)
```

### 运行时配置参考

**pi0_config.json**

```jsonc
{
  "runtime_type": "Pi0Sdk",
  "model": {
    "version": "0",
    "denoise_num": 10,
    "work_path": "/root/VLA/pi0",
    "model_runner": {
      "visual": "xxxx_vision_224x224_w8_nash-p_corenum_1.hbm",
      "lm": "xxxx_llm_action_horizon_50_w8_nash-p_corenum_4.hbm",
      "action": "xxxx_action_horizon_50_w8_nash-p_corenum_4.hbm"
    },
    "backends": {
      "visual": [1, 2, 3],
      "lm": [1, 2, 3, 4],
      "action": [1, 2, 3, 4]
    },
    "state_size": 14,
    "euler_step": true,
    "use_rtc": true
  },
  "rtc": {
    "execution_horizon": 15,
    "leftover_count": 10,
    "inference_delay": 9,
    "max_guidance_weight": 5.0,
    "prefix_attention_schedule": "linear",
    "control_frequency": 30.0
  },
  "interface": {
    "action_horizon": 50,
    "raw_state_size": 14,
    "raw_action_size": 14,
    "image_mask": [true, true, true]
  },
  "processing": {
    "preproc": true,
    "postproc": true,
    "filter": {
      "type": "none",
      "fs": 15,
      "mask": [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
      "cutoff_hz": 1.0,
      "max_velocity": []
    },
    "use_absolute_action": true,
    "use_quantiles_norm": false,
    "delta_action_mask": [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
    "inject_state": false
  },
  "dfx": {
    "verbose": false,
    "dump": false,
    "dump_per_chunk": false,
    "dump_dir": "./output/",
    "stub_dir": "./stub/"
  }
}
```

**pi0_network_demo.json**

```jsonc
{
  "default_mode": "network",               // ← 使用网络推理方式
  "modes": ["local", "network"],
  "io": {"input_dir": "input", "output_dir": "output", "multi_chunk": false},
  "demo": {"infer_nums": 1, "image_count": 3, "language_count": 1, "state_count": 1},
  "network": {"server_ip": "127.0.0.1", "server_port": 30005, "timeout": 120}  // ← 关注 ip 与端口号
}
```

:::info 说明

- state 归一化在 host 侧：state=(state-mean)/std（用 norm_stats.json 的 state），HBM 内只做 state_proj。
- 输入图：可发 640×480 交给板端 resize（板端 ResizeWithPadToBuffer 非抗锯齿，与训练 torch 一致）。
- 运行时端口：config/demo.json（server_port=30005）。

:::

### 开环测试

不开硬件/遥控，用 GT 观测（图像 + state）逐步喂板端 HBM，把预测动作与 GT 对比。板端脚本 `pi0_toolkit/deploy/openloop_infer_piper.py`（+ 同目录 `plot_openloop_npz.py`，跑完自动出图）。

**数据获取（训练机侧）**

用 `pi0_toolkit/tool/extract_episodes_v3.py` 从 v3.0 数据集抽取指定 episode：

```bash
conda activate lerobot
# 抽 episode 0/3/5，每个 episode 每 30 帧一条（≈ 每个 chunk 起点）
python3 extract_episodes_v3.py --episodes 0 3 5 --stride 30 -o <out>
# 每个 episode 均匀抽 20 条：加 --num-per-episode 20
```

产出 `openloop_infer_piper.py --eval-data` 需要的布局：

```text
<out>/calib_image/<sid>/image_{0,1,2}.jpg        # head_cam, left_cam, right_cam
<out>/action_calib_data/<sid>/state.npy          # [14] raw
<out>/action_calib_data/<sid>/action.npy         # [14] GT (chunk step0, raw)
<out>/action_calib_data/<sid>/x_t.npy            # [50,32]（板端不用）
<out>/prompt.json · norm_stats.json · manifest.json
```

**板端开环**

将上一步抽取的数据拷到板端：

```bash
# 用系统 python3 建独立 venv（aarch64；有网即可）
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy pillow pyarrow matplotlib opencv-python-headless
# ffmpeg/ffprobe 需在 PATH（板端一般自带 /usr/bin/ffmpeg；否则 apt-get install -y ffmpeg）
# 自检：
python -c "import numpy,PIL,pyarrow,matplotlib; print('deps ok')"
```

```bash
python3 openloop_infer_piper.py --model-dir <model_path>  --eval-data <eval_data_path> --model <pi0/pi05>
```

:::warning 注意

- --model pi0：--model 默认 pi05。用 pi0 HBM + pi05 预设会报 \[layout\] suffix_pad=1 invalid ... suffix layout mismatch with HBM（version/suffix 不匹配）。
- --model-dir 决定读哪个目录的 3 个 .hbm。norm_stats 默认取 --model-dir/norm_stats.json，必须含 state（缺则--norm-stats \<含 state 的文件>）。
- 结果：跑完自动出 \*_trajectories.png / \*_frame_mae.png / \*_perdim_mae.png。

:::

![板端开环测试结果：Calib openloop: CT action vs pred (chunk step 0) 各关节 GT 动作与预测动作对比曲线](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/pi0-pi05-openloop-trajectories.png)

### 真机运行

在板端启动 pi0 runtime。`--mode network` 时，runtime 作为 TCP client，主动连接客户端监听的 `30005` 端口：

```bash
# pi0 (RTC)
cd D-Robotics_LLM_S600_2.0.0-Beta_SDK/oellm_runtime/examples/vla_demo/pi0
export LD_LIBRARY_PATH=<D-Robotics_LLM_S600_2.0.0-Beta_SDK/oellm_runtime/lib>:$PWD/dist:${LD_LIBRARY_PATH:-}
export HB_DNN_USER_DEFINED_L2M_SIZES=6:6:6:6
./dist/vla_sdk_demo \
  --oellm_config <pi0_config_json_path> \
  --demo_config  <demo_json_path> \
  --mode network
```

客户端（`pi0_toolkit/deploy/vla_robot` 交付包：纯 Python、双臂 piper_sdk 直控 CAN，不依赖 ROS，控制包作为参考，可进一步优化；用法见下，详见 vla_robot/README.md）：

```bash
cd vla_robot
bash setup.sh                 # 首次/迁移后执行一次: 建共用 venv + 装依赖 + 写路径 (幂等)

# —— 机械臂自检（默认只读；先 sudo ip link set can_left/right up type can bitrate 1000000）
./run_arm.sh --list           # 列 CAN 接口 + RealSense 序列号，对应设备序列号填写在vla_robot/client/config/client.yaml中
./run_arm.sh                  # 连接双臂, 读状态
./run_arm.sh --home           # 归位到 sleep_position，sleep_position也在client.yaml中设置

# —— VLA 客户端（先起 T2 runtime；客户端与 pi0/pi05 无关，模型由板端 runtime 配置决定）
./run_client.sh                        # realsense 直连 + piper_sdk 双臂 (config/client.yaml)
./run_client.sh --record-commands          # 记录 + 停止自动出图
./run_client.sh --mock --duration 20   # 无硬件全链路自检 (合成相机 + 空跑臂 + mock runtime)
```

- 配置：client/config/client.yaml（服务端端口、相机后端/顺序、14 维 arms.action_joint_names、obs.image_size、RTC、下发滤波、退出归位）、arm_control/config/arm.yaml（CAN 口、夹爪行程/力、sleep_position）。
- 重点关注相机序号的配置以及机械臂 CAN 口名称与实际一致。
- 板端约定一致：客户端进程监听 server.host:server.port（默认 0.0.0.0:30005），板端 runtime 主动连入。
- 包内路径全为相对交付包根目录，可整体拷贝。piper_sdk 已 vendored 在 arm_control/third_party/，新机器只需 bash setup.sh。

**网络通信协议**

- 角色方向：板端 runtime（dist/vla_sdk_demo --mode network）是 TCP client，主动 connect() 到客户端机器。客户端侧（arm_interface 部署链的相机/臂节点所在机器，参考实现 deploy/src/inference_runner/inference_runner/oellm_tcp.py::OellmTcpClient）是 TCP server。地址/端口在 demo.json 的 network.\{server_ip,server_port,timeout\}（默认 127.0.0.1:30005）。
- 分帧：每帧 = \[4 字节大端序长度\]\[protobuf 字节流\]。板端 vla_demo_network.h 用 htonl/ntohl 读写长度头、SerializeToString/ParseFromString 收发。客户端用 struct.pack(">I", len) 对齐。请求与响应同为一种消息（MultiModalInput）。
- 消息定义（oellm_runtime/examples/vla_demo/common/src/msg.proto）：

  ```proto
  message Time  { int64 sec = 1; int32 nsec = 2; }
  message Header {
    uint32 seq = 1;      // 自增序列号
    Time   stamp = 2;    // 采集时刻
    string frame_id = 3;
    uint32 type = 4;     // 图像类型 (RGB/BGR)
    bool   reset = 5;    // 重置推演 (RTC: 任务开始清缓存)
    bool   view_only = 6;
  }
  message Tensor {
    enum DataType { FLOAT64=0; UINT8=1; STRING=2; FLOAT32=3; INT32=4; FP16=5; }
    DataType       dtype = 1;
    repeated int32 shape = 2;   // int32（跨架构）
    bytes          data  = 3;   // 原始字节
  }
  message MultiModalInput {
    Header         header    = 1;
    repeated Tensor images   = 2;  // 3 张，shape=[3,H,W] CHW，DT_UINT8
    repeated Tensor languages= 3;  // prompt 文本，DT_STRING（板端内部 tokenize）
    repeated Tensor states   = 4;  // state 向量，DT_FLOAT64（pi0 走此张量做 state_proj）
  }
  ```

- 请求 → 响应：客户端发 images/languages/states（+可选 field 5/6 RTC 约束），板端回同型 MultiModalInput，动作放 languages\[0\]（dtype 为 FLOAT64 或 FP16，shape = \[action_horizon, action_dim\] 的原始维度）。
- pi0 的 state 走 states 张量（inject_state=false，不进 prompt）：客户端发原始值，由 runtime host 侧归一化（见下）。

### 请求张量的格式与归一化

| 字段 | dtype | shape | 内容 | 是否归一化 |
| :--- | :--- | :--- | :--- | :--- |
| images\[i\] | DT_UINT8（也接受 FLOAT32/FP16） | \[3, H, W\]（CHW，RGB） | 相机原图像素 0–255 | 未归一化；UINT8 时 runtime 内部统一做 ResizeWithPad(→224×224) + 归一化 |
| languages\[0\] | DT_STRING（或 DT_INT32） | \[\]（或 \[token_len\]） | prompt 原文（UTF-8）；或已分词 token ids | 不涉及（文本）；runtime 内部 tokenize（pi0 inject_state=false，不把 state 注入 prompt） |
| states\[0\] | DT_FLOAT64 | \[14\] | 原始关节值（双臂 6 关节+夹爪，raw 物理量） | 未归一化；runtime host 侧按 norm_stats_runtime.json 的 state.mean/std 归一化后再喂 HBM（preproc=true） |
| prev_actions(field 5) | DT_FLOAT64 | \[n\*14\] 展平 | 上一 chunk 未执行的尾巴（raw） | 未归一化；engine 侧按 action 统计处理 |

:::warning 注意

- preproc=true（默认）：states 必须发 raw（DT_FLOAT64）——网络层据 dtype 置 state_raw=true，runtime 才做归一化。发 DT_FLOAT32 会被当作“已归一化”（state_raw=false），不要在客户端预归一化。
- preproc=false：输入须已预处理——states 必须是已归一化值且长度 == state_size(=14)，languages 必须发 DT_INT32 token ids（prompt 文本无法离线转 tokens），否则报错。
- 图像若设 obs.image_size=\[0,0\]（不缩放），客户端把相机原图（如 1280×720）交给 runtime，由 runtime 统一 ResizeWithPad 到 224×224 再归一化。
- 响应侧 languages\[0\] 的动作是模型输出空间的绝对关节动作（配合 use_absolute_action/filter 等 processing），与上述请求张量的原始量纲不同。

:::

## 问题与解决方法

### 训练 / 数据

| 现象 | 根因 | 解决 |
| :--- | :--- | :--- |
| 加载卡死 / 访问 huggingface 超时 | 离线环境仍尝试联网 | HF_HUB_OFFLINE=1；base 权重走 hf-mirror 镜像本地化 |
| tokenizer 加载失败（gated） | google/paligemma-3b-pt-224 需授权 | 本地下载并改 pi05_base/policy_preprocessor.json 路径；训练后 ckpt 自带 tokenizer/ |
| v2.1 数据集读不了 | lerobot ≥0.4 抛 BackwardCompatibilityError | 训练/校准用 v3.0；v2.1 用 drrm(0.3.3) 或先转 v3.0（格式差异见 [数据集格式说明](#数据集格式说明-v21-vs-v30)） |
| 数据集 key 是扁平名 | 训练特征名与策略不符 | --rename_map 映射 head_cam→observation.images.head_cam 等 |

### 板端运行时

| 现象 | 根因 | 解决 | 效果 |
| :--- | :--- | :--- | :--- |
| 动作完全不对 | euler_step 缺省 false（velocity 当 x_t 回灌） | euler_step=true | 0.4955 → 0.4172 |
| 动作完全不对 | use_absolute_action 缺省 false（又叠一次 state） | use_absolute_action=true | 量级 1.99 → 1.00 |
| norm_stats 初始化失败 | norm_stats.json 只有 actions 缺 state | 用 norm_stats_runtime.json（含 state） | — |

### 数据/配置配比

| 项 | 训练侧 | 板端 |
| :--- | :--- | :--- |
| 归一化 | MEAN_STD；state/action 14 维 | norm_stats_runtime.json（state+actions） |
| 动作空间 | 绝对动作 | use_absolute_action=true |
| state | 注入 prompt（inject_state） | inject_state=true + state_size=14 |
| 图像 | 480×640 存储，模型内 resize 224 | 先 openpi resize_with_pad 到 224 |


## 验收指标参考

### 量化精度

:::tip 提示

仅作为本任务的参考，校准集 30 样本，伪量化 vs float。

:::

| 阶段 | 指标 | 值 |
| :--- | :--- | :--- |
| calib_eval | action MAE | 0.001846 |
| calib_eval | action RMSE | 0.003304 |
| calib_eval | action cosine | 0.999772 |
| calib_eval | tensor MAE | 0.002611 |
| calib_eval | tensor cosine | 0.999775 |

preproc 0.1ms + visual ~20ms + lm ~100ms + action ~125ms + postproc 0.1ms ≈ 250-270ms。此处为高精度版本，若欲提升推理性能，可参考 OELLM 工具链中的均衡版本以及高性能版本
