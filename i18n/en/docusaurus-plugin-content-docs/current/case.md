---
sidebar_position: 1
slug: /case
---

# RDK S600 Application Cases

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

- **[Multimodal Interactive Assistant)](/intermediate/vlm_voice_dialogue)**: Combines Whisper-medium and Qwen3VL-8B with a USB microphone and camera for "voice + vision" multimodal dialogue—for example, asking "What do you see?"

### 4. Advanced Cases

For embodied intelligence scenarios, demonstrating on-device VLA (Vision-Language-Action) model deployment and PC simulation co-debugging.

- **[Vision-Language-Action Model (VLA)](/advanced/vla)**: Deploy the RoboTwin simulation environment on PC and the Pi0 model on S600 for inference, covering PC simulation deployment, S600 on-device deployment, and run results.

### 5. More Resources

Provides SDK documentation, quantization toolchain, S600 user manual, and extended reading on Pi0 quantization and real-robot deployment.

### 6. FAQ

Common issues encountered in practice, such as BPU memory allocation failures and HBM model format errors, with troubleshooting steps and solutions.
