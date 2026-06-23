[English](./README_EN.md) | 简体中文

# 文档仓库

本仓库是 RDK S600 应用开发文档站点源码，基于 Docusaurus 构建，包含中文主文档、英文文档翻译、站点主题定制。

## 仓库结构概览

主要目录说明如下：

- `docs/`：中文文档主内容
- `i18n/en/docusaurus-plugin-content-docs/current/`：英文文档内容
- `scripts/`：文档维护与构建辅助脚本（编号、链接修复、范围构建等）
- `src/`：主题定制、插件与 remark 扩展
- `static/`：静态资源
- `.github/workflows/`：CI/CD 工作流（Pages 部署与 OSS 同步）
- `docusaurus.config.js`：站点主配置
- `sidebars.js`：文档侧边栏配置入口

## 环境准备

- Node.js：`>= 18`
- 包管理：`npm`

```bash
# 日常开发快速安装（会按 semver 更新依赖）
npm install
```

## 文档维护流程

推荐按以下顺序执行：

```bash
# 1) 本地预览（中文）
npm run start

# 2) 本地预览（英文）
npm run start:en

# 3) 提交前执行完整构建校验
npm run build

# 4) 本地托管 build 产物进行验证
npm run serve
```

## 维护常用命令

### 内容与结构维护

```bash
# 生成侧边栏范围配置（Doc Scope）
npm run generate-sidebar-config

# 开发时监听文档变化，自动更新侧边栏范围配置
npm run watch-sidebar-config
```

### 本地运行

```bash
# 中文开发模式（包含侧边栏配置监听）
npm run start

# 英文开发模式（包含侧边栏配置监听）
npm run start:en

# 中文开发模式，使用 3001 端口
npm run start:port

# 中文开发模式（不启动监听）
npm run start:no-watch

# 英文开发模式（不启动监听）
npm run start:no-watch:en

# 清理 Docusaurus 缓存
npm run clear
```

### 构建与产物验证

```bash
# 标准全量构建
npm run build

# 本地预览 build 目录
npm run serve

# 指定 host 和 port 预览（示例）
npm run serve -- --host=10.64.62.34 --port=1688 --no-open

```

常见访问路径（端口以实际 `serve` 输出为准）：
- 英文：`http://localhost:3000/en/case_doc/case`
- 中文：`http://localhost:3000/case_doc/case`



