# Open Contributions Descriptor (OCD)

## Specification — Version 1.0 (Draft)

The **Open Contributions Descriptor (OCD)** is a machine-readable JSON format that allows an organization to describe its participation in the open ecosystem, including:

- Open source software projects
- Open data publications
- Open standards contributions
- Participation and governance metadata
- Machine-consumable interfaces (e.g., OpenAPI)

The descriptor is intended to be published at a predictable location:

`https://<organization-domain>/.well-known/open-contributions.json`

The Open Contributions Descriptor provides a unified, extensible, and discoverable way for organizations to publish their participation in the global open ecosystem through a single machine-readable document.

# Design Goals

- Provide a **single discovery endpoint** for organizational open activities
- Remain compatible with the philosophy of the original [Mozilla’s `contribute.json`](https://github.com/mozilla/contribute.json)
- Support both **human discovery** and **machine automation**
- Be extensible without breaking compatibility
- Allow partial adoption

Unknown fields MUST be ignored by consumers.

# Top-Level Structure

| Field | Type | Required | Description |
|---|---|---|---|
| `spec_version` | string | YES | Version of the OCD specification implemented by the file. |
| `generated_at` | string (RFC3339 datetime) | YES | Timestamp indicating when the file was generated. |
| `organization` | object | YES | Metadata describing the publishing organization. |
| `contacts` | object | NO | Contact information related to open activities. |
| `policies` | object | NO | Organizational policies relevant to openness and participation. |
| `projects` | array | NO | List of open source projects maintained or contributed to. |
| `open_data` | array | NO | Published open datasets and feeds. |
| `open_standards` | array | NO | Participation in standards organizations or specifications. |
| `extensions` | object | NO | Vendor or organization-specific extensions. |

# Organization Object

Describes the entity publishing the descriptor.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | YES | Official organization name. |
| `domain` | string | YES | Primary domain hosting the descriptor. |
| `description` | string | NO | Short description of the organization. |
| `country` | string | NO | ISO 3166-1 alpha-2 country code. |
| `links` | object | NO | Public organizational links. |

### organization.links

| Field | Description |
|---|---|
| `homepage` | Main organizational website. |
| `opensource_page` | Dedicated open-source or OSPO page. |
| `github_org` | Primary source-code organization profile. |


# Contacts Object

Provides points of contact.

| Field | Type | Description |
|---|---|---|
| `opensource` | object | General open-source contact. |
| `security` | object | Security disclosure reference (SHOULD point to `security.txt`). |
| `community` | object | Community engagement contact. |

Each contact object MAY contain:

| Field | Type | Description |
|---|---|---|
| `email` | string | Contact email address. |
| `url` | string | Contact webpage. |


# Policies Object

Links to organizational governance and participation policies.

| Field | Description |
|---|---|
| `code_of_conduct` | Community code of conduct. |
| `contributing` | Contribution guidelines. |
| `vulnerability_disclosure` | Vulnerability disclosure policy. |
| `license_policy` | Licensing strategy or guidance. |


# Projects Array

Describes open source projects.

Each entry represents one project.

## Required Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Project name. |
| `description` | string | Short description. |
| `repository` | object | Source repository metadata. |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `links` | object | Human-facing and machine-facing project resources. |
| `status` | enum | `["active","archived","disabled"]` |  

### status 

- `active` : Maintained and accepting contributions.
- `archived`: No active development but preserved.
- `disabled`: Service or project no longer available.

## Repository Object

| Field | Required | Description |
|---|---|---|
| `url` | YES | Canonical repository URL. |
| `license` | YES | SPDX license identifier. |
| `type` | NO | Repository type (e.g., `git`). |
| `clone` | NO | Clone URL. |
| `tests` | NO | Continuous integration or test URL. |

## Links Object

Human-facing and machine-facing project resources.

| Field | Description |
|---|---|
| `project_page` | Canonical human-readable project page (RECOMMENDED). |
| `homepage` | Organization-hosted overview page. |
| `documentation` | Official documentation. |
| `demo` | Live deployment or demo instance. |
| `releases` | Release or download page. |
| `community` | Chat/forum/community hub. |
| `metadata` | Machine-consumable descriptors. |

### links.metadata

Machine-readable interfaces associated with the project.

| Field | Description |
|---|---|
| `openapi` | URL to OpenAPI specification describing the project API. |

Additional metadata keys MAY be added.

## Participate Object

Describes how external contributors can engage.

| Field | Description |
|---|---|
| `issues` | Issue tracker URL. |
| `good_first_issues` | Beginner-friendly issues. |
| `chat` | Real-time communication channel. |
| `docs` | Contribution or developer documentation. |


## Governance Object

Project governance information.

| Field | Description |
|---|---|
| `maintainers` | List of maintainer contacts. |
| `codeowners` | CODEOWNERS file location. |

## Release Object

Release and security lifecycle information.

| Field | Description |
|---|---|
| `changelog` | Release history. |
| `security_policy` | Project security policy. |


## Tags

Array of keywords describing the project domain.

Example:

`["security", "csirt", "automation"]`

# Open Data Array

Describes datasets published as open data.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | YES | Dataset name. |
| `description` | string | NO | Dataset summary. |
| `license` | string | YES | Data license (e.g., CC-BY-4.0). |
| `publisher` | string | NO | Publishing entity. |
| `urls` | object | YES | Access points. |
| `formats` | array | NO | Available formats. |
| `update_frequency` | string | NO | Publication cadence. |
| `schema` | string | NO | Schema definition URL. |
| `tags` | array | NO | Dataset categories. |

### open_data.urls

| Field | Description |
|---|---|
| `landing_page` | Human-readable dataset page. |
| `download` | Direct dataset download. |
| `api` | API endpoint. |

# Open Standards Array

Describes participation in standards bodies.

| Field | Type | Description |
|---|---|---|
| `body` | string | Standards organization (e.g., IETF, W3C). |
| `working_groups` | array | Associated working groups. |
| `contributions` | array | Contributions made. |
| `contacts` | array | Standards participation contacts. |

### contributions object

| Field | Description |
|---|---|
| `type` | Contribution type (`draft-author`, `editor`, `implementation`, `review`, etc.). |
| `title` | Contribution title. |
| `url` | Reference URL. |

# Extensions Object

Allows custom additions without breaking compatibility.

Rules:

- Consumers MUST ignore unknown extension fields.
- Extensions SHOULD be namespaced logically.

Example:

~~~
"extensions": {
"research": {
"funded_by": "EU Program Example"
}
}
~~~

# Versioning

- `spec_version` identifies the schema version.
- Minor additions MUST remain backward compatible.
- Consumers SHOULD ignore unknown fields.

# Recommended Validation Rules

- JSON MUST be UTF-8 encoded.
- Licenses SHOULD use SPDX identifiers.
- Datetimes MUST follow RFC 3339.

# Intended Use Cases

- OSPO inventories
- Government and automatic open-source catalogs
- CSIRT ecosystem discovery
- Automated API/service discovery
- Research and funding transparency
- Open ecosystem mapping


# Sample JSON

~~~
{
  "spec_version": "1.0",
  "generated_at": "2026-02-23T09:00:00Z",

  "organization": {
    "name": "Example Organization",
    "domain": "example.org",
    "description": "An organization contributing to open source software, open data, and open standards.",
    "country": "LU",
    "links": {
      "homepage": "https://example.org",
      "opensource_page": "https://example.org/open",
      "github_org": "https://github.com/example-org"
    }
  },

  "contacts": {
    "opensource": {
      "email": "opensource@example.org"
    },
    "security": {
      "url": "https://example.org/.well-known/security.txt"
    },
    "community": {
      "email": "community@example.org"
    }
  },

  "policies": {
    "code_of_conduct": "https://example.org/code-of-conduct",
    "contributing": "https://example.org/contributing",
    "vulnerability_disclosure": "https://example.org/security",
    "license_policy": "https://example.org/open/licensing"
  },

  "projects": [
    {
      "name": "Vulnerability Lookup",
      "description": "An open platform to correlate and explore vulnerability intelligence.",
      "status": "active",

      "repository": {
        "url": "https://github.com/example-org/vulnerability-lookup",
        "license": "AGPL-3.0",
        "type": "git",
        "clone": "https://github.com/example-org/vulnerability-lookup.git",
        "tests": "https://ci.example.org/job/vulnerability-lookup/"
      },

      "links": {
        "project_page": "https://www.vulnerability-lookup.org",
        "homepage": "https://example.org/projects/vulnerability-lookup",
        "documentation": "https://docs.vulnerability-lookup.org",
        "demo": "https://vulnerability.example.org",
        "releases": "https://github.com/example-org/vulnerability-lookup/releases",
        "community": "https://matrix.to/#/#vulnlookup:matrix.org",
        "metadata": {
          "openapi": "https://vulnerability.example.org/openapi.json"
        }
      },

      "participate": {
        "issues": "https://github.com/example-org/vulnerability-lookup/issues",
        "good_first_issues": "https://github.com/example-org/vulnerability-lookup/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22",
        "chat": "https://matrix.to/#/#vulnlookup:matrix.org",
        "docs": "https://docs.vulnerability-lookup.org"
      },

      "governance": {
        "maintainers": [
          "maintainers@example.org"
        ],
        "codeowners": "https://github.com/example-org/vulnerability-lookup/blob/main/CODEOWNERS"
      },

      "release": {
        "changelog": "https://github.com/example-org/vulnerability-lookup/releases",
        "security_policy": "https://github.com/example-org/vulnerability-lookup/security/policy"
      },

      "tags": [
        "security",
        "vulnerability-management",
        "open-source"
      ]
    },

    {
      "name": "Flowintel",
      "description": "Threat intelligence ingestion and correlation framework.",
      "status": "archived",

      "repository": {
        "url": "https://github.com/example-org/flowintel",
        "license": "GPL-3.0-or-later",
        "type": "git"
      },

      "links": {
        "project_page": "https://example.org/projects/flowintel",
        "documentation": "https://docs.example.org/flowintel",
        "releases": "https://github.com/example-org/flowintel/releases",
        "metadata": {
          "openapi": "https://api.example.org/flowintel/openapi.json"
        }
      },

      "participate": {
        "issues": "https://github.com/example-org/flowintel/issues"
      },

      "tags": [
        "threat-intelligence",
        "csirt",
        "automation"
      ]
    }
  ],

  "open_data": [
    {
      "name": "Daily Threat Indicators",
      "description": "Open dataset of curated threat intelligence indicators.",
      "license": "CC-BY-4.0",
      "publisher": "Example Organization",

      "urls": {
        "landing_page": "https://example.org/data/threat-indicators",
        "download": "https://example.org/data/threat-indicators/latest.json",
        "api": "https://example.org/api/threat-indicators"
      },

      "formats": [
        "json",
        "csv"
      ],

      "update_frequency": "daily",
      "schema": "https://example.org/data/threat-indicators/schema.json",

      "tags": [
        "open-data",
        "cybersecurity",
        "threat-intelligence"
      ]
    }
  ],

  "open_standards": [
    {
      "body": "IETF",
      "working_groups": [
        "openpgp",
        "sidrops"
      ],

      "contributions": [
        {
          "type": "draft-author",
          "title": "Example Secure Exchange Format",
          "url": "https://datatracker.ietf.org/doc/draft-example-secure-exchange/"
        },
        {
          "type": "implementation",
          "title": "Reference implementation",
          "url": "https://github.com/example-org/secure-exchange"
        }
      ],

      "contacts": [
        {
          "email": "standards@example.org"
        }
      ]
    }
  ],

  "extensions": {}
}
~~~

# JSON Schema

~~~
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/open-contributions-descriptor-1.0.schema.json",
  "title": "Open Contributions Descriptor (OCD)",
  "description": "Machine-readable descriptor for an organization's open source projects, open data publications, and open standards participation.",
  "type": "object",
  "additionalProperties": true,

  "required": ["spec_version", "generated_at", "organization"],

  "properties": {
    "spec_version": {
      "type": "string",
      "description": "Version of the OCD specification implemented by this document.",
      "minLength": 1
    },

    "generated_at": {
      "type": "string",
      "description": "Timestamp indicating when the file was generated (RFC 3339 date-time).",
      "format": "date-time"
    },

    "organization": { "$ref": "#/$defs/organization" },
    "contacts": { "$ref": "#/$defs/contacts" },
    "policies": { "$ref": "#/$defs/policies" },

    "projects": {
      "type": "array",
      "description": "List of open source projects maintained or contributed to.",
      "items": { "$ref": "#/$defs/project" }
    },

    "open_data": {
      "type": "array",
      "description": "Published open datasets and feeds.",
      "items": { "$ref": "#/$defs/openData" }
    },

    "open_standards": {
      "type": "array",
      "description": "Participation in standards organizations or specifications.",
      "items": { "$ref": "#/$defs/openStandards" }
    },

    "extensions": {
      "type": "object",
      "description": "Vendor or organization-specific extensions. Consumers MUST ignore unknown extension fields.",
      "additionalProperties": true
    }
  },

  "$defs": {
    "url": {
      "type": "string",
      "format": "uri",
      "minLength": 1
    },

    "email": {
      "type": "string",
      "format": "email",
      "minLength": 3
    },

    "tags": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 },
      "uniqueItems": true
    },

    "organization": {
      "type": "object",
      "additionalProperties": true,
      "required": ["name", "domain"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "domain": {
          "type": "string",
          "description": "Primary domain hosting the descriptor (e.g., example.org).",
          "minLength": 1
        },
        "description": { "type": "string" },
        "country": {
          "type": "string",
          "description": "ISO 3166-1 alpha-2 country code.",
          "pattern": "^[A-Z]{2}$"
        },
        "links": {
          "type": "object",
          "additionalProperties": true,
          "properties": {
            "homepage": { "$ref": "#/$defs/url" },
            "opensource_page": { "$ref": "#/$defs/url" },
            "github_org": { "$ref": "#/$defs/url" }
          }
        }
      }
    },

    "contacts": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "opensource": { "$ref": "#/$defs/contact" },
        "security": { "$ref": "#/$defs/contact" },
        "community": { "$ref": "#/$defs/contact" }
      }
    },

    "contact": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "email": { "$ref": "#/$defs/email" },
        "url": { "$ref": "#/$defs/url" }
      },
      "anyOf": [
        { "required": ["email"] },
        { "required": ["url"] }
      ]
    },

    "policies": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "code_of_conduct": { "$ref": "#/$defs/url" },
        "contributing": { "$ref": "#/$defs/url" },
        "vulnerability_disclosure": { "$ref": "#/$defs/url" },
        "license_policy": { "$ref": "#/$defs/url" }
      }
    },

    "project": {
      "type": "object",
      "additionalProperties": true,
      "required": ["name", "description", "repository"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "description": { "type": "string", "minLength": 1 },

        "status": {
          "type": "string",
          "description": "Lifecycle status of the project.",
          "enum": ["active", "archived", "disabled"]
        },

        "repository": { "$ref": "#/$defs/repository" },
        "links": { "$ref": "#/$defs/projectLinks" },
        "participate": { "$ref": "#/$defs/participate" },
        "governance": { "$ref": "#/$defs/governance" },
        "release": { "$ref": "#/$defs/release" },
        "tags": { "$ref": "#/$defs/tags" }
      }
    },

    "repository": {
      "type": "object",
      "additionalProperties": true,
      "required": ["url", "license"],
      "properties": {
        "url": { "$ref": "#/$defs/url" },
        "license": {
          "type": "string",
          "description": "SPDX license identifier (recommended).",
          "minLength": 1
        },
        "type": { "type": "string", "minLength": 1 },
        "clone": { "$ref": "#/$defs/url" },
        "tests": { "$ref": "#/$defs/url" }
      }
    },

    "projectLinks": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "project_page": { "$ref": "#/$defs/url" },
        "homepage": { "$ref": "#/$defs/url" },
        "documentation": { "$ref": "#/$defs/url" },
        "demo": { "$ref": "#/$defs/url" },
        "releases": { "$ref": "#/$defs/url" },
        "community": { "$ref": "#/$defs/url" },
        "metadata": { "$ref": "#/$defs/projectMetadata" }
      }
    },

    "projectMetadata": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "openapi": { "$ref": "#/$defs/url" }
      }
    },

    "participate": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "issues": { "$ref": "#/$defs/url" },
        "good_first_issues": { "$ref": "#/$defs/url" },
        "chat": { "$ref": "#/$defs/url" },
        "docs": { "$ref": "#/$defs/url" }
      }
    },

    "governance": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "maintainers": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 }
        },
        "codeowners": { "$ref": "#/$defs/url" }
      }
    },

    "release": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "changelog": { "$ref": "#/$defs/url" },
        "security_policy": { "$ref": "#/$defs/url" }
      }
    },

    "openData": {
      "type": "object",
      "additionalProperties": true,
      "required": ["name", "license", "urls"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "license": { "type": "string", "minLength": 1 },
        "publisher": { "type": "string" },

        "urls": { "$ref": "#/$defs/openDataUrls" },

        "formats": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true
        },

        "update_frequency": {
          "type": "string",
          "description": "Publication cadence (e.g., daily, weekly, monthly)."
        },

        "schema": { "$ref": "#/$defs/url" },
        "tags": { "$ref": "#/$defs/tags" }
      }
    },

    "openDataUrls": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "landing_page": { "$ref": "#/$defs/url" },
        "download": { "$ref": "#/$defs/url" },
        "api": { "$ref": "#/$defs/url" }
      },
      "anyOf": [
        { "required": ["download"] },
        { "required": ["api"] },
        { "required": ["landing_page"] }
      ]
    },

    "openStandards": {
      "type": "object",
      "additionalProperties": true,
      "required": ["body"],
      "properties": {
        "body": { "type": "string", "minLength": 1 },

        "working_groups": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true
        },

        "contributions": {
          "type": "array",
          "items": { "$ref": "#/$defs/standardsContribution" }
        },

        "contacts": {
          "type": "array",
          "items": { "$ref": "#/$defs/contact" }
        }
      }
    },

    "standardsContribution": {
      "type": "object",
      "additionalProperties": true,
      "required": ["type", "title", "url"],
      "properties": {
        "type": {
          "type": "string",
          "description": "Contribution type (e.g., draft-author, editor, implementation, review).",
          "minLength": 1
        },
        "title": { "type": "string", "minLength": 1 },
        "url": { "$ref": "#/$defs/url" }
      }
    }
  }
}
~~~
