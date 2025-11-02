import customtkinter as ctk
from tkinter import messagebox
import time, math, random, threading
from collections import deque

class SimuladorPaginacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Paginación")
        self.root.geometry("1400x900")
        self.root.state("zoomed")

        # --- Estados ---
        self.paused = False
        self.stop_simulation = False
        self.page_faults = 0
        self.speed = 0.3
        self.log_window = None
        self.info = None

        # --- Colores ---
        self.colors = {
            "bg": "#f4f6f7",
            "card": "#ffffff",
            "primary": "#4f6caa",
            "secondary": "#10b981",
            "accent": "#f59e0b",
            "danger": "#ef4444",
            "text": "#363434"
        }

        # --- UI ---
        self.create_ui()

    # ----------------------------------------------------
    def create_ui(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Frame principal
        main = ctk.CTkFrame(self.root, corner_radius=25)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # --- HEADER ---
        header = ctk.CTkFrame(main, fg_color=self.colors["primary"], corner_radius=20)
        header.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(header, text="Simulador de Paginación",
                     font=("Segoe UI", 26, "bold"), text_color="white").pack(pady=10)

        # --- CONFIGURACIÓN ---
        config_frame = ctk.CTkFrame(main, fg_color="transparent")
        config_frame.pack(fill="x", pady=10)
        config = ctk.CTkFrame(config_frame, corner_radius=20)
        config.pack(pady=10)

        ctk.CTkLabel(config, text="⚙️ Configuración",
                     font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=8, sticky="w", padx=15, pady=10)

        # Entradas de configuración
        ctk.CTkLabel(config, text="💾 Memoria (KB):").grid(row=1, column=0, padx=10, pady=5)
        self.memoria_entry = ctk.CTkEntry(config, width=80)
        self.memoria_entry.insert(0, "600")
        self.memoria_entry.grid(row=1, column=1)

        ctk.CTkLabel(config, text="📄 Página (KB):").grid(row=1, column=2, padx=10)
        self.pagina_entry = ctk.CTkEntry(config, width=80)
        self.pagina_entry.insert(0, "100")
        self.pagina_entry.grid(row=1, column=3)

        ctk.CTkLabel(config, text="🧩 Procesos:").grid(row=1, column=4, padx=10)
        self.procesos_entry = ctk.CTkEntry(config, width=300)
        self.procesos_entry.insert(0, "A=75,B=350,C=135,D=250,E=100,F=300")
        self.procesos_entry.grid(row=1, column=5)

        # --- Selector de algoritmo ---
        ctk.CTkLabel(config, text="🧮 Algoritmo:").grid(row=1, column=6, padx=10)
        self.algoritmo_var = ctk.StringVar(value="FIFO")
        self.algoritmo_menu = ctk.CTkOptionMenu(config, variable=self.algoritmo_var,
                                                values=["FIFO", "LRU", "Óptimo"],
                                                fg_color=self.colors["primary"],
                                                button_color=self.colors["primary"],
                                                text_color="white",
                                                font=("Segoe UI", 13, "bold"))
        self.algoritmo_menu.grid(row=1, column=7, padx=10)

        # --- Control de velocidad ---
        speed_frame = ctk.CTkFrame(config, fg_color="transparent", corner_radius=15)
        speed_frame.grid(row=2, column=0, columnspan=8, pady=10, padx=15, sticky="ew")
        ctk.CTkLabel(speed_frame, text="⚡ Velocidad de simulación", font=("Segoe UI", 12, "bold")).pack()
        self.speed_scale = ctk.CTkSlider(speed_frame, from_=0.05, to=1.0, number_of_steps=10, command=self.set_speed)
        self.speed_scale.set(0.3)
        self.speed_scale.pack(pady=5)
        self.speed_label = ctk.CTkLabel(speed_frame, text="Normal 🚴", text_color="#202020")
        self.speed_label.pack()

        # --- Botones de control ---
        buttons = ctk.CTkFrame(main, fg_color="transparent", corner_radius=15)
        buttons.pack(pady=10)
        ctk.CTkButton(buttons, text="🚀 Iniciar Simulación", fg_color=self.colors["primary"],
                      text_color="white", font=("Segoe UI", 14, "bold"),
                      command=self.iniciar_hilo).pack(side="left", padx=10)
        ctk.CTkButton(buttons, text="⏸️ Pausa/Reanudar", fg_color=self.colors["accent"],
                      text_color="white", font=("Segoe UI", 14, "bold"),
                      command=self.toggle_pause).pack(side="left", padx=10)
        ctk.CTkButton(buttons, text="📜 Ver Log", fg_color=self.colors["secondary"],
                      text_color="white", font=("Segoe UI", 14, "bold"),
                      command=self.abrir_log).pack(side="left", padx=10)

        # --- Panel principal dividido ---
        viz = ctk.CTkFrame(self.root, fg_color="transparent")
        viz.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo (tablas de páginas por proceso)
        self.left = ctk.CTkScrollableFrame(viz, fg_color=self.colors["primary"], corner_radius=20)
        self.left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(self.left, text="📘 Tablas de Páginas",
                     text_color="white", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=15, pady=10)

        self.process_tables = {}  # almacenamiento de tablas

        # Panel derecho (visualización de memoria)
        right = ctk.CTkFrame(viz, fg_color=self.colors["primary"], corner_radius=20)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(right, text="💾 Memoria Principal", text_color="white",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
        
        canvas_container = ctk.CTkFrame(right, fg_color="white", corner_radius=10)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = ctk.CTkCanvas(canvas_container, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas.bind("<Configure>", self.redibujar_memoria)

        # Etiqueta de fallos
        self.page_fault_label = ctk.CTkLabel(main, text="💥 Fallos de página: 0",
                                             font=("Segoe UI", 13, "bold"))
        self.page_fault_label.pack(pady=5)

    # ----------------------------------------------------
    def abrir_log(self):
        """Abre una ventana pequeña tipo CMD con el registro."""
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return

        self.log_window = ctk.CTkToplevel(self.root)
        self.log_window.title("📜 Registro de simulación")
        self.log_window.geometry("600x500")
        self.log_window.resizable(True, True)
        self.log_window.configure(fg_color=self.colors["primary"])

        ctk.CTkLabel(self.log_window, text="📜 Registro",
                     text_color="white", font=("Segoe UI", 16, "bold")).pack(pady=10)

        self.info = ctk.CTkTextbox(self.log_window, font=("Consolas", 11),
                                   fg_color="black", text_color="white", corner_radius=15)
        self.info.pack(fill="both", expand=True, padx=10, pady=10)
        self.info.insert("end", "🎯 Listo para simular.\n")

    def log(self, mensaje):
        if self.info:
            self.info.insert("end", mensaje + "\n")
            self.info.see("end")

    # ----------------------------------------------------
    def crear_tabla_proceso(self, nombre, color, num_paginas):
        frame = ctk.CTkFrame(self.left, fg_color="white", corner_radius=10)
        frame.pack(fill="x", pady=10, padx=15)
        ctk.CTkLabel(frame, text=f"Proceso {nombre}", font=("Segoe UI", 14, "bold"),
                     text_color=color).pack(anchor="center", pady=5)

        rows = []
        for i in range(num_paginas):
            fila = ctk.CTkFrame(frame, fg_color=self.colors["bg"], corner_radius=8)
            fila.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(fila, text=f"{i}", width=30,
                         font=("Consolas", 11, "bold")).pack(side="left", padx=5)
            label = ctk.CTkLabel(fila, text="---", width=50, fg_color=color,
                                 text_color="white", font=("Consolas", 11, "bold"),
                                 corner_radius=6)
            label.pack(side="right", padx=5)
            rows.append(label)
        self.process_tables[nombre] = rows

    def actualizar_tabla(self, nombre, pagina, marco):
        if nombre in self.process_tables and pagina < len(self.process_tables[nombre]):
            self.process_tables[nombre][pagina].configure(text=str(marco))

    # ----------------------------------------------------
    def redibujar_memoria(self, event=None):
        if not hasattr(self, "memoria_actual") or not hasattr(self, "colores_actuales"):
            return

        self.canvas.delete("all")
        marcos = len(self.memoria_actual)
        ancho = self.canvas.winfo_width() - 100
        altura = (self.canvas.winfo_height() - 40) / marcos

        for i, nombre in enumerate(self.memoria_actual):
            y = 20 + i * altura
            color = self.colores_actuales.get(nombre, "white") if nombre else "white"
            self.canvas.create_rectangle(
                50, y, 50 + ancho, y + altura - 2,
                fill=color, outline="#fbbf24" if nombre else "#cbd5e1",
                width=3 if nombre else 1
            )
            self.canvas.create_text(25, y + altura / 2, text=f"M{i}", font=("Segoe UI", 9, "bold"))
            if nombre:
                self.canvas.create_text(50 + ancho / 2, y + altura / 2,
                                        text=f"{nombre}", fill="white", font=("Segoe UI", 12, "bold"))

    # ----------------------------------------------------
    def set_speed(self, val):
        self.speed = float(val)
        if self.speed <= 0.2:
            label, color = "Muy Lenta 🐌", "#dc2626"
        elif self.speed <= 0.4:
            label, color = "Lenta 🚶", "#ea580c"
        elif self.speed <= 0.6:
            label, color = "Normal 🚴", "#15803d"
        elif self.speed <= 0.8:
            label, color = "Rápida 🏃", "#2563eb"
        else:
            label, color = "Muy Rápida 🚀", "#7c3aed"
        self.speed_label.configure(text=label, text_color=color)

    def toggle_pause(self):
        self.paused = not self.paused

    def esperar(self):
        while self.paused:
            self.root.update()
            time.sleep(0.1)

    def iniciar_hilo(self):
        threading.Thread(target=self.simular).start()

    # ----------------------------------------------------
    def simular(self):
        try:
            memoria_total = int(self.memoria_entry.get())
            pagina = int(self.pagina_entry.get())
            procesos_texto = self.procesos_entry.get()
            algoritmo = self.algoritmo_var.get()
        except:
            messagebox.showerror("Error", "Entradas inválidas.")
            return

        procesos = {}
        for parte in procesos_texto.split(","):
            n, t = parte.split("=")
            procesos[n.strip()] = int(t.strip())

        self.page_faults = 0
        marcos = memoria_total // pagina
        self.canvas.delete("all")
        self.memoria_actual = [None] * marcos
        self.colores_actuales = {}

        paleta = ["#4f6caa", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]
        cola_fifo = deque()
        uso_lru = {}
        colores = {}

        # Limpia tablas anteriores
        for widget in self.left.winfo_children()[1:]:
            widget.destroy()
        self.process_tables.clear()

        for i, (nombre, tamaño) in enumerate(procesos.items()):
            color = paleta[i % len(paleta)]
            colores[nombre] = color
            num_paginas = math.ceil(tamaño / pagina)
            self.crear_tabla_proceso(nombre, color, num_paginas)
            self.log(f"🧩 Iniciando proceso {nombre} ({tamaño} KB → {num_paginas} páginas).")

            for p in range(num_paginas):
                self.esperar()
                if None in self.memoria_actual:
                    idx = self.memoria_actual.index(None)
                else:
                    if algoritmo == "FIFO":
                        idx = cola_fifo.popleft()
                    elif algoritmo == "LRU":
                        idx = min(uso_lru, key=uso_lru.get)
                    else:
                        idx = random.randint(0, marcos - 1)
                self.page_faults += 1

                self.memoria_actual[idx] = f"{nombre}{p}"
                cola_fifo.append(idx)
                uso_lru[idx] = time.time()

                self.colores_actuales = {m: colores[m[0]] for m in self.memoria_actual if m}
                self.redibujar_memoria()
                self.actualizar_tabla(nombre, p, idx)
                self.page_fault_label.configure(text=f"💥 Fallos de página: {self.page_faults}")
                self.log(f"➡️ Proceso {nombre} - Página {p} asignada a marco {idx}")
                time.sleep(self.speed)

            self.log(f"✅ Proceso {nombre} completado.\n")

        messagebox.showinfo("Simulación completa", f"Total de fallos de página: {self.page_faults}")
        self.log(f"🏁 Simulación finalizada. Fallos totales: {self.page_faults}")

# ----------------------------------------------------
if __name__ == "__main__":
    root = ctk.CTk()
    app = SimuladorPaginacion(root)
    root.mainloop()
