---
title: "Pi0"
description: "The complete pipeline for the Pi0 vision-language-action model, from LeRobot training and OELLM2.0 quantization and compilation to on-device deployment on the RDK S600, with troubleshooting."
sidebar_position: 2
sidebar_label: 1. Pi0
---

# Pi0


## Workflow overview

```text
[Stage 1] Training
   pi0_base  (HF pretrained)
        │  finetune  (v3.0 dataset, 30 fps)
        ▼
   checkpoints/030000/pretrained_model  (bf16, chunk=50, absolute actions)

        │
        ▼
[Stage 2] Quantization + compilation (oe_llm_s600/pi0_conver/)
   float_eval  → floating-point baseline / reference dump
   calib       → fake-quant weights (pi0 has no time-mod LUT)
   calib_eval  → fake-quant accuracy (calibration set)
   compile     → 3× HBM (w8 nash-p)

        │
        ▼
[Stage 3] On-device deployment and running
   3× HBM + norm_stats_runtime.json + tokenizer/
   server (vla_sdk_demo) + client (vla_robot)
```

- Model: PaliGemma (gemma_2b) + Gemma action expert (gemma_300m), 3 cameras + 14-dim state/action (padded to 32), chunk=50, 10 denoising steps.
- Quantization: int8 weights (w8) / action expert W8A16, compiled to nash-p HBM.
- The pi0 model/pipeline code lives in pi0_pkg and hooks into the framework through runtime registration + monkey-patching.


## Get the toolkit

```shell
wget https://archive.d-robotics.cc/downloads/rdk_demo/rdk_s600_demo/pi0_toolkit.tar.gz
```

## Stage 1: Training (LeRobot pi0)

Code: https://github.com/huggingface/lerobot (lerobot 0.6.2 d451fe4).

### Environment setup

| Purpose | conda environment | Notes |
| :--- | :--- | :--- |
| Training | lerobot | <ul><li>RTX 5090</li><li>CUDA 13.3</li><li>Python 3.12</li><li>torch 2.11</li><li>lerobot 0.6.2 (editable)</li></ul> |

- After the base environment is set up, clone the lerobot code and install the dependencies.

  ```bash
  # Clone the lerobot code
  git clone https://github.com/huggingface/lerobot.git

  pip install -e ".[core_scripts]"  # For robot workflows (recording, replaying, calibrate)
  pip install -e ".[training]"      # For training policies
  pip install -e ".[all]"     # Everything (all policies, envs, hardware, dev tools)
  ```

