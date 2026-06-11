import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# 'src' klasöründeki modülleri tanıtıyoruz
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from linker_parser import ObjParser
from linker_core import PicoLinker

class LinkerStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("Pico-Linker Pro: Smart Dependency Resolver")
        self.root.geometry("900x750")
        
        self.selected_files = [] # Kullanıcının seçtiği dosyalar
        self.setup_ui()

    def setup_ui(self):
        top_frame = ttk.LabelFrame(self.root, text=" 📂 Object Files & Smart Linking ")
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(top_frame, text="Add .obj Files", command=self.add_files).pack(side="left", padx=5, pady=10)
        ttk.Button(top_frame, text="Clear List", command=self.clear_list).pack(side="left", padx=5, pady=10)
        
        ttk.Label(top_frame, text="Start Addr (Hex):").pack(side="left", padx=5)
        self.addr_entry = ttk.Entry(top_frame, width=10)
        self.addr_entry.insert(0, "0000")
        self.addr_entry.pack(side="left", padx=5)

        ttk.Button(top_frame, text="⚡ Smart Link", command=self.start_linking).pack(side="right", padx=10)

        self.file_listbox = tk.Listbox(self.root, height=6, font=("Consolas", 10))
        self.file_listbox.pack(fill="x", padx=10, pady=5)

        self.terminal = scrolledtext.ScrolledText(self.root, bg="#1e1e1e", fg="#f8f8f2", font=("Consolas", 11))
        self.terminal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.terminal.tag_config("green", foreground="#50fa7b")
        self.terminal.tag_config("cyan", foreground="#8be9fd")
        self.terminal.tag_config("yellow", foreground="#f1fa8c")
        self.terminal.tag_config("error", foreground="#ff5555")

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Object Files", "*.obj;*.o")])
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.file_listbox.insert(tk.END, os.path.basename(f))

    def clear_list(self):
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.terminal.delete(1.0, tk.END)

    def log(self, text, tag=None):
        self.terminal.insert(tk.END, text + "\n", tag)
        self.terminal.see(tk.END)

    def start_linking(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please add at least one .obj file!")
            return

        try:
            start_addr = int(self.addr_entry.get(), 16)
        except:
            messagebox.showerror("Error", "Invalid hex address!")
            return

        self.terminal.delete(1.0, tk.END)
        self.log(">>> SMART LINKING PROCESS STARTED...", "cyan")

        # 1. Başlangıç Dosyalarını Yükle
        final_list = list(self.selected_files)
        current_parsed = []
        for f in final_list:
            data = ObjParser.parse_obj_file(f)
            if data: current_parsed.append(data)

        # 2. OTOMATİK ARAMA MANTIĞI (Auto-Discovery)
        search_dir = os.path.dirname(self.selected_files[0])
        candidate_files = [os.path.join(search_dir, f) for f in os.listdir(search_dir) 
                           if (f.endswith(".obj") or f.endswith(".o")) and os.path.join(search_dir, f) not in final_list]

        self.log(f"> Checking dependencies in: {search_dir}")

        while True:
            needed_symbols = set()
            for mod in current_parsed:
                for ref in mod.get("R", []):
                    needed_symbols.add(ref)

            defined_symbols = set()
            for mod in current_parsed:
                for def_label in mod.get("D", {}).keys():
                    defined_symbols.add(def_label)

            missing = needed_symbols - defined_symbols
            if not missing:
                break 

            self.log(f"> Missing dependencies: {list(missing)}", "yellow")
            
            found_any = False
            for cand_path in list(candidate_files):
                cand_data = ObjParser.parse_obj_file(cand_path)
                if not cand_data: continue
                
                cand_defines = set(cand_data.get("D", {}).keys())
                if cand_defines & missing:
                    self.log(f"[AUTO-FOUND] Adding '{os.path.basename(cand_path)}' to satisfy requirements.", "green")
                    final_list.append(cand_path)
                    current_parsed.append(cand_data)
                    candidate_files.remove(cand_path)
                    self.file_listbox.insert(tk.END, f" {os.path.basename(cand_path)} (Auto-Added)")
                    found_any = True
                    break 
            
            if not found_any:
                self.log(f"CRITICAL: Could not find providers for: {list(missing)}", "error")
                messagebox.showerror("Error", f"Missing symbols could not be resolved: {missing}")
                return

        # 3. LINKER ÇEKİRDEĞİNİ ÇALIŞTIR (Dosya Kilidi Korumalı)
        try:
            linker = PicoLinker()
            s1, m1 = linker.pass_one(current_parsed, start_addr)
            if not s1:
                self.log(m1, "error")
                return
            
            s2, m2 = linker.pass_two(current_parsed)
            if not s2:
                self.log(m2, "error")
                return

            e_p, m_p, h_p = linker.save_outputs()
            self.log("\n--- SMART LINKING SUCCESSFUL ---", "green")
            self.log(f"ESTAB Preview:\n", "cyan")
            with open(e_p, "r") as ef:
                self.log(ef.read())

            messagebox.showinfo("Success", "Linking complete with auto-resolved dependencies!")
            
        except PermissionError:
            self.log("\n[ERROR] Windows Dosya İzni Hatası (WinError 5)", "error")
            messagebox.showerror("Dosya Kilitli", "Arka planda output.mem veya ESTAB.txt açık kalmış. Lütfen kapatın!")
        except Exception as e:
            import traceback
            self.log(f"\n[CRITICAL ERROR]\n{traceback.format_exc()}", "error")
            messagebox.showerror("Sistem Hatası", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = LinkerStudio(root)
    root.mainloop()