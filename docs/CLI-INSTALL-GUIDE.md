# CLI Installation Guide for PA Framework

> **Don't have a CLI installed? This guide will help you get started!**
> 
> *Version: v0.3.0-alpha | Updated: April 2026*

---

## Table of Contents

1. [Overview](#-overview)
2. [OpenCode CLI](#-opencode-cli)
3. [Claude CLI](#-claude-cli)
4. [Gemini CLI](#-gemini-cli)
5. [Platform-Specific Instructions](#-platform-specific-instructions)
6. [Verification Commands](#-verification-commands)
7. [Alternative: Manual Magic Prompt Method](#-alternative-manual-magic-prompt-method)
8. [Troubleshooting](#-troubleshooting)

---

## Overview

PA Framework works with AI CLIs (Command Line Interfaces) to provide a powerful personal assistant experience. This guide covers how to install and configure each supported CLI.

### Supported CLIs

| CLI | Provider | Installation Difficulty | Features |
|-----|----------|------------------------|----------|
| **OpenCode** | Open Source | Easy | Free, supports auto-inject |
| **Claude Code** | Anthropic | Medium | Claude models, advanced reasoning |
| **Gemini CLI** | Google | Medium | Gemini models, gcloud integration |

---

## OpenCode CLI

OpenCode is a free, open-source CLI that supports auto-prompt injection with PA Framework.

### Installation

#### macOS (via Homebrew)

```bash
brew install opencode
```

#### macOS (via npm)

```bash
npm install -g opencode
```

#### Linux (via npm)

```bash
# Requires Node.js 18+ first
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g opencode
```

#### Windows (via npm)

```powershell
# Requires Node.js 18+ first
# Download from: https://nodejs.org/

npm install -g opencode
```

#### Windows (via Chocolatey)

```powershell
choco install opencode
```

### Verification

```bash
opencode --version
opencode --help
```

---

## Claude CLI

Claude Code is Anthropic's official CLI for Claude AI models.

### Prerequisites

- Node.js 18 or higher
- An Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Installation

#### macOS / Linux

```bash
# Using npm
npm install -g @anthropic-ai/claude-code

# Or using the official installer
curl -fsSL https://claude.ai/install.sh | sh
```

#### Windows

```powershell
# Using npm (recommended)
npm install -g @anthropic-ai/claude-code
```

### Configuration

After installation, configure your API key:

```bash
# The CLI will prompt for your API key on first run
claude

# Or set it via environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Verification

```bash
claude --version
claude auth status
```

---

## Gemini CLI

Gemini CLI is Google's command-line interface for Gemini models via Google Cloud.

### Prerequisites

- A Google Cloud account
- A Google Cloud project with Gemini API enabled
- gcloud CLI installed

### Step 1: Install Google Cloud SDK

#### macOS (via Homebrew)

```bash
brew install --cask google-cloud-sdk
```

#### macOS (via installer)

1. Download from: https://cloud.google.com/sdk/docs/install
2. Run the installer
3. Initialize: `./google-cloud-sdk/bin/gcloud init`

#### Linux (Debian/Ubuntu)

```bash
# Add Google Cloud SDK repository
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Install
sudo apt-get update && sudo apt-get install google-cloud-sdk
```

#### Linux (Fedora/RHEL)

```bash
# Add Google Cloud SDK repository
sudo tee -a /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-sdk]
name=Google Cloud SDK
baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
       https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM

# Install
sudo yum install google-cloud-sdk
```

#### Windows

1. Download the installer from: https://cloud.google.com/sdk/docs/install
2. Run the installer and follow prompts
3. Or via Chocolatey: `choco install gcloudsdk`

### Step 2: Install Gemini CLI Component

```bash
# Install Gemini CLI component
gcloud components install gemini-cli

# Update all components
gcloud components update
```

### Step 3: Authentication

```bash
# Initialize gcloud (if not done)
gcloud init

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable Gemini API
gcloud services enable aiplatform.googleapis.com
```

### Verification

```bash
gcloud --version
gemini --help
# or
gcloud ai gemini --help
```

---

## Platform-Specific Instructions

### macOS

#### Prerequisites

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js (required for npm-based CLIs)
brew install node
```

#### Recommended Setup

```bash
# Install all CLIs at once
brew install opencode node
npm install -g @anthropic-ai/claude-code
brew install --cask google-cloud-sdk
```

### Windows

#### Prerequisites

1. **Install PowerShell 7+** (recommended): https://github.com/PowerShell/PowerShell/releases
2. **Install Node.js**: https://nodejs.org/ (LTS version)
3. **Optional**: Install Chocolatey: https://chocolatey.org/install

#### Recommended Setup (PowerShell)

```powershell
# Using Chocolatey (recommended)
choco install nodejs opencode gcloudsdk

# Or using npm
npm install -g opencode
npm install -g @anthropic-ai/claude-code
```

#### Windows Path Issues

If commands aren't found after installation:

```powershell
# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Or restart your terminal/PowerShell
```

### Linux

#### Prerequisites (Debian/Ubuntu)

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install build tools (often needed for npm packages)
sudo apt install -y build-essential
```

#### Recommended Setup

```bash
# Install OpenCode
npm install -g opencode

# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

---

## Verification Commands

After installing your CLI(s), run these verification commands:

### Quick Verification Script

```bash
#!/bin/bash
# save as verify-cli.sh

echo "=== CLI Verification ==="
echo ""

# Check Node.js (required for most CLIs)
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js: Not installed"
fi

# Check npm
if command -v npm &> /dev/null; then
    echo "✅ npm: $(npm --version)"
else
    echo "❌ npm: Not installed"
fi

echo ""

# Check OpenCode
if command -v opencode &> /dev/null; then
    echo "✅ OpenCode: $(opencode --version 2>&1 | head -1)"
else
    echo "⚠️  OpenCode: Not installed"
fi

# Check Claude CLI
if command -v claude &> /dev/null; then
    echo "✅ Claude CLI: $(claude --version 2>&1 | head -1)"
else
    echo "⚠️  Claude CLI: Not installed"
fi

# Check Gemini/gcloud
if command -v gcloud &> /dev/null; then
    echo "✅ Google Cloud SDK: $(gcloud --version 2>&1 | head -1)"
else
    echo "⚠️  Google Cloud SDK: Not installed"
fi

echo ""
echo "=== Verification Complete ==="
```

### PowerShell Verification Script

```powershell
# save as verify-cli.ps1

Write-Host "=== CLI Verification ===" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "✅ Node.js: $(node --version)" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js: Not installed" -ForegroundColor Red
}

# Check npm
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "✅ npm: $(npm --version)" -ForegroundColor Green
} else {
    Write-Host "❌ npm: Not installed" -ForegroundColor Red
}

Write-Host ""

# Check OpenCode
if (Get-Command opencode -ErrorAction SilentlyContinue) {
    Write-Host "✅ OpenCode: installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  OpenCode: Not installed" -ForegroundColor Yellow
}

# Check Claude CLI
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "✅ Claude CLI: installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Claude CLI: Not installed" -ForegroundColor Yellow
}

# Check gcloud
if (Get-Command gcloud -ErrorAction SilentlyContinue) {
    Write-Host "✅ Google Cloud SDK: installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Google Cloud SDK: Not installed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
```

---

## Alternative: Manual Magic Prompt Method

If you cannot install any CLI, you can still use PA Framework by manually copying the magic prompt to any AI chat interface.

### What is the Magic Prompt?

The magic prompt is a special initialization string that tells the AI to read the PA Framework context files and follow the framework's rules.

### How to Use It

#### Step 1: Get the Magic Prompt

Run the PA Framework launcher and select your scenario:

```bash
# From PA Framework root directory
python core/scripts/pa.py

# Or on Windows
pa.bat

# Or on Mac/Linux
./pa.sh
```

When prompted, select **"Start Session"**. The magic prompt will be displayed:

```
╔══ MAGIC PROMPT ════════════════════════════════════╗
║ Lee 'core/.context/quick-start.md' para iniciar. Este archivo contiene todo lo necesario para comenzar.
╚════════════════════════════════════════════════════╝
```

#### Step 2: Copy the Prompt

Copy the magic prompt text from the box.

#### Step 3: Paste into Any AI Interface

Use the magic prompt in any of these interfaces:

- **Web ChatGPT**: https://chat.openai.com
- **Claude Web**: https://claude.ai
- **Gemini Web**: https://gemini.google.com
- **Any other AI chat interface**

#### Step 4: Provide Context Files

The AI will ask you to provide the context files. You can:

1. **Upload files directly** (if the interface supports it)
2. **Copy-paste the contents** of key files:

```
core/.context/profile.md      # Your profile and preferences
core/.context/navigation.md   # Navigation and file structure
AGENTS.md                     # Agent definitions and rules
```

### Manual Session Files

For manual sessions, you can create session files in:

```
core/.context/sessions/YYYY-MM-DD.md
```

Use this template:

```markdown
# Session YYYY-MM-DD

## Start
- **Time**: HH:MM
- **CLI**: Manual (Web Interface)
- **AI**: [ChatGPT/Claude/Gemini/Other]

## Topics Covered
- Topic 1
- Topic 2

## Decisions Made
- DEC-001: Description

## Notes
- Important notes here

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
```

---

## Troubleshooting

### "Command not found" after installation

**macOS/Linux:**
```bash
# Reload shell configuration
source ~/.bashrc   # or ~/.zshrc

# Or restart your terminal
```

**Windows:**
```powershell
# Refresh path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Or restart PowerShell
```

### npm permission errors (Linux/macOS)

```bash
# Option 1: Use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Option 2: Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### gcloud authentication issues

```bash
# Re-authenticate
gcloud auth login

# Revoke and login again
gcloud auth revoke
gcloud auth login

# Check current account
gcloud auth list
```

### Claude CLI API key issues

```bash
# Check if API key is set
claude auth status

# Re-authenticate
claude auth login

# Or set via environment variable (add to ~/.bashrc or ~/.zshrc)
export ANTHROPIC_API_KEY="your-key-here"
```

### OpenCode connection issues

```bash
# Check configuration
opencode config list

# Reset configuration
opencode config reset

# Reconfigure
opencode setup
```

---

## Quick Reference

| CLI | Install Command | Verify Command | Auth Setup |
|-----|-----------------|----------------|------------|
| OpenCode | `npm install -g opencode` | `opencode --version` | Auto-configured |
| Claude | `npm install -g @anthropic-ai/claude-code` | `claude --version` | `claude auth login` |
| Gemini | See [Gemini CLI](#-gemini-cli) section | `gcloud --version` | `gcloud auth login` |

---

## Need Help?

1. **Check the documentation**: `docs/GETTING-STARTED.md`
2. **Review troubleshooting**: See [Troubleshooting](#-troubleshooting) section
3. **Use manual method**: See [Alternative: Manual Magic Prompt Method](#-alternative-manual-magic-prompt-method)

---

*PA Framework v0.3.0-alpha | For more information, see the [main documentation](./GETTING-STARTED.md)*