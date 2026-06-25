from __future__ import annotations

import sys

from prompt_piper.demo.runner import run_implementation_report_demo
from prompt_piper.demo.scenario import repo_root


def main() -> int:
    root = repo_root()
    registry_path = root / "data" / "demo" / "registry"
    artifacts_path = root / "data" / "demo" / "artifacts"
    audit_path = root / "data" / "demo" / "audit"

    for path in (registry_path, artifacts_path, audit_path):
        path.mkdir(parents=True, exist_ok=True)

    try:
        result = run_implementation_report_demo(
            registry_path=registry_path,
            artifacts_path=artifacts_path,
            audit_path=audit_path,
        )
    except Exception as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1

    result.print_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
