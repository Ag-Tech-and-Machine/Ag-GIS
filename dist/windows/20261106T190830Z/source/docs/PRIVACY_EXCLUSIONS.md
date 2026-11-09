# Privacy Exclusions Documentation

## Files/Patterns Excluded from Public Commit

### Git-Ignored Files (Already Excluded)
These files are already excluded via .gitignore:
- `.aggis-agent/` - Private operation logs
- `.dev-profiles/` - Profile settings and auth stores
- `dist/` - Old generated artifacts/releases/screenshots
- `agent/` - Ignored private material
- `*.db, *.sqlite3` - Database files
- `temp_pctgdp.pctgdp` - Customer-format sample
- `nul` - Reserved device/path entry
- Other Git-ignored material

### Sanitized (Modified Before Commit)
The following file types were sanitized:
- `docs/*.md` - Documentation files
- `tools/*.py, *.bat` - Test and utility scripts
- `plugins/ag_tech_tooling/*` - Plugin source files

## Exclusion Strategy

### Conservative Approach
- Removed ALL personal identifiers
- Removed ALL machine-specific paths
- Removed ALL internal tooling references
- Kept ONLY product-relevant content

### Future Improvements
Consider:
1. Adding `.env` file for credentials
2. Creating `example.env` template
3. Documenting environment variables separately
4. Using placeholder values in documentation
