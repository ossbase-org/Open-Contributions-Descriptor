#!/usr/bin/env python3
"""
Generate or update an Open Contributions Descriptor (OCD) JSON file from a GitHub organization.

New in this version:
- Can update an existing OCD JSON file (merge by repository URL or name).
- Preserves non-project sections by default (open_data, open_standards, contacts, policies, extensions, etc.).
- Sorts projects by GitHub stars (descending), without adding a schema-visible field.

Requirements
- Python 3.9+
- requests (pip install requests)

Auth
- Optional but recommended to avoid low rate limits:
  export GITHUB_TOKEN="ghp_... or fine-grained token"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# ----------------------------
# GitHub API client
# ----------------------------

@dataclass
class GitHubClient:
    token: Optional[str]
    session: requests.Session

    @classmethod
    def create(cls, token: Optional[str]) -> "GitHubClient":
        s = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ocd-generator/1.1",
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


# ----------------------------
# Utility
# ----------------------------

def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def load_json_from_path_or_url(source: str) -> Any:
    if is_url(source):
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        return r.json()
    p = Path(source)
    if not p.exists():
        raise FileNotFoundError(f"Input JSON not found: {source}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_spdx(repo: dict) -> str:
    lic = repo.get("license")
    if isinstance(lic, dict):
        spdx = lic.get("spdx_id")
        if spdx:
            return str(spdx)
    return "NOASSERTION"


def repo_status(repo: dict) -> str:
    if repo.get("archived") is True:
        return "archived"
    if repo.get("disabled") is True:
        return "disabled"
    return "active"


def github_html(path: str) -> str:
    return f"https://github.com/{path.lstrip('/')}"


def build_good_first_issues_url(owner: str, repo_name: str) -> str:
    return github_html(
        f"{owner}/{repo_name}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22"
    )


def try_detect_openapi(gh: GitHubClient, owner: str, repo_name: str, default_branch: str) -> Optional[str]:
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
            return f"https://raw.githubusercontent.com/{owner}/{repo_name}/{default_branch}/{candidate}"
    return None


def try_detect_codeowners_link(gh: GitHubClient, owner: str, repo_name: str, default_branch: str) -> Optional[str]:
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


# ----------------------------
# Build a project from GitHub repo object
# ----------------------------

def build_project(repo: dict, gh: GitHubClient, owner: str) -> Dict[str, Any]:
    name = repo.get("name") or "unknown"
    description = repo.get("description") or ""
    status = repo_status(repo)
    default_branch = repo.get("default_branch") or "main"

    html_url = repo.get("html_url") or github_html(f"{owner}/{name}")
    clone_url = repo.get("clone_url")

    project: Dict[str, Any] = {
        "name": name,
        "description": description if description else "No description provided.",
        "status": status,

        # internal helper (removed later) used for sorting by popularity
        "_stars": repo.get("stargazers_count", 0),

        "repository": {
            "url": html_url,
            "license": safe_spdx(repo),
            "type": "git",
        },
    }

    if clone_url:
        project["repository"]["clone"] = clone_url

    # Links
    links: Dict[str, Any] = {}
    homepage = repo.get("homepage")
    if isinstance(homepage, str) and homepage.strip():
        links["project_page"] = homepage.strip()

        hp = homepage.strip().lower()
        if "docs" in hp or "readthedocs" in hp:
            links["documentation"] = homepage.strip()

    links["releases"] = github_html(f"{owner}/{name}/releases")

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

    if "links" in project and isinstance(project["links"], dict):
        doc_url = project["links"].get("documentation")
        if isinstance(doc_url, str) and doc_url:
            participate["docs"] = doc_url

    if participate:
        project["participate"] = participate

    # Governance
    codeowners = try_detect_codeowners_link(gh, owner, name, default_branch)
    if codeowners:
        project["governance"] = {"codeowners": codeowners}

    # Release
    project["release"] = {
        "changelog": github_html(f"{owner}/{name}/releases"),
        "security_policy": github_html(f"{owner}/{name}/security/policy"),
    }

    topics = repo.get("topics")
    if isinstance(topics, list) and topics:
        cleaned = sorted({t.strip() for t in topics if isinstance(t, str) and t.strip()})
        if cleaned:
            project["tags"] = cleaned

    return project


# ----------------------------
# Merging logic (update existing JSON)
# ----------------------------

def project_key(p: Dict[str, Any]) -> str:
    """
    Prefer repository.url as stable key; fall back to name.
    """
    repo = p.get("repository")
    if isinstance(repo, dict):
        url = repo.get("url")
        if isinstance(url, str) and url.strip():
            return f"repo:{url.strip()}"
    name = p.get("name")
    if isinstance(name, str) and name.strip():
        return f"name:{name.strip().lower()}"
    return "unknown"


def deep_merge_preserve(existing: Any, incoming: Any) -> Any:
    """
    Deep merge dicts where incoming wins on conflicts, but keeps existing keys not present in incoming.
    For non-dicts, incoming replaces existing.
    """
    if isinstance(existing, dict) and isinstance(incoming, dict):
        out = dict(existing)
        for k, v in incoming.items():
            if k in out:
                out[k] = deep_merge_preserve(out[k], v)
            else:
                out[k] = v
        return out
    return incoming


def merge_projects(existing_projects: List[Dict[str, Any]], new_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge by repository.url (preferred) or name. Keep custom fields from existing projects,
    but refresh core/project data from GitHub.
    """
    existing_index: Dict[str, Dict[str, Any]] = {project_key(p): p for p in existing_projects if isinstance(p, dict)}

    merged: List[Dict[str, Any]] = []
    for p in new_projects:
        k = project_key(p)
        if k in existing_index:
            # Preserve existing custom fields, but let GitHub-derived project win for known/core fields
            merged_project = deep_merge_preserve(existing_index[k], p)
            merged.append(merged_project)
        else:
            merged.append(p)

    return merged


