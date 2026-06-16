# -*- coding: utf-8 -*-
"""
GUI version of local blog publisher.
Double-click to run, configure, and publish with one click.

Dependencies: tkinter (built-in Python), plus project scripts.
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class BlogPublisherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Blog Publisher")
        self.root.geometry("640x560")
        self.root.minsize(520, 440)
        self.root.configure(bg="#f5f5f7")

        # Apple-style fonts
        self.font_title = ("Segoe UI", 16, "bold")
        self.font_body = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 9)
        self.font_mono = ("Consolas", 10)

        self.publishing = False
        self._setup_credentials()
        self._build_ui()
        self._log("Ready. Click Publish to start.")

    def _setup_credentials(self):
        """Load credentials quietly."""
        base = os.path.dirname(os.path.abspath(__file__))
        proj = os.path.dirname(base)

        self.creds_ok = True
        self.creds_msg = ""

        # Load .env.local
        env_path = os.path.join(proj, ".env.local")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()

        # Load blogger_tokens.json
        tokens_path = os.path.join(proj, "blogger_tokens.json")
        if not os.path.exists(tokens_path):
            self.creds_ok = False
            self.creds_msg = f"Missing: {tokens_path}"
            return

        with open(tokens_path, "r") as f:
            tokens = json.load(f)

        for key in ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN", "BLOGGER_BLOG_ID"]:
            if key in tokens:
                os.environ[key] = tokens[key]

        missing = []
        for k in ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN", "BLOGGER_BLOG_ID", "DEEPSEEK_API_KEY"]:
            if not os.environ.get(k):
                missing.append(k)

        if missing:
            self.creds_ok = False
            self.creds_msg = f"Missing creds: {', '.join(missing)}"

    # ==================== UI ====================

    def _build_ui(self):
        # --- Top bar ---
        top = tk.Frame(self.root, bg="#ffffff", height=56)
        top.pack(fill="x")
        top.pack_propagate(False)

        title = tk.Label(top, text="AI Blog Publisher", font=self.font_title,
                         fg="#1d1d1f", bg="#ffffff")
        title.pack(side="left", padx=20, pady=12)

        self.status_dot = tk.Canvas(top, width=12, height=12, bg="#ffffff",
                                    highlightthickness=0)
        self.status_dot.pack(side="right", padx=20, pady=12)
        self._draw_status("#34c759")  # green = ready

        # --- Creds warning ---
        if not self.creds_ok:
            warn = tk.Frame(self.root, bg="#fff3cd")
            warn.pack(fill="x", padx=12, pady=(8, 0))
            tk.Label(warn, text=f"[!] {self.creds_msg}",
                     font=self.font_small, fg="#856404", bg="#fff3cd",
                     wraplength=580).pack(padx=10, pady=6)

        # --- Settings panel ---
        panel = tk.LabelFrame(self.root, text="Settings", font=self.font_body,
                              fg="#1d1d1f", bg="#f5f5f7", padx=16, pady=12)
        panel.pack(fill="x", padx=12, pady=(8, 0))

        row = tk.Frame(panel, bg="#f5f5f7")
        row.pack(fill="x")

        # Article count
        tk.Label(row, text="Articles:", font=self.font_body,
                 fg="#1d1d1f", bg="#f5f5f7").pack(side="left")
        self.count_var = tk.IntVar(value=1)
        count_spin = ttk.Spinbox(row, from_=1, to=5, width=5,
                                 textvariable=self.count_var,
                                 font=self.font_body)
        count_spin.pack(side="left", padx=(4, 24))

        # Draft checkbox
        self.draft_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="Save as draft", variable=self.draft_var,
                       font=self.font_body, fg="#1d1d1f", bg="#f5f5f7",
                       selectcolor="#f5f5f7", activebackground="#f5f5f7",
                       ).pack(side="left", padx=(0, 24))

        # Skip images
        self.noimg_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="Skip images", variable=self.noimg_var,
                       font=self.font_body, fg="#1d1d1f", bg="#f5f5f7",
                       selectcolor="#f5f5f7", activebackground="#f5f5f7",
                       ).pack(side="left", padx=(0, 24))

        # No delay
        self.now_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="Publish now", variable=self.now_var,
                       font=self.font_body, fg="#1d1d1f", bg="#f5f5f7",
                       selectcolor="#f5f5f7", activebackground="#f5f5f7",
                       ).pack(side="left")

        # --- Publish button ---
        btn_frame = tk.Frame(self.root, bg="#f5f5f7")
        btn_frame.pack(fill="x", padx=12, pady=(10, 0))

        self.publish_btn = tk.Button(
            btn_frame,
            text="Publish",
            command=self._start_publish,
            font=("Segoe UI", 12, "bold"),
            bg="#0071e3", fg="#ffffff",
            activebackground="#0077ed", activeforeground="#ffffff",
            relief="flat", bd=0, padx=32, pady=8,
            cursor="hand2",
        )
        self.publish_btn.pack()
        self._set_btn_style()

        # --- Log area ---
        log_frame = tk.LabelFrame(self.root, text="Log", font=self.font_body,
                                  fg="#1d1d1f", bg="#f5f5f7", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(10, 12))

        self.log = scrolledtext.ScrolledText(
            log_frame,
            font=self.font_mono,
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="#ffffff",
            relief="flat", bd=0,
            wrap=tk.WORD,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")

        # Configure tags for colored log output
        self.log.tag_configure("ok", foreground="#4ec9b0")
        self.log.tag_configure("err", foreground="#f44747")
        self.log.tag_configure("info", foreground="#569cd6")
        self.log.tag_configure("dim", foreground="#808080")

    def _set_btn_style(self):
        """Apple-style button with rounded corners."""
        self.publish_btn.configure(
            bg="#0071e3", fg="#ffffff",
            activebackground="#0077ed", activeforeground="#ffffff",
        )

    def _draw_status(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline="")

    # ==================== Logging ====================

    def _log(self, text, tag=None):
        self.log.configure(state="normal")
        self.log.insert(tk.END, text + "\n", tag or "")
        self.log.see(tk.END)
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    # ==================== Publishing ====================

    def _start_publish(self):
        if self.publishing:
            return
        if not self.creds_ok:
            messagebox.showerror("Error", self.creds_msg)
            return

        self.publishing = True
        self.publish_btn.configure(text="Publishing...", bg="#86868b",
                                   state="disabled")
        self._draw_status("#ff9500")  # orange = working
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

        thread = threading.Thread(target=self._do_publish, daemon=True)
        thread.start()

    def _do_publish(self):
        try:
            import time
            import random

            count = self.count_var.get()
            is_draft = self.draft_var.get()
            skip_images = self.noimg_var.get()
            no_wait = self.now_var.get()

            # Random delay
            if not no_wait:
                delay = random.randint(60, 300)  # 1-5 min locally
                self._log(f"Natural delay: {delay}s...", "dim")
                time.sleep(delay)

            # Skip images
            if skip_images and "PEXELS_API_KEY" in os.environ:
                del os.environ["PEXELS_API_KEY"]

            from publish_to_blogger import run_pipeline
            results = run_pipeline(count=count, is_draft=is_draft)

            # Show result
            success = sum(1 for r in results if r["success"])
            if success == count:
                self._log(f"\nAll {count} article(s) published!", "ok")
            else:
                self._log(f"\n{success}/{count} published, {count - success} failed", "err")

            # Per-article results
            for r in results:
                status = "OK" if r["success"] else "FAIL"
                self._log(f"  [{status}] {r['title']}",
                          "ok" if r["success"] else "err")
                if r.get("url"):
                    self._log(f"         {r['url']}", "dim")

            self._draw_status("#34c759")  # green

        except Exception as e:
            self._log(f"\nError: {e}", "err")
            self._draw_status("#f44747")  # red

        finally:
            self.publishing = False
            self.publish_btn.configure(text="Publish", bg="#0071e3",
                                       state="normal", cursor="hand2")
            self._set_btn_style()


def main():
    root = tk.Tk()

    # Center window
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w, h = 640, 560
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # Windows taskbar icon
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = BlogPublisherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
