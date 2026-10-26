"""Bounded offline symbol/neighbor lookup; outputs original source locations."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('graph', type=Path)
parser.add_argument('query')
parser.add_argument('--limit', type=int, default=10)
args = parser.parse_args()
limit = max(1, min(args.limit, 50))
graph = json.loads(args.graph.read_text('utf-8'))
nodes = {n['id']: n for n in graph['nodes']}
matches = [n for n in nodes.values() if args.query.casefold() in n['label'].casefold()]
results = []
for node in matches[:limit]:
    edges = [e for e in graph['edges'] if node['id'] in (e['source'], e['target'])]
    results.append({'node': node, 'edge_count': len(edges), 'edges': [
        {**e, 'source_label': nodes[e['source']]['label'], 'target_label': nodes[e['target']]['label']}
        for e in edges[:limit]]})
print(json.dumps({'match_count': len(matches), 'results': results,
                  'limitations': graph.get('metadata', {}).get('limitations')}, ensure_ascii=False, indent=2))
