import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math
import io
import os

# ---------------------------------------------------------------------
# Base shape class
# ---------------------------------------------------------------------
class Shape:
    def __init__(self):
        self.selected = False
        self.handles = {}  # {handle_name: canvas_item_id}
        self.item = None

    def draw(self, canvas):
        pass

    def contains_point(self, x, y):
        return False

    def select(self, canvas):
        self.selected = True
        self.draw_handles(canvas)

    def deselect(self, canvas):
        self.selected = False
        self.delete_handles(canvas)

    def delete_handles(self, canvas):
        for hid in self.handles.values():
            canvas.delete(hid)
        self.handles = {}

    def draw_handles(self, canvas):
        pass

# ---------------------------------------------------------------------
# RectangleShape
# ---------------------------------------------------------------------
class RectangleShape(Shape):
    def __init__(self, x, y, width, height, angle=0):
        super().__init__()
        self.base_x = x
        self.base_y = y
        self.base_width = width
        self.base_height = height
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle

    def draw(self, canvas):
        corners = self.get_corners()
        if self.item is None:
            self.item = canvas.create_polygon(corners, fill="", outline="black", width=4)
        else:
            canvas.coords(self.item, *corners)

    def get_corners(self):
        w2 = self.width / 2
        h2 = self.height / 2
        pts = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]
        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        coords = []
        for dx, dy in pts:
            rx = self.x + dx * cos_a - dy * sin_a
            ry = self.y + dx * sin_a + dy * cos_a
            coords.extend([rx, ry])
        return coords

    def contains_point(self, px, py):
        rad = math.radians(-self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        dx, dy = px - self.x, py - self.y
        lx = dx * cos_a - dy * sin_a
        ly = dx * sin_a + dy * cos_a
        return (abs(lx) <= self.width / 2) and (abs(ly) <= self.height / 2)

    def draw_handles(self, canvas):
        self.delete_handles(canvas)
        corners = self.get_corners()
        pts = [(corners[i], corners[i+1]) for i in range(0, len(corners), 2)]
        hs = 6
        bx, by = pts[2]
        rsz = canvas.create_rectangle(bx - hs, by - hs, bx + hs, by + hs, fill="blue")
        self.handles["resize"] = rsz
        top_mid = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        rx, ry = top_mid[0], top_mid[1] - 20
        rot = canvas.create_rectangle(rx - hs, ry - hs, rx + hs, ry + hs, fill="red")
        self.handles["rotate"] = rot

# ---------------------------------------------------------------------
# CircleShape
# ---------------------------------------------------------------------
class CircleShape(Shape):
    def __init__(self, x, y, radius):
        super().__init__()
        self.base_x = x
        self.base_y = y
        self.base_radius = radius
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, canvas):
        if self.item is None:
            self.item = canvas.create_oval(self.x - self.radius, self.y - self.radius,
                                           self.x + self.radius, self.y + self.radius,
                                           fill="", outline="black", width=4)
        else:
            canvas.coords(self.item,
                          self.x - self.radius, self.y - self.radius,
                          self.x + self.radius, self.y + self.radius)

    def contains_point(self, px, py):
        return ((px - self.x) ** 2 + (py - self.y) ** 2) <= self.radius ** 2

    def draw_handles(self, canvas):
        self.delete_handles(canvas)
        hs = 6
        rx = self.x + self.radius
        ry = self.y
        rsz = canvas.create_rectangle(rx - hs, ry - hs, rx + hs, ry + hs, fill="blue")
        self.handles["resize"] = rsz
        top_y = self.y - self.radius - 20
        rot = canvas.create_rectangle(self.x - hs, top_y - hs, self.x + hs, top_y + hs, fill="red")
        self.handles["rotate"] = rot

