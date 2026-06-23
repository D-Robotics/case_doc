---
sidebar_position: 1
sidebar_label: 视觉语言动作模型（VLA）
---

# 视觉语言动作模型（VLA）

VLA（Vision-Language-Action Model，视觉-语言-动作模型）是一种融合视觉理解、语言交互与机器人控制能力的端到端模型，可根据视觉信息和语言指令直接生成机器人动作，广泛应用于具身智能与机器人操作场景。代表工作有 Google 的 RT-2 和 Physical Intelligence 的 pi0。

| 硬件要求 | 算法依赖 | 性能 Benchmark |
| --- | --- | --- |
| RDK S600 | Pi0 | all(ms)：98<br />pre-process(ms)：1.5<br />vision(ms)：18.5<br />language(ms)：39<br />action(ms)：38.5<br />post-process(ms)：0.05<br />memory(GB)：4.4 |

- 在 PC 部署 RoboTwin 仿真环境，用于得到模型输入和执行模型输出，以及观测 Pi0 模型推理效果。

- 在 S600 部署 Pi0 模型，用于端侧推理并统计耗时。

- 如需部署自训练的 pi0 模型或进行实机联调部署，请参阅[参考资料](/more_resources)。

该流程体验需要搭建 PC 端仿真环境，交互流程如下：

```shell
         【 S600 】                                 【 PC 】
    +-------------------+                    +-------------------+
    |   OELLM 环境部署   |                    |  x86 仿真环境部署  |
    +---------+---------+                    +---------+---------+
              |                                        |
              v                                        v
    +---------+---------+                    +---------+---------+
    |     运行模型       |                    |      运行仿真     |
    +---------+---------+                    +---------+---------+
              |                                        |
              v                                        v
    +---------+---------+                    +---------+---------+
    |     等待状态       |<------------------+      发送状态      |
    +---------+---------+                    +---------+---------+
              |                                        ^
              v                                        |
    +---------+---------+                    +---------+---------+
    |     模型推理       |                    |      仿真迭代     |
    +---------+---------+                    +-----------+-------+
              |                                        ^
              v                                        |
    +---------+---------+                    +---------+---------+
    |     发送动作       +------------------->|      接收动作     |
    +-------------------+                    +-------------------+
```

## PC 仿真部署

### 准备环境

```shell
#下载仓库
git clone https://github.com/D-Robotics/RoboTwin.git
cd RoboTwin/
git checkout pi0pub

#准备虚拟环境
# RoboTwin 目录下
conda create -n RoboTwin python=3.10 -y
conda activate RoboTwin
pip install uv
# RoboTwin/policy/pi0 目录下
cd policy/pi0
GIT_LFS_SKIP_SMUDGE=1 uv sync
cp -r ./src/openpi/models_pytorch/transformers_replace/* .venv/lib/python3.11/site-packages/transformers/

#安装 cuboro
# RoboTwin/policy/pi0 目录下
conda deactivate
source .venv/bin/activate
# At this point, you should be in the (openpi) environment
cd ../../envs
git clone https://github.com/NVlabs/curobo.git
cd curobo
export CUROBO_DISABLE_CUDA_EXT=0
pip install -e . --no-build-isolation # 耗时较久

#下载数据
# 进入 Robotwin/assets 目录
# 以 2M/s 下载速度为标准，此流程需 2h 以上
bash download.sh
```

:::warning

- **curboro 安装失败**

 尝试 `export CUROBO_DISABLE_CUDA_EXT=1` 然后执行 `pip install -e . --no-build-isolation # 耗时较久`

- **高版本 CUDA 不适配**

 若您使用 CUDA13.0 及以上版本，需在执行 `uv sync` 后更新 torch 版本，在 `openpi` 虚拟环境中执行 `pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu130`
:::

### 修改配置

修改 `RoboTwin/task_config/config.yaml` 配置文件，如下所示：

