# Ag-GIS user commitments

Adopted as the product's governing direction on 15 October 2026. These commitments guide implementation and release decisions. This document is not a claim that future online features exist today, and it is not a substitute for the eventual service/privacy terms.

## People own and control their data

Your farm records, maps, documents and uploaded content remain yours. Ag-GIS will not require a transfer of ownership to use the product. You choose what stays on your device, what is uploaded and whom you share it with. Other parties' basemaps and datasets retain their own licences; we identify those separately.

Local work must remain useful without a subscription. Cancelling a cloud service must not disable local access or editing. We will provide a usable export of supported hosted data, including the project, managed datasets, attachments and the information needed to interpret them. We will explain any unsupported dependencies or export limitations before upload; an export button that leaves a project unusable does not satisfy this commitment.

We will not sell customer farm data, use it for advertising, or use it to train AI models. Uploads, optional analytics and diagnostics require clear explanations and deliberate choices; no background collection of farm contents disguised as feedback. Any separately requested AI service must explain its processing destinations and controls before data is sent.

## Explain the service before asking for trust or payment

For every online feature, explain what leaves the device, why, where it is hosted, which providers process it, who can access it, how long it is retained and how to export/delete it. Disclose staff access and its controls. Do not claim end-to-end encryption or that we cannot read hosted data unless the implemented architecture supports that claim, including recovery and mobile viewing.

Show the price, included users/storage/processing, renewal, cancellation and any overage behaviour before purchase. Publish the exit/export period and backup deletion schedule before customers upload data. Avoid surprise usage bills; require a deliberate choice for paid overages. A failed payment is not permission to delete a user's local files.

Show accurate backup/sync state: last successful protection time, failed or incomplete items and any conflicts. A backup is not protected until the service has verified it. Describe restore limitations, connectivity requirements and supported formats. Publish material incidents and their resolution without exposing customer information.

## Freedom to contribute and influence direction

Provide a visible feedback route and a public roadmap for shareable work. Accept ideas, bug reports, documentation and code contributions when the corresponding contribution channel is available. Publish contribution rules, licence terms and review criteria. Give contributors credit and explain declined/deferred proposals respectfully. Do not require exclusive ownership of contributions merely to submit them; any additional agreement needs a clear explanation and deliberate acceptance.

Show how decisions are made and record the reasons for significant changes. Community input should shape priorities; voting does not guarantee a feature or delivery date. Paying customers do not purchase exclusive control of community direction. Safety, data integrity, accessibility and user control remain priorities even when a requested change is commercially inconvenient.

Keep commercial service commitments distinct from community participation. Avoid promising a democratic foundation or independent governance before it exists. Consider broader stewardship as the contributor community and funding develop.

## Honest status today

- Ag-GIS is currently a QGIS-based desktop plugin/distribution under GPL-2.0-or-later. Retain upstream credits and applicable source/licence rights.
- Main source/history and installer releases are public in [Ag-Tech-and-Machine/Ag-GIS](https://github.com/Ag-Tech-and-Machine/Ag-GIS), transferred and made public on 15 October 2026. Forks and pull requests are available; maintainers review proposed changes. Unreleased local work is not automatically published by a visibility change.
- The public [feedback tracker](https://github.com/JamRov/Ag-GIS-Feedback/issues) accepts problems, ideas and questions. Reports and attachments there are public: do not upload private farm/customer records or credentials. Saved/email reports offer another route; posting is not automatic.

Local Ag-GIS use and agent-instruction copying require no sign-in. The discoverable feedback dialog prepares local drafts and opens a browser form; GitHub sign-in and deliberate submission happen there. Secure in-app GitHub sign-in is unfinished. An unwired direct-token prototype is not a supported authentication route; do not create a broad PAT for onboarding. Any API token used for authentication would be sent to GitHub, not kept exclusively on-device. See [the implementation audit](GITHUB_ISSUE_SUBMISSION.md).
- Public source contributions are available through forks and pull requests. A self-hosted cloud package is not available yet; do not advertise that deployment route as implemented.
- Cloud backup, mobile access, team synchronisation and hosted desktops are proposals. No paid online service, subscription or uptime promise has launched. Current prices in WORK_LOG.md are internal research hypotheses.
- No foundation, community board, public voting mechanism or community control of company assets has been established.

## Release and business decision checks

Before a feature is promoted or sold, record:

1. What works now, what remains experimental, and a reproducible acceptance result.
2. What data it reads, copies, uploads or shares, including third-party services and credentials.
3. How users decline it, continue locally, export, cancel and recover their work.
4. What staff/providers can access, retention/deletion behaviour and the actual security controls.
5. Price/limits and the effect of expiry, outages and account closure.
6. Which feedback shaped the decision and where users can question it.

If a capability fails these checks, correct it or narrow the claim before release. Product and revenue plans must follow these commitments; convenience or income does not justify concealed data use or lock-in.
