"""Generate the tox-ansible GitHub Actions matrix."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


def read_tox_envlist(output_path: Path) -> list[dict[str, object]]:
    contents = output_path.read_text(encoding="utf-8")
    values = []
    for line in contents.splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key.strip() == "envlist":
            values.append(value.strip())

    if len(values) != 1:
        raise SystemExit("tox-ansible must write exactly one envlist output")

    envlist = json.loads(values[0])
    if not isinstance(envlist, list):
        raise SystemExit("tox-ansible envlist output must be a JSON list")
    return envlist


def main() -> None:
    output_path = Path(os.environ["GITHUB_OUTPUT"])
    config_path = Path(os.environ["MATRIX_CONFIG"])

    with tempfile.TemporaryDirectory(prefix="tox-ansible-matrix-") as temp_dir:
        tox_output_path = Path(temp_dir) / "tox-output"
        env = os.environ.copy()
        env["GITHUB_OUTPUT"] = str(tox_output_path)
        result = subprocess.run(
            ["uv", "run", "--no-project", "tox", "--ansible", "--gh-matrix"],
            check=False,
            env=env,
        )
        if result.returncode:
            raise SystemExit(result.returncode)
        generated = read_tox_envlist(tox_output_path)

    envlist = []
    for entry in generated:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise SystemExit("tox-ansible returned a malformed environment entry")
        if entry["name"].startswith(("unit-", "sanity-")):
            if not isinstance(entry.get("python"), str) or not entry["python"]:
                raise SystemExit(f"tox-ansible returned no Python version for {entry['name']}")
            envlist.append(entry)

    if not envlist:
        raise SystemExit("tox-ansible did not generate unit or sanity environments")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    companions = config.get("companion_envs")
    if not isinstance(companions, list):
        raise SystemExit("matrix config must contain a companion_envs list")

    existing = {entry["name"] for entry in envlist}
    for companion in companions:
        if not isinstance(companion, dict):
            raise SystemExit("each companion environment must be a JSON object")
        name = companion.get("name")
        python_version = companion.get("python")
        if not isinstance(name, str) or not isinstance(python_version, str):
            raise SystemExit("each companion environment needs string name and python values")
        if name not in existing:
            envlist.append(
                {
                    "description": f"Run {name}",
                    "factors": name.split("-"),
                    "name": name,
                    "python": python_version,
                }
            )
            existing.add(name)

    with output_path.open("a", encoding="utf-8") as github_output:
        github_output.write(f"envlist={json.dumps(envlist, separators=(',', ':'))}\n")


if __name__ == "__main__":
    main()
