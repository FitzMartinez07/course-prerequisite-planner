"""
main.py  -  Course Prerequisite Planner (the GUI)

SCENARIO   A study program says which courses must be passed before others
           (for example Programming 1 before Programming 2). The planner answers:
             - "What does this course lead to?"          -> DFS and BFS
             - "In what order can I take every course?"  -> topological sort
             - "Would this new rule be a circle?"        -> path check (DFS)

ADT        Graph (directed)       vertex = a course
STORAGE    Adjacency list         edge u -> v = "u must be passed before v"

Run it with:   python main.py      (needs only Python 3; tkinter is included)
"""

import textwrap
import tkinter as tk
from tkinter import messagebox, ttk
from graph_adt import Graph

# ----------------------------------------------------------------------
# Sample data. Replace these two lists with your own program's courses.
# ----------------------------------------------------------------------
SAMPLE_COURSES = [
    "Programming 1", "Programming 2", "Data Structures", "Algorithms",
    "Discrete Math", "Computer Org", "Operating Systems", "Networks",
    "Databases", "Web Development", "Software Engineering",
    "Calculus 1", "Statistics", "Machine Learning",
]
# (take first, then take)  means  first -> then
SAMPLE_PREREQUISITES = [
    ("Programming 1", "Programming 2"),
    ("Programming 1", "Computer Org"),
    ("Programming 2", "Data Structures"),
    ("Discrete Math", "Data Structures"),
    ("Discrete Math", "Algorithms"),
    ("Data Structures", "Algorithms"),
    ("Data Structures", "Operating Systems"),
    ("Computer Org", "Operating Systems"),
    ("Data Structures", "Databases"),
    ("Programming 2", "Web Development"),
    ("Databases", "Software Engineering"),
    ("Web Development", "Software Engineering"),
    ("Operating Systems", "Networks"),
    ("Calculus 1", "Statistics"),
    ("Statistics", "Machine Learning"),
    ("Algorithms", "Machine Learning"),
]

# ----------------------------------------------------------------------
# Look and feel: graph paper, ink, and highlighter pens
# ----------------------------------------------------------------------
DESK = "#EDF0F5"       # window background
PAPER = "#FBFCFE"      # canvas background
GRID = "#E4EBF3"       # graph-paper lines
INK = "#1B2A41"        # text
PENCIL = "#7A8AA3"     # arrows and course borders
SELECT = "#1F5FBF"     # border of the selected course
DFS_COLORS = ("#FFF1A6", "#C79A00")    # yellow highlighter  (fill, border)
BFS_COLORS = ("#BFE0FF", "#2A7DB8")    # blue highlighter
TOPO_COLORS = ("#C7F0C4", "#2F8F3A")   # green highlighter

