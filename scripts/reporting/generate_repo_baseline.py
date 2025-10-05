import ast
import fnmatch
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
AGENT_ROOT = SRC / "agent"
PLUGINS_ROOT = SRC / "plugins"
CODEOWNERS_PATH = ROOT / ".github" / "CODEOWNERS"
REPORT_DIR = ROOT / "docs" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_counts(path: Path) -> tuple[int, int]:
    total = 0
    sloc = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            total += 1
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                sloc += 1
    return total, sloc


def collect_module_metrics(root: Path) -> list[dict]:
    metrics: list[dict] = []
    for file_path in sorted(root.rglob("*.py")):
        total, sloc = read_counts(file_path)
        metrics.append(
            {
                "path": file_path.relative_to(ROOT).as_posix(),
                "total_lines": total,
                "sloc": sloc,
            }
        )
    return metrics


def load_codeowners() -> list[tuple[str, list[str]]]:
    if not CODEOWNERS_PATH.exists():
        return []
    rules: list[tuple[str, list[str]]] = []
    with CODEOWNERS_PATH.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            pattern = parts[0]
            owners = parts[1:]
            rules.append((pattern, owners))
    return rules


def match_codeowner(relative_path: str, rules: list[tuple[str, list[str]]]) -> list[str]:
    owners: list[str] = []
    for pattern, pattern_owners in rules:
        if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch("/" + relative_path, pattern):
            owners = pattern_owners
    return owners


def collect_plugin_inventory(rules: list[tuple[str, list[str]]]) -> list[dict]:
    plugins: list[dict] = []
    for file_path in sorted(PLUGINS_ROOT.glob("*.py")):
        rel_path = file_path.relative_to(ROOT).as_posix()
        owner_list = match_codeowner("/" + rel_path, rules)
        owner = owner_list[0] if owner_list else "unassigned"
        try:
            module = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            docstring = ast.get_docstring(module)
        except SyntaxError:
            docstring = None
        summary = ""
        if docstring:
            first_line = docstring.strip().splitlines()[0]
            summary = first_line
        plugins.append(
            {
                "name": file_path.stem,
                "path": rel_path,
                "owner": owner,
                "summary": summary,
            }
        )
    return plugins


def build_module_map() -> dict[str, Path]:
    module_map: dict[str, Path] = {}
    for file_path in SRC.rglob("*.py"):
        rel = file_path.relative_to(SRC)
        module_name = ".".join(rel.with_suffix("").parts)
        module_map[module_name] = file_path
    return module_map


def resolve_absolute_module(current: str, node: ast.ImportFrom) -> str | None:
    module = node.module or ""
    if node.level == 0:
        return module or None
    current_parts = current.split(".")
    if node.level > len(current_parts):
        base_parts: list[str] = []
    else:
        base_parts = current_parts[:-node.level]
    if module:
        base_parts.append(module)
    if not base_parts:
        return None
    return ".".join(part for part in base_parts if part)


def build_dependency_graph(module_map: dict[str, Path]) -> dict[str, list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for module_name, file_path in module_map.items():
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    parts = target.split(".")
                    while parts:
                        candidate = ".".join(parts)
                        if candidate in module_map and candidate != module_name:
                            graph[module_name].add(candidate)
                            break
                        parts.pop()
            elif isinstance(node, ast.ImportFrom):
                target_module = resolve_absolute_module(module_name, node)
                if not target_module:
                    continue
                parts = target_module.split(".")
                while parts:
                    candidate = ".".join(parts)
                    if candidate in module_map and candidate != module_name:
                        graph[module_name].add(candidate)
                        break
                    parts.pop()
    return {module: sorted(targets) for module, targets in graph.items()}


def write_markdown_summary(
    agent_metrics: list[dict],
    plugin_metrics: list[dict],
    plugin_inventory: list[dict],
    module_count: int,
    edge_count: int,
) -> None:
    largest_agent = sorted(agent_metrics, key=lambda item: item["sloc"], reverse=True)[:10]
    largest_plugins = sorted(plugin_metrics, key=lambda item: item["sloc"], reverse=True)
    largest_plugins = largest_plugins[: len(largest_plugins)]
    over_200 = [item for item in agent_metrics if item["total_lines"] > 200]

    lines: list[str] = []
    lines.append("# Repository Baseline Snapshot")
    lines.append("")
    lines.append(f"- Module count (src): {module_count}")
    lines.append(f"- Dependency edges: {edge_count}")
    lines.append(f"- Agent modules >200 lines: {len(over_200)}")
    lines.append("")
    lines.append("## Largest Agent Modules by SLOC")
    lines.append("")
    lines.append("| Path | Total Lines | SLOC |")
    lines.append("| --- | --- | --- |")
    for item in largest_agent:
        lines.append(f"| {item['path']} | {item['total_lines']} | {item['sloc']} |")
    lines.append("")
    lines.append("## Plugins")
    lines.append("")
    lines.append("| Name | Path | Owner | Summary | SLOC |")
    lines.append("| --- | --- | --- | --- | --- |")
    plugin_metric_map = {metric["path"]: metric for metric in plugin_metrics}
    for plugin in plugin_inventory:
        metric = plugin_metric_map.get(plugin["path"], {"sloc": "-", "total_lines": "-"})
        summary = plugin["summary"].replace("|", "\\|")
        lines.append(
            f"| {plugin['name']} | {plugin['path']} | {plugin['owner']} | {summary} | {metric['sloc']} |"
        )
    lines.append("")
    lines.append("## Agent Modules Over 200 Lines")
    lines.append("")
    lines.append("| Path | Total Lines | SLOC |")
    lines.append("| --- | --- | --- |")
    for item in sorted(over_200, key=lambda entry: entry["total_lines"], reverse=True):
        lines.append(f"| {item['path']} | {item['total_lines']} | {item['sloc']} |")
    lines.append("")

    (REPORT_DIR / "repo_baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rules = load_codeowners()
    module_map = build_module_map()
    dependency_graph = build_dependency_graph(module_map)
    agent_metrics = collect_module_metrics(AGENT_ROOT)
    plugin_metrics = collect_module_metrics(PLUGINS_ROOT)
    plugin_inventory = collect_plugin_inventory(rules)

    baseline_payload = {
        "agent_metrics": agent_metrics,
        "plugin_metrics": plugin_metrics,
        "dependency_graph": dependency_graph,
        "module_count": len(module_map),
        "edge_count": sum(len(targets) for targets in dependency_graph.values()),
    }

    (REPORT_DIR / "repo_baseline.json").write_text(
        json.dumps(baseline_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (REPORT_DIR / "plugin_inventory.json").write_text(
        json.dumps(plugin_inventory, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown_summary(
        agent_metrics,
        plugin_metrics,
        plugin_inventory,
        baseline_payload["module_count"],
        baseline_payload["edge_count"],
    )


if __name__ == "__main__":
    main()