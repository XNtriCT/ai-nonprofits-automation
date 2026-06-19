import os
import sys
import io
import threading
import tkinter as tk
import requests
from pathlib import Path

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FG = "#1c1c1c"
FG2 = "#242424"
FG3 = "#2e2e2e"
TEXT = "#d4d0c8"
TEXT2 = "#9a948a"
ACCENT = "#8b7d6b"
BORDER = "#3a3a3a"


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


class ModelSelector(ctk.CTkFrame):
    """Model picker — lightweight tk.Listbox popup, no flicker, instant scroll."""

    POPUP_W = 500
    POPUP_H = 560

    def __init__(self, master, values, initial="", on_select=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._all = values
        self._on_select = on_select
        self._selected = initial if initial in values else (values[0] if values else "")
        self._popup = None

        self._entry = ctk.CTkEntry(
            self, font=("Menlo", 10), text_color=TEXT,
            fg_color=FG2, border_color=BORDER, border_width=1, height=30,
        )
        self._entry.insert(0, self._selected)
        self._entry.configure(state="readonly")
        self._entry.grid(row=0, column=0, sticky="ew")
        self._entry.bind("<Button-1>", self._toggle, add="+")

        self._btn = ctk.CTkButton(
            self, text="\u25bc",
            font=("Menlo", 8), text_color=TEXT2,
            fg_color=FG3, hover_color=FG2,
            border_color=BORDER, border_width=1,
            width=28, height=30, command=self._toggle,
        )
        self._btn.grid(row=0, column=1)

    def get(self):
        return self._selected

    def set(self, value):
        if value in self._all or not self._all:
            self._selected = value
            self._entry.configure(state="normal")
            self._entry.delete(0, "end")
            self._entry.insert(0, value)
            self._entry.configure(state="readonly")

    def configure_values(self, values, initial=None):
        self._all = values
        if initial:
            self.set(initial)
        elif self._selected not in values:
            self.set(values[0] if values else "")

    def configure_state(self, state):
        self._entry.configure(state=state if state == "disabled" else "readonly")
        self._btn.configure(state=state)

    def _toggle(self):
        if self._popup and self._popup.winfo_exists():
            self._close()
        else:
            self._open()

    def _open(self):
        if not self._all:
            return

        self._popup = ctk.CTkToplevel(self)
        self._popup.withdraw()
        self._popup.title("")
        self._popup.configure(fg_color=FG2)
        self._popup.attributes("-topmost", True)
        self._popup.transient(self.winfo_toplevel())
        self._popup.resizable(False, False)
        self._popup.protocol("WM_DELETE_WINDOW", self._close)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self._popup.geometry(f"{self.POPUP_W}x{self.POPUP_H}+{x}+{y}")

        frame = tk.Frame(self._popup, bg=FG2)
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        sb = tk.Scrollbar(frame, bg=FG3, troughcolor=FG2,
                          activebackground=ACCENT)
        sb.pack(side="right", fill="y")

        self._lb = tk.Listbox(
            frame,
            yscrollcommand=sb.set,
            bg=FG2, fg=TEXT,
            selectbackground=FG3, selectforeground=TEXT,
            font=("Menlo", 10),
            borderwidth=0, highlightthickness=0,
            activestyle="none",
            exportselection=False,
        )
        self._lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self._lb.yview)

        for val in self._all:
            self._lb.insert("end", val)

        if self._selected in self._all:
            idx = self._all.index(self._selected)
            self._lb.selection_set(idx)
            self._lb.see(idx)

        self._lb.bind("<ButtonRelease-1>", self._on_lb_click)
        self._lb.bind("<Double-Button-1>", self._on_lb_click)
        self._popup.bind("<Escape>", lambda e: self._close())

        self._popup.deiconify()
        self._popup.grab_set()
        self._popup.focus_set()
        self._lb.focus_set()

    def _on_lb_click(self, event):
        sel = self._lb.curselection()
        if sel:
            self._pick(self._all[sel[0]])

    def _pick(self, value):
        self._selected = value
        self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._entry.configure(state="readonly")
        if self._on_select:
            self._on_select(value)
        self._close()

    def _close(self, event=None):
        if self._popup:
            try:
                self._popup.destroy()
            except:
                pass
            self._popup = None



