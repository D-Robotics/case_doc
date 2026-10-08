---
title: "概述"
description: "在 RDK S600 上完成 Pi0 与 Pi05 视觉语言动作模型的 LeRobot 训练、OELLM2.0 量化编译与板端部署运行。"
sidebar_position: 1
sidebar_label: 概述
---

# 概述

本文档汇总 pi0 / pi05（微调 ckpt 030000）从 LeRobot 训练、到 S600 量化编译、再到板端部署运行的完整链路，<br />以及各阶段已遇到的问题与解决方法。



## pi0 与 pi05 差异说明

| | pi05 | pi0 |
| --- | --- | --- |
| version | 0.5 | 0 |
| state 注入 | 无 token；<br />走 AdaRMSNorm(adarms) 调制 | state_proj(32→1024) + **前缀 state token** |
| time 注入 | time_mlp → adarms 调制 | action_time_mlp 与 action 拼接进输入 |
| prompt 长度 | 200 | 48 |
| action suffix | \[action_horizon\]（50） | \[state_token\] + \[action_horizon\]（51） |
| 引擎 time_horizon_ | 0 | 1 |
| enable_time_mod_lut | true | false |
| 运行时 state 注入 | inject_state=true（prompt 注入） | inject_state=false（走 state 张量） |
