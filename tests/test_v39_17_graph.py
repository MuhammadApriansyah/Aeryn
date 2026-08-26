"""Test V39.17 — Graph traversal & Obsidian Local Graph."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_graph_index_building():
    """Graph builds index from vault."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry1 = VaultEntry(layer=LAYER_WIKI, title="Note A", body="Links to [[Note B]] and [[Note C]].")
    entry2 = VaultEntry(layer=LAYER_WIKI, title="Note B", body="Links back to [[Note A]].")
    vault.write(entry1)
    vault.write(entry2)
    
    graph = VaultGraph(vault=vault)
    assert len(graph._index) >= 2


def test_graph_outgoing_links():
    """Find outgoing links from a note."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry = VaultEntry(layer=LAYER_WIKI, title="Source Note", body="See [[Target One]] and [[Target Two]].")
    vault.write(entry)
    
    graph = VaultGraph(vault=vault)
    links = graph.get_outgoing_links("Source Note")
    assert "Target One" in links
    assert "Target Two" in links


def test_graph_backlinks():
    """Find backlinks to a note."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry1 = VaultEntry(layer=LAYER_WIKI, title="Popular Note", body="Important content.")
    entry2 = VaultEntry(layer=LAYER_WIKI, title="Other Note", body="References [[Popular Note]].")
    vault.write(entry1)
    vault.write(entry2)
    
    graph = VaultGraph(vault=vault)
    backlinks = graph.get_backlinks("Popular Note")
    assert "Other Note" in backlinks


def test_graph_local():
    """Get local graph centered on a note."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry1 = VaultEntry(layer=LAYER_WIKI, title="Center", body="Links to [[Left]] and [[Right]].")
    entry2 = VaultEntry(layer=LAYER_WIKI, title="Left", body="Connected to [[Center]].")
    entry3 = VaultEntry(layer=LAYER_WIKI, title="Right", body="Also linked to [[Center]].")
    vault.write(entry1)
    vault.write(entry2)
    vault.write(entry3)
    
    graph = VaultGraph(vault=vault)
    local = graph.get_local_graph("Center", depth=1)
    assert len(local["nodes"]) >= 2


def test_graph_related():
    """Find related notes via shared tags."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry1 = VaultEntry(layer=LAYER_WIKI, title="AI Research", body="About AI.", tags=["ai", "research"])
    entry2 = VaultEntry(layer=LAYER_WIKI, title="ML Study", body="About ML.", tags=["ai", "study"])
    vault.write(entry1)
    vault.write(entry2)
    
    graph = VaultGraph(vault=vault)
    related = graph.find_related("AI Research")
    assert len(related) >= 1


def test_graph_orphans():
    """Find orphaned notes."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry1 = VaultEntry(layer=LAYER_WIKI, title="Orphan Note", body="No links here.")
    entry2 = VaultEntry(layer=LAYER_WIKI, title="Connected", body="Links to [[Orphan Note]].")
    vault.write(entry1)
    vault.write(entry2)
    
    graph = VaultGraph(vault=vault)
    orphans = graph.find_orphans()
    assert "Orphan Note" not in orphans  # it has incoming link from Connected


def test_graph_summary():
    """Render graph summary for system prompt."""
    from aeryn_core.graph import VaultGraph
    from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
    
    vault = AerynVault()
    entry = VaultEntry(layer=LAYER_WIKI, title="Summary Test", body="Content with links.")
    vault.write(entry)
    
    graph = VaultGraph(vault=vault)
    summary = graph.render_graph_summary()
    assert "KNOWLEDGE GRAPH" in summary
