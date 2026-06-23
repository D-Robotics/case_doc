---
sidebar_position: 1
slug: /case
---

# RDK S600 应用案例

本文档汇总 RDK S600 平台典型应用案例，从基础外设接入到端侧 AI 推理，再到多模态交互与具身智能，按难度递进组织，便于快速上手并逐层深入。

## 文档结构

### 1. 入门案例

介绍常用外设的接入与使用方法，帮助完成硬件环境搭建与基础功能验证。

- **[USB 外设使用](/getting_started/usb_peripherals)**：涵盖 USB 串口、USB 摄像头与 USB 语音设备的 Python 调用示例，包括 OpenCV 采图、sounddevice 录音播放等。
- **[UART 使用](/getting_started/uart)**：介绍 UART 通信原理与 pyserial 调用流程，并以 STS3215 总线舵机为例演示 RS485 控制。

### 2. 低阶案例

在 S600 端侧部署入门级 AI 模型，覆盖视觉、语音与大模型三类典型场景，提供完整的环境准备、案例启动与效果展示流程。

- **[目标检测](/basic/object_detection)**：基于 robogo 平台 YOLO26x 的标注、训练、量化与部署，支持图片与 USB 摄像头实时检测（单核 120fps）。
- **[语音转文字（ASR）](/basic/speech_to_text)**：使用 Whisper-medium 模型，将麦克风或音频文件中的语音实时转为文本。
- **[大语言模型（LLM）](/basic/llm)**：部署 Qwen3-8B，在终端进行文字问答与对话交互。
- **[视觉语言模型（VLM）](/basic/vlm)**：部署 Qwen3VL-8B，支持基于图片的看图问答与图文理解。

### 3. 进阶案例

将多种模态能力组合，构建更接近真实产品的交互体验。

- **[多模态交互助手](/intermediate/vlm_voice_dialogue)**：结合 Whisper-medium 与 Qwen3VL-8B，通过 USB 麦克风与摄像头实现“语音 + 视觉”多模态对话，例如向系统提问“你看到了什么”。

### 4. 高阶案例

面向具身智能场景，展示视觉-语言-动作（VLA）模型的端侧部署与 PC 仿真联调。

- **[视觉语言动作模型（VLA）](/advanced/vla)**：在 PC 端部署 RoboTwin 仿真环境，在 S600 端侧部署 Pi0 模型进行推理，涵盖 PC 仿真部署、S600 端侧部署与运行结果展示。

### 5. 参考资料

提供更详细的 SDK 文档、量化工具链、S600 用户手册，以及 Pi0 量化与真机部署等扩展阅读材料。

### 6. FAQ

汇总案例实践中的常见问题，例如 BPU 内存分配失败、HBM 模型格式错误等，并给出排查与解决方法。
