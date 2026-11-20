"""Reading a Work folder (docs/work-format.md), shared by the validator and the LaTeX converters.

`paper_order` mirrors src/paperOrder.ts (ADR 0003); scripts/test_paper_order.py checks
that both give the same order.
"""
import re
from pathlib import Path

import yaml

TYPES = ["result", "method", "concept", "primer", "context", "discussion", "conclusion"]
EDGE_TYPES = ["uses", "relies_on", "supports", "explains", "discusses", "situates", "synthesises"]
TIERS = ["Gist", "Summary", "Full"]
INF = float("inf")


def read_text(path):
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")


def split_node(text):
    """(header dict, body) of a Node file."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("missing YAML header")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def split_tiers(body):
    """{'gist': ..., 'summary': ..., 'full': ...} for the tiers present, text stripped."""
    parts = re.split(r"^## (Gist|Summary|Full)[ \t]*$", body, flags=re.M)
    return {parts[i].lower(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


class Work:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.manifest = yaml.safe_load(read_text(self.folder / "manifest.yaml")) or {}
        refs = self.folder / "references.yaml"
        self.references = (yaml.safe_load(read_text(refs)) or {}) if refs.exists() else {}
        self.nodes = {}  # id -> {"meta": dict, "body": str}
        for path in sorted((self.folder / "nodes").glob("*.md")):
            meta, body = split_node(read_text(path))
            self.nodes[path.stem] = {"meta": meta, "body": body}

    def type_of(self, nid):
        return self.nodes[nid]["meta"].get("type")

    @property
    def edges(self):
        """(type, from, to) for every declared Edge whose target exists."""
        out = []
        for nid, n in self.nodes.items():
            for etype, targets in (n["meta"].get("edges") or {}).items():
                for t in targets or []:
                    if t in self.nodes:
                        out.append((etype, nid, t))
        return out

    def paper_order(self):
        return paper_order(
            {nid: self.type_of(nid) for nid in self.nodes},
            self.edges,
            self.manifest.get("results") or [],
            self.manifest.get("order"),
        )


def _sort_within(ids, before, key):
    left = set(ids)
    out = []
    while left:
        remaining = sorted(left, key=key)
        ready = [i for i in remaining if not (before.get(i, set()) & left)]
        nxt = ready[0] if ready else remaining[0]  # a cycle: break it at the smallest key
        out.append(nxt)
        left.discard(nxt)
    return out


def paper_order(types, edges, results, order=None):
    """Paper order of Nodes. `types` maps id -> Node type; `edges` are (type, from, to)."""
    if order:
        return list(order)
    ids = sorted(types)
    of_type = lambda t: [i for i in ids if types[i] == t]
    edges = [e for e in edges if e[1] in types and e[2] in types]

    before = {i: set() for i in ids}
    for etype, a, b in edges:
        if types[a] != types[b] or a == b:
            continue
        first, then = (a, b) if etype in ("supports", "situates") else (b, a)
        before[then].add(first)

    users = {i: set() for i in ids}
    for etype, a, b in edges:
        if etype in ("uses", "relies_on"):
            users[b].add(a)

    def dependents(nid):
        seen, stack = set(), list(users[nid])
        while stack:
            u = stack.pop()
            if u in seen or u == nid:
                continue
            seen.add(u)
            stack.extend(users[u])
        return seen

    positions = lambda lst: {nid: i for i, nid in enumerate(lst)}

    def min_pos(pos, items):
        return min([pos[i] for i in items if i in pos], default=INF)

    def result_index(nid):
        return results.index(nid) if nid in results else INF

    res = _sort_within(of_type("result"), before, lambda i: (result_index(i), i))
    rpos = positions(res)
    meth = _sort_within(of_type("method"), before, lambda i: (min_pos(rpos, dependents(i)), i))
    mpos = positions(meth)
    conc = _sort_within(
        of_type("concept"), before, lambda i: (min_pos(rpos, dependents(i)), min_pos(mpos, dependents(i)), i)
    )

    home = {}
    for p in of_type("primer"):
        explained = [b for etype, a, b in edges if etype == "explains" and a == p]
        home[p] = min([conc.index(c) for c in explained if c in conc], default=INF)
    primers = sorted(of_type("primer"), key=lambda p: (home[p], p))
    group = []
    for i, c in enumerate(conc):
        group.append(c)
        group.extend(p for p in primers if home[p] == i)
    group.extend(p for p in primers if home[p] == INF)

    targets = lambda nid, t: [b for etype, a, b in edges if etype == t and a == nid]
    bpos = positions(group + meth + res)
    disc = _sort_within(of_type("discussion"), before, lambda i: (min_pos(bpos, targets(i, "discusses")), i))
    concl = of_type("conclusion")
    rest = positions(group + meth + res + disc + concl)
    ctx = _sort_within(of_type("context"), before, lambda i: (min_pos(rest, targets(i, "situates")), i))
    return ctx + group + meth + res + disc + concl


PAPER_GROUPS = [["context"], ["concept", "primer"], ["method"], ["result"], ["discussion"], ["conclusion"]]


def paper_group(ntype):
    return next(i for i, g in enumerate(PAPER_GROUPS) if ntype in g)
