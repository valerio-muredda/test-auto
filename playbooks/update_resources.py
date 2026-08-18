#!/usr/bin/env python3
"""Update the CPU/memory requests for a named container in a Kubernetes
Deployment manifest (YAML), preserving comments/formatting as much as
possible via ruamel.yaml if available, falling back to PyYAML.

Usage: update_resources.py <manifest_path> <container_name> <cpu> <memory>
"""
import sys


def main():
    manifest_path, container_name, cpu, memory = sys.argv[1:5]

    try:
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        with open(manifest_path) as f:
            data = yaml.load(f)
        _patch(data, container_name, cpu, memory)
        with open(manifest_path, "w") as f:
            yaml.dump(data, f)
    except ImportError:
        import yaml as pyyaml
        with open(manifest_path) as f:
            data = pyyaml.safe_load(f)
        _patch(data, container_name, cpu, memory)
        with open(manifest_path, "w") as f:
            pyyaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"Updated {container_name} resources in {manifest_path}: cpu={cpu} memory={memory}")


def _patch(data, container_name, cpu, memory):
    containers = data["spec"]["template"]["spec"]["containers"]
    for container in containers:
        if container.get("name") == container_name:
            resources = container.setdefault("resources", {})
            requests = resources.setdefault("requests", {})
            if cpu:
                requests["cpu"] = cpu
            if memory:
                requests["memory"] = memory
            return
    raise SystemExit(f"Container {container_name} not found in manifest")


if __name__ == "__main__":
    main()
