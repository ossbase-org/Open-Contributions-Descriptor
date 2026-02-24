#!/usr/bin/env python3
"""
Generate an Open Contributions Descriptor (OCD) JSON file from a GitHub organization.

What it does
- Pulls public repositories from a GitHub org
- Produces OCD JSON adhering to your draft spec:
  - Top-level: spec_version, generated_at, organization
  - Projects: name, description, status (active|archived|disabled), repository (url/license/...), links (project_page/metadata.openapi when detected)
- Optionally detects OpenAPI specs by looking for common files in the repo root:
  openapi.json, openapi.yaml, openapi.yml, swagger.json, swagger.yaml, swagger.yml

Requirements
- Python 3.9+
- requests (pip install requests)

Auth
- Optional but recommended to avoid low rate limits:
  export GITHUB_TOKEN="ghp_... or fine-grained token"

Examples
  python generate_ocd.py --org example-org --domain example.org > open-contributions.json
  python generate_ocd.py --org example-org --domain example.org --output open-contributions.json

Notes / Limitations
- GitHub does not provide a reliable "organization domain" value; you must supply --domain.
- License can be missing; we default to "NOASSERTION" to keep schema validity.
- "tests" URL is not reliably derivable across all CI systems; we omit it by default.
- "security_policy" link is included heuristically (GitHub renders it if present).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests


GITHUB_API = "https://api.github.com"
DEFAULT_SPEC_VERSION = "1.0"

OPENAPI_CANDIDATES = [
    "openapi.json",
    "openapi.yaml",
    "openapi.yml",
    "swagger.json",
    "swagger.yaml",
    "swagger.yml",
]


@dataclass
class GitHubClient:
    token: Optional[str]
    session: requests.Session

    @classmethod
    def create(cls, token: Optional[str]) -> "GitHubClient":
        s = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ocd-generator/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        s.headers.update(headers)
        return cls(token=token, session=s)

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        r = self.session.get(url, params=params, timeout=30)
        if r.status_code == 403 and "rate limit" in (r.text or "").lower():
            raise RuntimeError(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN to increase limits."
            )
        return r

    def paginated_get(self, url: str, params: Optional[dict] = None) -> List[dict]:
        items: List[dict] = []
        page = 1
        while True:
            p = dict(params or {})
            p.update({"per_page": 100, "page": page})
            r = self.get(url, params=p)
            if r.status_code != 200:
                raise RuntimeError(f"GitHub API error {r.status_code}: {r.text}")
            batch = r.json()
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected GitHub response: {batch}")
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def safe_spdx(repo: dict) -> str:
    """
    Return SPDX license id if present; otherwise NOASSERTION.
    """
    lic = repo.get("license")
    if isinstance(lic, dict):
        spdx = lic.get("spdx_id")
        if spdx and spdx != "NOASSERTION":
            return str(spdx)
        # GitHub often returns "NOASSERTION" explicitly; keep it valid
        if spdx:
            return str(spdx)
    return "NOASSERTION"


def repo_status(repo: dict) -> str:
    """
    Map GitHub repository flags to OCD project.status enum:
      - archived -> archived
      - disabled -> disabled
      - else     -> active
    """
    if repo.get("archived") is True:
        return "archived"
    if repo.get("disabled") is True:
        return "disabled"
    return "active"


def github_html(path: str) -> str:
    return f"https://github.com/{path.lstrip('/')}"


def build_good_first_issues_url(owner: str, repo_name: str) -> str:
    # GitHub issues query URL (human friendly)
    return github_html(
        f"{owner}/{repo_name}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22"
    )


def try_detect_openapi(
    gh: GitHubClient, owner: str, repo_name: str, default_branch: str
) -> Optional[str]:
    """
    Detect common OpenAPI spec files in the repo root via the contents API.
    If found, return a raw.githubusercontent.com URL.
    """
    # Contents API: /repos/{owner}/{repo}/contents/{path}
    # Use path "" (root) to list root entries.
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}/contents"
    r = gh.get(url, params={"ref": default_branch})
    if r.status_code != 200:
        return None
    data = r.json()
    if not isinstance(data, list):
        return None

    names = {item.get("name", "") for item in data if isinstance(item, dict)}
    for candidate in OPENAPI_CANDIDATES:
        if candidate in names:
            # Prefer raw content URL (stable, directly fetchable)
            return f"https://raw.githubusercontent.com/{owner}/{repo_name}/{default_branch}/{candidate}"
    return None


def try_detect_codeowners_link(
    gh: GitHubClient, owner: str, repo_name: str, default_branch: str
) -> Optional[str]:
    """
    Check typical CODEOWNERS locations. If present, return a GitHub blob URL.
    """
    candidates = [
        "CODEOWNERS",
        ".github/CODEOWNERS",
        "docs/CODEOWNERS",
    ]
    for path in candidates:
        url = f"{GITHUB_API}/repos/{owner}/{repo_name}/contents/{path}"
        r = gh.get(url, params={"ref": default_branch})
        if r.status_code == 200:
            return github_html(f"{owner}/{repo_name}/blob/{default_branch}/{path}")
    return None


def build_project(repo: dict, gh: GitHubClient, owner: str) -> Dict[str, Any]:
    name = repo.get("name") or "unknown"
    description = repo.get("description") or ""
    status = repo_status(repo)
    default_branch = repo.get("default_branch") or "main"

    html_url = repo.get("html_url") or github_html(f"{owner}/{name}")
    clone_url = repo.get("clone_url")  # https clone

    project: Dict[str, Any] = {
        "name": name,
        "description": description if description else "No description provided.",
        "status": status,
        "_stars": repo.get("stargazers_count", 0),  # Use to sort the table
        "repository": {
            "url": html_url,
            "license": safe_spdx(repo),
            "type": "git",
        },
    }

    if clone_url:
        project["repository"]["clone"] = clone_url

    # Links (human + machine)
    links: Dict[str, Any] = {}

    # project_page: prefer repo homepage if provided; else omit
    homepage = repo.get("homepage")
    if isinstance(homepage, str) and homepage.strip():
        links["project_page"] = homepage.strip()

    # documentation: if homepage looks like docs or is explicitly set, keep as documentation too (optional)
    # (We keep it conservative: only set documentation if explicitly contains 'docs' or 'readthedocs' or similar.)
    if isinstance(homepage, str) and homepage.strip():
        hp = homepage.strip().lower()
        if "docs" in hp or "readthedocs" in hp:
            links["documentation"] = homepage.strip()

    # releases: always available
    links["releases"] = github_html(f"{owner}/{name}/releases")

    # Optional OpenAPI detection
    openapi_url = try_detect_openapi(gh, owner, name, default_branch)
    if openapi_url:
        links.setdefault("metadata", {})
        links["metadata"]["openapi"] = openapi_url

    if links:
        project["links"] = links

    # Participate
    participate: Dict[str, Any] = {}
    if repo.get("has_issues") is True:
        participate["issues"] = github_html(f"{owner}/{name}/issues")
        participate["good_first_issues"] = build_good_first_issues_url(owner, name)
    # docs link: if we have documentation link, reuse it
    if "links" in project and isinstance(project["links"], dict):
        doc_url = project["links"].get("documentation")
        if isinstance(doc_url, str) and doc_url:
            participate["docs"] = doc_url

    if participate:
        project["participate"] = participate

    # Governance: CODEOWNERS if found
    codeowners = try_detect_codeowners_link(gh, owner, name, default_branch)
    if codeowners:
        project["governance"] = {"codeowners": codeowners}

    # Release: changelog + security_policy (heuristic)
    release: Dict[str, Any] = {
        "changelog": github_html(f"{owner}/{name}/releases"),
        "security_policy": github_html(f"{owner}/{name}/security/policy"),
    }
    project["release"] = release

    # Tags: optionally use topics if present (requires preview in older APIs; now generally available)
    topics = repo.get("topics")
    if isinstance(topics, list) and topics:
        # Only keep non-empty strings
        cleaned = sorted({t.strip() for t in topics if isinstance(t, str) and t.strip()})
        if cleaned:
            project["tags"] = cleaned

    return project


def build_ocd(
    org: str,
    domain: str,
    spec_version: str,
    gh: GitHubClient,
    include_forks: bool,
    include_archived: bool,
    max_repos: Optional[int],
) -> Dict[str, Any]:
    # Org metadata
    org_url = f"{GITHUB_API}/orgs/{org}"
    r = gh.get(org_url)
    if r.status_code != 200:
        raise RuntimeError(f"Unable to read org '{org}': {r.status_code}: {r.text}")
    org_data = r.json()

    org_name = org_data.get("name") or org
    org_desc = org_data.get("description") or ""

    # Repos
    repos_url = f"{GITHUB_API}/orgs/{org}/repos"
    repos = gh.paginated_get(repos_url, params={"type": "public", "sort": "full_name"})

    projects: List[Dict[str, Any]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        if not include_forks and repo.get("fork") is True:
            continue
        if not include_archived and repo.get("archived") is True:
            continue

        projects.append(build_project(repo, gh, owner=org))
        if max_repos is not None and len(projects) >= max_repos:
            break
    projects.sort(key=lambda p: p.get("_stars", 0), reverse=True)

    for p in projects:
        p.pop("_stars", None)

    ocd: Dict[str, Any] = {
        "spec_version": spec_version,
        "generated_at": now_rfc3339(),
        "organization": {
            "name": org_name,
            "domain": domain,
        },
        "projects": projects,
        "extensions": {},
    }

    if org_desc:
        ocd["organization"]["description"] = org_desc

    # Optional org links (best-effort)
    links: Dict[str, str] = {}
    blog = org_data.get("blog")
    if isinstance(blog, str) and blog.strip():
        # Sometimes "blog" is a homepage URL; keep it
        links["homepage"] = blog.strip()
    html_url = org_data.get("html_url")
    if isinstance(html_url, str) and html_url.strip():
        links["github_org"] = html_url.strip()
    if links:
        ocd["organization"]["links"] = links

    # Keep empty open_data/open_standards out (spec says optional)
    return ocd


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate OCD JSON from a GitHub organization.")
    ap.add_argument("--org", required=True, help="GitHub organization login (e.g., 'mozilla').")
    ap.add_argument("--domain", required=True, help="Organization domain hosting /.well-known/open-contributions.json (e.g., example.org).")
    ap.add_argument("--spec-version", default=DEFAULT_SPEC_VERSION, help="OCD spec version (default: 1.0).")
    ap.add_argument("--output", default="-", help="Output file path, or '-' for stdout (default).")
    ap.add_argument("--include-forks", action="store_true", help="Include forked repositories.")
    ap.add_argument("--include-archived", action="store_true", help="Include archived repositories.")
    ap.add_argument("--max-repos", type=int, default=None, help="Limit number of repos processed (debug/testing).")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    gh = GitHubClient.create(token=token)

    try:
        ocd = build_ocd(
            org=args.org,
            domain=args.domain,
            spec_version=args.spec_version,
            gh=gh,
            include_forks=args.include_forks,
            include_archived=args.include_archived,
            max_repos=args.max_repos,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    out = json.dumps(ocd, indent=2, ensure_ascii=False)
    if args.output == "-" or not args.output:
        print(out)
        return 0

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
