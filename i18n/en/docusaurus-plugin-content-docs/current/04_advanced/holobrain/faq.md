---
title: "FAQ"
description: "Common issues and solutions for deploying and using HoloBrain general object grasping."
sidebar_position: 2
sidebar_label: 2. FAQ
---

# FAQ

## Q1: What if `apt` cannot locate a package?

```text
E: Unable to locate package ...
```

**A:** Run the following command to update the package index, then retry the install.

```bash
sudo apt update
```

## Q2: What if the `ros2` command is not found?

```text
ros2: command not found
```

**A:** Source the ROS 2 environment with the following commands.

```bash
source /opt/ros/jazzy/setup.bash
# If this is a RoboOrchard ROS 2 package, also run:
source ros2_package/install/setup.bash
```

## Q3: What if the `can_left` device is missing when you need it?

**A:** Check CAN devices with the following commands.

```bash
# List all recognized devices
ip link

# Check CAN mapping
bash teleop/find-all-can-port.sh
```

Confirm that the actual CAN devices have been renamed correctly to:

```text
can_left
can_right
```

## Q4: What if the camera has no image?

**A:** Check whether the camera is recognized with the following commands.

```bash
# First, confirm that the camera is recognized
rs-enumerate-devices

# Then check whether image topics exist
ros2 topic list | grep image

# Then inspect a specific image topic
ros2 topic hz <image_topic>
ros2 topic info <image_topic> -v
```

Key checks:

- USB connection is normal
- USB 3.0 is used
- Serial Number is configured correctly
- ROS 2 RealSense driver is running normally

## Q5: What if there is a NumPy / OpenCV / SciPy version conflict?

**A:** Reinstall the related dependencies with the following commands.

```bash
pip install \
    "numpy==1.26.4" \
    "opencv-python<4.11" \
    "scipy<1.14" \
    "numpydantic<1.7"
```

## Q6: How do I calibrate the pose relationship between the left arm and the middle camera? {#handeye-calib}

**A:**
- See the [calibration tutorial](https://horizonrobotics.github.io/robot_lab/holobrain/real_env/modules/handeye_calib.html).
- Pay attention to the `RoboOrchard/projects/HoloBrain/handeye_calib/launch_handeye_calib.sh` script configuration.
- After starting `./launch/start.sh`, start the calibration service with `bash handeye_calib/launch_handeye_calib.sh`.
- Short-press the button on the robotic arm until it turns green, then move the arm manually to different poses and click **Record Current Pose**.
- After recording multiple poses, click **Save and Compute Hand-Eye Calibration** to save the calibration file to the current path.
- Required materials: [aruco marker](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/aruco-100.svg) and a [stand for attaching the aruco marker](https://rdk-doc.oss-cn-beijing.aliyuncs.com/doc/img/samples/s600/zh/Unnamed2-M-COMA-340012-B_final_plate.stl).
