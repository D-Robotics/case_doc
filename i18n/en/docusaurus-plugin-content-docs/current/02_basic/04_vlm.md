---
sidebar_position: 2
sidebar_label: Vision-Language Model (VLM)
---

# Vision-Language Model (VLM)

VLM (Vision-Language Model) is a multimodal model that combines vision and language capabilities, understanding both image content and text semantics to enable visual understanding and language interaction. Typical applications include image Q&A, image captioning, scene understanding, and image-text retrieval.

| Hardware Requirements | Model | Performance Benchmark |
| --- | --- | --- |
| RDK S600 | Qwen3VL-8B | max context: 1024<br />TTFT (ms): 37.2<br />Decode (TPS): 35.1<br />memory (GB): 8.1 |


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
# Create folder and download models
# For more VLM models, see D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model/resolve_model_nash-p.md
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir Qwen3-VL-8B-Instruct
cd Qwen3-VL-8B-Instruct
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_vision_448x448_w8-4_nash-p_corenum_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_language_chunk_512_cache_1024_w4_nash-p_corenum_4_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_embed_tokens_w4_fp16.bin
```

## Launch the Case

```shell
# Run
cd ../../examples/vlm_demo/

# Load an image at startup, or use /image <image_path>; type exit to quit
bash run_vlm.sh qwen3vl_8b_config.json image0.jpg
```

## Result Demo

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/vlm2.mp4" type="video/mp4" />
 Your browser does not support the video tag.
</video>
