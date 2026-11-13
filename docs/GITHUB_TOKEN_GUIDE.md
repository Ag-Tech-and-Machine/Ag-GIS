# GitHub Personal Access Token for Ag-GIS

> **Superseded prototype instructions — 19 October 2026. Do not follow the PAT setup below.**
> The discoverable feedback route uses browser review; embedded GitHub login is
> unfinished. The unwired prototype has runtime and token-storage defects.
> Do not generate a broad `repo` token. See the source audit
> and [Start Here](../START_HERE.md) for current offline-first onboarding.

## Purpose

Ag-GIS uses GitHub's REST API to create issue reports directly from the application without requiring users to log into GitHub each time. This requires a Personal Access Token (classic) with the `repo` scope.

## Why we need a token

- **No login required**: Farmers can submit issues from the Ag-GIS tool without opening GitHub
- **Short pipeline**: Submit → API call → Confirmation
- **Privacy**: Token is stored locally in the plugin settings, never shared or uploaded

## Creating your token

### 1. Go to GitHub

1. Visit [GitHub](https://github.com)
2. Log in with your GitHub account
3. Go to **Settings** (⚙️ in the top-right)
4. In the left sidebar, find **Developer settings**
5. Click **Personal access tokens** → **Tokens (classic)**

### 2. Create a new token

1. Click **"Generate new token (classic)"**
2. Fill in the form:
   - **Note**: `Ag-GIS issue submission` (or any name you prefer)
   - **Expiration**: Choose a date (e.g., 1 year or never)
   - **Scopes**: Check only **repo** (full control of private repositories)

### 3. Copy the token

1. Click **"Generate token"**
2. **IMPORTANT**: Copy the entire token string immediately
   - It will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **You will not see this again!**
3. Save it somewhere secure (password manager, encrypted file, etc.)

### 4. Save the token in Ag-GIS

1. Open Ag-GIS
2. Click **Feedback and Help…** in the menu
3. In the dialog, you'll see: "No GitHub token stored. Login to create a token…"
4. Click **Login to create token**
5. Paste the token you copied
6. Click **OK**
7. You should see: "GitHub token saved. You can now submit reports."

## Using the token

Once saved:
1. Click **Feedback and Help…**
2. Fill out the report form
3. Click **Submit report**
4. Your report is created on GitHub without logging in

## Security notes

### What is stored?
- Only your **Personal Access Token** in: `~/.qgis2/plugins/ag_tech_tooling/github_oauth_token.ini`
- This file contains ONLY the token (40 characters), nothing else

### What is NOT stored?
- Your GitHub username
- Your email address
- Farm data, maps, or files
- Any logs or credentials

### Best practices
1. **Don't share your token** - Treat it like a password
2. **Use a password manager** - Store the token securely
3. **Set an expiration** - Choose a date, then create a new token when it expires
4. **Delete old tokens** - If you see "token expired" errors, create a new one and delete the old one

### Revoking a token

If you need to delete a token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Find the token note (`Ag-GIS issue submission`)
3. Click **Revoke**
4. Create a new token in Ag-GIS

## Token scopes explained

| Scope | Purpose | Recommended |
|-------|---------|-------------|
| **repo** | Create, read, update issues in any repo (public or private) | ✅ **YES** |
| delete:issues | Delete issues | ❌ NO |
| public_repo | Push to public repositories | ❌ NO |
| repo:status | Control Git status | ❌ NO |

**Only `repo` scope is needed.**

## Troubleshooting

### "Token is invalid or expired"

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Revoke the old token
3. Create a new token with `repo` scope
4. In Ag-GIS, click **Login to create token**
5. Paste the new token

### "Could not save the token"

1. Ensure you're using the correct GitHub URL (not a mirror)
2. Check that the token doesn't have spaces or extra characters
3. Try a different password manager if you copied from there

### "Submission failed"

1. Check your internet connection
2. Verify the token still has `repo` scope
3. Try creating a new token
4. If problems persist, use **Copy report** and paste into GitHub manually

## Support

If you need help creating or managing tokens:
1. Check this document
2. Review GitHub's help: [Personal access tokens (classic)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
3. Contact Ag-GIS support
