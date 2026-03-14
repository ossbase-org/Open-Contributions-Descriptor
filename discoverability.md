# OCD Discoverability Guide

This guide explains practical ways an open source contributor or maintainer can make an **Open Contributions Descriptor (OCD)** document easy for tools and people to discover.

## Goal

Publish a valid `open-contributions.json` file at a predictable location so:

- discovery tools can find it automatically,
- catalog and compliance systems can index it,
- contributors and users can verify openness and participation metadata.

The canonical location is:

`https://<your-domain>/.well-known/open-contributions.json`

## 1) Create and Validate the Descriptor

1. Start from one of the examples in `samples/`.
2. Adapt it to your organization and projects.
3. Validate against the repository schema:

```bash
python3 bin/validator.py path/to/open-contributions.json
```

Tip: add validation to CI so updates are always schema-compliant.

## 2) Publish on a Stable Domain

Use a domain you control (organization root domain preferred). Serve the descriptor from:

- `/.well-known/open-contributions.json` (recommended), or
- a stable alternate URL plus a redirect from `/.well-known/...`.

### Web server examples

#### NGINX

```nginx
location = /.well-known/open-contributions.json {
    default_type application/json;
    add_header Cache-Control "public, max-age=300";
    try_files $uri =404;
}
```

#### Apache

```apache
<Files "open-contributions.json">
  Header set Content-Type "application/json"
  Header set Cache-Control "public, max-age=300"
</Files>
```

#### Static hosting (GitHub Pages / object storage)

If your host does not support `.well-known` directly, use:

- edge routing rules,
- reverse proxy mapping,
- or HTTP redirect rules.

## 3) Make Machine Discovery Reliable

For robust discovery, keep behavior predictable:

- Return `200 OK` for the descriptor URL.
- Set `Content-Type: application/json`.
- Use HTTPS.
- Avoid auth requirements for read access.
- Keep URL stable across site redesigns.
- Prefer short cache TTLs (or purge on update).

Optional but helpful:

- Add `Link` headers from your homepage pointing to the descriptor.
- Include descriptor URL in developer docs and OSPO pages.

## 4) Make Human Discovery Easy

Even with `.well-known`, add visible references:

- Repository `README.md`
- Project website footer or trust page
- Security and governance pages
- API or developer portal

Suggested snippet:

```md
## Open Contributions Descriptor

We publish our OCD file at:
https://example.org/.well-known/open-contributions.json
```

## 5) Keep the File Fresh

A discoverable but stale file reduces trust. Maintain it as operational metadata:

- Update `generated_at` on every release/update.
- Add new projects, datasets, standards activity promptly.
- Remove archived or deprecated items (or mark status explicitly).
- Version-control the JSON document.
- Review quarterly (or automatically in release workflows).

## 6) Suggested Automation Pattern

A lightweight implementation pattern:

1. Source metadata from repository/org config.
2. Generate `open-contributions.json` in CI.
3. Validate with `bin/validator.py`.
4. Publish to web root `/.well-known/open-contributions.json`.
5. Run a smoke check:

```bash
curl -sSf https://<your-domain>/.well-known/open-contributions.json | jq .spec_version
```

## 7) Maintainer Checklist

- [ ] Descriptor is valid against `schema/ocd-schema.json`.
- [ ] Published at `/.well-known/open-contributions.json`.
- [ ] Served with `Content-Type: application/json`.
- [ ] Publicly accessible via HTTPS without authentication.
- [ ] Referenced from human-facing docs/pages.
- [ ] Included in ongoing maintenance workflow.

## 8) Multi-Organization and Project-Level Publication

If your ecosystem spans multiple domains:

- Publish one OCD per organization domain.
- Use each file's `relationships` section to connect related entities.
- Keep project-level metadata in the organization's canonical descriptor.

This enables federated ecosystem discovery while preserving clear ownership boundaries.
