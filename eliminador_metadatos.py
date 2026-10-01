#!/usr/bin/env python3
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, "limpiar_metadatos.sh")
GIF_PATH = os.path.join(BASE, "metadata_cleanup.gif")

BG = "#02080f"
PANEL = "#06121c"
CYAN = "#00f5d4"
BLUE = "#00a8ff"
GREEN = "#76ff03"
WHITE = "#d9ffff"
MUTED = "#79a9b5"
RED = "#ff3158"
FONT = "DejaVu Sans"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ELIMINADOR DE METADATOS  |  ReconForense")
        self.geometry("1220x760")
        self.minsize(1000, 650)
        self.configure(bg=BG)

        self.file = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value="● SISTEMA ACTIVO")
        self.progress = tk.DoubleVar(value=0)
        self.q = queue.Queue()
        self.worker_running = False
        self.gif_frames = []
        self.gif_index = 0

        self._load_gif()
        self._style()
        self._build()
        self.after(80, self._poll_queue)
        self.after(120, self._animate_gif)

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TProgressbar", troughcolor="#07151e",
                        background=GREEN, bordercolor=CYAN,
                        lightcolor=GREEN, darkcolor=GREEN)

    def _load_gif(self):
        if not os.path.exists(GIF_PATH):
            return
        i = 0
        while True:
            try:
                img = tk.PhotoImage(file=GIF_PATH, format=f"gif -index {i}")
                self.gif_frames.append(img)
                i += 1
            except tk.TclError:
                break

    def _panel(self, parent, title):
        f = tk.Frame(parent, bg=PANEL, highlightbackground=CYAN,
                     highlightcolor=CYAN, highlightthickness=1, bd=0)
        tk.Label(f, text=title, bg=PANEL, fg=CYAN,
                 font=(FONT, 11, "bold")).pack(anchor="w", padx=14, pady=(10,5))
        return f

    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=18, pady=(14,8))
        tk.Label(header, text="◈  ELIMINADOR DE METADATOS",
                 bg=BG, fg=WHITE, font=(FONT, 20, "bold")).pack(side="left")
        tk.Label(header, text="v1.0  |  VIDEO FORENSICS LAB",
                 bg=BG, fg=CYAN, font=(FONT, 10, "bold")).pack(side="left", padx=15)
        tk.Label(header, textvariable=self.status,
                 bg=BG, fg=GREEN, font=(FONT, 10, "bold")).pack(side="right")

        # File selector
        top = self._panel(self, "ARCHIVO SELECCIONADO")
        top.pack(fill="x", padx=18, pady=6)
        row = tk.Frame(top, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(2,12))
        self.entry = tk.Entry(row, textvariable=self.file, bg="#02070c", fg=WHITE,
                              insertbackground=CYAN, relief="flat",
                              font=(FONT, 10))
        self.entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0,8))
        self._button(row, "SELECCIONAR", self.select_file, BLUE).pack(side="left", padx=4)
        self._button(row, "ANALIZAR", self.analyze, GREEN).pack(side="left", padx=4)

        # Main split
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=18, pady=6)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # Metadata
        left = self._panel(main, "METADATOS ENCONTRADOS")
        left.grid(row=0, column=0, sticky="nsew", padx=(0,7))
        self.tree = ttk.Treeview(left, columns=("tag","value"), show="headings", height=18)
        self.tree.heading("tag", text="ETIQUETA")
        self.tree.heading("value", text="VALOR")
        self.tree.column("tag", width=155)
        self.tree.column("value", width=280)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        # Animation
        right = self._panel(main, "ELIMINANDO METADATOS")
        right.grid(row=0, column=1, sticky="nsew", padx=(7,0))
        self.anim_label = tk.Label(right, bg=PANEL, fg=CYAN)
        self.anim_label.pack(fill="both", expand=True, padx=10, pady=8)
        self._set_gif_frame()

        pbrow = tk.Frame(right, bg=PANEL)
        pbrow.pack(fill="x", padx=18, pady=(0,6))
        ttk.Progressbar(pbrow, variable=self.progress, maximum=100).pack(
            side="left", fill="x", expand=True)
        self.pct = tk.Label(pbrow, text="0%", bg=PANEL, fg=GREEN,
                            font=(FONT, 11, "bold"), width=6)
        self.pct.pack(side="left")

        self.msg = tk.Label(right, text="Seleccione un archivo para comenzar.",
                            bg=PANEL, fg=MUTED, font=(FONT, 10))
        self.msg.pack(pady=(0,12))

        # Bottom
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="both", padx=18, pady=(4,14))
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=1)

        logp = self._panel(bottom, "REGISTRO DE ACTIVIDAD")
        logp.grid(row=0, column=0, sticky="nsew", padx=(0,7))
        self.log = tk.Text(logp, height=7, bg="#010509", fg=GREEN,
                           insertbackground=GREEN, relief="flat",
                           font=("DejaVu Sans Mono", 9))
        self.log.pack(fill="both", expand=True, padx=10, pady=8)

        sum_p = self._panel(bottom, "RESUMEN")
        sum_p.grid(row=0, column=1, sticky="nsew", padx=(7,0))
        self.summary = tk.Label(sum_p, text="Metadatos encontrados: 0\n"
                                            "Metadatos eliminados: 0\n"
                                            "Estado: Esperando",
                                justify="left", bg=PANEL, fg=WHITE,
                                font=(FONT, 10), anchor="w")
        self.summary.pack(fill="x", padx=14, pady=8)

        buttons = tk.Frame(sum_p, bg=PANEL)
        buttons.pack(fill="x", padx=10, pady=(0,10))
        self.clean_btn = self._button(buttons, "ELIMINAR METADATOS",
                                       self.clean, GREEN)
        self.clean_btn.pack(side="left", fill="x", expand=True, padx=3)
        self._button(buttons, "CERRAR", self.destroy, RED).pack(
            side="left", fill="x", expand=True, padx=3)

    def _button(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg="#06121c",
                         fg=color, activebackground="#0b2230",
                         activeforeground=WHITE, highlightbackground=color,
                         highlightcolor=color, highlightthickness=1,
                         relief="flat", font=(FONT, 9, "bold"),
                         padx=12, pady=8, cursor="hand2")

    def _set_gif_frame(self):
        if self.gif_frames:
            self.anim_label.configure(image=self.gif_frames[self.gif_index])

    def _animate_gif(self):
        if self.gif_frames:
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            self._set_gif_frame()
        self.after(120, self._animate_gif)

    def _log(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def select_file(self):
        p = filedialog.askopenfilename(
            title="Seleccionar evidencia",
            filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv *.mts *.m2ts"),
                       ("Todos los archivos", "*.*")])
        if p:
            self.file.set(p)
            base, ext = os.path.splitext(p)
            self.output.set(base + "_SIN_METADATOS" + ext)
            self._log("[INFO] Archivo seleccionado: " + p)

    def analyze(self):
        if not self.file.get():
            messagebox.showwarning("Archivo", "Seleccione un archivo primero.")
            return
        self.worker_running = True
        self._log("[INFO] Analizando metadatos con ExifTool...")
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self):
        try:
            r = subprocess.run([BACKEND, "analyze", self.file.get()],
                               capture_output=True, text=True, check=True)
            data = json.loads(r.stdout)[0]
            self.q.put(("metadata", data))
        except Exception as e:
            self.q.put(("error", str(e)))

    def clean(self):
        if self.worker_running:
            return
        if not self.file.get():
            messagebox.showwarning("Archivo", "Seleccione un archivo primero.")
            return

        inp = self.file.get()
        base, ext = os.path.splitext(inp)
        out = self.output.get() or (base + "_SIN_METADATOS" + ext)

        if os.path.abspath(inp) == os.path.abspath(out):
            messagebox.showerror("Salida", "La salida debe ser diferente al original.")
            return

        if os.path.exists(out):
            if not messagebox.askyesno("Archivo existente",
                                       f"¿Sobrescribir?\n{out}"):
                return

        self.worker_running = True
        self.clean_btn.configure(state="disabled")
        self.progress.set(0)
        self.pct.configure(text="0%")
        self.status.set("● ELIMINANDO METADATOS")
        self.msg.configure(text="Procesando evidencia; el original no se modifica.")
        self._log("[INFO] Iniciando limpieza...")
        self.summary.configure(text=self.summary.cget("text").split("Estado:")[0] +
                               "Estado: Eliminando...")

        threading.Thread(target=self._clean_worker, args=(inp,out), daemon=True).start()

    def _clean_worker(self, inp, out):
        # Barra visual durante la operación real. No representa bytes exactos.
        start = time.time()
        proc = subprocess.Popen([BACKEND, "clean", inp, out],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        while proc.poll() is None:
            elapsed = time.time() - start
            p = min(92, 15 + elapsed * 12)
            self.q.put(("progress", p))
            time.sleep(0.15)

        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            self.q.put(("done", out))
        else:
            self.q.put(("error", stderr.strip() or stdout.strip() or
                        "Falló ExifTool."))

    def _poll_queue(self):
        try:
            while True:
                typ, value = self.q.get_nowait()
                if typ == "metadata":
                    self._show_metadata(value)
                elif typ == "progress":
                    self.progress.set(value)
                    self.pct.configure(text=f"{int(value)}%")
                elif typ == "done":
                    self.progress.set(100)
                    self.pct.configure(text="100%")
                    self.status.set("● SISTEMA ACTIVO")
                    self.msg.configure(text="Limpieza completada. Original preservado.")
                    self._log("[OK] Archivo limpio generado: " + value)
                    self.summary.configure(
                        text=self.summary.cget("text").split("Estado:")[0] +
                             "Estado: COMPLETADO\nSalida: " + os.path.basename(value))
                    self.worker_running = False
                    self.clean_btn.configure(state="normal")
                    messagebox.showinfo("Proceso completado",
                                        "Los metadatos soportados por ExifTool "
                                        "fueron procesados.\n\n"
                                        "El archivo original se conservó.")
                elif typ == "error":
                    self.worker_running = False
                    self.clean_btn.configure(state="normal")
                    self.status.set("● ERROR")
                    self._log("[ERROR] " + value)
                    messagebox.showerror("Error", value)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _show_metadata(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        count = 0
        for k, v in data.items():
            if k in ("SourceFile", "ExifToolVersion"):
                continue
            if isinstance(v, (dict,list)):
                v = json.dumps(v, ensure_ascii=False)
            self.tree.insert("", "end", values=(k, str(v)))
            count += 1
        self._log(f"[OK] {count} etiquetas/metadatos encontrados.")
        self.summary.configure(
            text=f"Metadatos encontrados: {count}\n"
                 "Metadatos eliminados: pendiente\n"
                 "Estado: Analizado")
        self.status.set("● ANÁLISIS COMPLETADO")

if __name__ == "__main__":
    App().mainloop()
