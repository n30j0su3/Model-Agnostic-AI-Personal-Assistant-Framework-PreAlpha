# 🚀 Getting Started with PA Framework

> **5-Minute Visual Tutorial for New Users**
> 
> *Version: v0.3.7-alpha | Updated: April 2026*

---

## 📖 What You'll Learn

In just 5 minutes, you'll know how to:
1. ✅ Install the framework on your computer
2. ✅ Start your first session
3. ✅ Understand the key concepts
4. ✅ Ask your first questions
5. ✅ Access the visual dashboard

---

## 🎯 What is PA Framework?

PA Framework is your **personal AI assistant** that lives on your computer. 

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │              PA Framework                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────────────┐ │  │
│  │  │ Sessions│ │ Skills  │ │   Knowledge Base    │ │  │
│  │  │ (Memory)│ │(Tools)  │ │   (Your Files)      │ │  │
│  │  └─────────┘ └─────────┘ └─────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                          ↑                              │
│                    YOU CONTROL                          │
│                    EVERYTHING                           │
└─────────────────────────────────────────────────────────┘
```

### Why PA Framework?

| Traditional AI Apps | PA Framework |
|---------------------|--------------|
| ❌ Data stored on company servers | ✅ Data stays on YOUR computer |
| ❌ Can't remember past conversations | ✅ Remembers all your sessions |
| ❌ Limited to one AI provider | ✅ Works with OpenAI, Claude, Gemini, or local AI |
| ❌ Can't customize | ✅ You can edit everything |

---

## ⚡ Step 1: Quick Install (2 minutes)

### Windows Users

```powershell
# 1️⃣ Download the framework
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# 2️⃣ Go to the folder
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha

# 3️⃣ Run the installer
pa.bat
```

> **No Git?** Download the ZIP from the [Releases page](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases) and extract it.

### Mac & Linux Users

```bash
# 1️⃣ Download the framework
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# 2️⃣ Go to the folder
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha

# 3️⃣ Run the installer
./pa.sh
```

---

## 🎨 Step 2: Configuration Wizard (1 minute)

When you first run `pa.bat` (Windows) or `pa.sh` (Mac/Linux), you'll see:

```
╔════════════════════════════════════════════════════════════╗
║           🎉 WELCOME TO PA FRAMEWORK SETUP                 ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Question 1: What language do you prefer?                 ║
║  → [E] English  |  [S] Spanish                             ║
║                                                            ║
║  Question 2: Which AI tool will you use?                  ║
║  → [O] OpenCode | [C] Claude Code | [G] Gemini CLI        ║
║    | [L] Local (Ollama)                                    ║
║                                                            ║
║  Question 3: What's your name?                            ║
║  → (Type your name for personalized responses)            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

**That's it! Your assistant is ready.** 🎉

---

## 🔑 Key Concepts Explained

### 📅 Sessions = Your Memory

Think of **Sessions** as daily journals. The assistant remembers what you talked about each day.

```
Day 1 (Monday)              Day 2 (Tuesday)            Day 3 (Wednesday)
┌────────────────┐         ┌────────────────┐         ┌────────────────┐
│ "Help me with  │ ───→    │ "Remember the  │ ───→    │ "Based on what │
│  my resume"    │         │  resume from   │         │  we discussed  │
│                │         │  yesterday..." │         │  on Monday..." │
└────────────────┘         └────────────────┘         └────────────────┘
     ↓                          ↓                          ↓
session-2026-04-17.md     session-2026-04-18.md     session-2026-04-19.md
```

**What gets saved each session:**
- Your questions and the AI's answers
- Files you worked on
- Decisions made
- Tasks created

---

### 🛠️ Skills = Your Tools

**Skills** are specialized tools the assistant can use. Think of them as apps on your phone.

| Skill Icon | Skill Name | What It Does |
|------------|------------|--------------|
| 📄 | `@pdf` | Read, extract, and analyze PDF files |
| 📊 | `@xlsx` | Work with Excel spreadsheets |
| 📝 | `@docx` | Create and edit Word documents |
| 📈 | `@data-viz` | Create charts and visualizations |
| 📋 | `@task-management` | Manage your to-do lists |
| 🎨 | `@pptx` | Create PowerPoint presentations |
| 📉 | `@dashboard-pro` | Build professional dashboards |
| 💻 | `@skill-creator` | Create your own custom skills |

**22 Skills Available!**

#### How to Use a Skill

Simply mention the skill name with `@`:

```
You: "Use @pdf to extract the text from my report.pdf"
You: "Use @xlsx to analyze the data in budget.xlsx"
You: "Use @task-management to create a new task"
```

---

### 🤖 Agents = Your Helpers

**Agents** are specialized assistants for different tasks. You can switch between them like changing channels on TV.

```
┌─────────────────────────────────────────────────────────┐
│                    AGENTS                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🎯 FreakingJSON-PA ─────── Main assistant             │
│     Your primary helper for daily tasks                 │
│                                                         │
│  🔍 @context-scout ─────── Research helper             │
│     Finds information in your files                     │
│                                                         │
│  📝 @doc-writer ─────────── Document creator           │
│     Helps write and format documents                    │
│                                                         │
│  📋 @session-manager ────── Session organizer          │
│     Manages your daily sessions                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 First Session Flow Diagram

Here's what happens when you start a session:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FIRST SESSION FLOW                            │
└──────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │  START  │  Type: pa.bat (Windows) or ./pa.sh (Mac/Linux)
    └─────────┘
         │
         ↓
    ┌─────────────────┐
    │ Context Loading │  Framework loads your previous sessions
    │   (~4 seconds)  │  and knowledge base
    └─────────────────┘
         │
         ↓
    ┌─────────────────┐
    │   Welcome! 🎉   │  Shows today's date, active skills,
    │                 │  and previous session summary
    └─────────────────┘
         │
         ↓
    ┌─────────────────┐
    │  Ready for      │  The assistant is now listening!
    │   Your Input    │  Type your first question...
    └─────────────────┘
         │
         ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                    YOUR CONVERSATION                            │
    │                                                                 │
    │  You: "What can you help me with today?"                       │
    │  ───────────────────────────────────────────────────────────── │
    │  Assistant: "I can help you with documents, data analysis,     │
    │              task management, and much more! Here are some     │
    │              things you can ask me..."                          │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
         │
         ↓
    ┌─────────────────┐
    │     END         │  When you're done, the session is
    │   Session       │  automatically saved to your history
    └─────────────────┘
```

