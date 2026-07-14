#!/usr/bin/env python3
"""query-graph.py — 从 graph/index.json 查询相关知识摘要。

用法:
    python scripts/query-graph.py --module backend
    python scripts/query-graph.py --feature FEAT-AUTH --format detailed
    python scripts/query-graph.py --pitfall PIT-007
    python scripts/query-graph.py --format json

输出:
    short: 一行摘要（适合注入 context）
    detailed: 完整依赖树（适合人工阅读）
    json: JSON 格式（适合程序处理）
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_graph(graph_path="docs/graph/index.json"):
    """加载知识图谱数据。"""
    if not os.path.exists(graph_path):
        print(f"错误: 图谱文件不存在: {graph_path}", file=sys.stderr)
        print("提示: 先运行 python scripts/build-graph.py 构建图谱", file=sys.stderr)
        sys.exit(1)
    
    with open(graph_path) as f:
        return json.load(f)


def query_by_module(graph, module_tag):
    """按模块标签查询相关知识。"""
    results = []
    for node in graph.get("nodes", []):
        modules = node.get("metadata", {}).get("modules", [])
        if module_tag in modules:
            results.append(node)
    return results


def query_by_feature(graph, feature_id):
    """按 Feature ID 查询依赖。"""
    for node in graph.get("nodes", []):
        if node.get("id") == feature_id:
            return node
    return None


def query_by_pitfall(graph, pitfall_id):
    """按 Pitfall ID 查询影响范围。"""
    affected = []
    for edge in graph.get("edges", []):
        if edge.get("source") == pitfall_id or edge.get("target") == pitfall_id:
            affected.append(edge)
    return affected


def format_short(results):
    """输出 short 格式（一行摘要）。"""
    lines = []
    for node in results:
        nid = node.get("id", "?")
        ntype = node.get("type", "?")
        metadata = node.get("metadata", {})
        depends = metadata.get("depends", [])
        
        dep_str = ", ".join(depends) if depends else "(无依赖)"
        lines.append(f"{nid} ({ntype}) → depends: [{dep_str}]")
    
    return "\n".join(lines) if lines else "(无结果)"


def format_detailed(results, graph):
    """输出 detailed 格式（完整依赖树）。"""
    lines = []
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    
    for node in results:
        nid = node.get("id", "?")
        ntype = node.get("type", "?")
        metadata = node.get("metadata", {})
        depends = metadata.get("depends", [])
        
        lines.append(nid)
        lines.append(f"├── type: {ntype}")
        
        # 依赖
        lines.append("├── depends:")
        for dep_id in depends:
            dep_node = node_map.get(dep_id, {})
            dep_summary = dep_node.get("metadata", {}).get("summary", "(未知)")
            lines.append(f"│   ├── {dep_id} ({dep_summary})")
        
        # 相关 Feature
        related = [e["target"] for e in graph.get("edges", []) 
                   if e["source"] == nid and e["type"] == "related"]
        if related:
            lines.append("├── related:")
            for rel_id in related:
                rel_node = node_map.get(rel_id, {})
                rel_summary = rel_node.get("metadata", {}).get("summary", "(未知)")
                lines.append(f"│   └── {rel_id} ({rel_summary})")
        
        # 受 Pitfall 影响
        affected = [e["source"] for e in graph.get("edges", [])
                    if e["target"] == nid and e["type"] == "affected-by"]
        if affected:
            lines.append("└── affected-by:")
            for aff_id in affected:
                aff_node = node_map.get(aff_id, {})
                aff_summary = aff_node.get("metadata", {}).get("summary", "(未知)")
                lines.append(f"    └── {aff_id} ({aff_summary})")
        
        lines.append("")  # 空行分隔
    
    return "\n".join(lines)


def format_json(results, graph):
    """输出 JSON 格式。"""
    return json.dumps(results, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="查询知识图谱")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--module", help="按模块标签查询")
    group.add_argument("--feature", help="按 Feature ID 查询")
    group.add_argument("--pitfall", help="按 Pitfall ID 查询")
    parser.add_argument("--format", choices=["short", "detailed", "json"],
                        default="short", help="输出格式（默认: short）")
    parser.add_argument("--graph", default="docs/graph/index.json",
                        help="图谱文件路径（默认: docs/graph/index.json）")
    
    args = parser.parse_args()
    
    # 加载图谱
    graph = load_graph(args.graph)
    
    # 执行查询
    if args.module:
        results = query_by_module(graph, args.module)
    elif args.feature:
        node = query_by_feature(graph, args.feature)
        results = [node] if node else []
    elif args.pitfall:
        edges = query_by_pitfall(graph, args.pitfall)
        results = edges
    
    # 输出结果
    if args.format == "short":
        print(format_short(results))
    elif args.format == "detailed":
        print(format_detailed(results, graph))
    elif args.format == "json":
        print(format_json(results, graph))


if __name__ == "__main__":
    main()
