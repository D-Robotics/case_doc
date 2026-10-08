---
title: "Overview"
description: "Train the Pi0 and Pi05 vision-language-action models with LeRobot, quantize and compile them with OELLM2.0, and deploy them on the RDK S600."
sidebar_position: 1
sidebar_label: Overview
---

# Overview

This document covers the full pipeline of pi0 / pi05 (fine-tuned checkpoint 030000), from LeRobot training through S600 quantization and compilation to on-device deployment and running, as well as the issues encountered at each stage and how to resolve them.



## Differences between pi0 and pi05

| | pi05 | pi0 |
| --- | --- | --- |
| version | 0.5 | 0 |
| state injection | no token;<br />uses AdaRMSNorm (adarms) modulation | state_proj (32→1024) + **prefix state token** |
| time injection | time_mlp → adarms modulation | action_time_mlp concatenated with the action into the input |
| prompt length | 200 | 48 |
| action suffix | \[action_horizon\] (50) | \[state_token\] + \[action_horizon\] (51) |
| engine time_horizon_ | 0 | 1 |
| enable_time_mod_lut | true | false |
| runtime state injection | inject_state=true (injected into the prompt) | inject_state=false (uses the state tensor) |