---

## 💬 Example First Questions

Try these to get started:

### 📄 Document Questions
```
"Can you help me write a professional email?"
"Use @pdf to summarize this research paper I have."
"Create a meeting agenda for my team."
```

### 📊 Data Questions
```
"Use @xlsx to analyze my monthly expenses."
"Create a chart showing my project progress."
"Help me organize this CSV file with customer data."
```

### 📋 Task Questions
```
"Create a to-do list for my project deadlines."
"What tasks do I have pending from last week?"
"Remind me what we discussed yesterday."
```

### 🎓 Learning Questions
```
"Explain the difference between sessions and skills."
"How do I create my own skill?"
"What files does the framework store?"
```

---

## 🎛️ Dashboard Access

The **Dashboard SPA** is a visual interface to see your framework status.

### How to Open the Dashboard

```
Option 1: Direct File
━━━━━━━━━━━━━━━━━━━━━━
Open in your browser:
  → dashboard.html

Option 2: From Command Line
━━━━━━━━━━━━━━━━━━━━━━━━━━
python core/scripts/dashboard-launcher.py
```

### What You'll See

```
┌──────────────────────────────────────────────────────────────────────┐
│                      DASHBOARD HOME                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│   │ Sessions │  │  Skills  │  │ Projects │  │Interactns │            │
│   │    17    │  │    22    │  │    0     │  │   Active  │            │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │                    Recent Sessions                            │ │
│   ├───────────────────────────────────────────────────────────────┤ │
│   │ • 2026-04-17 - Session Log                                     │ │
│   │ • 2026-03-20 - Release v0.2.2-prealpha                         │ │
│   │ • 2026-03-12 - Multi-Environment Diagnostics                   │ │
│   │ • 2026-02-24 - Skill @dashboard-pro Creation                   │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│   📍 Navigation: Home | Sessions | Framework | About                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Where Your Files Live

All your data is stored in plain text files you can edit:

```
PA Framework Folder
│
├── core/.context/
│   ├── sessions/           ← Your daily session logs (.md files)
│   ├── codebase/           ← Your project notes and reminders
│   ├── knowledge/          ← Extracted knowledge and insights
│   └── MASTER.md           ← Your main configuration file
│
├── workspaces/
│   ├── personal/           ← Personal projects
│   ├── professional/       ← Work-related files
│   ├── research/           ← Research and learning
│   └── content/            ← Content creation
│
├── core/skills/
│   └── core/               ← All 22 skills live here
│
└── dashboard.html          ← Visual dashboard
```

---

## ⚠️ Common First-Time Questions

### "Do I need an API key?"

> **No!** You can use local AI models (like Ollama) for free.
> 
> For cloud AI (OpenAI, Claude), you'll need a free account and API key.

### "Where is my data?"

> **On your computer.** Look in `core/.context/sessions/` for your conversation history.

### "Can I use this offline?"

> **Partially.** The framework works offline, but cloud AI needs internet. Use local AI (Ollama) for full offline work.

### "How do I update?"

```powershell
python core/scripts/update.py --check   # Check for updates
python core/scripts/update.py           # Apply updates
```

Your personal data is **automatically preserved** during updates.

---

## 🎯 Quick Reference Card

| What You Want | How To Do It |
|---------------|--------------|
| Start a session | `pa.bat` (Windows) or `./pa.sh` (Mac/Linux) |
| Use a skill | Mention it: `"Use @pdf to..."` |
| See dashboard | Open `dashboard.html` in browser |
| Check updates | `python core/scripts/update.py --check` |
| Find my files | Look in `core/.context/sessions/` |
| Switch language | Set during installation or edit `MASTER.md` |

---

## 📚 Next Steps

1. **Try your first session** - Just ask a simple question!
2. **Explore the skills** - Type `"What skills are available?"`
3. **Open the dashboard** - See your framework status
4. **Create a workspace** - Organize your projects

---

## 🆘 Need Help?

| Resource | Link |
|----------|------|
| 📖 Full Documentation | [docs/README.md](./README.md) |
| 🔄 Update Guide | [docs/UPDATE-GUIDE.md](./UPDATE-GUIDE.md) |
| 🛠️ Technical Docs | [docs/README-TECNICO.md](./README-TECNICO.md) |
| 💬 GitHub Issues | [Report a problem](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/issues) |

---

## 🎉 You're Ready!

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎊 CONGRATULATIONS! You completed the 5-minute tutorial!   ║
║                                                              ║
║   Your personal AI assistant is ready to help you with:     ║
║   • Documents (PDF, Word, Excel)                             ║
║   • Data analysis and visualization                          ║
║   • Task management                                          ║
║   • And much more!                                           ║
║                                                              ║
║   Start now: pa.bat (Windows) or ./pa.sh (Mac/Linux)         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

*Made with ❤️ by FreakingJSON*

> *"I own my context. I am FreakingJSON."*
> 
> *"True knowledge transcends to the public."*