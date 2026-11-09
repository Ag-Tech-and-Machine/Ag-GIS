# Ag-GIS desktop updates

Development implementation, 16 October 2026. **Experimental previews are not production-ready and do not provide a hosted farm service.** A catalogue must be validated and deliberately published before an installed application can discover an approved package. An older experimental GitHub download is not automatically an update candidate. Stable remains empty until a nonexperimental package is separately accepted; development previews belong only in Preview.

## User control and scope

- Desktop updates do not require an Ag-GIS account or paid subscription.
- Checks are manual by default. Background checks require an explicit preference; they do not install anything.
- Stable and Preview are separate choices. Stable must not silently accept experimental packages. Preview is for deliberate testing, not production acceptance.
- Update requests retrieve a public catalogue and, after a deliberate download choice, a plugin ZIP. They do not send farm files, project paths or feedback. GitHub/CDN providers see connection metadata, including the requesting IP address. QGIS's configured network/proxy settings still apply.
- Plugin updates do not upgrade QGIS, migrate farm data or restart the application automatically. QGIS/runtime upgrades remain a separately approved installer operation.
- The original farm workspace remains outside the plugin directory. An updater's recovery copy protects plugin files, **not farm data**, and does not make older software compatible with newer data schemas.

## User workflow

Prerequisites: a packaged Ag-GIS installation in the active QGIS user profile, a saved map and no active layer-editing sessions. Development/source-loaded copies may inspect update information but must not replace themselves.

1. Open **Plugins → Ag-GIS → Check for Updates…**. Review the installed version and selected channel. Simply opening this screen must not start a manual network request.
2. Choose **Check now** to retrieve the approved update catalogue. Read the offered version, plain-language changes, QGIS requirements and data-upgrade warning. A missing/unreachable/malformed catalogue is an error, not evidence that the installation is current.
3. Choose to download an available compatible package. Cancelling a request or encountering a connection/integrity error must leave the installed plugin unchanged. Retry after checking the connection or choose an offline ZIP.
4. Before installation, finish layer edits and save the map. Confirm the installation and recovery location. The updater verifies the package and retains a verified copy of the existing plugin before handing the ZIP to QGIS's native plugin installer.
5. Follow the native installation result, then save and close/reopen QGIS. A handoff alone is not proof of success. On the next load, the updater checks the installed version against the pending attempt and reports a match or unresolved attempt.
6. If using a downloaded offline ZIP, select it explicitly and review the warning. ZIP structure and compatibility checks cannot establish who produced an arbitrary offline file. Use packages from the project's official release destination. Experimental packages require the Preview choice.

Offline use remains supported. A network error does not prevent local farm work. Declining an update must not remove data or disable local editing.

## Delivery architecture

The plugin uses a bounded public JSON catalogue at `https://raw.githubusercontent.com/Ag-Tech-and-Machine/Ag-GIS/main/updates/catalog.json`. ZIPs are hosted as release assets under `Ag-Tech-and-Machine/Ag-GIS`. Downloads use QGIS's native network manager and TLS handling. The installed runtime's native `pyplugin_installer` owns installation and plugin reload; Ag-GIS supplies the user-facing review, compatibility/integrity checks and recovery preparation.

This is an Ag-GIS catalogue, **not** a QGIS plugin-repository XML feed. Native repository subscription/automatic upgrades and signed-catalogue verification are not implied. HTTPS plus a catalogue-provided SHA-256 protects against a damaged/mismatched download; it is not an independent publisher signature if the repository itself is compromised. Do not advertise attestation or immutable-release verification until implemented and tested.

Catalogue schema:

```json
{
  "schema_version": 1,
  "releases": []
}
```

Each approved release entry supplies version, `stable`/`preview` channel, QGIS minimum/maximum, official HTTPS ZIP URL, SHA-256, byte size, plain-text notes, `restart_required: true` and an explicit `data_upgrade` boolean. Versions are compared numerically, never as text. The parser and package verifier fail closed for invalid versions, incompatible runtimes, unsafe archive paths, unexpected plugin roots, size limits or metadata mismatches. An empty channel is reported as having no approved update, not a certification that the installation is supported.

## Preparing a catalogue candidate (maintainers)

This procedure prepares local files only. It does not publish, tag, upload or install anything.

1. Start from a reviewed immutable source snapshot. Run the complete source and extracted-package checks documented in [DEVELOPMENT.md](DEVELOPMENT.md), and perform user-workflow acceptance separately. Do not advertise the shared dirty working tree as a release.
2. Build the plugin with `python tools/build_plugin.py`. Its metadata controls version and experimental status. Stable approval requires nonexperimental metadata; changing that flag is not itself acceptance.
3. Write concise release notes to a UTF-8 text file outside the runtime package. Specify what changes, known limitations and any data compatibility consequences. Do not include private farm details or credentials.
4. Generate a separate candidate, substituting the exact tested version, intended release URL and notes path:

   ```text
   python tools/build_update_catalog.py --package dist/ag_tech_tooling-<version>.zip --channel preview --url https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v<version>/ag_tech_tooling-<version>.zip --notes <notes-file> --output dist/update-catalog-candidate.json
   ```

5. Review the candidate against the current catalogue. For a merge, first copy the current reviewed catalogue to the candidate output; the builder preserves its entries and rejects duplicate versions. Retain the approved Stable entry when adding Preview, and retain any still-supported compatibility targets. Add `--data-upgrade` when a separately reviewed data upgrade is required; otherwise the generated flag is false. Never silently replace approved Stable with an experimental build.
6. Publication is a separate authorised task: publish the exact verified release asset, download it back and verify its size/SHA-256, then publish the reviewed catalogue and read it back. The catalogue must not point at an unavailable/draft asset. No publication is performed by a development build.
7. Exercise discovery, cancellation, corrupt-download refusal, native install/restart and recovery in an isolated profile before promotion. Record exact source/package identities and evidence in WORK_LOG.md. Never test by replacing someone's normal working profile.

## Recovery and limits

A retained plugin directory is a recovery source, not automatic rollback or a farm backup. If an update fails to load, close QGIS and restore the recorded previous plugin directory into the same profile using a separately verified recovery procedure. Keep the failed installation for investigation; do not merge old and new runtime files. Preserve the profile settings and farm workspace. If data has been upgraded, use a compatible application or a verified pre-upgrade workspace copy rather than opening it blindly in older software.

A complete cold-process recovery drill and clean-machine/runtime installer acceptance remain distinct from automated catalogue/Qt tests. These must be recorded before calling the delivery path production-ready.
