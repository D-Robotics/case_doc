[English](./README.md) | 简体中文

# Documentation Repository

This repository contains the source code for the RDK case development documentation site, built with Docusaurus. It includes the main Chinese documentation, English translations, site theme customization.

## Repository Structure Overview

The main directories are described as follows:

- `docs/`: Main content of the Chinese documentation
- `i18n/en/docusaurus-plugin-content-docs/current/`: English documentation content
- `scripts/`: Maintenance and build helper scripts (numbering, link fixing, scope building, etc.)
- `src/`: Theme customization, plugins, and remark extensions
- `static/`: Static assets
- `.github/workflows/`: CI/CD workflows (Pages deployment and OSS synchronization)
- `docusaurus.config.js`: Main site configuration
- `sidebars.js`: Entry point for document sidebar configuration

## Environment Setup

- Node.js: `>= 18`
- Package manager: `npm`

```bash
#  Quick installation for daily development (updates dependencies according to semver)
npm install
```

## Documentation Maintenance Workflow

It is recommended to follow the steps below in order:

```bash

# 1) Local preview (Chinese)
npm run start

# 2) Local preview (English)
npm run start:en

# 3) Perform a full build check before committing
npm run build

# 4) Locally serve the build output for verification
npm run serve
```

## Common Maintenance Commands

### Content and Structure Maintenance

```bash

# Generate sidebar scope configuration (Doc Scope)
npm run generate-sidebar-config

# Watch document changes during development and automatically update sidebar scope configuration
npm run watch-sidebar-config
```

### Local Development

```bash
# Chinese development mode (includes sidebar config watching)
npm run start

# English development mode (includes sidebar config watching)
npm run start:en

# Chinese development mode, using port 3001
npm run start:port

# Chinese development mode (without starting watcher)
npm run start:no-watch

# English development mode (without starting watcher)
npm run start:no-watch:en

# Clear Docusaurus cache
npm run clear
```

### Build and Output Verification

```bash
# Standard full build
npm run build

# Locally preview the build directory
npm run serve

# Preview with specified host and port (example)
npm run serve -- --host=10.64.62.34 --port=1688 --no-open
```

Common access paths (the port will depend on the actual `serve` output):
- English: `http://localhost:3000/en/case_doc/case`
- Chinese: `http://localhost:3000/case_doc/case`
