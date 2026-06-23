---
sidebar_position: 1
sidebar_label: USB Peripherals
---

# USB Peripherals

## Overview

USB (Universal Serial Bus) is a high-speed serial communication standard designed to unify PC peripheral interfaces. Its main advantages are plug-and-play, hot-plugging, and power delivery.

### Key Features

Topology: Strict host–device model; the host manages everything and supports tree expansion (up to 127 devices).

Differential signaling: Data is transmitted differentially on D+ and D− lines for strong noise immunity.

Speed generations: USB 2.0 reaches 480 Mbps; USB 3.x/4 reaches tens of Gbps.

Power delivery: Default 5 V, from 500 mA (2.0) up to 240 W (PD), enabling data transfer and charging at the same time.

Connector types: Type-A (common on hosts), Type-B (device side), Type-C (reversible, more capable), and others.

## Usage

Because USB is a general-purpose interface, different device types and protocols use different Python APIs. Below are three common Python–USB interfaces: USB serial, USB camera, and USB audio.

### USB Serial

Serial communication most often uses a USB-to-serial module (e.g. CH340, CP2102), which appears as a COM port on Windows or `/dev/ttyUSB0` on Linux. Use `pyserial`, installable via pip.

```text
pip install pyserial
```

Typical workflow: list available serial ports → open port → send/receive data → close port

```python
# Required imports
import serial
import serial.tools.list_ports

# List available serial ports
ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device, p.description)
    
# Open serial port
ser = serial.Serial(
    port='/dev/ttyUSB0',          # Adjust to your device
    baudrate=115200,              # Baud rate
    timeout=1                     # Read timeout (seconds); None blocks
)

# Send data
ser.write(b'Hello UART\r\n')

# Read data
data = ser.read(10) # Read 10 bytes; may return fewer on timeout

ser.close()
```

### USB Camera

USB cameras typically use the driverless UVC protocol and appear as video devices. OpenCV makes them easy to use; install via pip.

```text
pip install opencv-python
```

Typical workflow: open camera → set properties → read frames → release camera

```python
# Required imports
import cv2

# Open camera
cap = cv2.VideoCapture(0)

# Optional: set resolution and frame rate (must match device capabilities)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# Read frames in a loop
while True:    
    ret, frame = cap.read()   # ret is bool; frame is an image matrix 
        
    # Process image (display, analyze, etc.)
    # ...
    
cap.release()
```

### USB Audio

For USB audio devices, you usually do not need to handle USB protocols directly. These devices follow the USB Audio Class (UAC) standard and are exposed as regular audio devices by the OS. Python recommends `sounddevice` for recording and playback, with `soundfile` for WAV I/O.

Install dependencies:

```shell
pip install sounddevice soundfile numpy
```

Typical recording workflow:

```python
import sounddevice as sd
import soundfile as sf

duration = 5  # Recording duration in seconds
# Use default input device, or specify device=index after sd.query_devices()
samplerate = int(sd.query_devices(kind='input')['default_samplerate'])  # Device default sample rate
print(f"Recording at {samplerate} Hz ...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()  # Wait for recording to finish

sf.write('default_mic.wav', recording, samplerate)
print("Saved default_mic.wav")
```

Typical playback workflow:

```python
import sounddevice as sd
import soundfile as sf

data, samplerate = sf.read('default_mic.wav')
print(f"Playing at {samplerate} Hz ...")
sd.play(data, samplerate)
sd.wait()  # Wait for playback to finish
print("Playback complete")
```

## Example Applications

### USB Camera Example

#### Hardware Connection

Connect the USB camera to the USB port of the RDK S600 development board.

#### Software Call

The following Python example shows how to capture a frame with OpenCV:

```python
import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

ret, frame = cap.read()
if not ret:
    exit()

cv2.imwrite('capture.jpg', frame)
print("Screenshot saved as capture.jpg")

cap.release()
```

Save as e.g. `test_usb_camera.py`.

Connect the USB camera, then run `python3 test_usb_camera.py`. If successful, an image file appears in the current directory.

### USB Audio Example

#### Hardware Connection

Connect the USB microphone (or a USB camera with built-in mic) to the USB port of the RDK S600 development board.

#### Software Call

The following Python example records audio, plays it back, and saves a WAV file.

```python
import sounddevice as sd
import soundfile as sf
import numpy as np

devices = sd.query_devices()

# Input device
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

print(f"Recording... device index {in_idx}, sample rate {sr} Hz")
rec = sd.rec(int(3 * sr), samplerate=sr, channels=1, dtype='int16', device=in_idx)
sd.wait()
sf.write('usb_mic.wav', rec, sr)
print("Saved usb_mic.wav")

# Output device
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

print(f"Playing... device index {out_idx}, sample rate {dev_sr} Hz")
sd.play(rec, dev_sr, device=out_idx)
sd.wait()
print("Playback complete")
```

Save as e.g. `test_usb_audio.py`.

Connect a USB microphone (or a USB camera with built-in mic), then run `python3 test_usb_audio.py`. Speak during `Recording...`; playback runs during `Playing...`. The recording is saved as `usb_mic.wav`.
