---
title: "RDK S600 Application Cases Manual"
description: "A collection of typical RDK S600 application cases, from basic peripherals to on-device AI, multimodal interaction, and embodied intelligence."
sidebar_position: 1
---

# RDK S600 Application Cases Manual

This documentation collects typical application cases for the RDK S600 platform, organized by difficulty from basic peripheral integration to on-device AI inference, multimodal interaction, and embodied intelligence—helping you get started quickly and dive deeper step by step.

## Documentation Structure

### 1. Getting Started

Introduces how to connect and use common peripherals, helping you set up the hardware environment and verify basic functionality.

- **[USB Peripherals](/getting_started/usb_peripherals)**: Python examples for USB serial ports, USB cameras, and USB audio devices, including OpenCV image capture and sounddevice recording/playback.
- **[UART](/getting_started/uart)**: UART communication principles and pyserial usage, with an RS485 control demo using STS3215 bus servos.

### 2. Basic Cases

Deploy entry-level AI models on the S600 device, covering vision, audio, and LLM scenarios with complete environment setup, case launch, and result demonstration workflows.

- **[Object Detection](/basic/object_detection)**: Supporting image and USB camera real-time detection (120 fps on a single core).
- **[Voice-to-Text (ASR)](/basic/speech_to_text)**: Uses the Whisper-medium model to convert speech from a microphone or audio file to text in real time.
- **[Large Language Model (LLM)](/basic/llm)**: Deploy Qwen3-8B for text Q&A and conversational interaction in the terminal.
- **[Vision-Language Model (VLM)](/basic/vlm)**: Deploy Qwen3VL-8B for image-based Q&A and multimodal understanding.

### 3. Intermediate Cases

Combines multiple modality capabilities to build interaction experiences closer to real products.

- **[Multimodal Interactive Assistant](/intermediate/vlm_voice_dialogue)**: Combines Whisper-medium and Qwen3VL-8B with a USB microphone and camera for "voice + vision" multimodal dialogue—for example, asking "What do you see?"

### 4. Advanced Cases

For embodied intelligence scenarios, demonstrating PC simulation co-debugging and on-device deployment of the VLA (Vision-Language-Action) model, plus real-robot cases such as HoloBrain general object grasping and Pi0 & Pi05 towel folding.

- **[Vision-Language-Action Model (VLA)](/04_advanced/vla)**: Overview of the VLA cases, covering the three cases below.
  - **[Pi0 Hammer the Block (Simulation)](/advanced/vla)**: Deploy the RoboTwin simulation environment on PC and the Pi0 model on S600 for inference, covering PC simulation deployment, S600 on-device deployment, and run results.
  - **[HoloBrain General Object Grasping (Real Robot)](/advanced/vla/holobrain)**: Configure the HoloBrain environment on RDK S600, deploy the model, and run a general object-grasping task, covering hardware setup, environment setup, and start/stop. See [FAQ](/advanced/vla/holobrain#faq) for common issues.
  - **[Pi0 & Pi05 Fold the Towel (Real Robot)](/advanced/vla/pi0_pi05)**: Train Pi0 and Pi05 for the towel-folding task with LeRobot, quantize and compile with OELLM2.0, and deploy and run on-device; the training and deployment flow is covered in the [Pi0](/advanced/vla/pi0_pi05/pi0) and [Pi05](/advanced/vla/pi0_pi05/pi05) pages.

### 5. More Resources

Provides SDK documentation, quantization toolchain, S600 user manual, and extended reading on Pi0 quantization and real-robot deployment; see [References](/more_resources).

### 6. FAQ

Common issues encountered in practice, such as BPU memory allocation failures and HBM model format errors, with troubleshooting steps and solutions; see [FAQ](/qa).
