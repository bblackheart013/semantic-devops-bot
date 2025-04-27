# Semantic DevOps Bot 🚀

An intelligent AI-powered DevOps assistant that automatically **analyzes error logs**, **suggests real-time fixes**, and **creates GitHub issues** —  
Built using **Microsoft Semantic Kernel** and **OpenAI GPT models**.

> Accelerating DevOps troubleshooting with intelligent automation.

---

## ✨ Features

- 🔍 **AI-Driven Error Analysis**: Understands and diagnoses error logs using OpenAI GPT (gpt-3.5-turbo / gpt-4).
- 🚀 **Automatic GitHub Issue Creation**: Creates detailed GitHub issues based on AI analysis and recommended fixes.
- 🤖 **Microsoft Semantic Kernel Integration**: Orchestrates AI agents using Microsoft's enterprise-grade SK framework.
- 🔧 **Modular Design**: Easily extendable with plugins for Azure optimization, CI/CD pipeline improvements, and multi-agent collaboration.

---

## 📦 Tech Stack

- [x] Python 3.11
- [x] Microsoft Semantic Kernel
- [x] OpenAI API (GPT models)
- [x] GitHub API (PyGithub)

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- OpenAI API key (with sufficient quota)
- GitHub Personal Access Token (with `repo` scope)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/bblackheart013/semantic-devops-bot.git
cd semantic-devops-bot

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

```bash
# Set environment variables
export OPENAI_API_KEY=your_openai_api_key
export GITHUB_TOKEN=your_github_personal_access_token
```

### 4. Usage

```bash
# Place error logs inside the /logs directory
# Then run the DevOps bot
python devops_bot.py
```

The bot will:
- Analyze the error log
- Suggest a fix
- (Optionally) Auto-create a GitHub issue with the error details and fix.

---

## Project Structure

```
semantic-devops-bot/
├── agents/             # Specialized AI agents (Azure optimization, fix recommendation)
├── logs/               # Error log files to analyze
├── plugins/            # Extendable plugins (GitHub, Azure integrations)
├── services/           # API integration services (GitHubService)
├── devops_bot.py       # Main entry script
├── README.md
├── requirements.txt
└── venv/               # (Virtual environment)
```

## 🎯 Future Plans

- ✅ Multi-agent collaboration (triage, refund, billing agents)
- ✅ Automated CI/CD failure diagnosis and patch suggestions
- ✅ Azure DevOps integration for auto-scaling and optimization
- ✅ Slack / Teams bot integration
- ✅ Web App Frontend (log upload → instant AI analysis)

## 📜 License

This project is licensed under the MIT License.

## 🙏 Acknowledgements

- [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [GitHub API](https://docs.github.com/en/rest)

## 📣 Connect with me!

- [GitHub](https://github.com/bblackheart013)
- [Google Scholar](https://scholar.google.com/citations?user=o1hrV0kAAAAJ&hl=en)
- [LinkedIn](https://www.linkedin.com/in/mohd-sarfaraz-f-8bb52922a) <!-- Replace with your actual LinkedIn URL -->

If you find this project interesting or valuable, feel free to connect or collaborate.

Built with 💻 and ❤️ for making DevOps smarter.
