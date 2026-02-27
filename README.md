# Open Contributions Descriptor (OCD)

The **Open Contributions Descriptor (OCD)** is an open, machine-readable JSON format that allows an organization to publish a structured description of its participation in the open ecosystem.

It provides a single discovery endpoint describing:

- Open source software projects  
- Open data publications  
- Open standards contributions  
- Governance and participation information  
- Machine-consumable interfaces (e.g., OpenAPI)

The goal of OCD is to make organizational openness **discoverable, interoperable, and automatable**.

The format is described at [format.md](format.md) and described in the JSON schema at [ocd-schema.json](./schema/ocd-schema.json)

An online viewer and editor is available at: [https://ossbase-org.github.io/ocd-viewer/app/home.html](https://ossbase-org.github.io/ocd-viewer/app/home.html)

## Why OCD?

Organizations contribute to openness in many ways, but this information is usually scattered across websites, repositories, documentation portals, and standards bodies.

OCD solves this by defining a **single canonical document** that tools and humans can rely on.

Inspired by existing well-known metadata standards such as:

- `security.txt`
- OpenAPI specifications
- SBOM formats
- Mozilla’s historical [`contribute.json`](https://github.com/mozilla/contribute.json)

OCD extends the concept beyond open source code to include the broader open ecosystem.

## Discovery Location

An OCD file SHOULD be published at:

`https://<organization-domain>/.well-known/open-contributions.json`

An example with the MISP Project: [https://www.misp-project.org/.well-known/open-contributions.json](https://www.misp-project.org/.well-known/open-contributions.json).

This enables automatic discovery by tools, catalogs, and ecosystem services.

## What OCD Describes

### Organization Metadata

Basic information about the publishing organization:

- name and domain
- description
- country
- public links

### Open Source Projects

Each project can include:

- repository location and license
- lifecycle status (`active`, `archived`, `disabled`)
- documentation and community links
- contribution entry points
- governance metadata
- release and security policy links
- machine-readable interfaces (e.g., OpenAPI)

This enables automated project inventories and ecosystem indexing.


### Open Data

Organizations can publish datasets with:

- licensing information
- download and API endpoints
- update frequency
- schemas and formats

Supporting open data discovery and reuse.

### Open Standards Participation

OCD allows organizations to describe contributions to:

- standards bodies (IETF, W3C, etc.)
- working groups
- drafts, specifications, and implementations

Making standards participation transparent and discoverable.

### Extensions

The format is intentionally extensible:

- unknown fields MUST be ignored by consumers
- organizations MAY add custom namespaces under `extensions`

This allows experimentation without breaking compatibility.