class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI for Nonprofits")
        self.geometry("640x520")
        self.minsize(560, 420)
        self.configure(fg_color=FG)

        self._running = False
        self._stdout_redirected = False

        self._models = []
        self._load_models()

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        header = ctk.CTkLabel(
            self, text="AI FOR NONPROFITS",
            font=("Helvetica", 13, "normal"),
            text_color=TEXT2,
            anchor="w",
        )
        header.grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        line = ctk.CTkFrame(self, height=1, fg_color=BORDER)
        line.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="ew")

        topic_frame = ctk.CTkFrame(self, fg_color="transparent")
        topic_frame.grid(row=2, column=0, padx=24, pady=(0, 8), sticky="ew")
        topic_frame.grid_columnconfigure(1, weight=1)

        topic_label = ctk.CTkLabel(
            topic_frame, text="Topic",
            font=("Helvetica", 11, "normal"),
            text_color=TEXT2,
        )
        topic_label.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="w")

        self.topic_entry = ctk.CTkEntry(
            topic_frame,
            placeholder_text="Leave empty to auto-fetch news",
            fg_color=FG2,
            text_color=TEXT,
            placeholder_text_color=TEXT2,
            border_color=BORDER,
            border_width=1,
            font=("Helvetica", 12),
            height=34,
        )
        self.topic_entry.grid(row=0, column=1, padx=(0, 8), pady=0, sticky="ew")

        self.go_btn = ctk.CTkButton(
            topic_frame, text="Go",
            font=("Helvetica", 11, "normal"),
            text_color=TEXT,
            fg_color=FG3,
            hover_color=FG2,
            border_color=ACCENT,
            border_width=1,
            width=56,
            height=34,
            command=self._on_go,
        )
        self.go_btn.grid(row=0, column=2, padx=0, pady=0)

        note = ctk.CTkLabel(
            self,
            text="Enter a custom news topic to skip news-fetching, or leave empty and click Run below",
            font=("Helvetica", 10, "normal"),
            text_color=TEXT2,
            anchor="w",
        )
        note.grid(row=3, column=0, padx=24, pady=(0, 8), sticky="w")

        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.grid(row=4, column=0, padx=24, pady=(0, 12), sticky="ew")
        model_frame.grid_columnconfigure(1, weight=1)

        model_label = ctk.CTkLabel(
            model_frame, text="Model",
            font=("Helvetica", 11, "normal"),
            text_color=TEXT2,
        )
        model_label.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="w")

        from config import cfg
        current_model = cfg.FREELLMAPI_MODEL

        self.model_selector = ModelSelector(
            model_frame,
            values=self._models if self._models else [current_model],
            initial=current_model,
            on_select=self._on_model_change,
        )
        self.model_selector.grid(row=0, column=1, padx=0, pady=0, sticky="ew")

        self.run_btn = ctk.CTkButton(
            self, text="Run Pipeline",
            font=("Helvetica", 12, "normal"),
            text_color=TEXT,
            fg_color=FG3,
            hover_color=FG2,
            border_color=ACCENT,
            border_width=1,
            height=38,
            command=self._on_run,
        )
        self.run_btn.grid(row=6, column=0, padx=24, pady=(0, 16), sticky="ew")

        log_frame = ctk.CTkFrame(self, fg_color=FG2, border_color=BORDER, border_width=1)
        log_frame.grid(row=7, column=0, padx=24, pady=(0, 20), sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=("Menlo", 10),
            text_color=TEXT,
            fg_color=FG2,
            border_width=0,
            wrap="word",
            state="disabled",
        )
        self.log_text.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self._log("Waiting for you to start...\n")

    def _append_text(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log(self, text):
        self._append_text(text)

    def _load_models(self):
        from config import cfg
        try:
            r = requests.get(f"{cfg.FREELLMAPI_BASE}/models", timeout=10)
            data = r.json()
            ids = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            ids.sort()
            self._models = ids
        except Exception as e:
            print(f"[models] Failed to fetch: {e}")
            self._models = []

    def _on_model_change(self, choice):
        from config import cfg
        cfg.FREELLMAPI_MODEL = choice
        print(f"[models] Set to: {choice}")

    def _set_running(self, running):
        self._running = running
        state = "disabled" if running else "normal"
        self.run_btn.configure(state=state)
        self.go_btn.configure(state=state)
        self.topic_entry.configure(state=state)
        self.model_selector.configure_state(state)
        if running:
            self.run_btn.configure(text="Running...")
        else:
            self.run_btn.configure(text="Run Pipeline")

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

    def _refresh_model_combo(self):
        from config import cfg
        current_model = cfg.FREELLMAPI_MODEL
        model_list = self._models if self._models else [current_model]
        if current_model not in model_list:
            model_list = [current_model] + model_list
        self.model_selector.configure_values(model_list, initial=current_model)

    def _execute(self, topic):
        old_out = sys.stdout
        old_err = sys.stderr
        redirector = LogRedirector(self._append_text)
        sys.stdout = redirector
        sys.stderr = redirector
        self._stdout_redirected = True

        try:
            from main import run_pipeline
            run_pipeline(dry_run=False, custom_topic=topic)
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