# ----------------------------
# Build OCD (new or updated)
# ----------------------------

def build_ocd(
    org: str,
    domain: str,
    spec_version: str,
    gh: GitHubClient,
    include_forks: bool,
    include_archived: bool,
    max_repos: Optional[int],
    existing_ocd: Optional[Dict[str, Any]],
    replace_projects: bool,
) -> Dict[str, Any]:
    # Org metadata from GitHub
    org_url = f"{GITHUB_API}/orgs/{org}"
    r = gh.get(org_url)
    if r.status_code != 200:
        raise RuntimeError(f"Unable to read org '{org}': {r.status_code}: {r.text}")
    org_data = r.json()

    org_name = org_data.get("name") or org
    org_desc = org_data.get("description") or ""

    # Fetch repos
    repos_url = f"{GITHUB_API}/orgs/{org}/repos"
    repos = gh.paginated_get(repos_url, params={"type": "public", "sort": "full_name"})

    new_projects: List[Dict[str, Any]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        if not include_forks and repo.get("fork") is True:
            continue
        if not include_archived and repo.get("archived") is True:
            continue

        new_projects.append(build_project(repo, gh, owner=org))
        if max_repos is not None and len(new_projects) >= max_repos:
            break

    # Sort by stars desc (internal field), then remove helper
    new_projects.sort(key=lambda p: p.get("_stars", 0), reverse=True)
    for p in new_projects:
        p.pop("_stars", None)

    # Start from existing or create new
    if existing_ocd and isinstance(existing_ocd, dict):
        ocd: Dict[str, Any] = dict(existing_ocd)  # shallow copy
    else:
        ocd = {}

    # Ensure required top-level fields
    ocd["spec_version"] = spec_version
    ocd["generated_at"] = now_rfc3339()

    # Organization: merge/preserve extra fields if present, but update name/domain/description
    existing_org = ocd.get("organization") if isinstance(ocd.get("organization"), dict) else {}
    org_obj: Dict[str, Any] = dict(existing_org) if isinstance(existing_org, dict) else {}

    org_obj["name"] = org_name
    org_obj["domain"] = domain
    if org_desc:
        org_obj["description"] = org_desc

    # Optional org links (best-effort)
    links: Dict[str, str] = {}
    blog = org_data.get("blog")
    if isinstance(blog, str) and blog.strip():
        links["homepage"] = blog.strip()
    html_url = org_data.get("html_url")
    if isinstance(html_url, str) and html_url.strip():
        links["github_org"] = html_url.strip()
    if links:
        org_links = org_obj.get("links") if isinstance(org_obj.get("links"), dict) else {}
        org_obj["links"] = deep_merge_preserve(org_links, links)

    ocd["organization"] = org_obj

    # Projects: merge or replace
    if replace_projects:
        ocd["projects"] = new_projects
    else:
        existing_projects = ocd.get("projects") if isinstance(ocd.get("projects"), list) else []
        merged = merge_projects(existing_projects, new_projects)
        # Keep the merged list sorted by the GitHub stars ordering we already used (new_projects order):
        # We can enforce that order by building a key->index map from new_projects.
        order = {project_key(p): i for i, p in enumerate(new_projects)}
        merged.sort(key=lambda p: order.get(project_key(p), 10**9))
        ocd["projects"] = merged

    # Ensure extensions exists (nice default)
    if "extensions" not in ocd or not isinstance(ocd.get("extensions"), dict):
        ocd["extensions"] = {}

    return ocd


# ----------------------------
# CLI
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate or update OCD JSON from a GitHub organization.")
    ap.add_argument("--org", required=True, help="GitHub organization login (e.g., 'mozilla').")
    ap.add_argument("--domain", required=True, help="Organization domain hosting /.well-known/open-contributions.json (e.g., example.org).")
    ap.add_argument("--spec-version", default=DEFAULT_SPEC_VERSION, help="OCD spec version (default: 1.0).")
    ap.add_argument("--output", default="-", help="Output file path, or '-' for stdout (default).")

    ap.add_argument(
        "--input",
        default=None,
        help="Existing OCD JSON file path or URL to update (optional). If provided, non-project sections are preserved.",
    )

    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--merge-projects", action="store_true", help="Merge projects into existing OCD (default).")
    mode.add_argument("--replace-projects", action="store_true", help="Replace projects entirely with GitHub-derived list.")

    ap.add_argument("--include-forks", action="store_true", help="Include forked repositories.")
    ap.add_argument("--include-archived", action="store_true", help="Include archived repositories.")
    ap.add_argument("--max-repos", type=int, default=None, help="Limit number of repos processed (debug/testing).")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    gh = GitHubClient.create(token=token)

    existing_ocd: Optional[Dict[str, Any]] = None
    if args.input:
        try:
            loaded = load_json_from_path_or_url(args.input)
            if isinstance(loaded, dict):
                existing_ocd = loaded
            else:
                raise ValueError("Input JSON must be a JSON object at the top level.")
        except Exception as e:
            print(f"ERROR: Failed to load --input: {e}", file=sys.stderr)
            return 2

    replace = bool(args.replace_projects)
    # default to merge if input exists (or if user requested merge explicitly)
    if args.merge_projects:
        replace = False

    try:
        ocd = build_ocd(
            org=args.org,
            domain=args.domain,
            spec_version=args.spec_version,
            gh=gh,
            include_forks=args.include_forks,
            include_archived=args.include_archived,
            max_repos=args.max_repos,
            existing_ocd=existing_ocd,
            replace_projects=replace,
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
