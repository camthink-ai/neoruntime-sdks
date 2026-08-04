# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in NE503, please report it privately:

1. Email the maintainers (see the repo's security advisories tab, or the
   contact in the README).
2. **Do not** open a public GitHub issue for security findings.
3. Include: affected component, steps to reproduce, impact, and any fix ideas.

We acknowledge reports within 5 business days and aim for a fix or mitigation
within 90 days, coordinated with public disclosure timing.

## Scope

- Platform services (Go) under `platform/`
- HAL (C/C++) under `hal/`, `hal_v2/`
- Web console under `web/`
- Python SDK under `sdk/python/`

Out of scope: issues in vendored third-party code (report upstream).

## Hardening notes

- Authentication secrets are **not** baked into the repo. Set `AIPC_TOKEN_KEY`,
  `AIPC_AUTH_USERNAME`, `AIPC_AUTH_PASSWORD` at deploy time. A missing
  `AIPC_TOKEN_KEY` causes platform-api to generate a random per-boot secret and
  log it once; set the env var to persist it across restarts.
- HTTPS is on by default with a self-signed auto-generated certificate; supply
  your own cert/key via the `tls` config block for production.
- The seccomp profile is at `configs/security/seccomp-default.json`.
