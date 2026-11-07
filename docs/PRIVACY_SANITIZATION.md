# Privacy Sanitization Guide for Ag-GIS Public Release

## Overview
This document describes the sanitization strategy applied to make Ag-GIS source code suitable for public release.

## Sanitization Categories

### 1. Local User Paths (local-user-path)
**Why:** Exposes local filesystem paths that are machine-specific and could reveal user data.

**Patterns Sanitized:**
- `[USER_PATH]\...` → `[local path]`
- `[USER_PATH]\AppData` → `[local path]`
- `settings/auth/Qt/temp/origins` → `[local path]`

**Examples:**
- Before: `settings/auth/Qt/temp/origins isolated`
- After: `[local path]` isolated

### 2. Private Names and Emails (private-name)
**Why:** Exposes personal identity information.

**Patterns Sanitized:**
- `Michael <email>` → `[user identity]`
- `admin@agtechandmachine.com` → `[user identity]`

**Examples:**
- Before: `Configured Git author Michael <admin@agtechandmachine.com>`
- After: `Configured Git author [user identity]`

### 3. Conversation Context/Session IDs (conversation-context)
**Why:** Exposes internal debugging/session identifiers that are not useful for public documentation.

**Patterns Sanitized:**
- `SupportedXXXX` → `[session ID]`
- `warmXXXX/coldXXXX` → `[session ID]`
- `normalXXXX` → `[session ID]`

**Examples:**
- Before: `Supported7253 recover/claim after owner direction`
- After: `[session ID] recover/claim after owner direction`

### 4. Internal Platform References (internal-platform)
**Why:** Exposes internal tooling names that are not relevant to end users.

**Patterns Sanitized:**
- `Hermes kernel` → `[internal tooling]`
- `free local Qwen` → `[internal tooling]`
- `local Qwen` → `[internal tooling]`

**Examples:**
- Before: `Local Qwen123/68-token review retained`
- After: `[internal tooling] review retained`

## Rationale

### What We Keep (Publicly Appropriate)
- **Competitor references** (Deere, Ag Leader SMS, PTx FarmENGAGE) - These are mentions of compatible products, not endorsements
- **Product names** (Ag-GIS, Hulppa) - The actual product being documented
- **Technical terms** (QGIS, PyQGIS, QgsAuthManager) - Industry-standard terminology
- **Feature descriptions** - The actual functionality being documented

### What We Remove
- Personal identifiers
- Machine-specific paths
- Internal tooling names
- Debugging/session IDs

## Files Sanitized
- `docs/WORK_LOG.md` - Primary development log
- `docs/INSTALL.md` - Installation guide
- `docs/TOOLING.md` - Tooling documentation
- `tools/*.py` - Test and utility scripts
- `plugins/ag_tech_tooling/*` - Plugin files
- Other documentation files

## Verification
After sanitization, files should pass publication gate checks for:
- No personal names or emails
- No machine-specific paths
- No internal tooling identifiers
- No session/debug IDs

## Exclusions (Not Sanitized)
The following are intentionally kept as-is because they are:
1. Ignored by Git (in .gitignore)
2. Database files
3. Generated artifacts
4. Private operational files (.aggis-agent/, .dev-profiles/)
