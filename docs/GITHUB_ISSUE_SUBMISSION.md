# GitHub Issue Submission Implementation

> **Superseded prototype instructions — 19 October 2026. Do not follow the PAT setup below.**
> The discoverable feedback route uses browser review; embedded GitHub login is
> unfinished. The unwired prototype has runtime and token-storage defects.
> Do not generate a broad `repo` token. See [Start Here](START_HERE.md) for current offline-first onboarding.

## Overview

Ag-GIS now supports direct issue submission to GitHub without requiring users to log in each time. This uses OAuth token persistence with a short pipeline: submit → API call → confirmation.

## Architecture

### Components

1. **feedback_submission.py** - Main submission module
   - `FeedbackSubmissionDialog` - Qt dialog for report creation and submission
   - `SubmissionActions` - Plugin integration actions
   - Token storage: `~/.qgis2/plugins/ag_tech_tooling/github_oauth_token.ini`

2. **Token Management**
   - `load_oauth_token()` - Load stored token with expiry validation
   - `save_oauth_token(token, expiry)` - Persist token to config
   - `delete_oauth_token()` - Remove stored token

3. **GitHub API Integration**
   - Base URL: `https://api.github.com`
   - Repository: `JamRov/Ag-GIS-Feedback`
   - Authentication: Bearer token in Authorization header

### Token Storage

Location: `~/.qgis2/plugins/ag_tech_tooling/github_oauth_token.ini`

Format:
```ini
[github]
token = ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
expiry = 2026-12-31T00:00:00Z
```

**Security**: 
- Token is stored locally, never shared
- Includes expiry timestamp for validation
- 40-character hex format validation

## User Flow

### With GitHub Token (No Login)

1. User opens **Feedback and Help…** dialog
2. Dialog checks for stored token
3. User fills report form
4. User clicks **Submit report**
5. API call creates issue on GitHub
6. Confirmation with issue link displayed

### Without GitHub Token

1. User sees "No GitHub token stored" message
2. Clicks **Login to create token**
3. Token creation guide appears
4. User creates token on GitHub with `repo` scope
5. User pastes token in dialog
6. Token saved and dialog refreshed
7. User can now submit reports

### Alternative: Browser Login

1. Fill report form
2. Click **Open GitHub form…**
3. Browser opens with pre-filled issue
4. User logs in and submits
5. Issue created with issue number

## API Integration

### Creating an Issue

```python
POST https://api.github.com/repos/JamRov/Ag-GIS-Feedback/issues
Authorization: Bearer <token>
Accept: application/vnd.github.v3+json
X-GitHub-Api-Version: 2022-11-28

{
  "title": "Issue title",
  "body": "Issue body with report details",
  "labels": ["feedback", "type:bug-report"]
}
```

### Response

```json
{
  "number": 123,
  "title": "Issue title",
  "html_url": "https://github.com/JamRov/Ag-GIS-Feedback/issues/123"
}
```

## Report Format

Generated in markdown with sections:
- Title and type
- Area and impact
- Details, steps, expected result
- Environment information (optional)
- Report ID and creation timestamp

Example:
```markdown
# Error loading layer

Type: Something went wrong
Area: Farm data
Impact: I can keep working

## What happened or would help
Layer failed to load

## How to see it
Open farm data browser, add layer

## Expected result
Layer should display

## App versions
QGIS: 3.38
Python: 3.10
System: Windows 11

Report ID: abc123def4
Created (UTC): 2026-10-16T10:00:00Z
```

## Error Handling

### Authentication Errors (401)
- Token is invalid or expired
- User must create a new token via **Login to create token**
- Token file is deleted for security

### Access Denied (403)
- Token lacks required scope (`repo`)
- User must recreate token with proper scope

### Network Errors
- Connection timeout or failure
- Error message suggests using Copy/Email instead

## Testing

### Unit Tests
Location: `plugins/ag_tech_tooling/test_feedback_submission.py`

Tests cover:
- Token storage (load/save/delete)
- Report text formatting
- Environment summary generation
- Report hash consistency
- Authentication header format

### Integration
Manual testing required in QGIS environment:
1. Dialog creation and form submission
2. Token persistence across QGIS sessions
3. API call success with valid token
4. Error handling with invalid/expired token

## Documentation

- `docs/GITHUB_TOKEN_GUIDE.md` - User guide for creating and managing tokens
- `docs/FEEDBACK.md` - Updated with no-login submission flow
- `docs/ARCHITECTURE.md` - Updated with token persistence note
- `docs/USER_COMMITMENTS.md` - Updated with direct submission capability

## Security Considerations

### What is stored
- Only the OAuth token (40 characters)
- Expiry timestamp

### What is NOT stored
- GitHub username
- Email address
- Farm data, maps, or files
- API responses or logs
- Any credentials beyond the token

### Best practices
- Token should have minimal scope (`repo` only)
- Set token expiration date
- Use password manager to store token
- Revoke and recreate if compromised
- Never share token with others

## Future Enhancements

Potential improvements:
- GitHub App authentication (app installation token)
- Token refresh mechanism
- Multiple token support (personal, organization)
- Issue template selection based on report type
- Auto-close duplicate detection
- Issue status notifications

## Related Files

- `plugins/ag_tech_tooling/feedback_submission.py` - Main implementation
- `plugins/ag_tech_tooling/test_feedback_submission.py` - Unit tests
- `docs/GITHUB_TOKEN_GUIDE.md` - User documentation
- `plugins/ag_tech_tooling/plugin.py` - Plugin integration points
