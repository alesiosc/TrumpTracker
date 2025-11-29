### ⚡ QUICK OPTION (Terminal)
Use these 4 commands in your VS Code terminal to do everything instantly.

**1. Create your new branch**
```powershell
git checkout -b "ADDED-Open-Router-Discord-Support"
2. Save your changes
code
Powershell
git add .
git commit -m "Implemented OpenRouter and Discord support"
3. Upload to your GitHub
code
Powershell
git push -u origin ADDED-Open-Router-Discord-Support
4. Link the Original Author
(Replace <URL> below with the link to the original repo)
code
Powershell
git remote add ORIGINAL <PASTE_AUTHOR_URL_HERE>

==================================================================================================================================================================================

### Fastest Workflow: VS Code’s Built-In Git+GitHub
VS Code includes Git support out-of-the-box.

You can publish your local folder to GitHub with only a few clicks or commands, directly from the Source Control panel.

Once Git is installed and you’re signed in with your GitHub account, VS Code can initialize a repository, commit changes, and push to GitHub without opening a separate terminal or installing anything extra.

**For new projects:**
1. Open your project folder in VS Code.
2. Click the **Source Control** icon (left sidebar), select “Initialize Repository.”
3. Add a commit message, stage your changes, and commit.
4. Click “Publish to GitHub” in the Source Control view (or use command palette: `Ctrl+Shift+P` → “Publish to GitHub”).
5. Follow the prompts to select repository name, privacy, and confirm.
6. VS Code handles the rest—your code is now on GitHub.

**For existing repos:**
Open, edit, commit, and push changes all without leaving VS Code.

**Minimal Setup Steps**
* **Install Git** if you haven’t yet (VS Code will prompt/instruct you).
* **Sign in to GitHub** inside VS Code for one-click publishing—no need for another tool.
* All instructions and actions happen within VS Code’s interface or quick command palette.

**Consider VS Code Extensions?**
If you want even deeper integration (like viewing pull requests and issues in VS Code), installing the official “GitHub Pull Requests and Issues” extension is a good optional upgrade. For basic pushing/publishing, it’s not required.

**Summary Table**

| Tool | Setup Required | Key Action | Extra Install Needed | Ease of Use |
| :--- | :--- | :--- | :--- | :--- |
| VS Code (built-in) | Install Git, login to GitHub | Source Control panel/Publish | No | Very easy |

***

### 🔱 How to Push Your Branch & Link the "ORIGINAL" Source

Since you cloned the repo from your own account (your Fork), VS Code already knows about your GitHub (`origin`).

Now we need to create a separate branch for your new code and tell VS Code where the **Author's** repo lives (naming it `ORIGINAL`) so you can get their updates later.

#### Step 1: Create Your Branch
Do this **before** you commit your changes so they remain separate from the main code.
1. Look at the very **bottom-left corner** of VS Code (it likely says `main` or `master`).
2. Click that name.
3. Select **+ Create new branch...**
4. Type exactly: `ADDED Open Router & Discord Support`
5. Press **Enter**.

#### Step 2: Commit and Push to YOUR Fork (`origin`)
1. Go to the **Source Control** tab (the fork icon on the left sidebar).
2. Type your message (e.g., "Updated tracker.py and env").
3. Click **Commit**.
4. Click the blue **Publish Branch** button (this sends this specific branch to your GitHub account).

#### Step 3: Add the "ORIGINAL" Remote
Now we link the **Author's** repository (the one you forked *from*).
1. Go to the GitHub page of the **original Author** (not your page).
2. Click the green **Code** button and copy that URL.
3. In VS Code, press `Ctrl + Shift + P`.
4. Type and select: **Git: Add Remote**.
5. It will ask for a name. Type: `ORIGINAL` (Case sensitive).
6. It will ask for the URL. Paste the **Author's** URL you just copied.

**You are now done.**
* **`origin`** links to **Your GitHub** (where your `ADDED Open Router...` branch lives).
* **`ORIGINAL`** links to the **Author's GitHub** (so you can download their future updates).