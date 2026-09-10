---
title: "FAQ"
description: "HoloBrain 通用物体抓取部署与使用过程中的常见问题与解决方法。"
sidebar_position: 2
sidebar_label: 2. FAQ
---

# FAQ

## Q1：执行 `apt` 命令找不到软件包怎么办？

```text
E: Unable to locate package ...
```

**A：** 执行以下命令更新软件源，然后尝试重新安装。

```bash
sudo apt update
```

## Q2：执行 `ros2` 命令找不到命令怎么办？

```text
ros2: command not found
```

**A：** 执行以下命令加载 ROS 2 环境。

```bash
source /opt/ros/jazzy/setup.bash
#如果是 RoboOrchard 的 ROS 2 package，还需要执行以下命令：
source ros2_package/install/setup.bash
```

## Q3：需要使用到 `can_left` 设备的时候找不到 `can_left` 设备怎么办？

**A：** 执行以下命令检查 CAN 设备。

```bash
#列出识别到的所有的设备
ip link

#检查 CAN 映射
bash teleop/find-all-can-port.sh
```

确认实际 CAN 设备已经被正确重命名为：

```text
can_left
can_right
```

## Q4：相机没有图像怎么办？

**A：** 执行以下命令检查相机是否被正常识别。

```bash
#首先检查，确认相机被正常识别
rs-enumerate-devices

#然后检查是否存在图像 Topic
ros2 topic list | grep image

#再检查具体图像 Topic
ros2 topic hz <image_topic>
ros2 topic info <image_topic> -v
```

重点检查：

- USB 连接是否正常
- 是否使用 USB 3.0
- Serial Number 是否配置正确
- ROS 2 RealSense driver 是否正常启动

## Q5：NumPy / OpenCV / SciPy 版本冲突怎么办？

**A：** 执行以下命令重新安装相关依赖。

```bash
pip install \
    "numpy==1.26.4" \
    "opencv-python<4.11" \
    "scipy<1.14" \
    "numpydantic<1.7"
```

## Q6：如何标定左臂与中间摄像头的位置关系？ {#handeye-calib}

**A：** 
- 参考 [标定教程](https://horizonrobotics.github.io/robot_lab/holobrain/real_env/modules/handeye_calib.html)。
- 注意 `RoboOrchard/projects/HoloBrain/handeye_calib/launch_handeye_calib.sh` 脚本配置。
- 启动 `./launch/start.sh` 之后，启动标定服务 `bash handeye_calib/launch_handeye_calib.sh`。
- 短按机械臂上的按钮变为绿色，即可手动移动机械臂，移动至不同的位置并单击 **Record Current Pose**。
- 记录多个位置之后点击 **Save and Compute Hand-Eye Calibration**，保存标定文件到当前路径下。
- 所需物料：[aruco marker](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/aruco-100.svg) 以及可粘贴 [aruco marker 的支架](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/Unnamed2-M-COMA-340012-B_final_plate.stl)。

