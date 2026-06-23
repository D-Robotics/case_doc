---
sidebar_position: 1
sidebar_label: Multimodal Interactive Assistant
---

# Multimodal Interactive Assistant

Combining ASR (Automatic Speech Recognition) with VLM (Vision-Language Model) enables "voice + vision" multimodal interaction—the system understands spoken input and combines it with the current scene for semantic understanding and interaction decisions. This is widely used in robotics, smart cockpits, smart terminals, and exhibition demos.

| Hardware Requirements | Models |
| --- | --- |
| RDK S600<br />USB Microphone<br />USB Camera | ASR: Whisper-medium<br />VLM: Qwen3VL-8B |

## Hardware Connection

- Connect the USB microphone to the USB port of the RDK S600 development board.
- Connect the USB camera to the USB port of the RDK S600 development board.  

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
# Confirm you have run the basic VLM and ASR demos; models should be downloaded and working
# Place asr_vlm_demo.tar (also available via wget) under D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/examples
cd D-Robotics_LLM_S600_1.0.2_SDK/oellm_runtime/examples
wget https://archive.d-robotics.cc/downloads/kol_test/asr_vlm_demo.tar

# Extract and enter the target folder
tar xvf asr_vlm_demo.tar
cd asr_vlm_demo

# Install dependencies
sudo apt update
sudo apt-get install libportaudio2 portaudio19-dev libsamplerate0-dev
# Build
bash build_asr_vlm_demo.sh

# Verify microphone
# List all devices and find the device name "MCP01"
aplay -l
#**** List of PLAYBACK Hardware Devices ****
#card 0: MCP01 [MCP01], device 0: USB Audio [USB Audio]
# Subdevices: 1/1
# Subdevice #0: subdevice #0

# Record 5 seconds and save to the current path; play on PC to verify microphone
# hw:0,0 corresponds to card 0 and device 0 above; adjust as needed
arecord -Dhw:0,0 -r 16000 -f S16_LE -t wav -d 5 ./record1.wav

# Verify USB camera
# Camera index defaults to 0
# After running, usb_image.jpg is saved to the current path; confirm the image is valid
python3 usb_cam.py
```

## Launch the Case

```shell
# In run_asr_vlm_demo.sh, use --mic_name to specify the microphone name, e.g. "MCP01"
# Run the demo and talk via the microphone; ask "What do you see?" and the model will describe the camera image
# Use a relatively quiet environment for best results!
bash run_asr_vlm_demo.sh
```

## Result Demo

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/vlm_voice_dialogue.mp4" type="video/mp4" />
 Your browser does not support the video tag.
</video>
