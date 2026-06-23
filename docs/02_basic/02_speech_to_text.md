---
sidebar_position: 2
sidebar_label: 语音转文字（ASR）
---

# 语音转文字（ASR）

ASR（Automatic Speech Recognition，自动语音识别）即语音转文字技术，是一种将人类语音实时转换为文本的技术，是语音助手、会议纪要、智能客服和语音输入等应用的重要基础。

| 硬件要求 | 模型选择 | 性能 Benchmark |
| --- | --- | --- |
| RDK S600 | Whisper-medium | max context：128<br />TTFT(ms)：110<br />Decode(TPS)：60.5<br />memory(GB)：1.9 |

## 环境准备

```shell
#配置环境内存空间并重启（若已经设置请忽略）
/usr/hobot/bin/hb_switch_ion.sh balanced
reboot

#下载 LLM_S600_SDK（也可通过 wget 方式），放置板端解压（已下载请忽略）
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
tar zxvf D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
```

```bash
#创建文件夹，下载模型
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/model
mkdir whisper_medium
cd whisper_medium
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/whisper-medium/w8/whisper-medium_audio_encode_duration_30s_sr_16k_w8_nash-p_corenum_4.hbm
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.0/models/whisper-medium/w8/whisper-medium_audio_decode_w8_nash-p_corenum_1_1.hbm
```

## 案例启动

```shell
#运行
cd ../../examples/whisper_demo/

#默认进行英文检测，中文可通过 json 文件中的 language 更换为 zh
bash run_whisper.sh
```

## 效果展示

```bash
root@ubuntu:~/D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/examples/whisper_demo# bash run_whisper.sh 
[UCP]: log level = 3
[UCP]: UCP version = 3.13.3
[VP]: log level = 3
[DNN]: log level = 3
[HPL]: log level = 3
[UCPT]: log level = 6
config_path: ./whisper_config.json
audio_path: ./0.wav
[I][11644][05-07][20:00:36:548][xlm_impl.cc:43][whisper][XlmImpl] max_batch_num is: 1
[I][11644][05-07][20:00:36:548][xlm_impl.cc:72][whisper][XlmImpl] Sampler chain sequence is currently determined by the order defined in the generation config. The built-in recommended sequence can be applied by setting use_sequence=false in model config.
[I][11644][05-07][20:00:36:548][xlm_impl.cc:144][whisper][XlmImpl] sampler_chain is: 
[BPU][[BPU_MONITOR]][281469625067712][INFO]BPULib verison(2, 2, 15)[f21ee84]!
[DNN]: 3.13.3_(4.8.1a2dev202512120401+7d8bb98.develop HBRT)
[I][11644][05-07][20:00:41:657][model_manager.cc:230][whisper][mod_mgr] Load hbm file '../../model/whisper_medium/whisper-medium_audio_encode_duration_30s_sr_16k_w8_nash-p_corenum_4.hbm' success.
[I][11644][05-07][20:00:41:657][model_manager.cc:252][whisper][mod_mgr] model_count_ is: 1
[I][11644][05-07][20:00:41:657][model_manager.cc:275][whisper][mod_mgr] Load dnn model success. hbm_name is: ../../model/whisper_medium/whisper-medium_audio_encode_duration_30s_sr_16k_w8_nash-p_corenum_4.hbm, model_name is: encode
[I][11644][05-07][20:00:42:999][model_manager.cc:230][whisper][mod_mgr] Load hbm file '../../model/whisper_medium/whisper-medium_audio_decode_w8_nash-p_corenum_1_1.hbm' success.
[I][11644][05-07][20:00:42:999][model_manager.cc:252][whisper][mod_mgr] model_count_ is: 2
[I][11644][05-07][20:00:42:999][model_manager.cc:275][whisper][mod_mgr] Load dnn model success. hbm_name is: ../../model/whisper_medium/whisper-medium_audio_decode_w8_nash-p_corenum_1_1.hbm, model_name is: decode
[I][11644][05-07][20:00:42:999][model_manager.cc:275][whisper][mod_mgr] Load dnn model success. hbm_name is: ../../model/whisper_medium/whisper-medium_audio_decode_w8_nash-p_corenum_1_1.hbm, model_name is: prefill
xlm init success
[Transcription]  Mr. Quilter is the apostle of the middle classes and we are glad to welcome his gospel.
[Performance] RTF: 0.085919 TTFT: 89.623000 ms TPS: 61.961324 tokens/s decode_tokens: 21
```