- Dataset format: training uses v3.0 (`CODEBASE_VERSION=v3.0`); v2.1 must first be converted to v3.0 (`convert_dataset_v21_to_v30.py`). For the v2.1/v3.0 directory structure comparison, see [Dataset format: v2.1 vs v3.0](#dataset-format-v21-vs-v30). The local data conversion command is:

  ```bash
  python lerobot/src/lerobot/scripts/convert_dataset_v21_to_v30.py  \
      --repo-id=xxx \
      --root=<path to the data to convert>  \
      --push-to-hub=false
  ```
    :::warning

    - Training depends on two Hugging Face resources:

      - The pretrained weights `lerobot/pi0_base`, and the tokenizer `google/paligemma-3b-pt-224` that `tokenizer_name` points to in its `policy_preprocessor.json`. If you can access Hugging Face and do not set `HF_HUB_OFFLINE=1` during training, you do not need to download them in advance; `lerobot-train` pulls them automatically by repository name. The training command below sets `HF_HUB_OFFLINE=1`, so you must complete the local preparation first.

      - `google/paligemma-3b-pt-224` is a gated model, so you must be granted access before downloading it: sign in to [Hugging Face](https://huggingface.co), open [google/paligemma-3b-pt-224](https://huggingface.co/google/paligemma-3b-pt-224), click Acknowledge license to accept the Gemma license (this takes effect immediately), then run `hf auth login`.

    - If your network is poor, or the training command sets `HF_HUB_OFFLINE=1` (which reads only local files and no longer contacts Hugging Face), download everything in advance under the `lerobot` directory. Use `./pi0_base` as `--policy.pretrained_path`; after downloading, change `tokenizer_name` in `pi0_base/policy_preprocessor.json` to `./paligemma-3b-pt-224`.

      ```bash
      cd lerobot
      hf download lerobot/pi0_base --local-dir ./pi0_base
      hf download google/paligemma-3b-pt-224 --local-dir ./paligemma-3b-pt-224
      ```

    :::

- To monitor training in wandb, sign in first:

  ```bash
  wandb login YOUR_API_KEY
  ```

### Training command

```bash
# Start the lerobot environment
cd lerobot
conda activate lerobot

# Fine-tune from pi0_base (use rename_map if the dataset needs remapping)
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
    --steps=3000 \
    --policy.device=cuda \
    --batch_size=32 \
    --rename_map '{"state":"observation.state","head_cam":"observation.images.head_cam",
"left_cam":"observation.images.left_cam","right_cam":"observation.images.right_cam"}'

# To resume from a checkpoint, refer to the following command:
HF_HUB_OFFLINE=1 lerobot-train \
  --config_path=outputs/pi0_training/checkpoints/030000/pretrained_model \
  --resume=true --steps=60000 --dataset.eval_split=0.05 --eval_steps=1000
```

#### Key configuration (`train_config.json` / `config.json`)

| Item | Value |
| :--- | :--- |
| policy | pi0 (gemma_2b + gemma_300m) |
| batch | 32 |
| steps | 30000 |
| lr | AdamW 2.5e-5<br />cosine + warmup 1000<br />decay 30000 |
| dtype | bfloat16<br />compile_model=true<br />compile_mode=max-autotune |
| freeze | true |
| train_expert_only | true |
| chunk | 50 |
| action / state | 14-dim output (padded to 32); 14-dim state (padded to 32) |
| normalization | ACTION/STATE=MEAN_STD<br />VISUAL=IDENTITY |
| tokenizer | tokenizer_max_length=48 |
| Deployment | type=pi0<br />chunk_size=50<br />n_action_steps=50<br />num_inference_steps=10<br />compile_model=true<br />image_resolution=\[224,224\]<br />use_relative_actions=false<br />control_fps=30 |

#### Training resources and time

| Item | Value |
| :--- | :--- |
| Machine | 1× NVIDIA RTX 5090 32GB (32607 MiB, driver 610.57.04) + Intel i9-14900KF (32 threads) |
| GPU memory usage | ~10.5 GB |
| batch | 32 |
| Precision | bfloat16 |
| Memory optimization | gradient_checkpointing=true<br />freeze_vision_encoder=true<br />train_expert_only=true<br />compile_model=true (max-autotune) |
| Trainable parameters | 578M (only the action expert is unfrozen) |
| Time per step | ~1.92 s/step |
| Measured throughput including eval/save | ~2.30 s/step |
| Training steps | 30000 |
| Data duration | 35s |
| Number of samples | 300 |
| Time for this stage | ≈ 16.3 h |

### Dataset format: v2.1 vs v3.0

:::info

The training environment lerobot (0.6.2, CODEBASE_VERSION=v3.0) can read only v3.0.
:::

#### v2.1 — fold_the_towel

```text
.
├── meta/
│   ├── info.json              codebase_version = "v2.1"
│   ├── tasks.jsonl            {"task_index":0,"task":"Fold the towel from bottom to top twice, then from right to left."}
│   ├── episodes.jsonl         {"episode_index","tasks","length"}
│   ├── episodes_stats.jsonl   {"episode_index","stats":{feature:{min,max,mean,std,count}}}
│   └── modality.json          segment index for state/action/endpose/...
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet     ← one file per episode (320 in total)
│       └── ...
└── videos/
    └── chunk-000/
        ├── head_cam/episode_000000.mp4
        ├── left_cam/episode_000000.mp4
        └── right_cam/episode_000000.mp4
```

#### v3.0 — fold_the_towel_v3

```text
.
├── meta/
│   ├── info.json              codebase_version = "v3.0"
│   ├── tasks.parquet          task_index | task
│   ├── stats.json             aggregated stats
│   └── episodes/
│       └── chunk-000/
│           └── file-000.parquet      ← one row per episode (data/video index + from/to_ts + length + stats columns for each feature)
├── data/
│   └── chunk-000/
│       ├── file-000.parquet          ← aggregated by data_files_size_in_mb
│       └── ...
└── videos/
    ├── head_cam/chunk-000/file-000.mp4     ← video_key moved before chunk, aggregated by video_files_size_in_mb
    ├── left_cam/chunk-000/file-000.mp4
    └── right_cam/chunk-000/file-000.mp4
```

#### Key differences

| Item | v2.1 | v3.0 |
| :--- | :--- | :--- |
| data | one file per episode | multiple episodes aggregated into one file |
| video | one video file per episode | multiple episodes aggregated into one video file |
| Per-episode metadata | episodes.jsonl + episodes_stats.jsonl | meta/episodes/chunk-XXX/file-XXX.parquet |
| task | tasks.jsonl | tasks.parquet |
| info.json | no per-feature fps; has total_videos/total_chunks | fps for each feature; has data_files_size_in_mb |
| modality.json | present | absent |

:::warning

- If you train directly on a v2.1 dataset, lerobot 0.6.2 throws `BackwardCompatibilityError`. Convert it to v3.0 first with the commands in [Environment setup](#environment-setup).
- The feature names in both v2.1 and v3.0 are flat names (such as `head_cam` and `state`), while the policy expects `observation.images.*` and `observation.state`. Add `--rename_map` during training; for a mapping example, see [Training command](#training-command).
- When `info.json.features.*.info.video.codec` is `av1`, decoding depends on `ffmpeg`. Install `ffmpeg` on the training machine and make sure it is on `PATH`.

:::

## Stage 2: Quantization + compilation (OELLM2.0)

### Environment setup

```bash
conda create -n oellm python=3.10 -y
pip install torch==2.8.0+cu128 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install $SDK/package/host/*.whl          # horizon / hbdk / hbm
pip install -r $SDK/llm_compression/requirements.txt
pip install --force-reinstall setuptools==80.10.2

# Create the pi0_conver folder; put the files needed for quantization and the generated artifacts in it
mkdir oe_llm_s600/pi0_conver
```

Quantization package `pi0_toolkit/quantize/pi0_pkg/`

| File | Purpose |
| :--- | :--- |
| model.py | Pi0Config + Pi0GemmaExpert (state_proj / action_time_mlp / standard RMSNorm) |
| process_utils.py | Denoising loop with state + expert attention mask/position_ids (\_SUFFIX_STATE_TOKENS=1) |
| pi0_model.py | Pi0 QModel (@MODEL_REGISTRY runtime registration; get_qconfig_setting("action") defines the quantization scheme) |
| float_model.py | Pi0FloatModel + build_pi0_float_model |
| patch.py | Monkey-patch vla_eval (pass state to the eval dump; state normalization + fp16 in HbmExecutor.\_run_expert; mask/pos for the suffix state token) |
| run.py | Unified entry point: float_eval / calib / calib_eval / compile |

### Data and model preparation

`pi0_toolkit/tool/prep_pi0.py` handles everything in one script: the model directory, the calibration data, `norm_stats_runtime.json`, and the configuration required for quantization.

```bash
# Use the lerobot environment (lerobot 0.6.2, reads v3.0)
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
      <th colSpan={2}>Artifact</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowSpan={3}>Model directory</td>
      <td>`<output-dir>/model_<step>/config.json`</td>
      <td>Pi05Config architecture constants: max_token_len=200, no uses_state</td>
    </tr>
    <tr>
      <td>`<output-dir>/model_<step>/model.safetensors`</td>
      <td>Generated automatically from the native ckpt by stripping the model. prefix</td>
    </tr>
    <tr>
      <td>`<output-dir>/model_<step>/paligemma_tokenizer.model`</td>
      <td>tokenizer symlink (located automatically from --ckpt-dir by default)</td>
    </tr>
    <tr>
      <td rowSpan={4}>Calibration data</td>
      <td>`<output-dir>/pi05_calib_image/{sid}/image_{0,1,2}.jpg`</td>
      <td>head / left / right (640×480, quality 95)</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi05_action_calib_data/{sid}/state.npy`<br />`action.npy`<br />`x_t.npy`</td>
      <td>\[14\] raw + \[50,32\] flow noise</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi05_prompt.json`</td>
      <td>\[\{"text": ...\} x N\] (reads the dataset tasks by default)</td>
    </tr>
    <tr>
      <td>`<output-dir>/norm_stats.json`</td>
      <td>mean/std/q01/q99 of actions (full statistics)</td>
    </tr>
    <tr>
      <td>On-device norm</td>
      <td>`<output-dir>/norm_stats_runtime.json`</td>
      <td>mean/std/q01/q99 of state + actions (used by the on-device runtime)</td>
    </tr>
    <tr>
      <td rowSpan={2}>Quantization yml</td>
      <td>`<output-dir>/pi0.yml`</td>
      <td>For calib / calib_eval / compile</td>
    </tr>
    <tr>
      <td>`<output-dir>/pi0_float.yml`</td>
      <td>For float_eval only: evaluation.calib_ckpt_load_path has been removed (otherwise torch_eval treats it as calib_eval)</td>
    </tr>
  </tbody>
</table>
</div>

- Sampling convention: frames are sampled at equal intervals across the whole dataset, the camera order is fixed as head→left→right, and action/state store raw physical values.
- --ckpt-dir is the input (the native lerobot model directory).
- --model-dir is the output (the converted llm_compression directory, default \<output-dir>/model_\<step>).
- The model. prefix is stripped inside the script.


### Quantize and compile

Run the following in `pi0_conver/`.

```bash
# Use the oellm environment
conda activate oellm

cd oe_llm_s600/pi0_conver

export PYTHONPATH="<D-Robotics_LLM_S600_2.0.0-Beta_SDK_path>:<D-Robotics_LLM_S600_2.0.0-Beta_SDK_path>/llm_compression/lightcompress:oe_llm_s600/pi0_conver"

# Put run.py and pi0_pkg under oe_llm_s600/pi0_conver; see pi0_toolkit for the script and the pkg
python run.py float_eval  --config_path pi0_float.yml  # 1) floating-point baseline + reference dump
python run.py calib   --config_path pi0.yml     # 2) calibration (generates calib_ckpt/)
python run.py calib_eval   --config_path pi0.yml # 3) fake-quant accuracy (calib_ckpt_load_path=./calib_ckpt in the yml)
python run.py compile   --config_path pi0.yml   # 4) compile HBM (CPU only, lm takes about 2~3h)
```

Key entries in `pi0.yml`:

```yaml
model:      {model_name: Pi0, model_path: .../model_060000, model_list: [visual,lm,action],
             model_dtype: bfloat16, max_token_len: 48, enable_time_mod_lut: false}
calibration:{dataset_type: vla_dataset, vla_image_path/vla_action_calib_data/vla_prompt_path: ...,
             calibration_step: 30, calib_ckpt_save_path: ./calib_ckpt}
evaluation: {norm_stats_path: .../norm_stats.json, eval_stages: [calib], dump_dir: ./eval_dump}
compile:    {hbm_save_path: ./compile, calib_ckpt_load_path: ./calib_ckpt, opt_level: 2, enable_hpc: true, skip_embed_tokens: true, skip_lm_pd_split: true, lm:   {enable_hpc: false, core_num: 4},          # HPC disabled for lm ((256*3+48)%32 issue, see "Data/configuration alignment")
action:{enable_hpc: true,  core_num: 4}}         # HPC enabled for action
```

Quantization scheme (pi0_model.py::get_qconfig_setting("action")):

- Default: Linear qint16 in / qint8 w / fp16 out; qk/sv matmul qint16×qint16; norm/add/cat/gate fp16.
- Modules unique to pi0 and quantized by default: state_proj, action_time_mlp_in, action_time_mlp_out.
- model.action_w16=true → the action expert weights use qint16 (W16A16) instead of qint8 (W8A16).

### Artifacts

| File | Component | Size |
| :--- | :--- | :--- |
| xxxx_vision_224x224_w8_nash-p_corenum_1.hbm | SigLIP | ~487 MB |
| xxxx_llm_action_horizon_50_w8_nash-p_corenum_4.hbm | Gemma-2B LM | ~3.45 GB |
| xxxx_action_horizon_50_w8_nash-p_corenum_4.hbm | Gemma-300M action expert | ~463 MB |

- Quantization accuracy: for model accuracy metrics, see [Quantization accuracy](#quantization-accuracy); to check and tune the accuracy of a quantized model, see the "Accuracy evaluation" chapter of the OELLM2.0 manual, which is not covered here.
- Compilation time (Intel Core i9-14900KF): visual ~23min + lm ~1h58min + action ~24min ≈ 2h46min.


## Stage 3: On-device deployment and running

Copy the SDK to the board and focus on `D-Robotics_LLM_S600_2.0.0-Beta_SDK/oellm_runtime/examples/vla_demo/pi0`. Before running, grant execute permission to `vla_sdk_demo` with: `chmod +x vla_sdk_demo`

### Required files at runtime

```text
pi0/
├── xxxx_{vision,llm,action}_*.hbm             # Stage 2 artifacts, three models
├── norm_stats.json                            # On-device runtime norm stats (includes state+actions, generated by prep_pi0)
├── tokenizer.json / tokenizer_config.json     # Located under paligemma-3b-pt-224
├── paligemma_tokenizer.model                  # tokenizer.model under paligemma-3b-pt-224, renamed
├── pi0_config.json                            # oellm model configuration (under oellm_runtime/examples/vla_demo/pi0)
└── demo.json                                  # demo configuration (network, 127.0.0.1:30005, under oellm_runtime/examples/vla_demo/pi0)
```

### Runtime configuration reference

#### pi0_config.json

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

#### pi0_network_demo.json

```jsonc
{
  "default_mode": "network",               // ← use network inference
  "modes": ["local", "network"],
  "io": {"input_dir": "input", "output_dir": "output", "multi_chunk": false},
  "demo": {"infer_nums": 1, "image_count": 3, "language_count": 1, "state_count": 1},
  "network": {"server_ip": "127.0.0.1", "server_port": 30005, "timeout": 120}  // ← set the IP and port
}
```

:::info

- State normalization happens on the host side: state=(state-mean)/std (using the state in norm_stats.json); inside the HBM only state_proj is performed.
- Input images: you can send 640×480 and let the board resize it (the board's ResizeWithPadToBuffer is not anti-aliased, matching the training torch path).
- Runtime port: config/demo.json (server_port=30005).

:::

### Open-loop test

Without hardware or teleoperation, feed GT observations (images + state) to the on-device HBM step by step and compare the predicted actions with the GT. On-device script: `pi0_toolkit/deploy/openloop_infer_piper.py` (plus `plot_openloop_npz.py` in the same directory, which generates the plots automatically when finished).

#### Data extraction (training machine side)

Use `pi0_toolkit/tool/extract_episodes_v3.py` to extract the specified episodes from a v3.0 dataset:

```bash
conda activate lerobot
# Extract episodes 0/3/5, one sample every 30 frames in each episode (≈ the start of each chunk)
python3 extract_episodes_v3.py --episodes 0 3 5 --stride 30 -o <out>
# To sample 20 evenly spaced samples per episode: add --num-per-episode 20
```

The output layout required by `openloop_infer_piper.py --eval-data`:

```text
<out>/calib_image/<sid>/image_{0,1,2}.jpg        # head_cam, left_cam, right_cam
<out>/action_calib_data/<sid>/state.npy          # [14] raw
<out>/action_calib_data/<sid>/action.npy         # [14] GT (chunk step0, raw)
<out>/action_calib_data/<sid>/x_t.npy            # [50,32] (not used on the board)
<out>/prompt.json · norm_stats.json · manifest.json
```

#### Open-loop test on the board

Copy the data extracted in the previous step to the board:

```bash
# Create a separate venv with the system python3 (aarch64; network access is enough)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy pillow pyarrow matplotlib opencv-python-headless
# ffmpeg/ffprobe must be on PATH (the board usually ships /usr/bin/ffmpeg; otherwise apt-get install -y ffmpeg)
# Self-check:
python -c "import numpy,PIL,pyarrow,matplotlib; print('deps ok')"
```

```bash
python3 openloop_infer_piper.py --model-dir <model_path>  --eval-data <eval_data_path> --model <pi0/pi05>
```

:::warning

- --model pi0: --model defaults to pi05; using pi0 HBM with the pi05 preset reports \[layout\] suffix_pad=1 invalid ... suffix layout mismatch with HBM (version/suffix mismatch).
- --model-dir determines which directory's three .hbm files are read; norm_stats defaults to --model-dir/norm_stats.json and must contain state (if missing, use --norm-stats \<a file containing state\>).
- Results: when finished, \*_trajectories.png / \*_frame_mae.png / \*_perdim_mae.png are generated automatically.

:::

![On-device open-loop test result: Calib openloop: CT action vs pred (chunk step 0), comparing the GT and predicted action curves for each joint](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/pi0-pi05-openloop-trajectories.png)

### Run on the real robot

Start the pi0 runtime on the board. With `--mode network`, the runtime acts as a TCP client and actively connects to port `30005`, which the client listens on:

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

Client (the `pi0_toolkit/deploy/vla_robot` delivery package: pure Python, dual-arm control of CAN directly through piper_sdk, no ROS dependency; the control package is a reference and can be optimized further; for usage see below, and vla_robot/README.md for details):

```bash
cd vla_robot
bash setup.sh                 # Run once on first use or after migrating: create the shared venv + install dependencies + write paths (idempotent)

# —— Robotic arm self-check (read-only by default; first run sudo ip link set can_left/right up type can bitrate 1000000)
./run_arm.sh --list           # List CAN interfaces + RealSense serial numbers; fill the corresponding device serial numbers into vla_robot/client/config/client.yaml
./run_arm.sh                  # Connect both arms and read their state
./run_arm.sh --home           # Return to sleep_position; sleep_position is also set in client.yaml

# —— VLA client (start the T2 runtime first; the client is independent of pi0/pi05, the model is decided by the on-device runtime configuration)
./run_client.sh                        # RealSense direct connection + piper_sdk dual arm (config/client.yaml)
./run_client.sh --record-commands          # Record + generate plots automatically on stop
./run_client.sh --mock --duration 20   # Full-chain self-check without hardware (synthetic camera + idle arm + mock runtime)
```

- Configuration: client/config/client.yaml (server port, camera backend/order, the 14-dim arms.action_joint_names, obs.image_size, RTC, output filtering, return home on exit) and arm_control/config/arm.yaml (CAN ports, gripper stroke/force, sleep_position).
- Pay close attention to the camera index configuration and to the arm CAN port names matching the actual hardware.
- The board and the client must agree: the client process listens on server.host:server.port (default 0.0.0.0:30005), and the on-device runtime connects to it.
- All paths inside the package are relative to the delivery package root, so the package can be copied as a whole; piper_sdk is already vendored under arm_control/third_party/, so a new machine only needs bash setup.sh.

#### Network communication protocol

- Roles and direction: the on-device runtime (dist/vla_sdk_demo --mode network) is the TCP client and actively connect()s to the client machine; the client side (the machine hosting the camera/arm nodes of the arm_interface deployment chain; reference implementation: deploy/src/inference_runner/inference_runner/oellm_tcp.py::OellmTcpClient) is the TCP server. The address and port are in demo.json under network.\{server_ip,server_port,timeout\} (default 127.0.0.1:30005).
- Framing: each frame = \[4-byte big-endian length\]\[protobuf byte stream\]. On the board, vla_demo_network.h reads and writes the length header with htonl/ntohl and sends/receives with SerializeToString/ParseFromString; the client aligns with struct.pack(">I", len). Requests and responses use the same message type (MultiModalInput).
- Message definition (oellm_runtime/examples/vla_demo/common/src/msg.proto):

  ```proto
  message Time  { int64 sec = 1; int32 nsec = 2; }
  message Header {
    uint32 seq = 1;      // auto-incrementing sequence number
    Time   stamp = 2;    // capture time
    string frame_id = 3;
    uint32 type = 4;     // image type (RGB/BGR)
    bool   reset = 5;    // reset the rollout (RTC: clear the cache at task start)
    bool   view_only = 6;
  }
  message Tensor {
    enum DataType { FLOAT64=0; UINT8=1; STRING=2; FLOAT32=3; INT32=4; FP16=5; }
    DataType       dtype = 1;
    repeated int32 shape = 2;   // int32 (cross-architecture)
    bytes          data  = 3;   // raw bytes
  }
  message MultiModalInput {
    Header         header    = 1;
    repeated Tensor images   = 2;  // 3 images, shape=[3,H,W] CHW, DT_UINT8
    repeated Tensor languages= 3;  // prompt text, DT_STRING (tokenized internally on the board)
    repeated Tensor states   = 4;  // state vector, DT_FLOAT64 (pi0 uses this tensor for state_proj)
  }
  ```

- Request → response: the client sends images/languages/states (plus the optional RTC constraints in fields 5/6), and the board returns a MultiModalInput of the same type, with the actions placed in languages\[0\] (dtype FLOAT64 or FP16, with shape = the original dimensions \[action_horizon, action_dim\]).
- pi0 sends state through the states tensor (inject_state=false, so it never enters the prompt): the client sends raw values and the runtime host side normalizes them (see below).

### Request tensor format and normalization

| Field | dtype | shape | Content | Normalized |
| :--- | :--- | :--- | :--- | :--- |
| images\[i\] | DT_UINT8 (FLOAT32/FP16 also accepted) | \[3, H, W\] (CHW, RGB) | Raw camera pixels 0–255 | Not normalized; for UINT8 the runtime performs ResizeWithPad(→224×224) + normalization internally |
| languages\[0\] | DT_STRING (or DT_INT32) | \[\] (or \[token_len\]) | Raw prompt text (UTF-8), or already-tokenized token ids | Not applicable (text); tokenized internally by the runtime (pi0 inject_state=false, so state is not injected into the prompt) |
| states\[0\] | DT_FLOAT64 | \[14\] | Raw joint values (6 joints per arm + gripper, raw physical values) | Not normalized; the runtime host side normalizes with the state.mean/std from norm_stats_runtime.json before feeding the HBM (preproc=true) |
| prev_actions (field 5) | DT_FLOAT64 | \[n\*14\] flattened | The unexecuted tail of the previous chunk (raw) | Not normalized; handled on the engine side using the action statistics |

:::warning

- preproc=true (default): states must be sent raw (DT_FLOAT64) — the network layer sets state_raw=true based on the dtype, and only then does the runtime normalize; sending DT_FLOAT32 is treated as "already normalized" (state_raw=false), so do not pre-normalize on the client.
- preproc=false: the input must already be preprocessed — states must be normalized values with length == state_size(=14), and languages must be sent as DT_INT32 token ids (prompt text cannot be converted to tokens offline); otherwise an error is reported.
- If images set obs.image_size=\[0,0\] (no scaling), the client passes the raw camera image (for example 1280×720) to the runtime, which then performs ResizeWithPad to 224×224 and normalization uniformly.
- The actions in the response-side languages\[0\] are absolute joint actions in the model output space (combined with processing such as use_absolute_action/filter), so their scale differs from that of the request tensors above.

:::

## Results

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/pi0-effect.mp4" type="video/mp4" />
 Your browser does not support the video tag.
</video>

## Troubleshooting

### Training / data

| Symptom | Root cause | Fix |
| :--- | :--- | :--- |
| Loading hangs / requests to Hugging Face time out | An offline environment still tries to reach the network | HF_HUB_OFFLINE=1; mirror the base weights locally through hf-mirror |
| tokenizer fails to load (gated) | google/paligemma-3b-pt-224 requires authorization | Download locally and change the path in pi05_base/policy_preprocessor.json; the ckpt saved after training carries its own tokenizer/ |
| A v2.1 dataset cannot be read | lerobot ≥0.4 throws BackwardCompatibilityError | Use v3.0 for training/calibration; for v2.1 use drrm(0.3.3) or convert to v3.0 first (for the format differences see [Dataset format: v2.1 vs v3.0](#dataset-format-v21-vs-v30)) |
| The dataset keys are flat names | The training feature names do not match the policy | Use --rename_map to map head_cam→observation.images.head_cam and so on |

### On-device runtime

| Symptom | Root cause | Fix | Effect |
| :--- | :--- | :--- | :--- |
| Actions are completely wrong | euler_step defaults to false (velocity is fed back as x_t) | euler_step=true | 0.4955 → 0.4172 |
| Actions are completely wrong | use_absolute_action defaults to false (state is added again) | use_absolute_action=true | Magnitude 1.99 → 1.00 |
| norm_stats fails to initialize | norm_stats.json contains only actions and no state | Use norm_stats_runtime.json (which contains state) | — |

### Data/configuration alignment

| Item | Training side | On-device |
| :--- | :--- | :--- |
| Normalization | MEAN_STD; 14-dim state/action | norm_stats_runtime.json (state+actions) |
| Action space | Absolute actions | use_absolute_action=true |
| state | Injected into the prompt (inject_state) | inject_state=true + state_size=14 |
| Images | Stored at 480×640, resized to 224 inside the model | First resized to 224 with openpi resize_with_pad |


## Acceptance metrics

### Quantization accuracy

:::tip

For reference only for this task; calibration set of 30 samples, fake-quant vs float.

:::

| Stage | Metric | Value |
| :--- | :--- | :--- |
| calib_eval | action MAE | 0.001846 |
| calib_eval | action RMSE | 0.003304 |
| calib_eval | action cosine | 0.999772 |
| calib_eval | tensor MAE | 0.002611 |
| calib_eval | tensor cosine | 0.999775 |

preproc 0.1ms + visual ~20ms + lm ~100ms + action ~125ms + postproc 0.1ms ≈ 250-270ms. This is the high-accuracy version; to improve inference performance, refer to the balanced and high-performance versions in the OELLM toolchain.
