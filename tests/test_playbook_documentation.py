"""Contracts for canonical playbook-domain documentation."""

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs" / "playbooks"
DOMAIN_ROLES = {
    "claude.md": ("claude",),
    "echo.md": ("echo",),
    "lm_studio.md": ("lm_studio",),
    "ollama.md": ("ollama",),
    "provisioning.md": ("ssh_provisioning",),
    "samba.md": ("samba",),
    "ssh.md": ("ssh",),
    "tailscale.md": ("tailscale",),
    "vscode.md": ("vscode",),
}
REQUIRED_HEADINGS = (
    "## Scope",
    "### Supported Hosts",
    "## Goal",
    "## Invocation",
    "## Architecture",
    "## Workflow",
    "## Variables",
    "## Usage",
    "## Verification",
)


def test_every_domain_page_uses_the_canonical_structure():
    """Every page has ordered required sections and both required diagrams."""
    assert {path.name for path in DOCS.glob("*.md")} == set(DOMAIN_ROLES)

    for page_name in DOMAIN_ROLES:
        content = (DOCS / page_name).read_text()
        positions = [content.index(heading) for heading in REQUIRED_HEADINGS]

        assert positions == sorted(positions), page_name
        architecture = content[
            content.index("## Architecture") : content.index("## Workflow")
        ]
        workflow = content[
            content.index("## Workflow") : content.index("## Variables")
        ]
        assert "```mermaid" in architecture, page_name
        assert "```mermaid" in workflow, page_name


def test_every_public_role_default_is_named_in_its_domain_page():
    """Documentation cannot silently omit a configurable role default."""
    for page_name, role_names in DOMAIN_ROLES.items():
        content = (DOCS / page_name).read_text()
        for role_name in role_names:
            defaults_path = REPO_ROOT / "roles" / role_name / "defaults" / "main.yml"
            defaults = yaml.safe_load(defaults_path.read_text()) or {}
            for variable in defaults:
                assert f"`{variable}`" in content, f"{page_name}: {variable}"


def test_testing_guide_routes_hil_to_the_canonical_procedure():
    """Testing guidance and the HIL index point to the live SSH procedure."""
    testing = (REPO_ROOT / "docs" / "testing.md").read_text()
    hil_index = (REPO_ROOT / "hil-test" / "readme.md").read_text()

    assert "../hil-test/readme.md" in testing
    assert "../hil-test/provisioning-ssh/readme.md" in testing
    assert "provisioning-ssh/readme.md" in hil_index


def test_documentation_links_resolve_locally():
    """Repository-relative links in the aligned documentation cannot drift."""
    pages = list(DOCS.glob("*.md")) + [
        REPO_ROOT / "docs" / "testing.md",
        REPO_ROOT / "hil-test" / "readme.md",
        REPO_ROOT / "hil-test" / "provisioning-ssh" / "readme.md",
    ]

    for page in pages:
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", page.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (page.parent / target.split("#", 1)[0]).resolve()
            assert path.exists(), f"{page.relative_to(REPO_ROOT)}: {target}"
