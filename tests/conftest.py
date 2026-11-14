import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    """Build the whole site once into a temp folder (runs every cell and check)."""
    import build_site

    out = tmp_path_factory.mktemp("site")
    site, reports = build_site.build(out)
    return {"out": out, "site": site, "reports": {r.slug: r for r in reports}}
