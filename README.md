# Course Prerequisite Planner

A desktop application that models a study program as a **directed graph**. Courses are vertices and "take this first" rules are directed edges. The app helps you explore what a course leads to, generate a valid study order, and blocks any rule that would create a circle.

Built as a case study for **Data Structure and Algorithm Analysis**, applying the **Graph Abstract Data Type** with an **adjacency list** representation.

<!-- Add a screenshot of the app: save it as docs/screenshot.png, then uncomment the next line -->
<!-- ![Course Prerequisite Planner](docs/screenshot.png) -->

## Features

- Add and remove courses (vertices) and prerequisites (edges)
- Click a course to see its in-degree (prerequisites) and out-degree (courses it unlocks)
- Depth-first search (DFS) using a stack
- Breadth-first search (BFS) using a queue
- Study order using topological sort
- Circle check: a prerequisite that would form a cycle is rejected with an explanation
- Step-by-step stack and queue tables for each algorithm, in the same format as the course packet
- Adjacency list and adjacency matrix view, with a storage comparison
- Graph drawing with numbered highlights that show the visit order
- Scrollable canvas for large graphs

## Built with

- Python 3 (developed and tested with Python 3.12)
- Tkinter, which is included with Python
- No external libraries

## Project structure

```
.
├── graph_adt.py   # The Graph ADT: adjacency list, operations, DFS, BFS, topological sort
├── main.py        # The Tkinter GUI: input, drawing, and output
├── .gitignore
└── README.md
```

The GUI only calls the public methods of the `Graph` class and never reads its internal storage. The ADT and the interface are independent of each other.

## Getting started

### Requirements

- Python 3 with Tkinter
  - Windows and macOS: Tkinter is included with the installers from [python.org](https://www.python.org/downloads/).
  - Linux (Debian or Ubuntu): `sudo apt install python3-tk`

### Run the app

1. Download or clone this repository.
2. Open a terminal in the project folder.
3. Run:

```
python main.py
```

On Windows you can also use `py main.py`. Both files must stay in the same folder.

The app opens with a sample curriculum of 14 courses and 16 prerequisites.

## How to use

| Action | How |
| --- | --- |
| Add a course | Type a name under **New course** and click **Add course** (or press Enter) |
| Select a course | Click its box on the graph, or choose it in **Selected** |
| Remove a course | Select it, then click **Remove course** |
| Add a prerequisite | Choose **Take first** and **Then take**, then click **Add prerequisite** |
| Remove a prerequisite | Choose the same two courses, then click **Remove prerequisite** |
| Search from a course | Select a course, then click **Depth-first search (DFS)** or **Breadth-first search (BFS)** |
| Get a study order | Click **Study order (topological sort)** |
| See how the graph is stored | Click **Adjacency list and matrix** |
| Reset | **Load sample** restores the sample curriculum. **Clear all** empties the graph |

Rules enforced by the app: a course cannot be its own prerequisite, the same prerequisite cannot be added twice, and a prerequisite that would create a circle is rejected.

## How it works

### The ADT and the data structure

The **Graph ADT** defines what you can do with a graph: add and remove vertices and edges, ask for neighbors and degrees, traverse, and sort. It is implemented with an **adjacency list**, a dictionary that maps each vertex to the list of vertices it points to:

```python
{"Programming 1": ["Computer Org", "Programming 2"], "Programming 2": ["Data Structures", "Web Development"], ...}
```

Prerequisite graphs are sparse. The sample has 14 courses and 16 prerequisites, so an adjacency matrix would need 196 cells for 16 edges.

| | Adjacency list (used) | Adjacency matrix |
| --- | --- | --- |
| Memory | O(V + E) | O(V²) |
| Neighbors of a vertex | Read one list | Scan a row of V cells |
| Is there an edge u → v? | Search u's list | One cell, O(1) |
| DFS, BFS, topological sort | O(V + E) | O(V²) |

### Algorithms

| Algorithm | Structure used | Purpose in the app | Time |
| --- | --- | --- | --- |
| Depth-first search | Stack | Find what a course leads to, following one path deeply | O(V + E) |
| Breadth-first search | Queue | Find what a course leads to, one step at a time | O(V + E) |
| Topological sort | Queue and in-degree counts | Produce a valid study order | O(V + E) |
| Path check (DFS) | Stack | Reject a prerequisite that would form a circle | O(V + E) |

Neighbors are processed in alphabetical order so every run produces the same, predictable output. DFS pushes neighbors in reverse alphabetical order and BFS enqueues them in alphabetical order, as described in the course packet.

## Customize the data

The sample courses and prerequisites are two lists at the top of `main.py`:

```python
SAMPLE_COURSES = [...]
SAMPLE_PREREQUISITES = [...]    # (take first, then take)
```

Replace them with your own program's subjects and click **Load sample**.

## Group members

| Name | Role |
| --- | --- |
| [Member name] | [Role] |
| [Member name] | [Role] |
| [Member name] | [Role] |

## Acknowledgments

Based on the Graph Abstract Data Type course packet (Course Packet 10) for Data Structure and Algorithm Analysis.
