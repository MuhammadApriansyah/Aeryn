"""V39.17 — Graph: knowledge graph traversal (Obsidian Local Graph style).

Implements:
- Bidirectional links between vault entries
- Graph traversal: find notes connected to a starting note
- Local graph: focused view from one note to related notes
- Backlinks: which notes link to this note?
- Related notes: semantic similarity via shared tags/links
"""
import os
import re
import json
from collections import defaultdict
from aeryn_core.memory.vault import AerynVault, VaultEntry, BASE, SUBDIRS


class VaultGraph:
    """Knowledge graph traversal over Obsidian-style vault."""
    
    def __init__(self, vault: AerynVault = None):
        self.vault = vault if vault is not None else AerynVault()
        self._index = {}  # title -> entry metadata
        self._links = defaultdict(set)  # title -> set of linked titles
        self._backlinks = defaultdict(set)  # title -> set of titles linking to it
        self._build_index()
    
    def _build_index(self):
        """Scan vault and build link index."""
        self._index = {}
        self._links = defaultdict(set)
        self._backlinks = defaultdict(set)
        
        for sub in SUBDIRS:
            dirpath = os.path.join(BASE, sub)
            if not os.path.isdir(dirpath):
                continue
            for fname in os.listdir(dirpath):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                
                # Extract title from frontmatter
                title = self._extract_title(content) or fname.replace(".md", "")
                
                # Extract links: [[target]] or from frontmatter links
                links = self._extract_links(content)
                
                self._index[title] = {
                    "path": fpath,
                    "layer": sub,
                    "tags": self._extract_tags(content),
                    "links": links,
                }
                
                for link in links:
                    self._links[title].add(link)
                    self._backlinks[link].add(title)
    
    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract title from frontmatter."""
        m = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
        if m:
            return m.group(1).strip()
        # Fallback: first heading
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if m:
            return m.group(1).strip()
        return ""
    
    @staticmethod
    def _extract_tags(content: str) -> list:
        """Extract tags from frontmatter."""
        m = re.search(r"^tags:\s*\[(.*?)\]", content, re.MULTILINE | re.DOTALL)
        if m:
            raw = m.group(1)
            return [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]
        return []
    
    @staticmethod
    def _extract_links(content: str) -> list:
        """Extract [[wikilinks]] and frontmatter links."""
        # Wikilinks: [[target]] or [[target|display]]
        links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        return [l.strip() for l in links]
    
    def get_backlinks(self, title: str) -> list:
        """Get notes that link TO this note."""
        title_lower = title.lower()
        results = []
        for source, targets in self._links.items():
            for target in targets:
                if target.lower() == title_lower:
                    results.append(source)
        return results
    
    def get_outgoing_links(self, title: str) -> list:
        """Get notes that this note links TO."""
        title_lower = title.lower()
        for t, links in self._links.items():
            if t.lower() == title_lower:
                return list(links)
        return []
    
    def get_local_graph(self, title: str, depth: int = 1) -> dict:
        """
        Get local graph centered on a note.
        Returns nodes and edges up to N depth.
        """
        visited = set()
        frontier = {title.lower()}
        nodes = {}
        edges = []
        
        for level in range(depth + 1):
            next_frontier = set()
            for node_title in frontier:
                if node_title in visited:
                    continue
                visited.add(node_title)
                
                # Find this note in index
                matching = None
                for t, meta in self._index.items():
                    if t.lower() == node_title:
                        matching = t
                        break
                
                if matching:
                    nodes[matching] = self._index[matching]
                
                # Get links at this level
                if level < depth:
                    outgoing = self.get_outgoing_links(node_title)
                    incoming = self.get_backlinks(node_title)
                    for target in outgoing + incoming:
                        edges.append((matching or node_title, target))
                        next_frontier.add(target.lower())
            
            frontier = next_frontier - visited
        
        return {"nodes": nodes, "edges": edges}
    
    def find_related(self, title: str, max_results: int = 10) -> list:
        """Find notes related via shared tags, direct links, or path proximity."""
        title_lower = title.lower()
        
        # Find this note
        source_tags = set()
        source_links = set()
        source_layer = ""
        for t, meta in self._index.items():
            if t.lower() == title_lower:
                source_tags = set(meta.get("tags", []))
                source_links = set(l.lower() for l in meta.get("links", []))
                source_layer = meta.get("layer", "")
                break
        
        scores = []
        for t, meta in self._index.items():
            if t.lower() == title_lower:
                continue
            score = 0
            # Shared tags
            target_tags = set(meta.get("tags", []))
            shared_tags = source_tags & target_tags
            score += len(shared_tags) * 2
            
            # Direct link (either direction)
            target_links = set(l.lower() for l in meta.get("links", []))
            if title_lower in target_links:
                score += 5  # backlink
            if any(l.lower() == title_lower for l in target_links):
                score += 3  # outgoing link
            
            # Shared links (co-citation)
            shared_links = source_links & target_links
            score += len(shared_links)
            
            # Same layer bonus
            if source_layer and meta.get("layer") == source_layer:
                score += 1
            
            if score > 0:
                scores.append((t, score, meta))
        
        scores.sort(key=lambda x: -x[1])
        return [{"title": t, "score": s, "layer": m.get("layer")} for t, s, m in scores[:max_results]]
    
    def find_orphans(self) -> list:
        """Find notes without any links."""
        orphans = []
        for t, meta in self._index.items():
            if not meta.get("links") and not self.get_backlinks(t):
                orphans.append(t)
        return orphans
    
    def render_graph_summary(self, title: str = None, depth: int = 1) -> str:
        """Render graph summary for system prompt injection."""
        self._build_index()
        
        parts = ["## KNOWLEDGE GRAPH"]
        
        if title:
            local = self.get_local_graph(title, depth=depth)
            parts.append(f"\n### Local Graph: {title}")
            parts.append(f"Connected nodes: {len(local['nodes'])}")
            for node in local["nodes"]:
                parts.append(f"- {node}")
            parts.append(f"\nEdges: {len(local['edges'])}")
            for src, tgt in local["edges"][:10]:
                parts.append(f"- {src} → {tgt}")
        
        # Overall stats
        total = len(self._index)
        total_links = sum(len(l) for l in self._links.values())
        orphans = self.find_orphans()
        
        parts.append(f"\n### Graph Stats")
        parts.append(f"Total notes: {total}")
        parts.append(f"Total links: {total_links}")
        parts.append(f"Orphans: {len(orphans)}")
        
        return "\n".join(parts)
