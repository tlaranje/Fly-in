from typing import TYPE_CHECKING
import tkinter as tk

if TYPE_CHECKING:
    from src.Parsing import DroneMap


class ToolTip:
    def __init__(self, canvas, item_id, title, details):
        self.canvas = canvas
        self.item_id = item_id
        self.title = title
        self.details = details
        self.tip_window = None
        self.canvas.tag_bind(self.item_id, "<Enter>", self.show_tip)
        self.canvas.tag_bind(self.item_id, "<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window:
            return

        x = self.canvas.winfo_pointerx() + 25
        y = self.canvas.winfo_pointery() + 25
        self.tip_window = tw = tk.Toplevel(self.canvas)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        container = tk.Frame(
            tw, bg="#1e1e1e", padx=20, pady=15,
            highlightthickness=2, highlightbackground="#454545"
        )
        container.pack()

        # No Ubuntu, 'Ubuntu' ou 'DejaVu Sans' são as fontes padrão nítidas
        tk.Label(
            container, text=self.title, font=("Ubuntu", 16, "bold"),
            bg="#1e1e1e", fg="#ffffff"
        ).pack(fill='x')

        line = tk.Frame(container, height=2, bg="#555555")
        line.pack(fill='x', pady=10)

        # Ajuste para Linux
        lines = self.details.split('\n')
        max_w = max(len(l) for l in lines)

        details_box = tk.Text(
            container,
            font=("DejaVu Sans Mono", 13), # Mono para garantir alinhamento dos pontos (bullets)
            bg="#1e1e1e",
            fg="#e0e0e0",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            # spacing2 = 12 é um espaço generoso e visível no Ubuntu
            spacing2=12,
            height=len(lines),
            width=max_w + 2
        )
        details_box.insert("1.0", self.details)
        details_box.config(state="disabled")
        details_box.pack(anchor='w')

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class Visualizer:
    def __init__(self, d_map: "DroneMap") -> None:
        self.d_map = d_map
        self.root = tk.Tk()
        self.root.title("Fly-in")

        self.scale: float = 64
        self.margin: float = 100

        self.min_x = min(z.x for z in d_map.zones.values())
        self.min_y = min(z.y for z in d_map.zones.values())
        self.max_x = max(z.x for z in d_map.zones.values())
        self.max_y = max(z.y for z in d_map.zones.values())

        self.width = (self.max_x - self.min_x) * self.scale + self.margin * 2
        self.height = (self.max_y - self.min_y) * self.scale + self.margin * 2
        self.bg_color = "#2b2b2b"
        self.root.configure(bg=self.bg_color)

        self.title_label = tk.Label(
            self.root, text="Turn 0", font=("Segoe UI", 32, "bold"),
            fg="white", bg=self.bg_color, pady=20
        )
        self.title_label.pack()

        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg=self.bg_color, highlightthickness=0
        )
        self.canvas.pack()
        self.turn_count = 0

    def draw_zones(self) -> None:
        for zone in self.d_map.zones.values():
            cx = (zone.x - self.min_x) * self.scale + self.margin
            cy = (zone.y - self.min_y) * self.scale + self.margin

            rec_id = self.canvas.create_oval(
                cx - 18, cy - 18, cx + 18, cy + 18,
                fill=zone.color or "grey", outline="black", width=1
            )

            title = f"ZONE: {zone.name.upper()}"
            details = (f"• Position: ({zone.x}, {zone.y})\n"
                       f"• Category: {zone.zone_type.name}\n"
                       f"• Capacity: {zone.max_drones}")
            ToolTip(self.canvas, rec_id, title, details)
            zone.canva_id = rec_id

    def draw_connections(self) -> None:
        for _, conn in self.d_map.connections.items():
            z1, z2 = self.d_map.zones[conn.zone1], self.d_map.zones[conn.zone2]
            x1 = (z1.x - self.min_x) * self.scale + self.margin
            y1 = (z1.y - self.min_y) * self.scale + self.margin
            x2 = (z2.x - self.min_x) * self.scale + self.margin
            y2 = (z2.y - self.min_y) * self.scale + self.margin

            line_id = self.canvas.create_line(
                x1, y1, x2, y2, width=4, fill="#1a1a1a", activefill="#ffffff"
            )

            title = f"LINK: {conn.name.upper()}"
            details = (f"• From: {conn.zone1}\n• To: {conn.zone2}\n"
                       f"• Max Cap: {conn.max_link_capacity}")
            ToolTip(self.canvas, line_id, title, details)

    def draw_drones(self) -> None:
        colors = [
            "#00ff00", "#ff00ff", "#00ffff", "#ffff00", "#ff8000", "#ffffff"
        ]
        z = self.d_map.zones[self.d_map.start_zone.name]
        cx = (z.x - self.min_x) * self.scale + self.margin
        cy = (z.y - self.min_y) * self.scale + self.margin

        for i in range(1, self.d_map.nb_drones):
            d = self.d_map.drones[i]
            tag = f"drone_{i}"
            color = colors[i % len(colors)]
            d.curr_zone = self.d_map.start_zone.name
            d.drone_tag = tag

            main_id = self.canvas.create_oval(
                cx - 12, cy - 12, cx + 12, cy + 12,
                fill=color, outline="black", width=1, tags=tag
            )

            off, r = 3, 6
            pts = [(cx-12+off, cy-12+off), (cx+12-off, cy-12+off),
                   (cx-12+off, cy+12-off), (cx+12-off, cy+12-off)]

            for px, py in pts:
                self.canvas.create_oval(
                    px-r, py-r, px+r, py+r,
                    fill=color, outline="black", width=1, tags=tag
                )

            ToolTip(
                self.canvas, tag,
                f"DRONE {i}", f"• Reference: {tag}\n• Status: Active"
            )
            d.canva_id = main_id

    def run(self) -> None:
        self.draw_connections()
        self.draw_zones()
        self.draw_drones()
        self.root.mainloop()
