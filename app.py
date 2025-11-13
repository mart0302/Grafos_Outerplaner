from flask import Flask, request, jsonify
from flask_cors import CORS
import networkx as nx
import itertools

app = Flask(__name__)
CORS(app)

def is_outerplanar_graph(G):
    """Valida outerplanaridad real: planar, sin K₄ ni K₂,₃ embebidos."""
    is_planar, _ = nx.check_planarity(G)
    if not is_planar:
        return False

    # Verificar todos los subconjuntos de 4 nodos para K4
    for nodes in itertools.combinations(G.nodes(), 4):
        subgraph = G.subgraph(nodes)
        if nx.is_isomorphic(subgraph, nx.complete_graph(4)):
            return False

    # Verificar todos los subconjuntos de 5 nodos para K2,3
    for nodes in itertools.combinations(G.nodes(), 5):
        subgraph = G.subgraph(nodes)
        if nx.is_isomorphic(subgraph, nx.complete_bipartite_graph(2, 3)):
            return False

    return True


def compute_mis_outerplanar(G):
    def compute_mis_tree(G):
        if len(G.nodes()) == 0:
            return []
        root = next(iter(G.nodes()))
        parent = {root: None}
        visited = set()
        stack = [root]
        while stack:
            u = stack.pop()
            if u not in visited:
                visited.add(u)
                for v in G.neighbors(u):
                    if v not in visited and v != parent[u]:
                        parent[v] = u
                        stack.append(v)
        post_order = list(nx.dfs_postorder_nodes(G, root))
        dp_include = {}
        dp_exclude = {}
        for u in post_order:
            children = [v for v in G.neighbors(u) if v != parent[u]]
            dp_include[u] = 1 + sum(dp_exclude.get(v, 0) for v in children)
            dp_exclude[u] = sum(max(dp_include.get(v, 0), dp_exclude.get(v, 0)) for v in children)
        mis = []
        stack = [(root, dp_include[root] > dp_exclude[root])]
        while stack:
            u, take = stack.pop()
            if take:
                mis.append(u)
                for v in G.neighbors(u):
                    if v != parent.get(u, None):
                        stack.append((v, False))
            else:
                for v in G.neighbors(u):
                    if v != parent.get(u, None):
                        stack.append((v, dp_include[v] > dp_exclude[v]))
        return mis

    if len(G.nodes()) == 0:
        return []
    if nx.is_tree(G):
        return compute_mis_tree(G)
    cycle_basis = nx.cycle_basis(G)
    if not cycle_basis:
        return compute_mis_tree(G)
    cycle = cycle_basis[0]
    v = cycle[0]
    G1 = G.copy()
    G1.remove_node(v)
    mis1 = compute_mis_outerplanar(G1)
    G2 = G.copy()
    G2.remove_nodes_from([v] + list(G.neighbors(v)))
    mis2 = [v] + compute_mis_outerplanar(G2)
    return max(mis1, mis2, key=len)


@app.route('/compute_mis', methods=['POST'])
def compute_mis():
    data = request.get_json()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    try:
        if not is_outerplanar_graph(G):
            return jsonify({'error': 'El grafo no es outerplanar'}), 400
    except Exception as e:
        print("Error validando outerplanaridad:", str(e))
        return jsonify({'error': 'Error interno al validar outerplanaridad'}), 500

    mis = compute_mis_outerplanar(G)
    return jsonify({'mis': mis})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
