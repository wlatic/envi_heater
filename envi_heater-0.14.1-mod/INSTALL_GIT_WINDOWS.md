# Installing Git on Windows

## Option 1: Install Git for Windows (Recommended)

1. **Download Git**:
   - Go to https://git-scm.com/download/win
   - Download the latest version (64-bit)
   - Run the installer

2. **Installation Settings**:
   - Use default settings (recommended)
   - Make sure "Git from the command line and also from 3rd-party software" is selected
   - Complete the installation

3. **Verify Installation**:
   - Open a new PowerShell window
   - Run: `git --version`
   - You should see the version number

4. **Configure Git** (first time only):
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

## Option 2: Install via Winget (Windows Package Manager)

If you have Windows 10/11 with winget:

```powershell
winget install --id Git.Git -e --source winget
```

## Option 3: Install via Chocolatey

If you have Chocolatey installed:

```powershell
choco install git
```

## After Installation

1. **Close and reopen PowerShell** (or restart your terminal)
2. Navigate to your project:
   ```powershell
   cd envi_heater-0.14.1-mod
   ```
3. Follow the steps in `CREATE_PR_GUIDE.md`

---

**Note**: After installing Git, you may need to restart your terminal/PowerShell for the changes to take effect.