```yaml
# 测试相关
sample: 0              # 样本索引
rnd: false             # 是否启用随机采样，false 表示使用 sample 的样本
restore: false         # 是否启用断点续测

# 部署相关
stage: 3               # 测试阶段 OBS=0, SKIP, ACTION, FULL
use_cpp: true          # 是否仅使用端侧推理，仿真侧不执行推理（stage 为 FULL 时可选）
torch_model: "policy/pi0/torch_model/pi0_aloha_pytorch_hammer_vispruner_1126"
                       # PyTorch 模型路径
port: 8888             # 监听 socket 连接的端口

# 滤波相关
filter:  0             # 滤波类型：0，禁用；1：ButterWorth；2：FIR；3：ZeroPhase
cutoff: 3              # 截止频率
fs: 50                 # 采样频率
channels: 14           # 滤波维度

# 推理相关
chunk: 50              # 每輪使用的 chunk_size(max=50)
visp: true             # 使用 vispruner 词汇压缩
do_preproc: false      # 发送预处理后的 OBS
do_postproc: false     # 接收动作进行后处理
debug: false

# 显示相关
use_video: true         # 是否保存视频
spcam: false            # 是否使用自定义 camera，在_camera_config.yaml 调整分辨率，在 eval_policy.py 中调整角度
raw_tri: false
cat_dim: 1              # 拼接维度：0 竖拼，1 横拼
fresh: 0                # 图像刷新时间，0 为不显示图像
hd: 2                   # 图像放大倍数
```

需要您重点关注的参数：

- **port：** 与端侧进行通信的接口，需要与端侧配置对齐。

- **use_video：** 是否保存仿真视频，默认开启，关闭可小幅提升性能。

- **fresh：** 是否实时显示仿真场景，默认开启，关闭可小幅提升性能。

- **sample 和 rnd：** 验证使用的样本集，如 sample=0 时，rnd=false 指使用现存的数据集 0，rnd=true 指随机采样新数据集 0（若存在则覆盖）。

- **restore：** 是否启用断点续测，若为 true 则优先读取该任务中上一次中断的测试进度和配置，若为 false 则重新开始一轮 eval。

### 仿真运行

进入 `RoboTwin/policy/pi0` 目录运行指令：

```shell
bash eval.sh beat_block_hammer demo_clean pi0_base_aloha_robotwin_full demo_clean 0 0
```

## RDK S600 端侧部署

### 准备环境

```shell
#创建文件夹，下载模型
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir Pi0
cd Pi0
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/Pi0/w8/Pi0_hammer-beat-block_vision_224x224_w8_nash-p_corenum_1.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/Pi0/w8/Pi0_hammer-beat-block_language_w8_nash-p_corenum_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/Pi0/w8/Pi0_hammer-beat-block_action_w8_nash-p_corenum_4.hbm

# 使用 balanced 模式
/usr/hobot/bin/hb_switch_ion.sh balanced
# 重启生效
reboot
```

### 示例文件说明

在 `oellm_runtime` 目录中，Pi0 示例使用到的文件和文件夹如下所示：

```python
.
├── configs                              # Tokenizer 文件
│   └── Pi0_config
├── examples
│   └── pi0_demo
│       ├── proto                        # proto 消息定义
│       ├── msg.proto
│       ├── build_pi0.sh                 # 交叉编译脚本
│       ├── CMakeLists.txt
│       ├── pi0_demo.cc                  # 可执行文件源码
│       ├── pi0                          # 可执行文件
│       ├── run_pi0.sh                   # 端侧运行脚本
│       └── pi0_config.json              # 端侧运行配置文件
├── include
├── lib
└── model
    ├── Pi0
    │   ├── Pi0_hammer-beat-block_vision_224x224_w8_nash-p_corenum_1.hbm
    │   ├── Pi0_hammer-beat-block_language_w8_nash-p_corenum_4.hbm
    │   └── Pi0_hammer-beat-block_action_w8_nash-p_corenum_4.hbm
    └── resolve_model_nash-p.md          # 端侧模型下载方式
```

### 配置文件说明

端侧运行配置文件 `{model}_config.json` 的配置参数及其说明：

| 参数名称 | 参数说明 | 可选/必选 |
| --- | --- | --- |
| siglip_hbm_path | 参数描述：vision 模型路径<br />参数类型：string | 必选 |
| paligemma_hbm_path | 参数描述：language 模型路径<br />参数类型：string | 必选 |
| action_hbm_path | 参数描述：action 模型路径<br />参数类型：string | 必选 |
| siglip_bpu_core | 参数描述：vision 模型使用的 bpu 核，<br />设定多个值时按照[0,1,2,3]填写<br />参数类型：[int] | 必选 |
| paligemma_bpu_core | 参数描述：language 模型使用的 bpu 核，<br />设定多个值时按照[0,1,2,3]填写<br />参数类型：[int] | 必选 |
| action_bpu_core | 参数描述：action 模型使用的 bpu 核，<br />设定多个值时按照[0,1,2,3]填写<br />参数类型：[int] | 必选 |
| tokenizer_dir | 参数描述：Tokenizer 配置文件路径<br />参数类型：string | 必选 |
| norm_stats_path | 参数描述：norm stats 文件路径<br />参数类型：string | 必选 |
| server_ip | 参数描述：端口号，需和仿真侧 config.yaml 配置端口对齐<br />参数类型：int<br />默认配置：8888 | 可选 |
| stage | 参数描述：设定运行模式，通常无需修改，建议保持为 6<br />参数类型：int | 必选 |
| preproc | 参数描述：是否在端侧做预处理，建议设定为 true<br />参数类型：bool | 必选 |
| postproc | 参数描述：是否在端侧做后处理，建议设定为 true<br />参数类型：bool | 必选 |
| fs | 参数描述：动作滤波的采样频率，可根据动作效果调整，0 为关闭滤波<br />参数类型：double | 必选 |

