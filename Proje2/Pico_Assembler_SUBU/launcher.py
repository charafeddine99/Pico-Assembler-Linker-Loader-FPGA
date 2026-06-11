import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# ==============================================================================
# ÖNEMLİ: Programın 'src' klasöründeki modülleri bulabilmesi için yol tanımı.
# ==============================================================================
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from assembler_core import PicoAssembler

class PicoStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("Pico-Assembler Professional Studio")
        self.root.geometry("1100x900") 
        
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=('Segoe UI', 10, 'bold'), padding=[10, 5])

        # --- ANA PANEL (Vertical PanedWindow) ---
        self.main_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
        self.main_pane.pack(expand=True, fill='both', padx=10, pady=10)

        # ÜST PANEL: EDİTÖR
        self.upper_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.upper_frame, weight=1)

        self.notebook = ttk.Notebook(self.upper_frame)
        self.notebook.pack(expand=True, fill='both')

        self.tab_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="📝 Kod Düzenleyici")
        self.setup_editor_tab()

        self.tab_file = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_file, text="📂 ASM Dosyası Yükle")
        self.setup_file_tab()

        # ALT PANEL: TERMİNAL
        self.lower_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.lower_frame, weight=2)
        self.setup_output_area()

    def setup_editor_tab(self):
        btn_frame = ttk.Frame(self.tab_editor)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame, text="▶ Derle ve OBJ Üret", command=self.assemble_text).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🧹 Ekranı Temizle", command=lambda: self.editor.delete(1.0, tk.END)).pack(side='left', padx=5)

        self.editor = scrolledtext.ScrolledText(self.tab_editor, font=("Consolas", 12), undo=True, bg="#f8f9fa")
        self.editor.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Hazır şablon
        ornek_kod = """MAIN   CSECT
       EXTDEF RE1
       EXTDEF HALT1
       EXTREF GET42
       EXTREF WRLED
BASLA  JAL x1, GET42    ; Makine Kodu: 0C200000 (Doğru!)
RE1    JAL x1, WRLED    ; Makine Kodu: 0C200000 (Doğru!)
HALT1  JAL x0, HALT1    ; Makine Kodu: 0C000000 (Doğru!)
LOGIC  CSECT
       EXTDEF GET42
       EXTREF RE1
GET42  ADDI x10, x0, 42 ; Makine Kodu: 200A002A (Doğru!)
       JAL x0, RE1      ; RE1 Dışarıda olduğu için 0C000000 (Doğru!)
IODRV  CSECT
       EXTDEF WRLED
       EXTREF HALT1
WRLED  SW x10, 128(x0)  ; Makine Kodu: AC0A0080 (Doğru!)
       JAL x0, HALT1    ; HALT1 Dışarıda olduğu için 0C000000 (Doğru!)"""
        self.editor.insert(tk.INSERT, ornek_kod)

    def setup_file_tab(self):
        frame = ttk.Frame(self.tab_file)
        frame.place(relx=0.5, rely=0.4, anchor='center')
        ttk.Button(frame, text="Dosya Seç ve Derle", command=self.assemble_file, width=25).pack(pady=10)
        self.selected_file_label = ttk.Label(frame, text="Seçili Dosya: Yok", font=('Segoe UI', 10, 'italic'), foreground="gray")
        self.selected_file_label.pack(pady=5)

    def setup_output_area(self):
        output_label_frame = ttk.LabelFrame(self.lower_frame, text=" 📊 Derleme Çıktısı ve Etkileşimli Terminal ")
        output_label_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.output_screen = scrolledtext.ScrolledText(output_label_frame, font=("Consolas", 11), bg="#1e1e1e", fg="#50fa7b", insertbackground="white")
        self.output_screen.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.output_screen.tag_config("system_white", foreground="#ffffff")
        self.output_screen.tag_config("error", foreground="#ff5555")
        self.output_screen.tag_config("success", foreground="#50fa7b")
        self.output_screen.tag_config("header", foreground="#8be9fd", font=("Consolas", 11, "bold"))
        self.output_screen.tag_config("symtab", foreground="#f1fa8c")

    def assemble_text(self):
        source = self.editor.get("1.0", tk.END).strip()
        if source: self.run_process(source)

    def assemble_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Assembly Files", "*.asm;*.s"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.run_process(f.read())

    def run_process(self, source):
        self.output_screen.delete(1.0, tk.END)
        
        # --- GHOST MODÜL ENGELLEYİCİ: Boşlukları ve yorumları temizleyerek böl ---
        chunks = []
        curr = []
        for line in source.splitlines():
            if ("START" in line.upper() or "CSECT" in line.upper()) and curr:
                if any(kw in "\n".join(curr).upper() for kw in ["START", "CSECT"]):
                    chunks.append("\n".join(curr))
                curr = [line]
            else:
                curr.append(line)
        if curr: chunks.append("\n".join(curr))

        # --- ANA DERLEME DÖNGÜSÜ ---
        for i, chunk in enumerate(chunks, 1):
            if not any(kw in chunk.upper() for kw in ["START", "CSECT"]):
                continue

            self.output_screen.insert(tk.END, f"[{i}. MODÜL DERLENİYOR...]\n", "header")
            
            asm = PicoAssembler()
            
            # YENİ: 5 Değeri karşılıyoruz (obj_content eklendi)
            success, msg, listing, symtab, obj_content = asm.assemble(chunk)
            
            if success:
                self.output_screen.insert(tk.END, f"> {msg}\n", "success")
                
                # 1. SYMTAB
                self.output_screen.insert(tk.END, "\n--- SEMBOL TABLOSU (SYMTAB) ---\n", "symtab")
                if symtab:
                    for label, addr in symtab.items():
                        self.output_screen.insert(tk.END, f"{label:<10} : {addr:06X}\n", "symtab")
                else:
                    self.output_screen.insert(tk.END, "Bu modülde yerel etiket yok.\n", "system_white")
                
                # 2. LISTING
                self.output_screen.insert(tk.END, "\n--- DERLEME ÇIKTISI (LISTING) ---\n", "system_white")
                self.output_screen.insert(tk.END, f"{'ADRES':<10} | {'MAKİNE KODU':<15} | {'KAYNAK KOD'}\n", "header")
                for item in listing:
                    addr, code, src_line = item
                    self.output_screen.insert(tk.END, f"{addr:<10} | {code:<15} | {src_line}\n", "system_white")
                
                # 3. YENİ: GERÇEK OBJ DOSYASI İÇERİĞİ EKRANA BASILIYOR
                self.output_screen.insert(tk.END, "\n--- ÜRETİLEN OBJ DOSYASI KAYITLARI ---\n", "header")
                self.output_screen.insert(tk.END, obj_content + "\n", "system_white")
                
                self.output_screen.insert(tk.END, "=" * 75 + "\n\n", "system_white")
            else:
                # KRİTİK HATA DURUMU
                self.output_screen.insert(tk.END, f"> DERLEME DURDURULDU: {msg}\n", "error")
                messagebox.showerror("Derleme Hatası", f"Modül {i} içerisinde hata saptandı:\n\n{msg}\n\nSüreç durduruldu.")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = PicoStudio(root)
    root.mainloop()