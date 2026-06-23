---
sidebar_position: 1
sidebar_label: 目标检测
---

# 目标检测

Object Detection 是计算机视觉中的核心任务，主要用于从图像或视频中识别并定位目标对象（如人、车辆、动物等），通常通过边界框标注目标位置。其广泛应用于安防监控、自动驾驶、工业质检等场景，代表模型包括 YOLO、R-CNN、DETR 等系列。 

| 硬件要求 | 模型选择 | 性能 Benchmark |
| --- | --- | --- |
| RDK S600<br />USB 摄像头 | YOLO26x | 单核 120fps |


## 硬件连接

将 USB 摄像头接入 RDK S600 开发板的 USB 接口。

## 模型部署

### 环境准备

```shell
#该案例使用单核模型
#下载 yolo26x_demo.tar（也可通过 wget 方式获取）放到板端，并解压
wget https://archive.d-robotics.cc/downloads/kol_test/yolo26x_demo.tar
tar xvf yolo26x_demo.tar
```

### 案例启动

```bash
#进入指定路径
cd yolo26x_demo/ultralytics_yolo26/runtime/python

#指定图片进行检测，通过 --test-img 指定图片，通过 --model-path 指定模型
python3 main.py

#启动摄像头，通过 --camera-id 指定 usb 相机
#为保证可视化功能正常且流畅，建议通过 HDMI 连接屏幕，在桌面端开启终端输入指令
python3 main.py --camera-id 0
```

### 效果展示

<video controls width="100%" preload="metadata">
 <source src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/zh/effect.webm" type="video/webm" />
 您的浏览器不支持 video 标签。
</video>
