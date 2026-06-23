---
sidebar_position: 3
sidebar_label: 大语言模型（LLM）
---

# 大语言模型（LLM）

LLM（Large Language Model，大语言模型）是一类基于海量文本数据训练的人工智能模型，具备自然语言理解与生成能力，可完成问答、翻译、摘要、代码生成等任务。典型代表包括 ChatGPT、GPT-4 和 Qwen 等。

|硬件要求 | 模型选择 | 性能 Benchmark |
| --- | --- | --- |
| RDK S600 | Qwen3-8B | max context：4096<br />TTFT(ms)：283.6<br />Decode(TPS)：31.4<br />memory(GB)：9.1 |

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
#LLM 更多模型获取方式请见 D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model/resolve_model_nash-p.md
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir Qwen3_8B
cd Qwen3_8B
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/Qwen3-8B/w4/Qwen3-8B_language_chunk_512_cache_4096_w4_nash-p_corenum_4_4.hbm
```

## 案例启动

```shell
#运行
cd ../../examples/llm_demo/

#在 run_llm.sh 中将 qwen3_1.7b_config.json 改为 qwen3_8b_config.json
#默认开启思考模式，关闭请将 json 文件中的 enable_thinking 设置为 false
#启动后在终端输入文字，exit 结束运行
bash run_llm.sh
```

## 效果展示

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/llm.mp4" type="video/mp4" />
 您的浏览器不支持 video 标签。
</video>