# ---------------------------------------------------------------------
# HourglassShape
# ---------------------------------------------------------------------
class HourglassShape(Shape):
    def __init__(self, x, y, width=60, height=80, angle=0):
        super().__init__()
        self.base_x = x
        self.base_y = y
        self.base_width = width
        self.base_height = height
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle

    def draw(self, canvas):
        coords = self._get_coords()
        if self.item is None:
            self.item = canvas.create_polygon(coords, fill="", outline="black", width=4)
        else:
            canvas.coords(self.item, *coords)

    def _get_coords(self):
        # Use the requested order for the hourglass:
        # local coordinates: [ -w/2, -h/2,  w/2,  h/2,  -w/2,  h/2,  w/2, -h/2,  -w/2, -h/2 ]
        w2 = self.width / 2
        h2 = self.height / 2
        local_pts = [
            (-w2, -h2),
            ( w2,  h2),
            (-w2,  h2),
            ( w2, -h2),
            (-w2, -h2)
        ]
        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        coords = []
        for lx, ly in local_pts:
            rx = self.x + lx * cos_a - ly * sin_a
            ry = self.y + lx * sin_a + ly * cos_a
            coords.extend([rx, ry])
        return coords

    def contains_point(self, px, py):
        coords = self._get_coords()
        return _point_in_polygon(px, py, coords)

    def draw_handles(self, canvas):
        self.delete_handles(canvas)
        coords = self._get_coords()
        hs = 6
        pts = [(coords[i], coords[i+1]) for i in range(0, len(coords)-2, 2)]
        right_pt = max(pts, key=lambda p: p[0])
        rx, ry = right_pt
        rsz = canvas.create_rectangle(rx - hs, ry - hs, rx + hs, ry + hs, fill="blue")
        self.handles["resize"] = rsz
        top_pt = min(pts, key=lambda p: p[1])
        tx, ty = top_pt
        rot = canvas.create_rectangle(tx - hs, ty - 20 - hs, tx + hs, ty - 20 + hs, fill="red")
        self.handles["rotate"] = rot

# ---------------------------------------------------------------------
# LineShape
# ---------------------------------------------------------------------
class LineShape(Shape):
    def __init__(self, x1, y1, x2, y2):
        super().__init__()
        self.base_x1 = x1
        self.base_y1 = y1
        self.base_x2 = x2
        self.base_y2 = y2
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def draw(self, canvas):
        if self.item is None:
            self.item = canvas.create_line(self.x1, self.y1, self.x2, self.y2, fill="black", width=4)
        else:
            canvas.coords(self.item, self.x1, self.y1, self.x2, self.y2)

    def contains_point(self, px, py):
        line_len = math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        if line_len == 0:
            return (abs(px - self.x1) < 5 and abs(py - self.y1) < 5)
        u = ((px - self.x1) * (self.x2 - self.x1) + (py - self.y1) * (self.y2 - self.y1)) / (line_len**2)
        if u < 0 or u > 1:
            return False
        cx = self.x1 + u * (self.x2 - self.x1)
        cy = self.y1 + u * (self.y2 - self.y1)
        return math.hypot(px - cx, py - cy) <= 5

    def draw_handles(self, canvas):
        self.delete_handles(canvas)
        hs = 5
        h1 = canvas.create_rectangle(self.x1 - hs, self.y1 - hs,
                                     self.x1 + hs, self.y1 + hs, fill="blue")
        h2 = canvas.create_rectangle(self.x2 - hs, self.y2 - hs,
                                     self.x2 + hs, self.y2 + hs, fill="blue")
        self.handles["end1"] = h1
        self.handles["end2"] = h2

# ---------------------------------------------------------------------
# TextShape (editable multi-line text, not rotatable)
# ---------------------------------------------------------------------
class TextShape(Shape):
    def __init__(self, x, y, text="", font_size=20):
        super().__init__()
        self.base_x = x
        self.base_y = y
        self.base_font_size = font_size
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.angle = 0  # Text is not rotatable.
        self.bbox = None
        self.text_tk = None

    def draw(self, canvas):
        if self.item is not None:
            canvas.delete(self.item)
        # Bold text
        self.item = canvas.create_text(self.x, self.y, text=self.text,
                                       font=("Arial", self.font_size, "bold"),
                                       fill="black", anchor="nw")
        self.bbox = canvas.bbox(self.item)

    def contains_point(self, px, py):
        if self.bbox:
            x1, y1, x2, y2 = self.bbox
            return (x1 <= px <= x2) and (y1 <= py <= y2)
        return False

    def draw_handles(self, canvas):
        self.delete_handles(canvas)
        if not self.bbox:
            return
        x1, y1, x2, y2 = self.bbox
        hs = 6
        box = canvas.create_rectangle(x1, y1, x2, y2, outline="black", dash=(3,3))
        self.handles["bbox"] = box
        rsz = canvas.create_rectangle(x2 - hs, y2 - hs, x2 + hs, y2 + hs, fill="blue")
        self.handles["resize"] = rsz
        self.bbox = canvas.bbox(self.item)

    def edit_text(self, parent):
        edit_win = tk.Toplevel(parent)
        edit_win.title("Edit Text")
        text_widget = tk.Text(edit_win, wrap="word", width=40, height=10)
        text_widget.insert("1.0", self.text)
        text_widget.pack(padx=10, pady=10)
        def save_and_close():
            self.text = text_widget.get("1.0", "end-1c")
            edit_win.destroy()
        btn = tk.Button(edit_win, text="OK", command=save_and_close)
        btn.pack(pady=5)
        edit_win.transient(parent)
        edit_win.grab_set()
        parent.wait_window(edit_win)

