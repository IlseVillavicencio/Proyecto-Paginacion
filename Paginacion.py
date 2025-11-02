import customtkinter as ctk
from tkinter import messagebox
import time, math, random, threading
from collections import deque

class SimuladorPaginacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Paginación Avanzado")
        self.root.geometry("1400x900")
        self.root.state("zoomed")

        # --- Estados ---
        self.paused = False
        self.stop_simulation = False
        self.page_faults = 0
        self.speed = 0.3

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
        ctk.CTkLabel(header, text="Simulador de Paginación Avanzado",
                     font=("Segoe UI", 26, "bold"), text_color="white").pack(pady=10)

        # --- CONFIGURACIÓN ---
        config_frame = ctk.CTkFrame(main, fg_color="transparent")
        config_frame.pack(fill="x", pady=10)

        config = ctk.CTkFrame(config_frame, corner_radius=20)
        config.pack(pady=10)
        config_frame.pack_propagate(False)
        config_frame.columnconfigure(0, weight=1)

        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.update_idletasks()
        config.pack(anchor="center")

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

        # --- Panel de visualización ---
        viz = ctk.CTkFrame(self.root, fg_color="transparent")
        viz.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo (registro tipo CMD)
        left = ctk.CTkFrame(viz, fg_color=self.colors["primary"], corner_radius=20)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(left, text="📜 Registro", text_color="white",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
        self.info = ctk.CTkTextbox(left, font=("Consolas", 11), fg_color="black", text_color="white")
        self.info.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel derecho (visualización de memoria)
        right = ctk.CTkFrame(viz, fg_color=self.colors["primary"], corner_radius=20)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(right, text="💾 Memoria", text_color="white",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
        
        # Subframe con fondo blanco y esquinas redondeadas
        canvas_container = ctk.CTkFrame(right, fg_color="white", corner_radius=6)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas dentro del contenedor curvado
        self.canvas = ctk.CTkCanvas(canvas_container,
                                    bg="white",
                                    highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Vincular evento para redibujar al cambiar tamaño
        self.canvas.bind("<Configure>", self.redibujar_memoria)

        # Etiqueta de fallos
        self.page_fault_label = ctk.CTkLabel(main, text="💥 Fallos de página: 0",
                                             font=("Segoe UI", 13, "bold"))
        self.page_fault_label.pack(pady=5)

        self.info.insert("end", "🎯 Listo para simular.\n")

    # ----------------------------------------------------
    def redibujar_memoria(self, event=None):
        """Redibuja el canvas manteniendo colores y texto."""
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
        estado = "⏸️ Pausado" if self.paused else "▶️ Reanudado"
        self.actualizar_info(estado)

    def esperar(self):
        while self.paused:
            self.root.update()
            time.sleep(0.1)

    def iniciar_hilo(self):
        threading.Thread(target=self.simular).start()

    def actualizar_info(self, text):
        self.info.insert("end", text + "\n")
        self.info.see("end")
        self.root.update()

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

        self.canvas.delete("all")
        self.info.delete("1.0", "end")
        self.page_faults = 0

        marcos = memoria_total // pagina
        altura = (self.canvas.winfo_height() - 40) / marcos
        ancho = self.canvas.winfo_width() - 100
        self.root.update()

        colores = {}
        paleta = ["#4f6caa", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]

        memoria = [None] * marcos
        cola_fifo = deque()
        uso_lru = {}

        self.colores_actuales = {}
        self.memoria_actual = memoria.copy()

        self.actualizar_info(f"🚀 Iniciando {algoritmo}\n")

        for i, (nombre, tamaño) in enumerate(procesos.items()):
            color = paleta[i % len(paleta)]
            colores[nombre] = color
            num_paginas = math.ceil(tamaño / pagina)
            self.actualizar_info(f"🧩 {nombre}: {tamaño} KB → {num_paginas} páginas")

            for p in range(num_paginas):
                self.esperar()
                if None in memoria:
                    idx = memoria.index(None)
                else:
                    if algoritmo == "FIFO":
                        idx = cola_fifo.popleft()
                    elif algoritmo == "LRU":
                        idx = min(uso_lru, key=uso_lru.get)
                    else:
                        idx = random.randint(0, marcos - 1)
                self.page_faults += 1

                memoria[idx] = f"{nombre}{p}"
                cola_fifo.append(idx)
                uso_lru[idx] = time.time()

                self.memoria_actual = memoria.copy()
                self.colores_actuales = {m: colores[m[0]] for m in memoria if m}

                self.redibujar_memoria()

                estado = " │ ".join([m if m else "─" for m in memoria])
                self.actualizar_info(f"➡ {nombre}{p} → M{idx}")
                self.actualizar_info(f"   Memoria: [{estado}]")
                self.page_fault_label.configure(text=f"💥 Fallos de página: {self.page_faults}")
                time.sleep(self.speed)

        self.actualizar_info(f"🎉 Finalizado. Total fallos: {self.page_faults}")
        messagebox.showinfo("Simulación completa", f"Total de fallos de página: {self.page_faults}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = SimuladorPaginacion(root)
    root.mainloop()