`pi0_config.json` 参考配置示例：

```json
{
  "siglip_hbm_path": "../../model/Pi0/Pi0_hammer-beat-block_vision_224x224_w8_nash-p_corenum_1.hbm",
  "paligemma_hbm_path": "../../model/Pi0/Pi0_hammer-beat-block_language_w8_nash-p_corenum_4.hbm",
  "action_hbm_path": "../../model/Pi0/Pi0_hammer-beat-block_action_w8_nash-p_corenum_4.hbm",
  "siglip_bpu_core": [
    0,1,2
  ],
  "paligemma_bpu_core": [
    0,1,2,3
  ],
  "action_bpu_core": [
    0,1,2,3
  ],
  "tokenizer_dir": "../../configs/Pi0_config/",
  "norm_stats_path": "../../configs/Pi0_config/norm_stats.json",
  "server_ip": "120.48.157.2",
  "server_port": 30001,
  "stage": 6,
  "preproc": true,
  "postproc": true,
  "fs": 15
}
```

### 端侧运行说明

示例提供运行脚本 `run_pi0.sh`，运行指令参考：

```shell
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/examples/pi0_demo/
bash run_pi0.sh
```

该脚本内容如下：

```shell
export LD_LIBRARY_PATH=../../lib:$LD_LIBRARY_PATH   # 指定动态库
export HB_DNN_USER_DEFINED_L2M_SIZES=6:6:6:6        # 为 BPU 分配 L2M 大小

./pi0 --config pi0_config.json
```

可执行文件的参数信息：

```shell
Usage:
  ./pi0 --config_path <config_path> [options]

Options:
  -c, --config_path <config_path>   Path to the pi0 config file (required)
  -h, --help                        Show this help message

Examples:
  ./pi0 --config_path ./pi0_config.json
```

## 运行结果展示

### RDK S600

```text
...

Filter fs: 15
xlm init success
开始连接：120.48.157.2:30001
连接成功：120.48.157.2:30001 ...

接收成功，长度：691484字节
===== 解析 Header 信息 =====
序列号: 0
时间戳: 1770106723.66053628
重置仿真： 1
===== 解析 Body 信息 =====
接收到 3 个图像张量：
类型=1，维度=3 240 320
类型=1，维度=3 240 320
类型=1，维度=3 240 320
接收到 1 个语言张量：
类型=2，维度=
接收到 1 个状态张量：
类型=0，维度=14
===== 开启 Pi0 推理 =====
Preprocess time: 1.573ms.
Siglip infer time: 18.468ms.
Paligemma infer time: 38.965ms.
Action infer time: 38.578ms.
Postprocess time: 0.059ms.
Pi0 Total time: 97.888ms.
===========================
发送成功，长度：5651字节

...
```

### PC

```yaml
...

Render Well
============= Config =============

Messy Table: False
Random Background: False
Random Light: False
Random Table Height: 0
Random Head Camera Distance: 0
Head Camera Config: D435, True
Wrist Camera Config: D435, True
Embodiment Config: aloha-agilex

==================================
missing pytorch3d
No model loaded!
Load tokenizer success!
NoFilter
NoFilter
Load model success!
Task Name: beat_block_hammer
Policy Name: pi0
Start new eval!

...

服务器启动成功，等待客户端连接...（端口：30001）
客户端已连接：IP=221.226.80.67, 端口=58799
发送成功，长度：691484字节

接收成功，长度：5651字节
===== 解析 Header 信息 =====
序列号 : 1
时间戳: 1770106723.508825449
====== 解析 Body 信息 ======
接收到 0 个图像张量：
接收到 1 个嵌入张量：
  语言0：类型=0，维度=1 50 14 
接收到 0 个状态张量：
============================
step: 1 / 400

...
```

![](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/vla_effect.png)



