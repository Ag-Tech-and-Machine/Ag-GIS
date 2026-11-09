# Quick Start: GitHub Token for Ag-GIS

> **Superseded prototype instructions — 19 October 2026. Do not follow the PAT setup below.**
> The discoverable feedback route uses browser review; embedded GitHub login is
> unfinished. The unwired prototype has runtime and token-storage defects.
> Do not generate a broad `repo` token. See [Start Here](../START_HERE.md) for current offline-first onboarding.
> and [Start Here](../START_HERE.md) for current offline-first onboarding.

## Create Your Token (One-Time Setup)

### Step 1: Go to GitHub
1. Visit [https://github.com](https://github.com)
2. Log in with your GitHub account
3. Click **Settings** (⚙️ top-right)
4. Scroll down to **Developer settings**
5. Click **Personal access tokens** → **Tokens (classic)**

### Step 2: Create Token
1. Click **"Generate new token (classic)"**
2. Fill in:
   - **Note**: `Ag-GIS issue submission`
   - **Expiration**: Choose a date (e.g., 1 year from now)
   - **Scopes**: Check only **repo** (full control of private repositories)
3. Click **"Generate token"**
4. **COPY THE TOKEN** immediately (it won't show again!)
   - Looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 3: Save in Ag-GIS
1. Open Ag-GIS
2. Click **Feedback and Help…** (top **Feedback** button)
3. Click **Login to create token**
4. Paste your token
5. Click **OK**
6. You should see: "GitHub token saved. You can now submit reports."

## Using the Token

1. Click **Feedback and Help…**
2. Choose report type (Something went wrong / An idea / I need help)
3. Fill in the form
4. Click **Submit report**
5. Done! Issue created instantly. No login needed.

## Troubleshooting

### "Token is invalid or expired"
- Go to GitHub Settings → Personal access tokens
- Revoke the old token (note named `Ag-GIS issue submission`)
- Create a new token
- Paste new token in Ag-GIS

### "Could not save the token"
- Make sure there are no spaces in the token
- Copy the token directly from GitHub (not from a password manager)
- Try again

### "Submission failed"
- Check your internet connection
- Verify token has `repo` scope
- Create a new token if needed

## Security Notes

- Token is stored locally: `~/.qgis2/plugins/ag_tech_tooling/github_oauth_token.ini`
- Token is **never** shared or uploaded
- Use a password manager to store the token
- Set an expiration date and create a new one when it expires

## Alternative: No Token (Use Browser Login)

If you don't want to create a token:
1. Fill the report form
2. Click **Open GitHub form…**
3. Browser opens with pre-filled issue
4. Log in and submit on GitHub

This requires logging in each time but doesn't store any token.
