"""
graph_adt.py  -  The Graph Abstract Data Type (ADT)

WHAT it is        A set of vertices V and a set of edges E, written G = (V, E),
                  plus the operations you may perform on it (add / remove,
                  neighbors, degrees, DFS, BFS, topological sort ...).
HOW it is stored  As an ADJACENCY LIST: a dictionary that maps every vertex to
                  the list of vertices it is connected to.

The GUI (main.py) only calls the public methods of this class. It never
touches self._adj directly, so the storage could be swapped for an adjacency
matrix later without breaking the GUI. That separation is the point of an ADT.
"""

from collections import deque


class Graph:
    """A simple graph: no self-loops and no parallel (duplicate) edges."""

    def __init__(self, directed=True):
        self.directed = directed
        # The adjacency list. For the edges A->B, A->C and B->C it holds:
        #     {"A": ["B", "C"], "B": ["C"], "C": []}
        self._adj = {}

    # ------------------------------------------------------------------
    # Vertices
    # ------------------------------------------------------------------
    def add_vertex(self, v):
        if v in self._adj:
            raise ValueError(f"'{v}' is already in the graph.")
        self._adj[v] = []                        # a new vertex starts with no edges

    def remove_vertex(self, v):
        self._require(v)
        del self._adj[v]                         # delete v's own list ...
        for neighbors in self._adj.values():     # ... and every edge that points to v
            if v in neighbors:
                neighbors.remove(v)

    def has_vertex(self, v):
        return v in self._adj

    def vertices(self):
        return sorted(self._adj)                 # alphabetical, so output is predictable

    def size(self):
        """Size of a graph = its number of vertices (Course Packet 10)."""
        return len(self._adj)

    # ------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------
    def add_edge(self, u, v):
        """Add the edge u -> v (and v -> u as well if the graph is undirected)."""
        self._require(u)
        self._require(v)
        if u == v:
            raise ValueError("A vertex cannot be connected to itself.")
        if v in self._adj[u]:
            raise ValueError(f"The edge {u} -> {v} already exists.")
        self._adj[u].append(v)
        self._adj[u].sort()                      # keep every list in alphabetical order
        if not self.directed:
            self._adj[v].append(u)
            self._adj[v].sort()

    def remove_edge(self, u, v):
        if not self.has_edge(u, v):
            raise ValueError(f"The edge {u} -> {v} does not exist.")
        self._adj[u].remove(v)
        if not self.directed:
            self._adj[v].remove(u)

    def has_edge(self, u, v):
        return u in self._adj and v in self._adj[u]

    def edges(self):
        """Every edge exactly once, as (u, v) pairs."""
        result = []
        for u in self.vertices():
            for v in self._adj[u]:
                if self.directed or u < v:       # undirected: list each edge only once
                    result.append((u, v))
        return result

    def edge_count(self):
        return len(self.edges())

    # ------------------------------------------------------------------
    # Neighbors and degrees
    # ------------------------------------------------------------------
    def neighbors(self, v):
        """Vertices that v points to (its successors)."""
        self._require(v)
        return list(self._adj[v])                # a copy, so callers cannot change our list

    def predecessors(self, v):
        """Vertices that point to v. An adjacency list has to scan every list to find them."""
        self._require(v)
        return sorted(u for u in self._adj if v in self._adj[u])

    def out_degree(self, v):
        return len(self.neighbors(v))

    def in_degree(self, v):
        return len(self.predecessors(v))

    def degree(self, v):
        """Course Packet 10: the degree of a vertex equals its out-degree."""
        return self.out_degree(v)

    # ------------------------------------------------------------------
    # The other representation from the packet, built on demand
    # ------------------------------------------------------------------
    def to_matrix(self):
        """Build the adjacency matrix. Returns (vertex names, 2-D list of 0/1)."""
        names = self.vertices()
        index = {name: i for i, name in enumerate(names)}
        matrix = [[0] * len(names) for _ in names]
        for u in names:
            for v in self._adj[u]:
                matrix[index[u]][index[v]] = 1
        return names, matrix

    # ------------------------------------------------------------------
    # Algorithms. dfs, bfs and topological_sort return (order, trace):
    #   order = the vertices in the order they were visited
    #   trace = one (vertex, stack-or-queue contents) row per step,
    #           the same table the packet draws by hand
    # ------------------------------------------------------------------
    def dfs(self, start):
        """Depth-first search with a STACK. Time O(V + E)."""
        self._require(start)
        visited, order, trace = set(), [], []
        stack = [start]
        while stack:
            v = stack.pop()                      # take the top of the stack
            if v in visited:
                continue                         # duplicates are allowed on the stack; skip repeats
            visited.add(v)
            order.append(v)
            for w in reversed(self._adj[v]):     # reversed, so the alphabetically first ends on top
                if w not in visited:
                    stack.append(w)
            trace.append((v, list(stack)))
        return order, trace

    def bfs(self, start):
        """Breadth-first search with a QUEUE. Time O(V + E)."""
        self._require(start)
        order, trace = [], []
        queue = deque([start])
        enqueued = {start}                       # no duplicates are allowed in the queue
        while queue:
            v = queue.popleft()                  # take the front of the queue
            order.append(v)
            for w in self._adj[v]:
                if w not in enqueued:
                    enqueued.add(w)
                    queue.append(w)
            trace.append((v, list(queue)))
        return order, trace

    def topological_sort(self):
        """Topological sorting with a QUEUE (directed graphs only). Time O(V + E).

        If the graph has a cycle, the vertices on it never reach in-degree 0, so
        the returned order is shorter than size(). has_cycle() relies on that.
        """
        if not self.directed:
            raise ValueError("Topological sorting needs a directed graph.")
        in_deg = {v: 0 for v in self._adj}       # step 1: count every vertex's in-degree
        for u in self._adj:
            for w in self._adj[u]:
                in_deg[w] += 1
        queue = deque(v for v in self.vertices() if in_deg[v] == 0)
        order, trace = [], []
        while queue:
            v = queue.popleft()                  # step 2: take a vertex with in-degree 0
            order.append(v)
            for w in self._adj[v]:               # step 3: "remove" v by lowering its neighbors' in-degree
                in_deg[w] -= 1
                if in_deg[w] == 0:               # step 4: that neighbor is now free to be taken
                    queue.append(w)
            trace.append((v, list(queue)))
        return order, trace

    def has_cycle(self):
        """True when no topological order exists (Course Packet 10: a cycle is present)."""
        order, _ = self.topological_sort()
        return len(order) < self.size()

    def has_path(self, start, goal):
        """True if you can walk from start to goal along the edges (uses DFS)."""
        order, _ = self.dfs(start)
        return goal in order

    # ------------------------------------------------------------------
    # Private helper (the leading underscore means "for use inside this class")
    # ------------------------------------------------------------------
    def _require(self, v):
        if v not in self._adj:
            raise ValueError(f"'{v}' is not in the graph.")