# ---------------------------------------------------------------------
# Helper: point in polygon
# ---------------------------------------------------------------------
def _point_in_polygon(px, py, coords):
    inside = False
    n = len(coords) // 2
    for i in range(n):
        x1, y1 = coords[2*i], coords[2*i+1]
        x2, y2 = coords[2*((i+1)%n)], coords[2*((i+1)%n)+1]
        if (y1 > py) != (y2 > py):
            xcross = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if xcross > px:
                inside = not inside
    return inside

# ---------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gaz Plani  - Hamit SOYSAL")

        # Bind Delete key for deletion
        self.root.bind("<Delete>", lambda event: self.delete_selected_shape())

        # Menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Aç", command=self.load_image)
        filemenu.add_command(label="Kaydet", command=self.save_image)
        menubar.add_cascade(label="Aç veya Kaydet", menu=filemenu)
        root.config(menu=menubar)

        # Toolbar
        self.toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        self.create_toolbar_icons()
        self.edit_text_btn = tk.Button(self.toolbar, text="Edit Text", command=self.edit_text_shape)
        self.edit_text_btn.pack(pady=5)
        self.edit_text_btn.config(state=tk.DISABLED)
        # Delete button (labeled 'SIL')
        self.delete_btn = tk.Button(self.toolbar, text="SIL", command=self.delete_selected_shape)
        self.delete_btn.pack(pady=5)

        # Canvas + scrollbars
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas_xscroll)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas_yscroll)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white",
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # State variables
        self.image = None
        self.original_image = None
        self.image_tk = None
        self.image_item = None

        self.shapes = []
        self.selected_shape = None
        self.current_tool = "select"
        self.current_shape = None
        self.mode = "idle"
        self.drag_data = {}

        self.canvas_width = 800
        self.canvas_height = 600
        self.base_canvas_width = self.canvas_width
        self.base_canvas_height = self.canvas_height

        # Zoom
        self.zoom_level = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_scroll)
        self.canvas.bind("<Button-4>", self.on_mousewheel_scroll)
        self.canvas.bind("<Button-5>", self.on_mousewheel_scroll)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.status_bar = tk.Label(root, text="Zoom: 100%", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.set_select_tool()
        self.load_default_image()  # Opens an image by default on startup

    def canvas_xscroll(self, *args):
        self.canvas.xview(*args)
    def canvas_yscroll(self, *args):
        self.canvas.yview(*args)

    # -----------------------------------------------------------------
    # Toolbar creation with icons
    # -----------------------------------------------------------------
    def create_toolbar_icons(self):
        btn_size = 40
        def make_button(draw_func, command):
            frm = tk.Frame(self.toolbar, width=btn_size, height=btn_size)
            cvs = tk.Canvas(frm, width=btn_size, height=btn_size, bd=2, relief="raised", highlightthickness=0)
            draw_func(cvs)
            cvs.pack(fill=tk.BOTH, expand=True)
            frm.pack(pady=5, padx=5)
            cvs.bind("<Button-1>", lambda e: command())
            return cvs
        def draw_select(cvs):
            cvs.create_text(20, 20, text="Seç", font=("Arial", 12, "bold"))
            # cvs.create_line(10, 10, 30, 30, width=4, arrow=tk.LAST)
        self.select_button = make_button(draw_select, self.set_select_tool)
        def draw_rect(cvs):
            cvs.create_rectangle(10, 10, 30, 30, outline="black", width=4)
        self.rect_button = make_button(draw_rect, self.set_rectangle_tool)
        def draw_circle(cvs):
            cvs.create_oval(8, 8, 32, 32, outline="black", width=4)
        self.circle_button = make_button(draw_circle, self.set_circle_tool)
        def draw_hourglass(cvs):
            pts = [10, 10, 30, 30, 10, 30, 30, 10, 10, 10]
            cvs.create_polygon(pts, fill="", outline="black", width=4)
        self.hourglass_button = make_button(draw_hourglass, self.set_hourglass_tool)
        def draw_line(cvs):
            cvs.create_line(10, 20, 30, 20, fill="black", width=4)
        self.line_button = make_button(draw_line, self.set_line_tool)
        def draw_text(cvs):
            cvs.create_text(20, 20, text="Text", font=("Arial", 12, "bold"))
        self.text_button = make_button(draw_text, self.set_text_tool)
        def draw_plus(cvs):
            cvs.create_oval(10, 10, 30, 30, outline="black", width=4)
            cvs.create_line(15, 20, 25, 20, width=4)
            cvs.create_line(20, 15, 20, 25, width=4)
        self.zoom_in_btn = make_button(draw_plus, self.zoom_in)
        def draw_minus(cvs):
            cvs.create_oval(10, 10, 30, 30, outline="black", width=4)
            cvs.create_line(15, 20, 25, 20, width=4)
        self.zoom_out_btn = make_button(draw_minus, self.zoom_out)
        def draw_reset(cvs):
            cvs.create_text(20, 20, text="100%", font=("Arial", 9, "bold"))
        self.reset_btn = make_button(draw_reset, self.reset_zoom)

    def highlight_tool_button(self, btn):
        for b in [self.select_button, self.rect_button, self.circle_button,
                  self.hourglass_button, self.line_button, self.text_button]:
            b.config(relief="raised", bg="SystemButtonFace")
        btn.config(relief="sunken", bg="lightblue")

    # -----------------------------------------------------------------
    # Tool setters
    # -----------------------------------------------------------------
    # In the tool setters, reset the mode and deselect any active shape.
    def set_select_tool(self):
        self.current_tool = "select"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.select_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    def set_rectangle_tool(self):
        self.current_tool = "rectangle"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.rect_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    def set_circle_tool(self):
        self.current_tool = "circle"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.circle_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    def set_hourglass_tool(self):
        self.current_tool = "hourglass"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.hourglass_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    def set_line_tool(self):
        self.current_tool = "line"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.line_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    def set_text_tool(self):
        self.current_tool = "text"
        self.deselect_all()
        self.mode = "idle"
        self.highlight_tool_button(self.text_button)
        self.edit_text_btn.config(state=tk.DISABLED)

    # -----------------------------------------------------------------
    # Mouse wheel for scrolling
    # -----------------------------------------------------------------
    def on_mousewheel_scroll(self, event):
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")

    # -----------------------------------------------------------------
    # Zoom functionality
    # -----------------------------------------------------------------
    def zoom_in(self):
        if self.zoom_level < self.max_zoom:
            self.zoom_level += self.zoom_step
            self.apply_zoom()

    def zoom_out(self):
        if self.zoom_level > self.min_zoom:
            self.zoom_level -= self.zoom_step
            self.apply_zoom()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.apply_zoom()

    def apply_zoom(self):
        self.update_status_bar()
        if self.original_image:
            w, h = self.original_image.width, self.original_image.height
            new_w = int(w * self.zoom_level)
            new_h = int(h * self.zoom_level)
            scaled = self.original_image.resize((new_w, new_h), Image.LANCZOS)
            self.image = scaled
            self.image_tk = ImageTk.PhotoImage(self.image)
            if self.image_item:
                self.canvas.delete(self.image_item)
            self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)
            self.canvas.tag_lower(self.image_item)
        new_w = max(800, int(self.base_canvas_width * self.zoom_level))
        new_h = max(600, int(self.base_canvas_height * self.zoom_level))
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
        self.canvas_width = new_w
        self.canvas_height = new_h
        for shp in self.shapes:
            if isinstance(shp, RectangleShape):
                shp.x = shp.base_x * self.zoom_level
                shp.y = shp.base_y * self.zoom_level
                shp.width = shp.base_width * self.zoom_level
                shp.height = shp.base_height * self.zoom_level
            elif isinstance(shp, CircleShape):
                shp.x = shp.base_x * self.zoom_level
                shp.y = shp.base_y * self.zoom_level
                shp.radius = shp.base_radius * self.zoom_level
            elif isinstance(shp, HourglassShape):
                shp.x = shp.base_x * self.zoom_level
                shp.y = shp.base_y * self.zoom_level
                shp.width = shp.base_width * self.zoom_level
                shp.height = shp.base_height * self.zoom_level
            elif isinstance(shp, LineShape):
                shp.x1 = shp.base_x1 * self.zoom_level
                shp.y1 = shp.base_y1 * self.zoom_level
                shp.x2 = shp.base_x2 * self.zoom_level
                shp.y2 = shp.base_y2 * self.zoom_level
            elif isinstance(shp, TextShape):
                shp.x = shp.base_x * self.zoom_level
                shp.y = shp.base_y * self.zoom_level
                shp.font_size = int(shp.base_font_size * self.zoom_level)
            if shp.item:
                self.canvas.delete(shp.item)
                shp.item = None
            shp.draw(self.canvas)
            if shp.selected:
                shp.draw_handles(self.canvas)
        self.update_status_bar()

    def update_status_bar(self):
        pct = int(self.zoom_level * 100)
        self.status_bar.config(text=f"Zoom: {pct}%")

    # -----------------------------------------------------------------
    # Load/Save
    # -----------------------------------------------------------------
    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if path:
            self.original_image = Image.open(path)
            self.image = self.original_image.copy()
            self.image_tk = ImageTk.PhotoImage(self.image)
            self.canvas_width = self.image.width
            self.canvas_height = self.image.height
            self.base_canvas_width = self.image.width
            self.base_canvas_height = self.image.height
            self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
            if self.image_item:
                self.canvas.delete(self.image_item)
            self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)
            self.canvas.tag_lower(self.image_item)
            self.zoom_level = 1.0
            self.update_status_bar()
            for s in self.shapes:
                if s.item:
                    self.canvas.delete(s.item)
                    s.item = None
                s.draw(self.canvas)
                if s.selected:
                    s.draw_handles(self.canvas)
    
    def load_default_image(self):
        default_image_path = "elgac-1.png"  # Update this path
        if not os.path.exists(default_image_path):
            print("Default image path does not exist:", default_image_path)
            return
        try:
            self.original_image = Image.open(default_image_path)
            self.image = self.original_image.copy()
            self.image_tk = ImageTk.PhotoImage(self.image)
            self.canvas_width = self.image.width
            self.canvas_height = self.image.height
            self.base_canvas_width = self.image.width
            self.base_canvas_height = self.image.height
            self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
            if self.image_item:
                self.canvas.delete(self.image_item)
            self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)
            self.canvas.tag_lower(self.image_item)
            self.zoom_level = 1.0
            self.update_status_bar()
        except Exception as e:
            print("Could not load default image:", e)

    def save_image(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG Images", "*.png")])
        if not path:
            return
        if self.image:
            w, h = self.image.width, self.image.height
            final_img = self.image.copy().convert("RGB")
        else:
            w, h = self.canvas_width, self.canvas_height
            final_img = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(final_img)
        for shp in self.shapes:
            if isinstance(shp, RectangleShape):
                corners = shp.get_corners()
                pts = [(corners[i], corners[i+1]) for i in range(0, len(corners), 2)]
                pts.append(pts[0])
                draw.line(pts, fill="black", width=4)
            elif isinstance(shp, CircleShape):
                x1 = shp.x - shp.radius
                y1 = shp.y - shp.radius
                x2 = shp.x + shp.radius
                y2 = shp.y + shp.radius
                draw.ellipse((x1, y1, x2, y2), outline="black", width=4)
            elif isinstance(shp, HourglassShape):
                coords = shp._get_coords()
                draw.polygon(coords, outline="black", width=4)
            elif isinstance(shp, LineShape):
                draw.line((shp.x1, shp.y1, shp.x2, shp.y2), fill="black", width=4)
            elif isinstance(shp, TextShape):
                try:
                    font = ImageFont.truetype("arialbd.ttf", shp.font_size)
                except:
                    font = ImageFont.load_default()
                draw.multiline_text((shp.x, shp.y), shp.text, fill="black", font=font)
        final_img.save(path, "PNG")

    # -----------------------------------------------------------------
    # Canvas events
    # -----------------------------------------------------------------
    def on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        # Check if clicking on a handle of a selected shape.
        if self.selected_shape and self.selected_shape.handles:
            for hname, hid in self.selected_shape.handles.items():
                bb = self.canvas.bbox(hid)
                if bb and bb[0] <= cx <= bb[2] and bb[1] <= cy <= bb[3]:
                    if hname in ["resize", "end1", "end2"]:
                        self.mode = "resizing"
                        self.drag_data["handle"] = hname
                        # If resizing text, store initial values
                        if isinstance(self.selected_shape, TextShape) and hname == "resize":
                            self.drag_data["init_x"] = cx
                            self.drag_data["init_y"] = cy
                            self.drag_data["init_font_size"] = self.selected_shape.font_size
                        return
                    elif hname == "rotate":
                        self.mode = "rotating"
                        return

        # Check if clicking on an existing shape.
        for s in reversed(self.shapes):
            if s.contains_point(cx, cy):
                self.select_shape(s)
                self.mode = "move"
                self.drag_data = {"x": cx, "y": cy}
                return

        # If no shape is clicked and we are in edit mode, then deselect and switch to idle.
        if self.mode == "edit":
            self.deselect_all()
            self.mode = "idle"
            return

        # If no shape was clicked and the tool is a drawing tool while in idle mode, create a new shape.
        if self.current_tool in ["rectangle", "circle", "hourglass", "line", "text"] and self.mode == "idle":
            self.mode = "create"
            if self.current_tool == "rectangle":
                self.current_shape = RectangleShape(cx, cy, 100, 60)
            elif self.current_tool == "circle":
                self.current_shape = CircleShape(cx, cy, 50)
            elif self.current_tool == "hourglass":
                self.current_shape = HourglassShape(cx, cy, 60, 40)
            elif self.current_tool == "line":
                self.current_shape = LineShape(cx, cy, cx+50, cy)
            elif self.current_tool == "text":
                self.current_shape = TextShape(cx, cy, "", 20)
            self.shapes.append(self.current_shape)
            self.current_shape.draw(self.canvas)
            self.drag_data = {"x": cx, "y": cy}
            return

        # For the select tool, if no shape is clicked, simply deselect.
        if self.current_tool == "select":
            self.deselect_all()
            self.mode = "idle"

    def on_canvas_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if not self.selected_shape:
            return
        shp = self.selected_shape
        dx = cx - self.drag_data.get("x", cx)
        dy = cy - self.drag_data.get("y", cy)
        if self.mode in ["create", "move"]:
            if isinstance(shp, LineShape):
                shp.x1 += dx
                shp.y1 += dy
                shp.x2 += dx
                shp.y2 += dy
                shp.base_x1 = shp.x1 / self.zoom_level
                shp.base_y1 = shp.y1 / self.zoom_level
                shp.base_x2 = shp.x2 / self.zoom_level
                shp.base_y2 = shp.y2 / self.zoom_level
            else:
                shp.x += dx
                shp.y += dy
                shp.base_x = shp.x / self.zoom_level
                shp.base_y = shp.y / self.zoom_level
            self.drag_data["x"] = cx
            self.drag_data["y"] = cy
            shp.draw(self.canvas)
            shp.draw_handles(self.canvas)
        elif self.mode == "resizing":
            hname = self.drag_data.get("handle", "")
            if isinstance(shp, RectangleShape) and hname == "resize":
                rad = math.radians(-shp.angle)
                dxr = cx - shp.x
                dyr = cy - shp.y
                local_x = dxr * math.cos(rad) - dyr * math.sin(rad)
                local_y = dxr * math.sin(rad) + dyr * math.cos(rad)
                shp.width = max(10, abs(local_x) * 2)
                shp.height = max(10, abs(local_y) * 2)
                shp.base_width = shp.width / self.zoom_level
                shp.base_height = shp.height / self.zoom_level
            elif isinstance(shp, CircleShape) and hname == "resize":
                r = math.hypot(cx - shp.x, cy - shp.y)
                shp.radius = max(10, r)
                shp.base_radius = shp.radius / self.zoom_level
            elif isinstance(shp, HourglassShape) and hname == "resize":
                rad = math.radians(-shp.angle)
                dxr = cx - shp.x
                dyr = cy - shp.y
                local_x = dxr * math.cos(rad) - dyr * math.sin(rad)
                local_y = dxr * math.sin(rad) + dyr * math.cos(rad)
                shp.width = max(10, abs(local_x) * 2)
                shp.height = max(10, abs(local_y) * 2)
                shp.base_width = shp.width / self.zoom_level
                shp.base_height = shp.height / self.zoom_level
            elif isinstance(shp, LineShape):
                if hname == "end1":
                    shp.x1 = cx
                    shp.y1 = cy
                    shp.base_x1 = cx / self.zoom_level
                    shp.base_y1 = cy / self.zoom_level
                else:
                    shp.x2 = cx
                    shp.y2 = cy
                    shp.base_x2 = cx / self.zoom_level
                    shp.base_y2 = cy / self.zoom_level
            elif isinstance(shp, TextShape) and hname =="resize":
                if "init_x" in self.drag_data and "init_y" in self.drag_data and "init_font_size" in self.drag_data:
                    # Compute the initial distance from the text's anchor to the initial click point.
                    init_distance = math.hypot(self.drag_data["init_x"] - shp.x, self.drag_data["init_y"] - shp.y)
                    current_distance = math.hypot(cx - shp.x, cy - shp.y)
                    # Prevent division by zero
                    if init_distance == 0:
                        init_distance = 1
                    ratio = current_distance / init_distance
                    new_font_size = max(8, int(self.drag_data["init_font_size"] * ratio))
                    shp.font_size = new_font_size
                    shp.base_font_size = shp.font_size / self.zoom_level
            shp.draw(self.canvas)
            shp.draw_handles(self.canvas)
        elif self.mode == "rotating":
            if not isinstance(shp, TextShape):
                # Record initial angles when starting rotation
                if "init_rotate_angle" not in self.drag_data:
                    self.drag_data["init_rotate_angle"] = math.degrees(math.atan2(cy - shp.y, cx - shp.x))
                    self.drag_data["init_shape_angle"] = shp.angle
                # Calculate the current angle from the shape's center to the mouse
                current_mouse_angle = math.degrees(math.atan2(cy - shp.y, cx - shp.x))
                # Compute the change in angle relative to the initial click
                delta_angle = current_mouse_angle - self.drag_data["init_rotate_angle"]
                # Update the shape's angle based on its initial angle plus the change
                shp.angle = (self.drag_data["init_shape_angle"] + delta_angle) % 360
                shp.draw(self.canvas)
                shp.draw_handles(self.canvas)
        self.drag_data["x"] = cx
        self.drag_data["y"] = cy

    def on_canvas_release(self, event):
        for key in ["init_rotate_angle", "init_shape_angle"]:
            if key in self.drag_data:
                del self.drag_data[key]
        if self.mode == "create" and self.current_shape:
            # Once the shape is created, select it and remain in edit mode.
            self.select_shape(self.current_shape)
            self.mode = "edit"  # Stay in edit mode after creation.
            if self.current_tool == "text":
                self.current_shape.edit_text(self.root)
                self.current_shape.draw(self.canvas)
                self.current_shape.draw_handles(self.canvas)
            # Keep the shape selected for editing.
            self.current_shape = None
        else:
            if self.selected_shape:
                self.mode = "edit"  # Switch to edit mode after dropping an object.
            else:
                self.mode = "idle"

    def on_double_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        for shp in self.shapes:
            if isinstance(shp, TextShape) and shp.contains_point(cx, cy):
                self.deselect_all()
                self.selected_shape = shp
                shp.select(self.canvas)
                self.edit_text_shape()
                break

    def select_shape(self, shp):
        self.deselect_all()
        self.selected_shape = shp
        shp.select(self.canvas)
        if shp.item:
            self.canvas.tag_raise(shp.item)
            for hid in shp.handles.values():
                self.canvas.tag_raise(hid)
        if isinstance(shp, TextShape):
            self.edit_text_btn.config(state=tk.NORMAL)
        else:
            self.edit_text_btn.config(state=tk.DISABLED)

    def deselect_all(self):
        if self.selected_shape:
            self.selected_shape.deselect(self.canvas)
        self.selected_shape = None
        self.edit_text_btn.config(state=tk.DISABLED)

    def edit_text_shape(self):
        if isinstance(self.selected_shape, TextShape):
            self.selected_shape.edit_text(self.root)
            self.selected_shape.draw(self.canvas)
            self.selected_shape.draw_handles(self.canvas)

    def delete_selected_shape(self):
        if self.selected_shape:
            self.canvas.delete(self.selected_shape.item)
            self.selected_shape.delete_handles(self.canvas)
            if self.selected_shape in self.shapes:
                self.shapes.remove(self.selected_shape)
            self.selected_shape = None
            self.edit_text_btn.config(state=tk.DISABLED)
# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    app = App(root)
    root.mainloop()
