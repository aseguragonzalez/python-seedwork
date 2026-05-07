# Security Policy

## Supported Versions

Only the latest released version of **python-seedwork** receives security fixes.
Older versions are not patched; please upgrade to the current release.

| Version | Supported |
| ------- | --------- |
| latest  | Yes       |
| older than latest | No |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Use one of the following private channels:

1. **GitHub Security Advisories (preferred)** — open a draft advisory at
   `Security → Advisories → Report a vulnerability` in this repository.
   GitHub keeps the report private until a fix is published.

2. **Email** — send details to <a.segura.gonzalez@gmail.com>.
   Encrypt your message with the PGP key published on the repository's
   Security Advisories page if the report is highly sensitive.

### What to include

- A clear description of the vulnerability and its potential impact.
- The affected version(s).
- Step-by-step reproduction instructions or a proof-of-concept.
- Any suggested mitigations you are already aware of.

### What to expect

| Timeline | Action |
| -------- | ------ |
| ≤ 3 business days | Acknowledgement of the report. |
| ≤ 14 days | Initial assessment and severity classification (CVSS). |
| ≤ 90 days | Patch release and coordinated public disclosure. |

The 90-day window follows [Google Project Zero's responsible disclosure
standard](https://googleprojectzero.blogspot.com/p/vulnerability-disclosure-faq.html).
Earlier disclosure may be agreed upon if a fix is ready sooner.

## Coordinated Disclosure

We follow the [CERT Coordinated Vulnerability Disclosure](https://vuls.cert.org/confluence/display/CVD)
model. Once a fix is shipped we will:

1. Publish a GitHub Security Advisory (which auto-requests a CVE from GitHub's
   CVE Numbering Authority if warranted).
2. Tag the patched release and update `CHANGELOG.md`.
3. Credit the reporter in the advisory unless they prefer to remain anonymous.

## Scope

This policy covers the `seedwork` package published on PyPI.
It does **not** cover vulnerabilities in downstream applications built on top of
this library, third-party dependencies, or example code in `docs/examples/`.

## Out of Scope

- Vulnerabilities in already-unsupported versions.
- Issues requiring physical access to infrastructure.
- Social engineering or phishing attacks.
- Theoretical attacks with no practical exploitation path.

## Security Best Practices for Consumers

`python-seedwork` ships pure Python with **no runtime dependencies**.
To reduce supply-chain risk in your project:

- Pin the exact version in your lock file (e.g. `uv lock`).
- Verify package provenance using trusted tooling (for example, Sigstore and
  GitHub release artifacts when available).
- Subscribe to GitHub Security Advisories for this repository to receive
  automated alerts.