BOX_W, BOX_H = 104, 40   # size of a course box on the canvas
COLUMN_GAP = 30          # smallest horizontal gap between two columns of boxes
PAD = 20                 # margin around the drawing


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.graph = Graph(directed=True)      # <-- the Graph ADT lives here

        self.positions = {}                    # course -> (x, y) centre on the canvas
        self.marks = {}                        # course -> step number shown in a badge
        self.mark_colors = DFS_COLORS          # colors used for the marked courses
        self.anim_job = None                   # the pending animation step (so we can cancel it)

        # Tk variables: a widget and our code share a value through these.
        self.new_var = tk.StringVar()          # text typed into "New course"
        self.selected_var = tk.StringVar()     # the selected course
        self.from_var = tk.StringVar()         # "Take first"  (the edge starts here)
        self.to_var = tk.StringVar()           # "Then take"   (the edge ends here)
        self.status_var = tk.StringVar()       # text in the status bar

        self.build_window()
        self.load_sample()

    # ==================================================================
    #  Building the window
    # ==================================================================
    def build_window(self):
        self.root.title("Course prerequisite planner - Graph ADT demo")
        self.root.geometry("1120x650")
        self.root.minsize(920, 600)
        self.root.configure(bg=DESK)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=DESK)
        style.configure("TLabel", background=DESK, foreground=INK)
        style.configure("TLabelframe", background=DESK)
        style.configure("TLabelframe.Label", background=DESK, foreground=INK,
                        font=("Helvetica", 10, "bold"))
        style.configure("TButton", padding=5)
        style.configure("Primary.TButton", background=INK, foreground="white")
        style.map("Primary.TButton", background=[("active", SELECT)])

        # The status bar is packed first so it keeps its place at the bottom.
        ttk.Label(self.root, textvariable=self.status_var, anchor="w",
                  padding=(12, 5)).pack(side="bottom", fill="x")

        side = ttk.Frame(self.root, padding=12)            # left column: controls
        side.pack(side="left", fill="y")
        main = ttk.Frame(self.root, padding=(0, 12, 12, 0))  # right column: drawing + output
        main.pack(side="left", fill="both", expand=True)

        self.build_course_panel(side)
        self.build_prerequisite_panel(side)
        self.build_algorithm_panel(side)
        self.build_sample_buttons(side)
        self.build_canvas(main)
        self.build_output(main)

    def build_course_panel(self, parent):
        box = ttk.LabelFrame(parent, text=" Courses ", padding=10)
        box.pack(fill="x", pady=(0, 10))
        box.columnconfigure(1, weight=1, minsize=120)

        ttk.Label(box, text="New course").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(box, textvariable=self.new_var, width=12)
        entry.grid(row=0, column=1, sticky="ew", padx=8, pady=2)
        entry.bind("<Return>", self.on_add_course)         # Enter works like the button
        ttk.Button(box, text="Add course", command=self.on_add_course).grid(
            row=0, column=2, sticky="ew")

        ttk.Label(box, text="Selected").grid(row=1, column=0, sticky="w")
        self.selected_box = ttk.Combobox(box, textvariable=self.selected_var,
                                         state="readonly", width=12)
        self.selected_box.grid(row=1, column=1, sticky="ew", padx=8, pady=2)
        self.selected_box.bind("<<ComboboxSelected>>", self.on_select_course)
        ttk.Button(box, text="Remove course", command=self.on_remove_course).grid(
            row=1, column=2, sticky="ew")

    def build_prerequisite_panel(self, parent):
        box = ttk.LabelFrame(parent, text=" Prerequisites ", padding=10)
        box.pack(fill="x", pady=(0, 10))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Take first").grid(row=0, column=0, sticky="w")
        self.from_box = ttk.Combobox(box, textvariable=self.from_var,
                                     state="readonly", width=16)
        self.from_box.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=2)

        ttk.Label(box, text="Then take").grid(row=1, column=0, sticky="w")
        self.to_box = ttk.Combobox(box, textvariable=self.to_var,
                                   state="readonly", width=16)
        self.to_box.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=2)

        buttons = ttk.Frame(box)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        buttons.columnconfigure((0, 1), weight=1)
        ttk.Button(buttons, text="Add prerequisite", command=self.on_add_prerequisite).grid(
            row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(buttons, text="Remove prerequisite", command=self.on_remove_prerequisite).grid(
            row=0, column=1, sticky="ew", padx=(3, 0))

    def build_algorithm_panel(self, parent):
        box = ttk.LabelFrame(parent, text=" Algorithms ", padding=10)
        box.pack(fill="x", pady=(0, 10))
        ttk.Label(box, text="DFS and BFS start at the selected course.").pack(
            anchor="w", pady=(0, 6))
        ttk.Button(box, text="Depth-first search (DFS)",
                   command=self.on_dfs).pack(fill="x", pady=2)
        ttk.Button(box, text="Breadth-first search (BFS)",
                   command=self.on_bfs).pack(fill="x", pady=2)
        ttk.Button(box, text="Study order (topological sort)", style="Primary.TButton",
                   command=self.on_topological_sort).pack(fill="x", pady=2)
        ttk.Button(box, text="Adjacency list and matrix",
                   command=self.on_show_representation).pack(fill="x", pady=2)

    def build_sample_buttons(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill="x")
        row.columnconfigure((0, 1), weight=1)
        ttk.Button(row, text="Load sample", command=self.load_sample).grid(
            row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(row, text="Clear all", command=self.on_clear).grid(
            row=0, column=1, sticky="ew", padx=(3, 0))

    def build_canvas(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, bg=PAPER, highlightthickness=1,
                                highlightbackground="#CBD5E1")
        self.add_scrollbars(frame, self.canvas)
        self.canvas.bind("<Configure>", self.on_canvas_resize)  # redraw when the size changes
        self.canvas.bind("<Button-1>", self.on_canvas_click)    # click a course to select it

    def build_output(self, parent):
        frame = ttk.LabelFrame(parent, text=" Output ", padding=6)
        frame.pack(fill="x", pady=10)
        self.output = tk.Text(frame, height=10, wrap="none", font="TkFixedFont",
                              bg="white", fg=INK, relief="flat", state="disabled")
        self.add_scrollbars(frame, self.output)

    def add_scrollbars(self, frame, widget):
        """Put a vertical and a horizontal scrollbar around a Text or Canvas widget."""
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=widget.xview)
        widget.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        widget.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    # ==================================================================
    #  Keeping the screen in sync with the graph
    # ==================================================================
    def refresh(self, message):
        """Call this after every change to the graph."""
        names = self.graph.vertices()
        for box in (self.selected_box, self.from_box, self.to_box):
            box["values"] = names                   # fill the drop-down lists
        for var in (self.selected_var, self.from_var, self.to_var):
            if var.get() not in names:              # forget a course that was just removed
                var.set("")
        self.clear_marks()
        self.show("Ready", ["Click a course to see its details,",
                            "or pick an algorithm on the left."])
        self.status_var.set(f"{message}     |     Courses (size): {self.graph.size()}"
                            f"     Prerequisites (edges): {self.graph.edge_count()}")
        self.draw_graph()

    def show(self, title, lines):
        """Replace the text in the Output box."""
        self.output.config(state="normal")          # unlock, write, lock again
        self.output.delete("1.0", "end")
        self.output.insert("end", title + "\n" + "-" * len(title) + "\n" + "\n".join(lines))
        self.output.config(state="disabled")

    # ==================================================================
    #  Handlers: courses (vertices) and prerequisites (edges)
    # ==================================================================
    def on_add_course(self, event=None):
        name = " ".join(self.new_var.get().split())    # trim and collapse extra spaces
        if not name:
            messagebox.showwarning("Course name needed",
                                   "Type a course name, then click Add course.")
            return
        try:
            self.graph.add_vertex(name)                # the ADT checks its own rules
        except ValueError as err:
            messagebox.showwarning("Cannot add course", str(err))
            return
        self.new_var.set("")
        self.refresh(f"Added course '{name}'")

    def on_remove_course(self):
        name = self.selected_var.get()
        if not name:
            messagebox.showinfo("Select a course",
                                "Click a course in the graph, or choose one in Selected.")
            return
        if messagebox.askyesno("Remove course",
                               f"Remove '{name}' and every prerequisite that involves it?"):
            self.graph.remove_vertex(name)
            self.refresh(f"Removed course '{name}'")

    def read_edge_choice(self):
        """Return (take first, then take), or None if one of them is missing."""
        first, then = self.from_var.get(), self.to_var.get()
        if not first or not then:
            messagebox.showwarning("Two courses needed",
                                   "Choose a course in both Take first and Then take.")
            return None
        return first, then

    def on_add_prerequisite(self):
        choice = self.read_edge_choice()
        if choice is None:
            return
        first, then = choice
        if first == then:
            messagebox.showwarning("Cannot add prerequisite",
                                   "A course cannot be its own prerequisite. Choose two different courses.")
            return
        # Scenario rule: prerequisites must never form a circle.
        # first -> then closes a circle exactly when 'then' can already reach 'first'.
        if self.graph.has_path(then, first):
            messagebox.showwarning(
                "Circular prerequisite",
                f"'{then}' already leads to '{first}', so requiring '{first}' before "
                f"'{then}' would form a circle. Choose a different pair.")
            return
        try:
            self.graph.add_edge(first, then)
        except ValueError as err:
            messagebox.showwarning("Cannot add prerequisite", str(err))
            return
        self.refresh(f"Added prerequisite {first} → {then}")

    def on_remove_prerequisite(self):
        choice = self.read_edge_choice()
        if choice is None:
            return
        first, then = choice
        try:
            self.graph.remove_edge(first, then)
        except ValueError as err:
            messagebox.showwarning("Cannot remove prerequisite", str(err))
            return
        self.refresh(f"Removed prerequisite {first} → {then}")

    def on_clear(self):
        if messagebox.askyesno("Clear all", "Remove every course and prerequisite?"):
            self.graph = Graph(directed=True)
            self.refresh("Graph cleared")

    def load_sample(self):
        self.graph = Graph(directed=True)
        for name in SAMPLE_COURSES:
            self.graph.add_vertex(name)
        for first, then in SAMPLE_PREREQUISITES:
            self.graph.add_edge(first, then)
        self.refresh("Sample curriculum loaded")

    # ==================================================================
    #  Handlers: selecting a course
    # ==================================================================
    def on_select_course(self, event=None):
        name = self.selected_var.get()
        if name:
            self.clear_marks()                 # an old algorithm result no longer matches the output
            self.show_details(name)
            self.draw_graph()

    def on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)               # window position -> drawing position
        cy = self.canvas.canvasy(event.y)               # (they differ when the canvas is scrolled)
        for name, (x, y) in self.positions.items():     # which box was clicked?
            if abs(cx - x) <= BOX_W / 2 and abs(cy - y) <= BOX_H / 2:
                self.selected_var.set(name)
                self.on_select_course()
                return

    def show_details(self, name):
        prereqs = self.graph.predecessors(name)
        unlocks = self.graph.neighbors(name)
        self.show(f"Course details: {name}", [
            f"In-degree  = {self.graph.in_degree(name)}   "
            f"prerequisites: {', '.join(prereqs) or 'none, it can be taken first'}",
            f"Out-degree = {self.graph.out_degree(name)}   "
            f"unlocks: {', '.join(unlocks) or 'nothing, no course needs it'}",
        ])

    # ==================================================================
    #  Handlers: algorithms (call the ADT, then format and animate the result)
    # ==================================================================
    def on_dfs(self):
        self.run_traversal("Depth-first search (uses a stack)", self.graph.dfs,
                           "Stack (top on the right)", DFS_COLORS)

    def on_bfs(self):
        self.run_traversal("Breadth-first search (uses a queue)", self.graph.bfs,
                           "Queue (front on the left)", BFS_COLORS)

    def run_traversal(self, title, algorithm, container_title, colors):
        start = self.selected_var.get()
        if not start:
            messagebox.showinfo("Select a course",
                                "Click a course in the graph, or choose one in Selected, "
                                "to start from.")
            return
        order, trace = algorithm(start)                 # the ADT does the real work
        lines = [f"Start: {start}",
                 self.format_order("Visit order", order),
                 ""]
        lines += self.trace_table(trace, "Visited", container_title)
        self.show(title, lines)
        self.animate(order, colors)

    def on_topological_sort(self):
        if self.graph.size() == 0:
            messagebox.showinfo("Nothing to sort", "Add some courses first.")
            return
        if self.graph.has_cycle():       # safety net: Add prerequisite already blocks circles
            self.show("No valid study order",
                      ["The prerequisites form a circle, so none of its courses can go first."])
            return
        order, trace = self.graph.topological_sort()
        lines = ["Each course comes after all of its prerequisites.",
                 "Courses with in-degree 0 (no prerequisites) go first.",
                 "",
                 self.format_order("Study order", order),
                 ""]
        lines += self.trace_table(trace, "Taken", "Queue (front on the left)")
        self.show("Study order (topological sort, uses a queue)", lines)
        self.animate(order, TOPO_COLORS)

    def format_order(self, label, order):
        """'label: A → B → C', wrapped to fit the Output box without splitting a name."""
        names = [name.replace(" ", "\u00a0") for name in order]   # non-breaking spaces
        return textwrap.fill(f"{label}: " + " → ".join(names), 80)

    def trace_table(self, trace, vertex_title, container_title):
        """Turn the ADT's trace into aligned text rows, like the tables in the packet."""
        width = max(len(vertex_title), max(len(v) for v, _ in trace)) + 3
        lines = [f"{'Step':<6}{vertex_title:<{width}}{container_title}"]
        for step, (v, container) in enumerate(trace, start=1):
            lines.append(f"{step:<6}{v:<{width}}[{', '.join(container)}]")
        return lines

    def on_show_representation(self):
        names, matrix = self.graph.to_matrix()
        if not names:
            messagebox.showinfo("Nothing to show", "Add some courses first.")
            return
        width = max(len(n) for n in names)
        lines = ["Adjacency list: each course followed by the courses it unlocks", ""]
        for name in names:
            unlocks = ", ".join(self.graph.neighbors(name)) or "-"
            lines.append(f"{name:<{width}}  ->  {unlocks}")
        lines += ["", "Adjacency matrix: row course -> column course, 1 = prerequisite", ""]
        lines.append(" " * (width + 3) + "".join(f"{j + 1:>3}" for j in range(len(names))))
        for i, row in enumerate(matrix):
            lines.append(f"{i + 1:>2} {names[i]:<{width}}" + "".join(f"{cell:>3}" for cell in row))
        lines += ["", f"Storage: the list holds {self.graph.edge_count()} entries; "
                      f"the matrix needs {len(names) ** 2} cells for the same graph."]
        self.clear_marks()
        self.show("Adjacency list and adjacency matrix", lines)
        self.draw_graph()

    # ==================================================================
    #  Animation: mark the visited courses one by one
    # ==================================================================
    def animate(self, order, colors):
        self.clear_marks()
        self.mark_colors = colors
        self.animate_step(order, 0)

    def animate_step(self, order, i):
        if i < len(order):
            self.marks[order[i]] = i + 1                # mark the next course ...
            self.draw_graph()
            # ... then call this method again in 450 milliseconds
            self.anim_job = self.root.after(450, self.animate_step, order, i + 1)
        else:
            self.anim_job = None

    def clear_marks(self):
        if self.anim_job is not None:                   # stop an animation that is still running
            self.root.after_cancel(self.anim_job)
            self.anim_job = None
        self.marks = {}

    # ==================================================================
    #  Drawing the graph on the canvas
    # ==================================================================
    def on_canvas_resize(self, event):
        self.draw_graph()

    def draw_graph(self):
        c = self.canvas
        c.delete("all")                                 # wipe the canvas, then redraw everything
        view_w, view_h = c.winfo_width(), c.winfo_height()

        if self.graph.size() == 0:
            self.positions = {}
            self.draw_paper(view_w, view_h)
            c.create_text(view_w / 2, view_h / 2, fill=PENCIL, font=("Helvetica", 12),
                          text="The graph is empty. Add a course on the left to start.")
            return

        self.positions, column_x, (width, height) = self.compute_layout(view_w, view_h)
        self.draw_paper(width, height)

        for level, x in column_x.items():               # column headers
            c.create_text(x, 18, text=f"Level {level + 1}", fill=PENCIL,
                          font=("Helvetica", 9, "bold"))

        for u, v in self.graph.edges():                 # arrows first, so boxes are drawn on top
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            c.create_line(x1 + BOX_W / 2, y1, x2 - BOX_W / 2, y2, arrow=tk.LAST,
                          arrowshape=(10, 12, 4), fill=PENCIL, width=1.6)

        for name, (x, y) in self.positions.items():
            self.draw_course(name, x, y)

        c.create_text(PAD, height - 10, anchor="sw", fill=PENCIL, font=("Helvetica", 9),
                      text="Arrow A → B: pass A before B.     Click a course to select it.")

    def draw_paper(self, width, height):
        """Graph-paper background. Also tells the canvas how far it may scroll."""
        self.canvas.configure(scrollregion=(0, 0, width, height))
        for x in range(0, width, 30):
            self.canvas.create_line(x, 0, x, height, fill=GRID)
        for y in range(0, height, 30):
            self.canvas.create_line(0, y, width, y, fill=GRID)

    def compute_layout(self, view_w, view_h):
        """Give every course an (x, y). Returns (positions, column_x, (width, height))."""
        # Level of a course = length of the longest prerequisite chain before it.
        level = {v: 0 for v in self.graph.vertices()}
        order, _ = self.graph.topological_sort()
        for v in order:
            for w in self.graph.neighbors(v):
                level[w] = max(level[w], level[v] + 1)

        columns = {}                                    # level -> courses on that level
        for v in self.graph.vertices():
            columns.setdefault(level[v], []).append(v)

        # The drawing is at least as big as the window. If it needs more room
        # than the window has, it gets that room and the canvas scrolls.
        last = max(columns)
        tallest = max(len(names) for names in columns.values())
        width = max(view_w, 2 * PAD + BOX_W + last * (BOX_W + COLUMN_GAP))
        height = max(view_h, 70 + tallest * (BOX_H + 20))

        step = min((width - 2 * PAD - BOX_W) / max(last, 1), 190)   # distance between columns
        left = max(PAD, (width - (last * step + BOX_W)) / 2)        # centre the drawing
        top, bottom = 40, height - 30

        positions, column_x = {}, {}
        for lvl in sorted(columns):                     # place the columns from left to right
            names = columns[lvl]
            # Courses are ordered by the average height of the courses that lead into
            # them, which makes the arrows cross each other less.
            names.sort(key=lambda n: self.average_height(n, positions))
            x = left + BOX_W / 2 + lvl * step
            column_x[lvl] = x
            row_height = (bottom - top) / len(names)
            for i, name in enumerate(names):
                positions[name] = (x, top + row_height * (i + 0.5))
        return positions, column_x, (width, height)

    def average_height(self, name, positions):
        """Average y of the already-placed courses that lead into 'name' (0 if none)."""
        ys = [positions[p][1] for p in self.graph.predecessors(name) if p in positions]
        return sum(ys) / len(ys) if ys else 0

    def draw_course(self, name, x, y):
        c = self.canvas
        left, top = x - BOX_W / 2, y - BOX_H / 2
        fill, border, border_width = "white", PENCIL, 1.5
        if name in self.marks:                          # visited by DFS / BFS / topological sort
            fill, border = self.mark_colors
        if name == self.selected_var.get():             # the selected course
            border, border_width = SELECT, 3
        c.create_rectangle(left, top, left + BOX_W, top + BOX_H,
                           fill=fill, outline=border, width=border_width)
        c.create_text(x, y, text=name, width=BOX_W - 10, justify="center",
                      font=("Helvetica", 9, "bold"), fill=INK)
        if name in self.marks:                          # numbered badge on the top-left corner
            c.create_oval(left - 11, top - 11, left + 11, top + 11,
                          fill=self.mark_colors[1], outline="white", width=2)
            c.create_text(left, top, text=str(self.marks[name]), fill="white",
                          font=("Helvetica", 9, "bold"))


def main():
    root = tk.Tk()
    PlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
