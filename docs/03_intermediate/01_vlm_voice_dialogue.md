---
sidebar_position: 1
sidebar_label: 多模态交互助手
---

# 多模态交互助手

ASR（自动语音识别）与 VLM（视觉语言模型）结合，可实现“语音 + 视觉”的多模态交互能力，使系统不仅能够理解用户语音内容，还能结合当前场景进行语义理解与交互决策，广泛应用于机器人、智能座舱、智能终端及展会交互等场景。

| 硬件要求 | 模型选择 |
| --- | --- |
| RDK S600<br />USB 麦克风<br />USB 摄像头 | ASR：Whisper-medium<br />VLM：Qwen3VL-8B |

## 硬件连接

- 将 USB 麦克风接入 RDK S600 开发板的 USB 接口。
- 将 USB 摄像头接入 RDK S600 开发板的 USB 接口。  

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
#请确认已经体验过低阶的 VLM 以及 ASR 两个 demo，相关模型已下载到指定文件，复现正常
#将 asr_vlm_demo.tar（也可通过 wget 方式获取）放到板端 D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/example 下
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/examples
wget https://archive.d-robotics.cc/downloads/kol_test/asr_vlm_demo.tar

#解压，进入指定文件夹
tar xvf asr_vlm_demo.tar
cd asr_vlm_demo

#安装依赖
sudo apt update
sudo apt-get install libportaudio2 portaudio19-dev libsamplerate0-dev
#编译
bash build_asr_vlm_demo.sh

#确认麦克风正常
#查看所有设备以及设备名称“MCP01”
aplay -l
#**** List of PLAYBACK Hardware Devices ****
#card 0: MCP01 [MCP01], device 0: USB Audio [USB Audio]
# Subdevices: 1/1
# Subdevice #0: subdevice #0

#录音 5 秒并保存到当前路径，完成后在 PC 端播放确认麦克风功能正常
#hw:0,0 对应上面的 card 0 以及 device 0，可根据实际情况更改
arecord -Dhw:0,0 -r 16000 -f S16_LE -t wav -d 5 ./record1.wav

#确认 usb 摄像头正常
#相机序号默认使用 0
#运行后将保存 usb_image.jpg 到当前路径，确保图片正常
python3 usb_cam.py
```

## 案例启动

```shell
#在 run_asr_vlm_demo.sh 脚本中使用--mic_name 指定麦克风名称，此处为“MCP01”
#运行 demo，通过麦克风进行对话，可以提问“你看到了什么”，大模型将描述摄像头拍摄的图片
#请在较为安静的环境中进行体验！
bash run_asr_vlm_demo.sh
```

## 效果展示

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/vlm_voice_dialogue.mp4" type="video/mp4" />
 您的浏览器不支持 video 标签。
</video>