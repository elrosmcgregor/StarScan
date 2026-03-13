import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
from pathlib import Path
from typing import Dict, Optional

class RSSignatureDecoder:
    """
    A compact, draggable overlay GUI for decoding Star Citizen mining radar signatures.
    Matches input RS value to material from CSV (single material multiples only, no combinations).
    Data loaded from 'Ressources.csv' with semicolon separator.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Signatures RS")
        self.root.geometry("100x80")
        self.root.configure(bg="#1a1a1a")
        self.root.overrideredirect(True)  # Remove window borders for custom title bar
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.lift()
        self.root.geometry("+0+0")
        
        self.materials: Dict[str, int] = {}
        self.csv_path = Path("Ressources.csv")
        
        self._load_data()
        self._create_title_bar()
        self._setup_ui()
    
    def _create_title_bar(self) -> None:
        """Creates draggable title bar with close button."""
        self.title_bar = tk.Frame(self.root, bg="#1a1a1a", height=14)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        
        self.close_btn = tk.Button(
            self.title_bar, 
            text="✕", 
            command=self.on_closing,
            bg="#d32f2f", 
            fg="white", 
            font=("Arial", 8, "bold"),
            width=2, 
            height=1, 
            bd=1, 
            relief="raised",
            highlightbackground="#d32f2f", 
            activebackground="#b71c1c",
            cursor="hand2"
        )
        self.close_btn.pack(side="left", padx=0)
        
        # Bind drag events to title bar
        self.title_bar.bind("<Button-1>", self._drag_start)
        self.title_bar.bind("<B1-Motion>", self._drag_motion)
    
    def _drag_start(self, event: tk.Event) -> None:
        """Capture mouse position for dragging."""
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _drag_motion(self, event: tk.Event) -> None:
        """Update window position during drag."""
        deltax = event.x_root - self._drag_x
        deltay = event.y_root - self._drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{int(x)}+{int(y)}")
    
    def _load_data(self) -> None:
        """Load material signatures from CSV. Skips invalid files/rows."""
        if not self.csv_path.exists():
            return
        try:
            df = pd.read_csv(self.csv_path, sep=';', dtype='Int64', on_bad_lines='skip')
            # Extract first valid positive value per column as material signature
            self.materials = {
                col: int(pd.to_numeric(df[col], errors='coerce').dropna().iloc[0])
                for col in df.columns 
                if len(df[col].dropna()) > 0 and pd.to_numeric(df[col].dropna().iloc[0], errors='coerce') > 0
            }
        except Exception:
            pass  # Silently fail on load errors
    
    def _setup_ui(self) -> None:
        """Setup input entry and result labels."""
        main_frame = tk.Frame(self.root, bg="#1a1a1a")
        main_frame.pack(fill="both", expand=True, padx=3, pady=0)
        
        # Input: RS label and entry
        input_frame = tk.Frame(main_frame, bg="#1a1a1a")
        input_frame.pack(fill="x")
        
        tk.Label(
            input_frame, 
            text="  RS:", 
            font=("Segoe UI", 9, "bold"), 
            fg="#00ff00", 
            bg="#1a1a1a"
        ).pack(side="left", padx=(0, 1))
        
        self.entry = tk.Entry(
            input_frame, 
            font=("Consolas", 8), 
            width=5, 
            justify="center",
            bg="#333333", 
            fg="#ffffff", 
            insertbackground="#ffffff", 
            relief="flat", 
            bd=1
        )
        self.entry.pack(side="left", pady=0)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus()
        
        # Results labels
        self.result_label = tk.Label(
            main_frame, 
            text="", 
            font=("Segoe UI", 8, "bold"), 
            fg="#00ff00", 
            bg="#1a1a1a"
        )
        self.result_label.pack(pady=0, fill="x")
        
        self.qty_label = tk.Label(
            main_frame, 
            text="", 
            font=("Segoe UI", 8, "bold"), 
            fg="#00ff00", 
            bg="#1a1a1a"
        )
        self.qty_label.pack(pady=0, fill="x")
    
    def _on_enter(self, event: Optional[tk.Event] = None) -> None:
        """Validate input and start decoding in thread."""
        try:
            target = int(self.entry.get().strip())
            if target <= 0:
                return
        except ValueError:
            return
        
        # Clear previous results
        self.result_label.config(text="")
        self.qty_label.config(text="")
        
        # Run decode in daemon thread to avoid blocking UI
        threading.Thread(target=self._decode, args=(target,), daemon=True).start()
    
    def _decode(self, target: int) -> None:
        """Find matching material where target % signature == 0."""
        for name, signature in self.materials.items():
            if target % signature == 0:
                qty = target // signature
                self.root.after(0, lambda n=name, q=qty: self._show_result(n, q))
                return
        self.root.after(0, self._show_none)
    
    def _show_result(self, name: str, qty: int) -> None:
        """Display material name and quantity."""
        self.result_label.config(text=name)
        self.qty_label.config(text=f"{qty}x roches" if qty > 1 else "")
    
    def _show_none(self) -> None:
        """Display no match."""
        self.result_label.config(text="❌")
        self.qty_label.config(text="")
    
    def on_closing(self) -> None:
        """Clean shutdown."""
        self.root.quit()
        self.root.destroy()
    
    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = RSSignatureDecoder()
    app.run()
