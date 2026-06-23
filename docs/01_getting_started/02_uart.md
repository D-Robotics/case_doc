---
sidebar_position: 2
sidebar_label: UART 使用
---

# UART 使用

## 外设介绍

UART（通用异步收发传输器）是最基础的点对点串行通信接口，仅需 TX、RX 和 GND 三根线即可实现双向传输，常用于调试、传感器、舵机等场景。

### 核心特征

全双工异步：发送与接收独立，双方无需共享时钟，依靠约定的波特率同步。

波特率：常见 9600、115200 等，通信双方必须一致。

帧格式：1 起始位 + 5~9 数据位（通常 8 位）+ 可选校验位 + 1/2 停止位。

电平：芯片直出为 TTL/CMOS 电平，可通过转换芯片变为 RS-232、RS-485 等以延长距离。

板载资源：RDK 的 40pin 引脚提供多路 UART，对应设备节点如 /dev/ttyS0、/dev/ttyAMA0 等。

## 使用方法

Python 中可以使用 pyserial 操作 UART，使用如下 pip 命令安装，方式同 USB 串口描述一致：

```shell
pip install pyserial
```

一般调用流程：列出可用的串口设备 → 打开串口 → 发送/接收数据 → 关闭串口

```python
# 必要的引用
import serial
import serial.tools.list_ports

# 列出可用串口
ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device, p.description)
    
# 打开板载 UART，例如 /dev/ttyACM0，请根据实际接线选择
ser = serial.Serial(
    port='/dev/ttyACM0', # 根据实际设备节点选择
    baudrate=115200, # 波特率
    timeout=1 # 读超时（秒），设为 None 则阻塞
    )
    
# 发送数据
ser.write(b'Hello UART\r\n')
# 读取数据
data = ser.read(10) # 读 10 个字节，超时返回可能不足 10 字节
ser.close()
```

## 示例应用

### 总线舵机使用

以 STS3215 总线舵机为例。

该舵机总线需要 RS485 电平才可正常通信，使用合适的控制板/转接板将板卡发出的 USB/TTL 电平转换为 RS485 电平。

该舵机使用 FT-SCS 自定义协议，协议的命令帧如下：

| 字头 | ID 号 | 数据长度 | 指令 | 参数 | 校验和 |
| --- | --- | --- | --- | --- | --- |
| 0xFF 0xFF | ID | Length | Instruction | Parameter1 …Parameter N | Check Sum |

查阅舵机手册获取数据长度、写指令、参数等信息，控制舵机角度对应的数据长度为 `0x04`，写指令为 `0x03`，参数有 3 个：`目标位置段地址 0x2A`，`目标位置低 8 位`，`目标位置高 8 位`。目标位置的取值范围：-32767 ~ 32767，BIT15 为符号位。

例：欲控制 ID 为 1 的舵机角度为 10000，需要按在一帧串口通信中发送以下内容，然后停止。

| Byte0 | Byte1 | Byte2 | Byte3 | Byte4 | Byte5 | Byte6 | Byte7 | Byte8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0xFF | 0xFF | 0x01 | 0x05 | 0x03 | 0x2A | 0x27 | 0x10 | 0x6A |

下方程序可以使用 S600 的 `/dev/ttyS7` 串口，控制 ID 为 1 的总线舵机角度在 2000±200 之间来回摆动。

```python
import serial
import time

ser = serial.Serial('/dev/ttyS7', 1000000, timeout=0.1)

def write(addr, data):
    cmd = bytearray([0xff, 0xff, 1, len(data) + 3, 0x03, addr]) + data
    s = sum(cmd[2:]) & 0xff
    cmd.append((~s) & 0xff)
    ser.write(cmd)
    time.sleep(0.001)

while True:
    # 1800
    write(0x2a, bytearray([0x08, 0x07, 0, 0, 0xe8, 0x03]))
    time.sleep(1)
    # 2200
    write(0x2a, bytearray([0x98, 0x08, 0, 0, 0xe8, 0x03]))
    time.sleep(1)
```
