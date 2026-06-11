import os

# ==============================================================================
# 5. PICO LINKER CORE
# GERÇEK RV32I / PICORV32 UYUMLU LINKER
# ==============================================================================

class PicoLinker:

    def __init__(self):

        self.estab = {}
        self.prog_map = {}
        self.memory = {}

        self.load_address = 0

    # ==========================================================================
    # PASS 1
    # ==========================================================================
    def pass_one(self, parsed_modules, start_addr=0x0000):

        self.load_address = start_addr

        self.estab.clear()
        self.prog_map.clear()

        current_addr = start_addr

        for mod in parsed_modules:

            mod_name = mod["H"]["name"].strip()
            mod_length = mod["H"]["length"]

            # --------------------------------------------------------------
            # Program map
            # --------------------------------------------------------------
            self.prog_map[mod_name] = {

                "start": current_addr,
                "length": mod_length
            }

            # --------------------------------------------------------------
            # CSECT adı ESTAB'e girer
            # --------------------------------------------------------------
            self.estab[mod_name] = {

                "addr": current_addr,
                "module": mod_name
            }

            # --------------------------------------------------------------
            # EXTDEF
            # --------------------------------------------------------------
            for label, rel_addr in mod["D"].items():

                label = label.strip()

                if label in self.estab:

                    return (
                        False,
                        f"ERROR: Duplicate external symbol: '{label}'"
                    )

                self.estab[label] = {

                    "addr": current_addr + rel_addr,
                    "module": mod_name
                }

            current_addr += mod_length

        return True, "PASS 1 OK"

    # ==========================================================================
    # PASS 2
    # ==========================================================================
    def pass_two(self, parsed_modules):

        self.memory.clear()

        # ==============================================================
        # TEXT RECORDLERİNİ MEMORY'YE YÜKLE
        # ==============================================================
        for mod in parsed_modules:

            mod_name = mod["H"]["name"].strip()
            mod_start = self.prog_map[mod_name]["start"]

            for t_rec in mod["T"]:

                t_start = t_rec["start_addr"]
                code_str = t_rec["code"]

                for i in range(0, len(code_str), 8):

                    word_hex = code_str[i:i + 8]

                    if len(word_hex) != 8:
                        continue

                    global_addr = (
                        mod_start +
                        t_start +
                        (i // 2)
                    )

                    self.memory[global_addr] = word_hex

        # ==============================================================
        # RELOCATION
        # ==============================================================
        for mod in parsed_modules:

            mod_name = mod["H"]["name"].strip()
            mod_start = self.prog_map[mod_name]["start"]

            for m_rec in mod["M"]:

                target_addr = mod_start + m_rec["addr"]

                rtype = m_rec["rtype"]
                symbol = m_rec["symbol"]

                # ------------------------------------------------------
                # Symbol kontrolü
                # ------------------------------------------------------
                if symbol not in self.estab:

                    return (
                        False,
                        f"ERROR: Undefined symbol '{symbol}'"
                    )

                sym_addr = self.estab[symbol]["addr"]

                if target_addr not in self.memory:

                    return (
                        False,
                        f"ERROR: Relocation target missing "
                        f"at {target_addr:06X}"
                    )

                original_code = int(
                    self.memory[target_addr],
                    16
                )

                # ======================================================
                # R_RISCV_JAL
                # ======================================================
                if rtype == "R_RISCV_JAL":

                    opcode = original_code & 0x7F
                    rd = (original_code >> 7) & 0x1F

                    # --------------------------------------------------
                    # PC-relative offset
                    # --------------------------------------------------
                    offset = sym_addr - target_addr

                    # Alignment check
                    if offset % 2 != 0:

                        return (
                            False,
                            f"ERROR: JAL alignment failure "
                            f"for '{symbol}'"
                        )

                    imm = offset & 0x1FFFFF

                    imm_20 = (imm >> 20) & 0x1
                    imm_10_1 = (imm >> 1) & 0x3FF
                    imm_11 = (imm >> 11) & 0x1
                    imm_19_12 = (imm >> 12) & 0xFF

                    patched_code = (

                        (imm_20 << 31) |
                        (imm_10_1 << 21) |
                        (imm_11 << 20) |
                        (imm_19_12 << 12) |
                        (rd << 7) |
                        opcode
                    )

                    self.memory[target_addr] = (
                        f"{patched_code:08X}"
                    )

                else:

                    return (
                        False,
                        f"ERROR: Unsupported relocation type "
                        f"'{rtype}'"
                    )

        return True, "PASS 2 OK"

    # ==========================================================================
    # OUTPUTS
    # ==========================================================================
    def save_outputs(self, build_dir="build"):

        estab_dir = os.path.join(build_dir, "estab")
        output_dir = os.path.join(build_dir, "output")

        os.makedirs(estab_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        estab_path = os.path.join(
            estab_dir,
            "ESTAB.txt"
        )

        mem_path = os.path.join(
            output_dir,
            "output.mem"
        )

        hex_path = os.path.join(
            output_dir,
            "output.hex"
        )

        # ==============================================================
        # ESTAB
        # ==============================================================
        with open(estab_path, "w") as f:

            f.write(
                "EXTERNAL SYMBOL TABLE\n"
            )

            f.write("-" * 60 + "\n")

            f.write(
                f"{'MODULE':<15} "
                f"{'SYMBOL':<15} "
                f"{'ADDRESS'}\n"
            )

            f.write("-" * 60 + "\n")

            for label, data in sorted(
                self.estab.items(),
                key=lambda x: x[1]["addr"]
            ):

                f.write(
                    f"{data['module']:<15} "
                    f"{label:<15} "
                    f"{data['addr']:06X}\n"
                )

        # ==============================================================
        # FPGA MEM OUTPUT (DÜZELTİLDİ)
        # ==============================================================
        with open(mem_path, "w") as f:

            for addr in sorted(self.memory.keys()):

                word = self.memory[addr]

                # Fazladan ters çeviren 'little' silindi, direkt 'word' basılıyor!
                f.write(
                    f"@{addr // 4:04X}\n"
                    f"{word}\n"
                )

        # ==============================================================
        # INTEL HEX (DÜZELTİLDİ)
        # ==============================================================
        with open(hex_path, "w") as f:

            for addr in sorted(self.memory.keys()):

                word = self.memory[addr]

                # 'little' silindi, doğrudan 'word' kullanılıyor
                payload = (
                    f"04"
                    f"{addr:04X}"
                    f"00"
                    f"{word}"
                )

                checksum = (
                    (~sum(bytes.fromhex(payload)) + 1)
                    & 0xFF
                )

                f.write(
                    f":{payload}{checksum:02X}\\n"
                )

            f.write(":00000001FF\n")

        return estab_path, mem_path, hex_path