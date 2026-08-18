#!/usr/bin/env python3
"""Update the CPU/memory requests (and, if needed, limits) for a named
container in a Kubernetes Deployment manifest (YAML).

Kubernetes requires requests <= limits, so if the VPA-recommended request
would exceed the current static limit, the limit is raised to keep the
manifest valid (Kubernetes rejects the patch otherwise).

Usage: update_resources.py <manifest_path> <container_name> <cpu> <memory>
"""
import re
import sys


def _to_millicpu(value):
    if value is None or value == "":
        return None
    value = str(value)
    if value.endswith("m"):
        return int(value[:-1])
    return int(float(value) * 1000)


_MEM_UNITS = {"Ki": 2**10, "Mi": 2**20, "Gi": 2**30, "Ti": 2**40, "K": 1e3, "M": 1e6, "G": 1e9}


def _to_bytes(value):
    if value is None or value == "":
        return None
    value = str(value)
    m = re.match(r"^([0-9.]+)([A-Za-z]*)$", value)
    if not m:
        return None
    num, unit = m.groups()
    if unit in _MEM_UNITS:
        return float(num) * _MEM_UNITS[unit]
    return float(num)


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
            limits = resources.setdefault("limits", {})

            if cpu:
                requests["cpu"] = cpu
                req_m = _to_millicpu(cpu)
                lim_m = _to_millicpu(limits.get("cpu"))
                if req_m is not None and (lim_m is None or req_m > lim_m):
                    limits["cpu"] = f"{req_m * 2}m"

            if memory:
                requests["memory"] = memory
                req_b = _to_bytes(memory)
                lim_b = _to_bytes(limits.get("memory"))
                if req_b is not None and (lim_b is None or req_b > lim_b):
                    limits["memory"] = memory  # request == recommended target; double it
                    limits["memory"] = f"{int(req_b * 2 / (2**20))}Mi"
            return
    raise SystemExit(f"Container {container_name} not found in manifest")


if __name__ == "__main__":
    main()
