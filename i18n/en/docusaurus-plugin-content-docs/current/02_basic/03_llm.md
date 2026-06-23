---
sidebar_position: 1
sidebar_label: Large Language Model (LLM)
---

# Large Language Model (LLM)

LLM (Large Language Model) is a class of AI models trained on massive text corpora with natural language understanding and generation capabilities, supporting tasks such as Q&A, translation, summarization, and code generation. Representative models include ChatGPT, GPT-4, and Qwen.

| Hardware Requirements | Model | Performance Benchmark |
| --- | --- | --- |
| RDK S600 | Qwen3-8B | max context: 4096<br />TTFT (ms): 283.6<br />Decode (TPS): 31.4<br />memory (GB): 9.1 |

## Environment Setup

```shell
# Configure memory mode and reboot (skip if already configured)
/usr/hobot/bin/hb_switch_ion.sh balanced
reboot

# Download LLM_S600_SDK (also available via wget), extract on the board (skip if already downloaded)
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
tar zxvf D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
```

```shell
# Create folder and download model
# For more LLM models, see D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model/resolve_model_nash-p.md
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir Qwen3_8B
cd Qwen3_8B
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/Qwen3-8B/w4/Qwen3-8B_language_chunk_512_cache_4096_w4_nash-p_corenum_4_4.hbm
```

## Launch the Case

```shell
# Run
cd ../../examples/llm_demo/

# In run_llm.sh, change qwen3_1.7b_config.json to qwen3_8b_config.json
# Thinking mode is enabled by default; set enable_thinking to false in the JSON to disable
# Type text in the terminal after launch; type exit to quit
bash run_llm.sh
```

## Result Demo

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/llm.mp4" type="video/mp4" />
 Your browser does not support the video tag.
</video>
