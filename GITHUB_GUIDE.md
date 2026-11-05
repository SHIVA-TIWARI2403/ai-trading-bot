# 🚀 How to Push this AI Trading Bot to GitHub Safely

Your project is already configured so that **your private API keys, passwords, and trading journals will NEVER be leaked to GitHub**.

---

### Step 1: Install Git (If not already installed)
1. Download Git from: **https://git-scm.com/download/win**
2. Run the installer and click **Next -> Next -> Finish**.

---

### Step 2: Create a New Repository on GitHub
1. Open your browser and go to [github.com/new](https://github.com/new).
2. Enter repository name: `ai-trading-bot`
3. Choose **Public** or **Private** (both are safe because `.gitignore` hides your secrets).
4. **DO NOT** check "Add a README file" (we already created a professional one).
5. Click **Create repository**.
6. Copy the URL of your new repository (e.g. `https://github.com/your-username/ai-trading-bot.git`).

---

### Step 3: Run these commands in PowerShell or Terminal:

Open PowerShell, navigate to your bot folder and run:

```bash
cd "C:\Users\SHIVA TIWARI\.gemini\antigravity\scratch\ai-trading-bot"

# Initialize Git
git init

# Add all project files (Notice: .env is automatically excluded!)
git add .

# Create your first commit
git commit -m "feat: complete AI intraday trading bot with paper trading & risk management"

# Rename branch to main
git branch -M main

# Link to your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/ai-trading-bot.git

# Push your code to GitHub
git push -u origin main
```

---

### 🛡️ Why Your Account is 100% Safe:
* Notice the `.gitignore` file in this folder.
* It explicitly blocks `.env`, `api_keys.json`, and `trades_journal.csv`.
* Anyone visiting your GitHub repo will see the clean algorithms, strategy, and README, but **NO ONE can access your broker or financial data!**
