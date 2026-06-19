import os
import sys
import io
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from config import cfg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Premium palette (cool indigo/platinum, no gold) ──────────
BG_DEEP = "#07070d"
BG_MID  = "#0a0814"
BG_LITE = "#0e0a1a"
SURFACE   = "#0c0c1e"
SURFACE2  = "#12122a"
SURFACE3  = "#181838"
TEXT      = "#e0e0ee"
TEXT2     = "#8888a0"
TEXT3     = "#505068"
ACCENT    = "#5c6cf0"
ACCENT2   = "#3a48c0"
BORDER    = "#1a1a38"
BORDER2   = "#282850"
INPUT_BG  = "#08081a"

_GRADIENT = ["#07070d", "#090715", "#0b0818", "#0d081a", "#0e081c", "#0c0818", "#0a0714"]

def _draw_gradient(canvas, w, h):
    bands = max(len(_GRADIENT), 2)
    bh = h / bands
    for i, c in enumerate(_GRADIENT):
        canvas.create_rectangle(0, i * bh, w, (i + 1) * bh, fill=c, outline="")

def _draw_blobs(canvas, w, h):
    """Subtle glowing orbs behind glass panels."""
    import math
    spots = [
        (w * 0.15, h * 0.25, 140, "#181848"),
        (w * 0.85, h * 0.55, 180, "#141450"),
        (w * 0.50, h * 0.80, 120, "#101048"),
        (w * 0.75, h * 0.15, 100, "#1a1848"),
    ]
    for cx, cy, r, color in spots:
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

def _glass_panel(parent):
    f = ctk.CTkFrame(parent, fg_color=SURFACE, border_color=BORDER, border_width=1, corner_radius=12)
    return f

def _style_entry(entry):
    entry.configure(fg_color=INPUT_BG, text_color=TEXT, border_color=BORDER,
                    placeholder_text_color=TEXT2, border_width=1)

def _style_btn(btn, accent=False):
    if accent:
        btn.configure(fg_color=ACCENT, text_color="#ffffff", hover_color=ACCENT2,
                      border_color=ACCENT, border_width=0)
    else:
        btn.configure(fg_color=SURFACE2, text_color=TEXT, hover_color=SURFACE3,
                      border_color=BORDER2, border_width=1)

def _deco_line(parent, row, col, padx, pady):
    f = ctk.CTkFrame(parent, height=1, fg_color=BORDER)
    f.grid(row=row, column=col, padx=padx, pady=pady, sticky="ew")
    return f


class LogRedirector(io.StringIO):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, text):
        super().write(text)
        if text.strip():
            self.callback(text)

    def flush(self):
        pass






