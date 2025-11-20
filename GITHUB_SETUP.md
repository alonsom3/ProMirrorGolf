# GitHub Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `ProMirrorGolf` (or your preferred name)
3. Description: "Professional golf swing analysis application with dual camera capture and launch monitor integration"
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add all files (excluding .gitignore items)
git add .

# Create initial commit
git commit -m "Initial commit: ProMirrorGolf application"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ProMirrorGolf.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Verify Connection

1. Go to your GitHub repository page
2. You should see all your files
3. Check that:
   - ✅ `data/` folder exists but is empty (user data excluded)
   - ✅ `__pycache__/` folders are not present
   - ✅ `config.json` is not present (use `config.json.example` instead)
   - ✅ Database files are not present

## Step 4: Making Future Edits

### Daily Workflow

```bash
# Check what changed
git status

# See what files changed
git diff

# Add specific files
git add path/to/file.py

# Or add all changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push
```

### Best Practices

1. **Commit often** - Small, logical commits are better
2. **Write clear commit messages** - Describe what changed and why
3. **Pull before push** - If working on multiple machines:
   ```bash
   git pull
   git push
   ```
4. **Check status** - Always check `git status` before committing

## Step 5: Branching (Optional)

For new features or experiments:

```bash
# Create new branch
git checkout -b feature-name

# Make changes, commit
git add .
git commit -m "Added new feature"

# Push branch
git push -u origin feature-name

# Switch back to main
git checkout main

# Merge feature branch
git merge feature-name
```

## Important Files

### What's Included
- ✅ All source code (`app/`, `core/`, `web/`)
- ✅ Documentation (`docs/`, `README.md`)
- ✅ Configuration example (`config.json.example`)
- ✅ Requirements (`requirements.txt`)
- ✅ `.gitignore` (excludes user data)

### What's Excluded (via .gitignore)
- ❌ User data (`data/promirror.db`, `data/clips/*.mp4`)
- ❌ Log files (`data/logs/*.log`)
- ❌ Python cache (`__pycache__/`)
- ❌ Personal config (`config.json`)
- ❌ IDE files (`.vscode/`, `.idea/`)

## Troubleshooting

### "Repository not found"
- Check repository name matches
- Verify you have access (for private repos)
- Check remote URL: `git remote -v`

### "Permission denied"
- Use HTTPS with personal access token, or
- Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### "Updates were rejected"
- Someone else pushed changes
- Pull first: `git pull`, then `git push`

### "Large file" errors
- Check `.gitignore` is working
- Remove large files: `git rm --cached large-file.mp4`
- Commit the removal

## Next Steps

1. ✅ Repository created on GitHub
2. ✅ Local repo connected
3. ✅ Initial commit pushed
4. ✅ Ready to make edits!

For more Git help: https://git-scm.com/doc

