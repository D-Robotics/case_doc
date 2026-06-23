---
sidebar_position: 4
sidebar_label: 视觉语言模型（VLM）
---

# 视觉语言模型（VLM）

VLM（Vision-Language Model，视觉语言模型）是一类融合视觉与语言能力的多模态模型，能够同时理解图像内容与文本语义，实现“看懂”图像并进行语言交互。典型应用包括看图问答、图像描述、场景理解和图文检索等。

| 硬件要求 | 模型选择 | 性能 Benchmark |
| --- | --- | --- |
| RDK S600 | Qwen3VL-8B | max context：1024<br />TTFT(ms)：37.2<br />Decode(TPS)：35.1<br />memory(GB)：8.1 |


## 环境准备

```shell
#配置环境内存空间并重启（若已经设置请忽略）
/usr/hobot/bin/hb_switch_ion.sh balanced
reboot

#下载 LLM_S600_SDK（也可通过 wget 方式），放置板端解压（已下载请忽略）
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
tar zxvf D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
```

```shell
#创建文件夹，下载模型
#VLM 更多模型获取方式请见 D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model/resolve_model_nash-p.md
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir Qwen3-VL-8B-Instruct
cd Qwen3-VL-8B-Instruct
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_vision_448x448_w8-4_nash-p_corenum_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_language_chunk_512_cache_1024_w4_nash-p_corenum_4_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/models/Qwen3-VL-8B-Instruct/w4/Qwen3-VL-8B-Instruct_embed_tokens_w4_fp16.bin
```

## 案例启动

```shell
#运行
cd ../../examples/vlm_demo/

#在启动时加载图片，也可输入 /image <image_path>加载，exit 结束运行
bash run_vlm.sh qwen3vl_8b_config.json image0.jpg
```

## 效果展示

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/vlm2.mp4" type="video/mp4" />
 您的浏览器不支持 video 标签。
</video>