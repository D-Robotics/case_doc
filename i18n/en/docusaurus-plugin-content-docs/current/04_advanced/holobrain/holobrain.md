---
sidebar_position: 1
sidebar_label: 1. HoloBrain General Object Grasping
---

# HoloBrain General Object Grasping

[HoloBrain](https://horizonrobotics.github.io/robot_lab/holobrain/) is a lightweight VLA foundation model from Horizon Robotics. It introduces an "embodied perception" architecture that fuses multi-view visual information with robot kinematics priors for stronger 3D spatial understanding and reasoning. A unified hybrid relative action space supports single-arm, dual-arm, and mobile manipulation platforms, breaking barriers across heterogeneous hardware. With only 0.2B parameters, it achieves industry-leading performance and SOTA results on benchmarks such as RoboTwin 2.0 and LIBERO, and supports complex long-horizon tasks including grasping, cloth folding, and deformable-object manipulation. Combined with the high-compute RDK S600 platform, HoloBrain enables real-time edge inference and a low-latency perception–decision–control loop, accelerating embodied AI applications. This document uses a general grasping task as an example and walks through environment setup, model deployment, and task execution of HoloBrain on RDK S600.

| Platform | RDK S600 Ubuntu 24.04 |
| :--- |:--- |
| ROS Version | ROS2 Jazzy |
| Model | [HoloBrain_v0.0_GD](https://huggingface.co/HorizonRobotics/HoloBrain_v0.0_GD) |
| Task | General object grasping |
| Performance (DECODE = 5) | wall=116.823ms <br/> text=9.3007ms <br/> enc=40.2941ms <br/> dec=54.6188ms |


## Hardware Setup

### Equipment List

<table style={{ width: '100%', tableLayout: 'fixed' }}>
  <thead>
    <tr>
      <th style={{ width: '30%', textAlign: 'left' }}>Device</th>
      <th style={{ width: '10%', textAlign: 'center' }}>Quantity</th>
      <th style={{ width: '60%', textAlign: 'center' }}>Image</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style={{ textAlign: 'left' }}>RDK S600 development kit</td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-s600.png" alt="S600" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>AgileX Piper robotic arm</td>
      <td style={{ textAlign: 'center' }}>2</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-piper-arm.png" alt="AgileX Piper robotic arm" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>Realsense D435i</td>
      <td style={{ textAlign: 'center' }}>3</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-realsense-d435i.png" alt="Realsense D435i" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>Robotic arm stand</td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-arm-stand.png" alt="Robotic arm stand" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>Wrist camera 3D-printed mount</td>
      <td style={{ textAlign: 'center' }}>2</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-wrist-camera-mount.png" alt="Wrist camera 3D-printed mount" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}><a href="https://github.com/HorizonRobotics/RoboOrchardHardware/blob/master/3d_print_assets/d435_mid_camera_mount(low).step">Head camera 3D-printed mount</a></td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-head-camera-mount.png" alt="Head camera 3D-printed mount" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>Small basket prop</td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-small-basket.png" alt="Small basket prop" width="30%" /></td>
    </tr>
  </tbody>
</table>

#### Assembly Result

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-assembly-overview.jpeg" alt="Assembly result" />


### Camera Check

#### Check USB Device Recognition

```shell
# Check whether USB devices are recognized
lsusb
```
<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-lsusb.png" alt="lsusb camera recognition" />

#### Query Serial Number

```shell
# Query Serial Number; this serial will be used in the HoloBrain project config launch.yaml
rs-enumerate-devices | grep Serial
```



<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-camera-serial.png" alt="RealSense Serial Number" />

#### Adjust the Middle Camera Position

The transform between the middle camera and the left arm is shown below. To ensure good results, adjust the middle camera so that the transform (position) is as close as possible to the figure. To determine the actual transform, see the calibration tutorial in [FAQ](./faq).

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-middle-camera-transform.png" alt="Transform between the middle camera and the left arm" width="40%"/>

### Configure Robotic Arm CAN Devices

#### List Existing CAN Devices

```shell
# List existing CAN devices
ip link show
```

#### Rename CAN Devices

```shell
# Rename CAN devices; adjust the commands to match the actual left/right arms. The arm names should be can_left and can_right
sudo ip link set canx name can_left
sudo ip link set canx name can_right
```

#### Configure CAN Baud Rate

```shell
# After renaming the CAN devices, configure the CAN baud rate
sudo ip link set can_left type can bitrate 1000000
sudo ip link set can_right type can bitrate 1000000
```

| Device | Purpose | Baud Rate |
| :--- |:--- |:--- |
| can_left | Left arm | 1Mbps |
| can_right | Right arm | 1Mbps |



:::info

The `ip link` configuration above is typically valid only for the current system session. After reboot, reconfigure it, or set it to start automatically via [systemd](https://developer.d-robotics.cc/rdk_s_doc/en/System_configuration/self_start?v=5.1.0&p=RDK+S600).

:::

## Environment Setup

### Install System Dependencies

:::tip

If `apt` reports that a package cannot be located, run `sudo apt update` first and then retry the install.

:::

```bash
sudo apt update
sudo apt install tmux \
    ros-jazzy-foxglove-bridge \
    ros-jazzy-rosbridge-server \
    ros-jazzy-realsense2-camera
```


| Package | Purpose |
| :--- |:--- |
| tmux | Terminal multiplexer for managing multiple background sessions |
| ros-jazzy-foxglove-bridge | Foxglove visualization bridge |
| ros-jazzy-rosbridge-server | ROS 2 WebSocket bridge service |
| ros-jazzy-realsense2-camera | Intel RealSense depth camera driver |

### Clone the RoboOrchard Repository

```bash
git clone https://github.com/HorizonRobotics/RoboOrchard

# Enter the RoboOrchard root directory
cd RoboOrchard
```

### Create a Python Virtual Environment

Run the following commands in the RoboOrchard root directory.

```bash
# Make sure the Python version is 3.12 before creating the environment
python3 -m venv venv/roboorchard-venv

# Activate the virtual environment and load ROS 2 Jazzy
source venv/roboorchard-venv/bin/activate
source /opt/ros/jazzy/setup.bash
```

If everything is set up correctly, the prompt should look like:

```text
(roboorchard-venv) root@drobot:~/VLA/holobrain/RoboOrchard#
```

To load them automatically, you can also add the source commands to `~/.bashrc`.

### Install RoboOrchard Development Dependencies

Run the following commands in the RoboOrchard root directory.

```bash
# Install RoboOrchard Python development dependencies, plus ROS 2 development, build, and related system dependencies
make dev-env
make ros2-dev-env

# Install the CPU version of PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install the RoboOrchard application
cd python/robo_orchard_inference_app
pip install .
```

### Build ROS 2 Packages

Run the following commands in the RoboOrchard root directory.

```bash
# Make sure the related environments are sourced
source venv/roboorchard-venv/bin/activate
source /opt/ros/jazzy/setup.bash

# Suppress Python warnings
export PYTHONWARNINGS="ignore"

# Build ROS 2 packages
make ros2-build

# Source the ROS 2 workspace after the build completes
source ros2_package/install/setup.bash
```

:::tip

If `make ros2-build` reports missing dependencies, run the following command first:

```bash
make ros2-dev-env
```

Then run again:

```bash
make ros2-build
```

:::

### HoloBrain Project Configuration

```bash
# Enter the HoloBrain project directory
cd projects/HoloBrain

# Install HoloBrain launch dependencies
pip install -r launch/requirements.txt
```

Edit the launch.yaml configuration as needed. Focus on the three camera serial numbers `XXX_CAMERA_SERIAL_NO`. For how to query the serial numbers, see [Hardware Setup - Camera Check](#camera-check).

```text
vim projects/HoloBrain/launch/launch.yaml
```

### Directory Structure

After deployment, the main directory structure is as follows:

```text
RoboOrchard
|-- LICENSE
|-- Makefile
|-- README.md
|-- projects
|   |-- HoloBrain
|-- pyproject.toml
|-- python
|   |-- robo_orchard_inference_app
|-- ros2_package
|   |-- Makefile
|   |-- README.md
|   |-- build
|   |-- install
|   |-- log
|   |-- requirements.txt
|   |-- robo_orchard_data_msg_ros2
|   |-- robo_orchard_data_ros2
|   |-- robo_orchard_deploy_ros2
|   |-- robo_orchard_handeye_calib_ros2
|   |-- robo_orchard_image_tools
|   |-- robo_orchard_pico_msg_ros2
|   |-- robo_orchard_piper_msg_ros2
|   |-- robo_orchard_piper_ros2
|   |-- robo_orchard_teleop_msg_ros2
|   |-- robo_orchard_teleop_ros2
|   |-- robo_orchard_wuji_glove_msg_ros2
|   |-- robo_orchard_wuji_glove_ros2
|-- scm
|   |-- lint
|   |-- qac
|   |-- requirements.txt
|-- venv
    |-- roboorchard-venv
```

## Start/Stop HoloBrain

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-architecture.png" alt="HoloBrain launch architecture" width="70%"/>

### Start the BPU Inference Service

```shell
cd ~
wget https://sdk.d-robotics.cc/downloads/rdk_demo/rdk_s600_demo/holobrain_runtime_S600.tar.gz
tar -xvf holobrain_runtime_S600.tar.gz

# Enter the script directory
cd ./holobrain_runtime_S600/cpp_hbm_ucp/runtime/script

# Run
DECODER_STEPS=5 sh run_hbm_http_server.sh
```

### Start holobrain_app

This script covers multiple functions such as ros_bridge, camera_service, robot_control, and inference; see launch.yaml for details.

1. Open a new terminal and run the following commands to start holobrain_app:

    ```bash
    # Enter RoboOrchard
    cd RoboOrchard

    # Make sure all environments are sourced before launch
    source venv/roboorchard-venv/bin/activate
    source /opt/ros/jazzy/setup.bash
    source ros2_package/install/setup.bash

    # Enter projects/HoloBrain
    cd projects/HoloBrain

    # Start
    ./launch/start.sh
    ```

2. After launch, you should see the following UI. Click the window numbers at the bottom to inspect each function, and make sure every function is running normally.

    <img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-tmux-runtime.png" alt="HoloBrain tmux runtime UI" />

3. Open `http://localhost:8501/` in a browser on the board.

4. Create a user, a task, and a description, then select the corresponding options on the right.

    <img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/en/holobrain-web-ui.png" alt="Horizon Robotics Lab Info UI" />

5. After making your selections, click **Start** to start the task, **Stop** to stop the task, and **Reset** to return the robotic arm to the zero position.



### Stop holobrain_app

In the tmux terminal, press `Ctrl+B`, then press `D` to detach from the tmux session.

```shell
# Kill all processes
./launch/stop.sh
```