class ModelDropdown(ctk.CTkFrame):
    """Dropdown with CTkScrollableFrame — mousewheel works natively on the list."""

    def __init__(self, master, **kwargs):
        self._var = kwargs.pop("variable", tk.StringVar())
        super().__init__(master, **kwargs)
        self._values = []
        self._dropdown = None
        self.grid_columnconfigure(0, weight=1)
        self._display = ctk.CTkEntry(
            self, font=("Helvetica", 11),
            fg_color=INPUT_BG, text_color=TEXT,
            border_color=BORDER, border_width=1,
            state="readonly",
        )
        self._display.grid(row=0, column=0, sticky="ew")
        self._display.bind("<Button-1>", self._toggle)
        self._display.bind("<MouseWheel>", self._on_wheel)
        self._display.bind("<Button-4>", self._on_wheel)
        self._display.bind("<Button-5>", self._on_wheel)

        self._btn = ctk.CTkButton(
            self, text="\u25bc", width=34,
            font=("Helvetica", 9),
            fg_color=SURFACE2, text_color=TEXT,
            hover_color=SURFACE3,
            command=self._toggle,
        )
        self._btn.grid(row=0, column=1)

    def _toggle(self, event=None):
        if self._dropdown:
            self._close()
        else:
            self._open()

    def _on_wheel(self, event):
        vals = self._values
        if not vals:
            return
        cur = self._var.get()
        try:
            i = vals.index(cur)
        except ValueError:
            i = -1
        d = -1 if (event.delta > 0 or event.num == 4) else 1
        i = max(0, min(len(vals) - 1, i + d))
        self._var.set(vals[i])
        self._sync_display(vals[i])

    def _open(self):
        if not self._values:
            return
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        h = min(280, len(self._values) * 30 + 8)

        self._dropdown = ctk.CTkToplevel(self)
        self._dropdown.overrideredirect(True)
        self._dropdown.configure(fg_color=SURFACE)
        self._dropdown.geometry(f"{w}x{h}+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(
            self._dropdown,
            fg_color=SURFACE,
            scrollbar_button_color=SURFACE2,
            scrollbar_button_hover_color=SURFACE3,
        )
        scroll.pack(fill="both", expand=True)

        for val in self._values:
            active = (val == self._var.get())
            item = ctk.CTkButton(
                scroll, text=val,
                font=("Helvetica", 11),
                fg_color=SURFACE2 if active else "transparent",
                text_color=TEXT, hover_color=SURFACE2,
                anchor="w",
                command=lambda v=val: self._select(v),
            )
            item.pack(fill="x", padx=4, pady=1)

        self._dropdown.focus_set()
        self._dropdown.bind("<FocusOut>", lambda e: self._close())

    def _select(self, value):
        self._var.set(value)
        self._sync_display(value)
        self._close()

    def _sync_display(self, value):
        self._display.configure(state="normal")
        self._display.delete(0, "end")
        self._display.insert(0, value)
        self._display.configure(state="readonly")

    def _close(self):
        if self._dropdown:
            self._dropdown.destroy()
            self._dropdown = None

    def configure(self, **kwargs):
        if "values" in kwargs:
            self._values = kwargs.pop("values")
        super().configure(**kwargs)

    def cget(self, attr):
        if attr == "values":
            return self._values
        return super().cget(attr)

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(value)
        self._sync_display(value)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI for Nonprofits")
        self.geometry("640x560")
        self.minsize(580, 480)
        self.configure(fg_color=BG_DEEP)

        self._running = False
        self._stdout_redirected = False

        # ── Canvas for gradient + blobs ─────────────────────
        self.bg_canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._on_resize_bg, add="+")
        self.after(50, self._redraw_bg)

        self._build_ui()

        self.after(100, self._refresh_models)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _redraw_bg(self):
        w = self.winfo_width() or 640
        h = self.winfo_height() or 560
        self.bg_canvas.delete("all")
        _draw_gradient(self.bg_canvas, w, h)
        _draw_blobs(self.bg_canvas, w, h)

    def _on_resize_bg(self, event=None):
        self._redraw_bg()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # ── Header ──────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=28, pady=(24, 2), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="AI FOR NONPROFITS",
            font=("Helvetica", 13, "normal"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top, text="/",
            font=("Helvetica", 13, "normal"),
            text_color=TEXT3,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(140, 0))

        ctk.CTkLabel(
            top, text="Automation",
            font=("Helvetica", 13, "normal"),
            text_color=TEXT2,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(154, 0))

        gear_btn = ctk.CTkButton(
            top, text="\u2699",
            font=("Helvetica", 15, "normal"),
            text_color=TEXT2, fg_color="transparent",
            hover_color=SURFACE2, width=32, height=32,
            command=self._on_settings, cursor="hand2",
        )
        gear_btn.grid(row=0, column=1, sticky="e")

        _deco_line(self, 1, 0, 28, (0, 16))

        # ── Topic panel ─────────────────────────────────────
        panel1 = _glass_panel(self)
        panel1.grid(row=2, column=0, padx=28, pady=(0, 8), sticky="ew")
        panel1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel1, text="Topic",
            font=("Helvetica", 10, "normal"),
            text_color=TEXT2,
        ).grid(row=0, column=0, padx=(16, 8), pady=(14, 4), sticky="w")

        self.topic_entry = ctk.CTkEntry(
            panel1,
            placeholder_text="Leave empty to auto-fetch news",
            font=("Helvetica", 12), height=36,
        )
        _style_entry(self.topic_entry)
        self.topic_entry.grid(row=0, column=1, padx=(0, 8), pady=(14, 4), sticky="ew")

        self.go_btn = ctk.CTkButton(
            panel1, text="Go",
            font=("Helvetica", 10, "normal"),
            width=48, height=36, command=self._on_go,
        )
        _style_btn(self.go_btn)
        self.go_btn.grid(row=0, column=2, padx=(0, 16), pady=(14, 4))

        ctk.CTkLabel(
            panel1,
            text="Enter a custom topic or leave empty",
            font=("Helvetica", 10, "normal"),
            text_color=TEXT3,
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="w")

        # ── Logo panel ──────────────────────────────────────
        panel2 = _glass_panel(self)
        panel2.grid(row=3, column=0, padx=28, pady=(0, 8), sticky="ew")
        panel2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel2, text="Logo",
            font=("Helvetica", 10, "normal"),
            text_color=TEXT2,
        ).grid(row=0, column=0, padx=(16, 8), pady=(12, 12), sticky="w")

        self._logo_path = tk.StringVar(value="")
        self.logo_entry = ctk.CTkEntry(
            panel2,
            placeholder_text="Select a logo image (optional)",
            font=("Helvetica", 12), height=36, state="disabled",
        )
        _style_entry(self.logo_entry)
        self.logo_entry.grid(row=0, column=1, padx=(0, 6), pady=(12, 12), sticky="ew")

        def _browse_logo():
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title="Select Logo Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")]
            )
            if path:
                self._logo_path.set(path)
                self.logo_entry.configure(state="normal")
                self.logo_entry.delete(0, "end")
                self.logo_entry.insert(0, path)
                self.logo_entry.configure(state="disabled")

        self.logo_btn = ctk.CTkButton(
            panel2, text="Browse",
            font=("Helvetica", 10, "normal"),
            width=56, height=36, command=_browse_logo,
        )
        _style_btn(self.logo_btn)
        self.logo_btn.grid(row=0, column=2, padx=(0, 6), pady=(12, 12))

        _OPTIONS = ["Bottom Right", "Bottom Left", "Top Right", "Top Left"]
        self.logo_corner_var = tk.StringVar(value="Bottom Right")
        self.logo_corner_menu = ctk.CTkOptionMenu(
            panel2, values=_OPTIONS,
            font=("Helvetica", 10, "normal"),
            text_color=TEXT, fg_color=SURFACE2,
            button_color=SURFACE2, button_hover_color=SURFACE3,
            dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE2, width=120, height=36,
            variable=self.logo_corner_var,
        )
        self.logo_corner_menu.grid(row=0, column=3, padx=(0, 16), pady=(12, 12))

        # ── Model row ───────────────────────────────────────
        model_frame = _glass_panel(self)
        model_frame.grid(row=4, column=0, padx=28, pady=(0, 8), sticky="ew")
        model_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            model_frame, text="Model",
            font=("Helvetica", 10, "normal"),
            text_color=TEXT2,
        ).grid(row=0, column=0, padx=(16, 8), pady=(8, 8), sticky="w")

        self._model_var = tk.StringVar(value="")
        self._model_var.trace_add("write", lambda *_: setattr(cfg, "MODEL", self._model_var.get()))
        self.model_drop = ModelDropdown(model_frame, variable=self._model_var)
        self.model_drop.grid(row=0, column=1, padx=(0, 16), pady=(8, 8), sticky="ew")

        # ── Run button ──────────────────────────────────────
        self.run_btn = ctk.CTkButton(
            self, text="\u25b6  Run Pipeline",
            font=("Helvetica", 12, "normal"),
            height=44,
            command=self._on_run,
            cursor="hand2",
        )
        _style_btn(self.run_btn, accent=True)
        self.run_btn.grid(row=5, column=0, padx=28, pady=(2, 14), sticky="ew")

        # ── Log panel ───────────────────────────────────────
        log_frame = _glass_panel(self)
        log_frame.grid(row=6, column=0, padx=28, pady=(0, 24), sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=("Menlo", 10),
            text_color=TEXT,
            fg_color="transparent",
            border_width=0,
            wrap="word",
            state="disabled",
        )
        self.log_text.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        self._log("Waiting for you to start...\n")

    def _append_text(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log(self, text):
        self._append_text(text)

    _CORNER_MAP = {
        "Bottom Right": "br", "Bottom Left": "bl",
        "Top Right": "tr", "Top Left": "tl",
    }

    def _on_settings(self):
        from api_client import PROVIDER_CONFIGS, DEFAULT_MODELS
        import time as _time

        dlg = ctk.CTkToplevel(self)
        dlg.title("API Settings")
        dlg.geometry("540x400")
        dlg.configure(fg_color=BG_DEEP)
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        panel = ctk.CTkFrame(dlg, fg_color=SURFACE, border_color=BORDER, border_width=1, corner_radius=8)
        panel.pack(fill="both", expand=True, padx=16, pady=14)
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel, text="API Settings",
            font=("Helvetica", 13, "normal"), text_color=TEXT,
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        _deco_line(panel, 1, 0, 16, (0, 6))

        provider_keys = list(PROVIDER_CONFIGS.keys())
        provider_labels = [PROVIDER_CONFIGS[k]["label"] for k in provider_keys]
        label_to_key = {PROVIDER_CONFIGS[k]["label"]: k for k in provider_keys}

        ROW = {"p": 2, "k": 3, "u": 4, "t": 5, "b": 6}
        _col = {"l": 0, "f": 1}

        def _dlg_label(text, r):
            ctk.CTkLabel(panel, text=text, font=("Helvetica", 11),
                         text_color=TEXT2).grid(row=r, column=_col["l"], padx=(16, 8), pady=7, sticky="w")

        _dlg_label("Provider", ROW["p"])
        provider_var = tk.StringVar(value=PROVIDER_CONFIGS.get(cfg.PROVIDER, PROVIDER_CONFIGS["custom"])["label"])
        provider_menu = ctk.CTkOptionMenu(
            panel, values=provider_labels,
            font=("Helvetica", 11), text_color=TEXT, fg_color=SURFACE2,
            button_color=SURFACE2, button_hover_color=SURFACE,
            dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE2, variable=provider_var,
        )
        provider_menu.grid(row=ROW["p"], column=_col["f"], pady=7, sticky="ew")

        _dlg_label("API Key", ROW["k"])
        key_entry = ctk.CTkEntry(panel, font=("Helvetica", 11))
        _style_entry(key_entry)
        key_entry.insert(0, cfg.API_KEY)
        key_entry.grid(row=ROW["k"], column=_col["f"], pady=7, sticky="ew")

        _dlg_label("Base URL", ROW["u"])
        url_entry = ctk.CTkEntry(panel, font=("Helvetica", 11))
        _style_entry(url_entry)
        url_entry.insert(0, cfg.BASE_URL)
        url_entry.grid(row=ROW["u"], column=_col["f"], pady=7, sticky="ew")

        test_btn = ctk.CTkButton(
            panel, text="Test Connection",
            font=("Helvetica", 11, "normal"), height=32,
        )
        _style_btn(test_btn, accent=True)
        test_btn.grid(row=ROW["t"], column=_col["l"], padx=(16, 0), pady=7, sticky="w")

        test_status_var = tk.StringVar(value="")
        test_status_label = ctk.CTkLabel(
            panel, textvariable=test_status_var,
            font=("Helvetica", 10), text_color=TEXT2, anchor="w",
        )
        test_status_label.grid(row=ROW["t"], column=_col["f"], padx=(12, 16), pady=7, sticky="w")

        sep = ctk.CTkFrame(panel, height=1, fg_color=BORDER)
        sep.grid(row=ROW["b"], column=0, columnspan=2, padx=16, pady=(6, 2), sticky="ew")

        # ── helpers ──────────────────────────────────────────

        def _get_pk():
            return label_to_key.get(provider_var.get(), "custom")

        def _get_pcfg():
            return PROVIDER_CONFIGS.get(_get_pk(), PROVIDER_CONFIGS["custom"])

        def _current_base():
            return url_entry.get().strip() or _get_pcfg().get("base_url", "")

        def _current_key():
            return key_entry.get().strip()

        def _fill_defaults(*_):
            pk = _get_pk()
            pcfg = _get_pcfg()
            known_url = pcfg.get("base_url", "")
            if known_url:
                url_entry.delete(0, "end")
                url_entry.insert(0, known_url)
            test_status_var.set("")

        def _test_connection():
            pk = _get_pk()
            pcfg = _get_pcfg()
            base = _current_base()
            key = _current_key()
            model = self.model_var.get() or DEFAULT_MODELS.get(pk, "")

            if not key:
                test_status_var.set("Enter an API key first")
                return

            test_btn.configure(text="Testing...", state="disabled")
            test_status_var.set("Testing...")
            dlg.update()

            try:
                start = _time.time()
                if pcfg.get("sdk") == "google":
                    try:
                        from google import genai
                        client = genai.Client(api_key=key)
                        client.models.generate_content(model=model or "gemini-2.0-flash", contents="Reply OK")
                    except ImportError:
                        import google.generativeai as genai
                        genai.configure(api_key=key)
                        gm = genai.GenerativeModel(model or "gemini-2.0-flash")
                        gm.generate_content("Reply OK")
                else:
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=base or None)
                    client.chat.completions.create(
                        model=model or "gpt-4o",
                        messages=[{"role": "user", "content": "Reply with OK"}],
                        max_tokens=5,
                    )
                elapsed = (_time.time() - start) * 1000
                test_status_var.set(f"\u2713 Connected ({elapsed:.0f}ms)")
            except Exception as e:
                test_status_var.set(f"\u2717 Failed: {e}")
            finally:
                test_btn.configure(text="Test Connection", state="normal")

        # ── wire up ──────────────────────────────────────────

        provider_menu.configure(command=_fill_defaults)
        test_btn.configure(command=_test_connection)
        _fill_defaults()

        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=ROW["b"] + 1, column=0, columnspan=2, pady=(12, 12))

        def _apply():
            cfg.PROVIDER = _get_pk()
            cfg.API_KEY = _current_key()
            cfg.BASE_URL = _current_base()
            dlg.destroy()
            self.after(200, self._refresh_models)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", font=("Helvetica", 11),
                       width=80, command=dlg.destroy)
        _style_btn(cancel_btn)
        cancel_btn.pack(side="right", padx=(6, 0))
        apply_btn = ctk.CTkButton(btn_frame, text="Apply", font=("Helvetica", 11),
                       width=80, command=_apply)
        _style_btn(apply_btn, accent=True)
        apply_btn.pack(side="right", padx=6)

    def _set_running(self, running):
        self._running = running
        state = "disabled" if running else "normal"
        self.run_btn.configure(state=state)
        self.go_btn.configure(state=state)
        self.topic_entry.configure(state=state)
        self.logo_btn.configure(state=state)
        self.logo_corner_menu.configure(state=state)
        self.model_drop._display.configure(state="disabled" if running else "readonly")
        self.model_drop._btn.configure(state=state)
        if running:
            self.run_btn.configure(text="\u25b6  Running...", fg_color=ACCENT2)
        else:
            self.run_btn.configure(text="\u25b6  Run Pipeline")
            _style_btn(self.run_btn, accent=True)

    def _refresh_models(self):
        from api_client import PROVIDER_CONFIGS, DEFAULT_MODELS
        import requests as req

        provider = cfg.PROVIDER
        pcfg = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["custom"])
        _KNOWN = {
            "freellmapi": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "openrouter": ["openai/gpt-oss-120b:free", "google/gemma-4-31b-it:free", "nvidia/nemotron-3-super-120b-a12b:free", "qwen/qwen3-coder:free", "meta-llama/llama-3.3-70b-instruct:free"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct", "mixtral-8x7b-32768", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
            "deepseek": ["deepseek-v4-flash", "deepseek-v4-pro"],
            "google": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
        }
        models = []
        if cfg.BASE_URL and cfg.API_KEY and pcfg.get("sdk") == "openai":
            try:
                print(f"[models] Fetching {cfg.BASE_URL}/models ...")
                resp = req.get(f"{cfg.BASE_URL}/models",
                               headers={"Authorization": f"Bearer {cfg.API_KEY}"}, timeout=10)
                data = resp.json()
                models = sorted(m.get("id", "") for m in data.get("data", []) if m.get("id"))
                print(f"[models] Got {len(models)} live models")
            except Exception as e:
                print(f"[models] Fetch failed: {e} — using presets")
        if not models:
            models = _KNOWN.get(provider, [])
            if models:
                print(f"[models] Using {len(models)} presets for {provider}")
        if not models:
            default = DEFAULT_MODELS.get(provider, "")
            models = [default] if default else [""]
            print(f"[models] Default fallback: {models}")
        self.model_drop.configure(values=models)
        current = self._model_var.get()
        if current not in models:
            self._model_var.set(models[0] if models else "")
        print(f"[models] Active: {self._model_var.get()}")

    def _on_run(self):
        if self._running:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.configure(state="disabled")
        self._set_running(True)
        threading.Thread(target=self._execute, args=(None,), daemon=True).start()

    def _on_go(self):
        if self._running:
            return
        topic = self.topic_entry.get().strip()
        if not topic:
            self._log("Enter a topic first.\n")
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.configure(state="disabled")
        self._set_running(True)
        threading.Thread(target=self._execute, args=(topic,), daemon=True).start()

    def _execute(self, topic):
        old_out = sys.stdout
        old_err = sys.stderr
        redirector = LogRedirector(self._append_text)
        sys.stdout = redirector
        sys.stderr = redirector
        self._stdout_redirected = True

        try:
            from main import run_pipeline
            logo_path = self._logo_path.get() or None
            logo_corner = self._CORNER_MAP.get(self.logo_corner_var.get(), "br")
            run_pipeline(dry_run=False, custom_topic=topic,
                         logo_path=logo_path, logo_corner=logo_corner)
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout = old_out
            sys.stderr = old_err
            self._stdout_redirected = False
            self.after(0, self._set_running, False)
            self.after(0, self._log, "\n--- Done ---\n")

    def _on_close(self):
        import subprocess
        try:
            subprocess.run(["taskkill", "/F", "/IM", "brave.exe"],
                           capture_output=True, timeout=5)
        except Exception:
            pass
        self.destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
