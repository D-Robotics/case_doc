---
sidebar_position: 1
sidebar_label: 1. HoloBrain 通用物体抓取
---

# HoloBrain 通用物体抓取

[HoloBrain](https://horizonrobotics.github.io/robot_lab/holobrain/) 是地平线推出的轻量化 VLA 基座模型，首创“具身感知”架构，融合多视角视觉信息与机器人运动学先验，实现更强的 3D 空间理解与推理能力。通过统一的混合相对动作空间，兼容单臂、双臂及移动操作平台，打破异构硬件壁垒。仅 0.2B 参数即可实现业界领先性能，在 RoboTwin 2.0、LIBERO 等基准测试中达到 SOTA 水平，并支持抓取、叠衣、柔性/变形物体操作等复杂长序列任务。结合 RDK S600 高算力平台，HoloBrain 可实现边缘端实时推理，构建感知—决策—控制全链路低延迟闭环，加速具身智能应用落地。本文将以通用抓取任务为例，详细介绍如何在 RDK S600 平台上完成 HoloBrain 的环境配置、模型部署及任务运行。

| 适用平台 | RDK S600 Ubuntu 24.04 |
| :--- |:--- |
| ROS 版本 | ROS2 Jazzy |
| 模型 | [HoloBrain_v0.0_GD](https://huggingface.co/HorizonRobotics/HoloBrain_v0.0_GD) |
| 任务 | 通用物体抓取 |
| 性能（DECODE = 5） | wall=116.823ms <br/> text=9.3007ms <br/> enc=40.2941ms <br/> dec=54.6188ms |


## 硬件准备

### 设备清单

<table style={{ width: '100%', tableLayout: 'fixed' }}>
  <thead>
    <tr>
      <th style={{ width: '30%', textAlign: 'left' }}>设备名称</th>
      <th style={{ width: '10%', textAlign: 'center' }}>数量</th>
      <th style={{ width: '60%', textAlign: 'center' }}>图片</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style={{ textAlign: 'left' }}>RDK S600 开发套件</td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-s600.png" alt="S600" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>松灵 Piper 机械臂</td>
      <td style={{ textAlign: 'center' }}>2</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-piper-arm.png" alt="松灵Piper机械臂" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}>Realsense D435i</td>
      <td style={{ textAlign: 'center' }}>3</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-realsense-d435i.png" alt="Realsense D435i" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}><a href="https://item.taobao.com/item.htm?abbucket=8&id=974751867024&mi_id=0000eLg1N9QR502J2CBUHxOfpRPt9cByxrbm1jAe-jpstnE&ns=1&priceTId=214783b717782310374276066e114a&spm=a21n57.1.hoverItem.1&utparam=%7B%22aplus_abtest%22%3A%226f11ecbc5161fe03b0256a3dbc22db84%22%7D&xxc=taobaoSearch">机械臂支架</a></td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-arm-stand.png" alt="机械臂支架" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}><a href="https://github.com/HorizonRobotics/RoboOrchardHardware/blob/master/3d_print_assets/d435_wrist_camera_mount.step">手部相机 3D 打印件</a></td>
      <td style={{ textAlign: 'center' }}>2</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-wrist-camera-mount.png" alt="手部相机3D打印件" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}><a href="https://github.com/HorizonRobotics/RoboOrchardHardware/blob/master/3d_print_assets/d435_mid_camera_mount(low).step">头部相机 3D 打印件</a></td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-head-camera-mount.png" alt="头部相机3D打印件" width="30%" /></td>
    </tr>
    <tr>
      <td style={{ textAlign: 'left' }}><a href="https://detail.tmall.com/item.htm?id=988515313979&mi_id=0000Kn0iHY9KaNACPRX0Uq7AJV4s4laPFF9Om5RV51ZlW1o&spm=tbpc.boughtlist.suborder_itemtitle.1.53352e8dwPWQLy">篮子道具-小号</a></td>
      <td style={{ textAlign: 'center' }}>1</td>
      <td style={{ textAlign: 'center' }}><img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-small-basket.png" alt="篮子道具-小号" width="30%" /></td>
    </tr>
  </tbody>
</table>

#### 组装效果

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-assembly-overview.jpeg" alt="组装效果" />


### 摄像头检查

#### 检查 USB 设备是否正常识别

```shell
#检查 USB 设备是否正常识别
lsusb
```
<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-lsusb.png" alt="lsusb 摄像头识别" />

#### 查询 Serial Number

```shell
#查询 Serial Number 前需先加载 ROS 2 环境
source /opt/ros/jazzy/setup.bash

#查询 Serial Number，该序列号在 HoloBrain 项目配置 -launch.yaml 中将会用到
rs-enumerate-devices | grep Serial
```



<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-camera-serial.png" alt="RealSense Serial Number" />

#### 调整中间摄像头位置

另外中间摄像头与左臂的变换关系如下，为保证效果，请调整中间摄像头位置，尽可能接近下图中摄像头和左臂的变换关系（position）。若需要确定实际变换关系，可参考 [FAQ](./faq) 中的标定教程

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-middle-camera-transform.png" alt="中间摄像头与左臂变换关系" width="40%"/>

### 配置机械臂 CAN 设备

#### 查看当前存在的 CAN 设备

```shell
#查看当前存在的can设备
ip link show
```

#### 重命名 CAN 设备

```shell
#对 CAN 进行重命名，根据实际左右臂情况更改以下指令，机械臂名称为 can_left 和 can_right
sudo ip link set canx name can_left
sudo ip link set canx name can_right
```

#### 配置 CAN 波特率

```shell
#完成 CAN 设备重命名后，配置 CAN 波特率
sudo ip link set can_left type can bitrate 1000000
sudo ip link set can_right type can bitrate 1000000
```

| 设备名称 | 用途 | 波特率 |
| :--- |:--- |:--- |
| can_left | 左机械臂 | 1Mbps |
| can_right | 右机械臂 | 1Mbps |

#### 启动 CAN 设备

```shell
#启动左右机械臂的 CAN 设备
sudo ifconfig can_left up
sudo ifconfig can_right up
```

可通过 `ifconfig` 命令查询 CAN 设备是否已启动：

```shell
#查询 CAN 设备是否已启动
ifconfig
```



:::info 说明

上述 `ip link` 配置通常只对当前系统运行周期有效。系统重启后需要重新配置，或者通过 [systemd 方式配置开机自动启动](https://developer.d-robotics.cc/rdk_s_doc/System_configuration/self_start?v=5.1.0&p=RDK+S600)。

:::

## 环境搭建

### 安装系统级依赖

:::tip 提示

如果 `apt` 命令提示找不到软件包，先执行 `sudo apt update` 后重新安装。

:::

```bash
sudo apt update
sudo apt install tmux \
    python3-colcon-common-extensions \
    ros-jazzy-rosidl-default-generators \
    ros-jazzy-ament-cmake-auto \
    ros-jazzy-ament-lint-auto \
    ros-jazzy-ros2launch \
    ros-jazzy-foxglove-bridge \
    ros-jazzy-rosbridge-server \
    ros-jazzy-realsense2-camera
```


| 软件包 | 作用 |
| :--- |:--- |
| tmux | 终端复用器，用于管理多个后台会话 |
| python3-colcon-common-extensions | colcon 常用扩展，ROS 2 构建工具 |
| ros-jazzy-rosidl-default-generators | ROS 接口定义语言默认代码生成器 |
| ros-jazzy-ament-cmake-auto | ament 构建系统的 CMake 自动配置 |
| ros-jazzy-ament-lint-auto | ament 代码规范检查自动配置 |
| ros-jazzy-ros2launch | ROS 2 launch 启动文件工具 |
| ros-jazzy-foxglove-bridge | Foxglove 可视化桥接 |
| ros-jazzy-rosbridge-server | ROS 2 WebSocket 桥接服务 | 
| ros-jazzy-realsense2-camera | Intel RealSense 深度相机驱动| 




### 克隆 RoboOrchard 仓库

```bash
git clone https://github.com/wunuo1/RoboOrchard

#进入 RoboOrchard 根目录
cd RoboOrchard
```

### 创建 Python 虚拟环境

在 RoboOrchard 根目录执行以下命令。

```bash
#创建前请确保 python 版本为 3.12
python3 -m venv venv/roboorchard-venv

#激活虚拟环境，加载 ROS 2 Jazzy 环境
source venv/roboorchard-venv/bin/activate
source /opt/ros/jazzy/setup.bash
```

正常情况下终端提示符会出现：

```text
(roboorchard-venv) root@drobot:~/VLA/holobrain/RoboOrchard#
```

如果希望自动加载，也可以将相关 source 命令加入 `~/.bashrc`。

### 安装 RoboOrchard 开发依赖

在 RoboOrchard 根目录执行以下命令。

```bash
#安装 RoboOrchard Python 开发环境相关依赖， ROS 2 开发、构建以及相关系统依赖
make dev-env
make ros2-dev-env

#安装 CPU 版本 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 安装 RoboOrchard 应用
cd python/robo_orchard_inference_app
pip install .
```

### 构建 ROS 2 软件包

在 RoboOrchard 根目录下执行以下命令。

```bash
#确保已 source 相关环境
source venv/roboorchard-venv/bin/activate
source /opt/ros/jazzy/setup.bash

#屏蔽 Python Warning
export PYTHONWARNINGS="ignore"

#构建 ROS 2功能包
make ros2-build

#构建完成后加载 ROS 2 工作空间
source ros2_package/install/setup.bash
```

:::tip 提示

如果执行 `make ros2-build` 报依赖缺失，先执行以下命令：

```bash
make ros2-dev-env
```

然后重新执行：

```bash
make ros2-build
```

:::

### HoloBrain 项目配置

```bash
#进入 HoloBrain 项目目录
cd projects/HoloBrain

#安装 HoloBrain 启动依赖
pip install -r launch/requirements.txt
```

根据具体情况更改 launch.yaml 配置，主要关注三组摄像头序列号 `XXX_CAMERA_SERIAL_NO`，序列号查询方式见 [硬件说明-摄像头检查](#摄像头检查)。

```text
vim projects/HoloBrain/launch/launch.yaml
```

### 文件结构

完成部署后，主要目录结构如下：

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

## 启动/停止 HoloBrain

<img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-architecture.png" alt="HoloBrain 启动架构" width="70%"/>

### 启动 BPU 推理服务

```shell
cd ~
wget https://sdk.d-robotics.cc/downloads/rdk_demo/rdk_s600_demo/holobrain_runtime_S600.tar.gz
tar -xvf holobrain_runtime_S600.tar.gz

#进入 script 文件
cd ./holobrain_runtime_S600/cpp_hbm_ucp/runtime/script

#运行
DECODER_STEPS=5 sh run_hbm_http_server.sh
```

### 启动 holobrain_app

该脚本包含 ros_bridge, camera_service, robot_control, inference 等多个功能，具体请查阅 launch.yaml。

1. 打开新终端，执行以下命令启动 holobrain_app：

    ```bash
    #进入 RoboOrchard
    cd RoboOrchard

    #启动前请确保终端已经 source 所有环境
    source venv/roboorchard-venv/bin/activate
    source /opt/ros/jazzy/setup.bash
    source ros2_package/install/setup.bash

    #进入 projects/HoloBrain
    cd projects/HoloBrain

    #启动
    ./launch/start.sh
    ```

2. 启动后可看到以下界面，点击界面底部的窗口号，可查看各功能的运行情况，请确保各功能运行正常。

    <img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-tmux-runtime.png" alt="HoloBrain tmux 运行界面" />

3. 在板端浏览器打开 `http://localhost:8501/`

4. 创建用户，任务以及描述，并在右侧选择对应选项。

    <img src="https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/holobrain-web-ui.png" alt="Horizon Robotics Lab Info 界面" />

5. 选择完成后，点击 **Start** 开始任务，**Stop** 停止任务，**Reset** 可让机械臂归到零位。

  

### 停止 holobrain_app 

在 tmux 终端界面，按 `Ctrl+B`，然后再按 `D`，退出 tmux 界面。

```shell
#杀掉所有进程
./launch/stop.sh
```
