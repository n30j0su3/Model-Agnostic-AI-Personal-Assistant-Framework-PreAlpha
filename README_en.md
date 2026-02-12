# Model-Agnostic AI Personal Assistant Framework v0.1.0-alpha

> "Your Personal AI Assistant. Your Knowledge. Your Control."

[![Release](https://img.shields.io/badge/release-v0.1.0--alpha-blue)](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.0-alpha)
[![Instagram](https://img.shields.io/badge/Instagram-%40freakingjson-E4405F?logo=instagram&logoColor=white)](https://instagram.com/freakingjson)
[![Linktree](https://img.shields.io/badge/Linktree-@freakingjson-43E55C?logo=linktree&logoColor=white)](https://linktr.ee/freakingjson)
[![Blog](https://img.shields.io/badge/Blog-freakingjson.com-FFA500?logo=firefoxbrowser&logoColor=white)](https://freakingjson.com)
[![Changelog](https://img.shields.io/badge/changelog-keep%20a%20changelog-green)](./CHANGELOG.md)
![Stage](https://img.shields.io/badge/stage-alpha-red)
![License](https://img.shields.io/badge/license-MIT-green)

[🇪🇸 Spanish Version](./README.md)

> **"True knowledge transcends to the public."**
> 
> *"El conocimiento verdadero trasciende a lo público."*
> 
> — *FreakingJSON*

---

## 🎯 Purpose and Philosophy

**What is this?**

An artificial intelligence assistant that lives on **your computer**, not on third-party servers. Your conversations, documents, and knowledge remain in local files that **you completely control**.

**The philosophy is simple:**

- 📍 **Local-first**: Everything works on your PC, without constantly depending on the internet
- 🔐 **Your control**: Your information is never sold or used to train external models
- 🔄 **No vendor lock-in**: Works with OpenAI, Claude, Gemini, or local models. You choose.

> *"True knowledge transcends to the public, but must remain under your control."*

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-AI** | Compatible with OpenCode, Claude Code, Gemini CLI, and more |
| 📁 **Your files** | All your knowledge in `.md` files that you can edit, move, or back up |
| 🛠️ **15 Skills included** | Work with Excel, PDF, Word, Markdown, tasks, and more |
| 🌍 **Bilingual** | Interface and documentation in Spanish and English |
| 📅 **Daily sessions** | The assistant remembers context between conversations |
| ⚡ **Easy to use** | 3-step installation, no complex configurations |

---

## 📁 Simple Structure

```
📂 Your assistant folder/
├── 📄 Knowledge/           # Context files (.md)
├── 🤖 Agents/              # Assistant configuration
├── 🛠️ Skills/              # Tools (Excel, PDF, etc.)
├── 💼 Workspaces/          # Workspaces by project
└── 📅 Sessions/            # Conversation history
```

**Everything is text files.** You can open them, edit them, back them up, or sync them with your favorite system (Google Drive, Dropbox, etc.).

---

## ⚡ Quick Start (Windows)

> 💡 **Also available for Mac and Linux** - see notes at the end.

### Step 1: Download
```powershell
# Option A: With Git (recommended for updates)
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# Option B: Download ZIP from the Releases page above ↑
```

### Step 2: Run
```powershell
# Enter the folder and run:
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha
pa.bat
```

### Step 3: Configure
The installer will ask you 3 simple questions:
1. What language do you prefer? (Spanish/English)
2. What AI tool will you mainly use? (OpenCode, Claude, etc.)
3. What's your name? (to personalize the assistant)

### Done! 🎉

Your assistant is configured. Now you can:
- Type `pa.bat` to start a session
- Edit files in the `workspaces/` folder to give it context
- Ask for help with documents, data, or daily tasks

---

## 📋 Requirements

### Hardware
| Minimum | Recommended |
|---------|-------------|
| 4-core CPU | 8-core CPU |
| 8 GB RAM | 16 GB RAM |
| 2 GB free space | 5 GB free space |

### Software
- **Windows 10/11** (also available for macOS 12+ and modern Linux)
- **Python 3.11+** *(installs automatically if missing)*
- **Git** *(optional, only for updates)*

### Optional: AI Accounts
To use advanced models (GPT-4, Claude, etc.) you'll need:
- A free account with the provider of your choice
- API key (we explain how to get it in the full documentation)

> 💡 **Works without API key too** - you can use free local models like Ollama.

---

## ❓ Basic FAQ

**Do I need to know programming?**
→ **No.** This guide is designed for anyone. If you know how to use a basic terminal, that's enough.

**Is it free?**
→ **The framework is 100% free** (MIT license). Some AI providers (OpenAI, etc.) may charge for intensive use, but there are free options available.

**Is my data mine?**
→ **Yes, completely.** Everything stays on your computer in text files. We don't send your information to external servers without your explicit permission.

**Can I use it without internet?**
→ **Partially.** The framework works offline, but you'll need internet to query cloud AI models. You can also install local models (like Ollama) for 100% offline work.

**How do I update the framework?**
If you used Git: `git pull`. If you downloaded ZIP: download the new version and copy your `.context/` folder (your knowledge) to the new installation.

**What if something doesn't work?**
→ Check our complete documentation or open an issue on GitHub. The community will help you.

---

## 🙏 Acknowledgments

Thanks to God for the Grace, Revelation, and Discernment necessary to build this framework.

Special thanks to **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** for inspiring the central philosophy of this project:

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*

His focus on data sovereignty and accessible learning was fundamental to the design of this framework.

---

## 🔗 Complete Documentation

**Are you a developer or need detailed technical information?**

👉 [View complete technical documentation here](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework/blob/main/README-FULL.md)

Includes:
- Advanced installation by operating system
- Configuration of multiple AI models
- Guide to developing custom skills
- Technical architecture of the framework
- Detailed troubleshooting

---

## 🍎 🐧 Note for Mac and Linux Users

This framework also works on **macOS 12+** and **modern Linux** (Ubuntu 20.04+, Fedora, etc.).

**Equivalent commands:**
```bash
# Instead of pa.bat, use:
./pa.sh

# Installation:
python3 scripts/install.py
```

The structure and operation are identical. Only the script file extensions change.

---

Made with ❤️ by **FreakingJSON**.

### 🔗 Connect with FreakingJSON

- 📸 **Instagram**: [@freakingjson](https://instagram.com/freakingjson)
- 🌐 **All socials**: [linktr.ee/freakingjson](https://linktr.ee/freakingjson)
- 📝 **Tech & Homelab Blog**: [freakingjson.com](https://freakingjson.com)
- ☕ **Support the project**: [buymeacoffee.com/freakingjson](https://buymeacoffee.com/freakingjson)

> *"I own my context. I am FreakingJSON."*
> 
> **"True knowledge transcends to the public."**
> 
> *"El conocimiento verdadero trasciende a lo público."*