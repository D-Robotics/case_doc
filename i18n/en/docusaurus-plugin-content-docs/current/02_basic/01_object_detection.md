---
sidebar_position: 1
sidebar_label: Object Detection
---

# Object Detection

Object Detection is a core task in computer vision, primarily used to identify and locate target objects (such as people, vehicles, and animals) in images or video, typically by annotating target positions with bounding boxes. It is widely used in security surveillance, autonomous driving, industrial inspection, and similar scenarios. Representative model families include YOLO, R-CNN, and DETR.

| Hardware Requirements | Model | Performance Benchmark |
| --- | --- | --- |
| RDK S600<br />USB Camera | YOLO26x | 120 fps (single core) |


## Hardware Connection

Connect the USB camera to the USB port of the RDK S600 development board.

## Model Deployment

### Environment Setup

```shell
# This case uses a single-core model
# Download yolo26x_demo.tar (also available via wget), place on the board, and extract
wget https://archive.d-robotics.cc/downloads/kol_test/yolo26x_demo.tar
tar xvf yolo26x_demo.tar
```

### Launch the Case

```bash
# Enter the target path
cd yolo26x_demo/ultralytics_yolo26/runtime/python

# Run detection on an image; use --test-img for the image and --model-path for the model
python3 main.py

# Start the camera; use --camera-id to specify the USB camera
# For smooth visualization, connect a display via HDMI and run the command in a desktop terminal
python3 main.py --camera-id 0
```

### Result Demo

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/effect.webm" type="video/webm" />
 Your browser does not support the video tag.
</video>
