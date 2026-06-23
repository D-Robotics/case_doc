---
sidebar_position: 1
sidebar_label: USB 外设使用
---

# USB 外设使用

## 外设介绍

USB（通用串行总线）是为了统一电脑外设接口而生的高速串行通信标准，最大特点是即插即用和热插拔，同时能供电。

### 核心特征

拓扑结构：严格的主从模式，主机（Host）管理一切，支持树状扩展（最多 127 个设备）。

差分信号：用 D+、D- 两根数据线差分传输，抗干扰强。

速度代际：USB 2.0 达 480 Mbps，USB 3.x/4 更高达数十 Gbps。

供电能力：默认 5V，最大从 500mA (2.0) 提升到最高 240W (PD 协议)，可边传数据边充电。

接口多样：Type-A（主机常见）、Type-B（设备端）、Type-C（正反插，功能更全）等。

## 使用方法

由于 USB 是一类通用接口，对于不同类型、不同协议的 USB 设备，Python 提供了不同接口，下面介绍 3 种常见的 Python-USB 接口：USB 串口、USB 摄像头和 USB 语音设备。

### USB 串口

串口通信最常见就是通过 USB 转串口模块（如 CH340、CP2102）连接设备，在电脑上映射成一个 COM 口（Linux 下是 `/dev/ttyUSB0` 等）。Python 里推荐用 `pyserial`，可以使用 pip 安装。

```text
pip install pyserial
```

一般调用流程：列出可用的串口设备 --> 打开串口 --> 发送/接收数据 --> 关闭串口

```python
# 必要的引用
import serial
import serial.tools.list_ports

# 列出可用串口
ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device, p.description)
    
# 打开串口
ser = serial.Serial(
    port='/dev/ttyUSB0',          # 根据实际选择
    baudrate=115200,              # 波特率
    timeout=1                     # 读超时（秒），设为 None 则阻塞
)

# 发送数据
ser.write(b'Hello UART\r\n')

# 读取数据
data = ser.read(10) # 读 10 个字节，超时返回少于 10 字节

ser.close()
```

### USB 摄像头

USB 摄像头一般是免驱 UVC 协议，在系统里被识别为视频设备，用 OpenCV 调用非常方便，可以使用 pip 安装。

```text
pip install opencv-python
```

一般调用流程：打开摄像头 --> 设置摄像头属性 --> 读取视频帧 --> 关闭摄像头

```python
# 必要的引用
import cv2

# 打开摄像头
cap = cv2.VideoCapture(0)

# 可选：设置分辨率和帧率，要根据实际设备支持的分辨率来设定
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# 循环读取视频帧
while True:    
    ret, frame = cap.read()   # ret 为布尔值，frame 是图像矩阵 
        
    # 处理图像（如显示、分析） 
    # ...
    
cap.release()
```

### USB 音频设备

对于 USB 音频设备，绝大多数情况下也不需要直接操作 USB 协议。这些设备遵循标准的 USB Audio Class（UAC）规范，操作系统会直接识别成常规音频设备。Python 推荐使用 `sounddevice` 库进行录音和播放，配合 `soundfile` 轻松读写 WAV 文件。

安装依赖：

```shell
pip install sounddevice soundfile numpy
```

一般录音流程：

```python
import sounddevice as sd
import soundfile as sf

duration = 5  # 录音秒数
# 使用默认输入设备，也可通过 sd.query_devices() 查看设备列表后指定 device=索引
samplerate = int(sd.query_devices(kind='input')['default_samplerate'])  # 使用设备默认采样率
print(f"录音中，采样率 {samplerate} Hz ...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()  # 等待录音结束

sf.write('default_mic.wav', recording, samplerate)
print("已保存 default_mic.wav")
```

一般播放流程为：

```python
import sounddevice as sd
import soundfile as sf

data, samplerate = sf.read('default_mic.wav')
print(f"播放中，采样率 {samplerate} Hz ...")
sd.play(data, samplerate)
sd.wait()  # 等待播放结束
print("播放完毕")
```

## 示例应用

### USB 摄像头使用

#### 硬件连接

将 USB 摄像头接入 RDK S600 开发板的 USB 接口。

#### 软件调用

以 Python 为例，下面展示如何使用 OpenCV 调用 Camera，

```python
import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

ret, frame = cap.read()
if not ret:
    exit()

cv2.imwrite('capture.jpg', frame)
print("截图已保存为 capture.jpg")

cap.release()
```

将程序保存为文件，例如 `test_usb_camera.py`。

保证 USB 摄像头接入了设备，然后使用 `python3 test_usb_camera.py` 运行，如果正常就可以看到目录下保存了图片文件。

### USB 音频设备使用

#### 硬件连接

将 USB 麦克风（或带麦克风的 USB 摄像头等）设备接入 RDK S600 开发板的 USB 接口。

#### 软件调用

以 Python 为例，下面展示如何录制一段音频，播放并保存为 WAV 文件。

```python
import sounddevice as sd
import soundfile as sf
import numpy as np

devices = sd.query_devices()

# 输入设备
in_idx = sd.default.device[0]
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0 and 'USB' in d['name']:
        in_idx = i
        break

rates = [96000, 48000, 44100, 32000, 22050, 16000, 11025, 8000]
sr = 48000
for r in rates:
    try:
        sd.check_input_settings(device=in_idx, samplerate=r, channels=1, dtype='int16')
        sr = r
        break
    except:
        pass

print(f"录音中... 设备索引 {in_idx}，采样率 {sr} Hz")
rec = sd.rec(int(3 * sr), samplerate=sr, channels=1, dtype='int16', device=in_idx)
sd.wait()
sf.write('usb_mic.wav', rec, sr)
print("已保存 usb_mic.wav")

# 输出设备
out_idx = sd.default.device[1]
for i, d in enumerate(devices):
    if d['max_output_channels'] > 0 and 'USB' in d['name']:
        out_idx = i
        break

dev_sr = int(devices[out_idx]['default_samplerate'])

if sr != dev_sr:
    dur = len(rec) / sr
    n = int(dur * dev_sr)
    if rec.ndim == 1:
        rec = np.interp(np.linspace(0, len(rec) - 1, n), np.arange(len(rec)), rec)
    else:
        out = np.zeros((n, rec.shape[1]))
        for c in range(rec.shape[1]):
            out[:, c] = np.interp(np.linspace(0, len(rec) - 1, n), np.arange(len(rec)), rec[:, c])
        rec = out.astype(rec.dtype)

print(f"播放中... 设备索引 {out_idx}，采样率 {dev_sr} Hz")
sd.play(rec, dev_sr, device=out_idx)
sd.wait()
print("播放完毕")
```

将程序保存为文件，例如 `test_usb_audio.py`。 

保证 USB 麦克风（或带麦克风的 USB 摄像头等）已接入设备，然后使用 `python3 test_usb_audio.py` 运行，根据输出提示，`录音中...` 时说话，`播放中...` 时将录音内容播放，录音内容保存为 `usb_mic.wav` 。
