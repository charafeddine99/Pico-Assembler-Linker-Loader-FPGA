# ==============================================================================
# assembler_core.py
# FULL RELOCATION DESTEKLİ GELİŞMİŞ RV32I ASSEMBLER CORE
# ==============================================================================

import os
from hata_yonetimi import AssemblerError
from encoder import Encoder
from parser import Parser


class PicoAssembler:
    def __init__(self):

        # ----------------------------
        # SYMBOL / EXTERNAL TABLES
        # ----------------------------
        self.symtab = {}

        self.extdef = {}
        self.extref = []

        # ----------------------------
        # PROGRAM INFO
        # ----------------------------
        self.program_name = "UNTITLED"
        self.start_address = 0
        self.length = 0

        # ----------------------------
        # OBJECT FILE RECORDS
        # ----------------------------
        self.records = {
            "H": "",
            "D": "",
            "R": "",
            "T": [],
            "M": [],
            "E": ""
        }

        self.listing_data = []

    # ==========================================================================
    # MAIN ASSEMBLE PROCESS
    # ==========================================================================
    def assemble(self, source_code, build_dir="build"):

        lines = source_code.splitlines()
        self.listing_data = []

        try:

            # ----------------------------------------------------------
            # PASS 1
            # ----------------------------------------------------------
            parsed_data = self._pass_one(lines)

            # ----------------------------------------------------------
            # EXTDEF CHECK
            # ----------------------------------------------------------
            for def_label in self.extdef.keys():

                if def_label not in self.symtab:
                    raise AssemblerError(
                        "EXTDEF",
                        f"'{def_label}' etiketi modülde tanımlanmamış!"
                    )

            # ----------------------------------------------------------
            # PASS 2
            # ----------------------------------------------------------
            self._pass_two(parsed_data)

            # ----------------------------------------------------------
            # OUTPUT DIRS
            # ----------------------------------------------------------
            symtab_dir = os.path.join(build_dir, "symtablar")
            obj_dir = os.path.join(build_dir, "objeler")

            os.makedirs(symtab_dir, exist_ok=True)
            os.makedirs(obj_dir, exist_ok=True)

            # ----------------------------------------------------------
            # SAVE SYMTAB
            # ----------------------------------------------------------
            self._save_symtab(
                os.path.join(
                    symtab_dir,
                    f"{self.program_name}_symtab.txt"
                )
            )

            # ----------------------------------------------------------
            # GENERATE OBJECT FILE
            # ----------------------------------------------------------
            obj_content = self._generate_object_file()

            obj_path = os.path.join(
                obj_dir,
                f"{self.program_name}.obj"
            )

            with open(obj_path, "w") as f:
                f.write(obj_content)

            return (
                True,
                f"{self.program_name}.obj başarıyla üretildi.",
                self.listing_data,
                self.symtab,
                obj_content
            )

        except AssemblerError as e:

            return (
                False,
                str(e.message),
                [],
                {},
                ""
            )

        except Exception as e:

            return (
                False,
                f"Sistem Hatası: {str(e)}",
                [],
                {},
                ""
            )

    # ==========================================================================
    # PASS ONE
    # ==========================================================================
    def _pass_one(self, lines):

        locctr = 0
        parsed_data = []

        for line_num, line in enumerate(lines, 1):

            label, mnemonic, args = Parser.parse_line(line)

            if not mnemonic and not label:
                continue

            # ==========================================================
            # START / CSECT
            # ==========================================================
            if mnemonic in ["START", "CSECT"]:

                self.program_name = label if label else "PROG"

                if mnemonic == "START":

                    if not args:
                        raise AssemblerError(
                            line_num,
                            "START direktifi adres bekliyor!"
                        )

                    if args[0].startswith("-"):
                        raise AssemblerError(
                            line_num,
                            "Başlangıç adresi negatif olamaz!"
                        )

                    if len(args[0]) > 6:
                        raise AssemblerError(
                            line_num,
                            f"Adres taşması (Maks 6 Hex): {args[0]}"
                        )

                    try:

                        self.start_address = int(args[0], 16)
                        locctr = self.start_address

                    except ValueError:

                        raise AssemblerError(
                            line_num,
                            "START adresi Hex formatında olmalıdır!"
                        )

                continue

            # ==========================================================
            # EXTDEF / EXTREF
            # ==========================================================
            if mnemonic in ["EXTDEF", "EXTREF"]:

                if not args:
                    raise AssemblerError(
                        line_num,
                        f"{mnemonic} yanında en az bir etiket olmalı!"
                    )

                for arg in args:

                    if len(arg) > 6:
                        raise AssemblerError(
                            line_num,
                            f"Dış etiket çok uzun (Maks 6): {arg}"
                        )

                    if mnemonic == "EXTDEF":

                        if arg in self.extdef:
                            raise AssemblerError(
                                line_num,
                                f"'{arg}' zaten EXTDEF yapılmış!"
                            )

                        self.extdef[arg] = 0

                    else:

                        if arg in self.extref:
                            raise AssemblerError(
                                line_num,
                                f"'{arg}' zaten EXTREF yapılmış!"
                            )

                        self.extref.append(arg)

                continue

            # ==========================================================
            # LABEL DEFINITION
            # ==========================================================
            if label:

                if len(label) > 6:
                    raise AssemblerError(
                        line_num,
                        f"Etiket çok uzun: {label}"
                    )

                if label in self.symtab:
                    raise AssemblerError(
                        line_num,
                        f"Mükerrer etiket tanımlaması: {label}"
                    )

                self.symtab[label] = locctr

            # ==========================================================
            # MNEMONIC CHECK
            # ==========================================================
            if mnemonic and not Encoder.is_valid_mnemonic(mnemonic):

                raise AssemblerError(
                    line_num,
                    f"Geçersiz komut saptandı: {mnemonic}"
                )

            parsed_data.append(
                (
                    line_num,
                    locctr,
                    label,
                    mnemonic,
                    args,
                    line
                )
            )

            # ==========================================================
            # LOCATION COUNTER
            # ==========================================================
            if mnemonic not in Encoder.DIRECTIVES or mnemonic == "WORD":
                locctr += 4

        self.length = locctr - self.start_address

        return parsed_data

    # ==========================================================================
    # PASS TWO
    # ==========================================================================
    def _pass_two(self, parsed_data):

        current_t_record = ""
        t_record_start = -1
        t_record_length = 0

        for (
            line_num,
            loc,
            label,
            mnemonic,
            args,
            original_line
        ) in parsed_data:

            # ----------------------------------------------------------
            # DIRECTIVES
            # ----------------------------------------------------------
            if not mnemonic or mnemonic in Encoder.DIRECTIVES:

                self.listing_data.append(
                    (
                        f"{loc:06X}",
                        "",
                        original_line.strip()
                    )
                )

                continue

            # ----------------------------------------------------------
            # RELOCATION FLAGS
            # ----------------------------------------------------------
            is_external = False

            encoded_args = []

            relocation_type = None

            # ----------------------------------------------------------
            # ARGUMENT PROCESSING
            # ----------------------------------------------------------
            for arg in args:

                clean_arg = arg

                # ------------------------------------------------------
                # MEM FORMAT
                # 128(x0)
                # ------------------------------------------------------
                if "(" in arg and ")" in arg:

                    before_paren = arg.split("(")[0]

                    if before_paren.strip():

                        clean_arg = before_paren

                # ------------------------------------------------------
                # EXTERNAL SYMBOL
                # ------------------------------------------------------
                if clean_arg in self.extref:

                    is_external = True

                    # --------------------------------------------------
                    # RV32I RELOCATION TYPES
                    # --------------------------------------------------
                    if mnemonic == "JAL":

                        relocation_type = "R_RISCV_JAL"

                    elif mnemonic in ["BEQ", "BNE"]:

                        relocation_type = "R_RISCV_BRANCH"

                    elif mnemonic in ["LW", "SW", "ADDI", "ANDI", "ORI"]:

                        relocation_type = "R_RISCV_LO12"

                    else:

                        relocation_type = "R_RISCV_32"

                    self.records["M"].append(
                        f"M^{loc:06X}^{relocation_type}^{clean_arg}"
                    )

                    encoded_args.append(arg)

                # ------------------------------------------------------
                # INTERNAL SYMBOL
                # ------------------------------------------------------
                elif clean_arg in self.symtab:

                    symbol_addr = self.symtab[clean_arg]

                    # JAL / BRANCH => PC RELATIVE
                    if mnemonic in ["JAL", "BEQ", "BNE"]:

                        rel_offset = symbol_addr - loc

                        encoded_args.append(
                            arg.replace(clean_arg, str(rel_offset))
                        )

                    else:

                        encoded_args.append(
                            arg.replace(clean_arg, str(symbol_addr))
                        )

                # ------------------------------------------------------
                # REGISTER
                # ------------------------------------------------------
                elif clean_arg.startswith("x"):

                    if not Encoder.is_valid_register(clean_arg):

                        raise AssemblerError(
                            line_num,
                            f"Geçersiz register: {clean_arg}"
                        )

                    encoded_args.append(arg)

                # ------------------------------------------------------
                # NUMERIC
                # ------------------------------------------------------
                elif clean_arg.lstrip("-").isdigit():

                    encoded_args.append(arg)

                # ------------------------------------------------------
                # UNDEFINED
                # ------------------------------------------------------
                else:

                    raise AssemblerError(
                        line_num,
                        f"Tanımsız etiket çağrısı: {clean_arg}"
                    )

            # ----------------------------------------------------------
            # MACHINE CODE
            # ----------------------------------------------------------
            obj_code = Encoder.get_machine_code(
                mnemonic,
                encoded_args,
                is_external
            )

            self.listing_data.append(
                (
                    f"{loc:06X}",
                    obj_code,
                    original_line.strip()
                )
            )

            # ----------------------------------------------------------
            # TEXT RECORD
            # ----------------------------------------------------------
            if t_record_start == -1:
                t_record_start = loc

            if t_record_length + 4 > 30:

                self.records["T"].append(
                    f"T^{t_record_start:06X}^{t_record_length:02X}^{current_t_record}"
                )

                t_record_start = loc
                current_t_record = ""
                t_record_length = 0

            current_t_record += obj_code
            t_record_length += 4

        # --------------------------------------------------------------
        # FINAL T RECORD
        # --------------------------------------------------------------
        if current_t_record:

            self.records["T"].append(
                f"T^{t_record_start:06X}^{t_record_length:02X}^{current_t_record}"
            )

        # --------------------------------------------------------------
        # HEADER
        # --------------------------------------------------------------
        self.records["H"] = (
            f"H^{self.program_name.ljust(6)[:6]}"
            f"^{self.start_address:06X}"
            f"^{self.length:06X}"
        )

        # --------------------------------------------------------------
        # DEFINE
        # --------------------------------------------------------------
        if self.extdef:

            d_parts = []

            for lbl in self.extdef:

                d_parts.append(
                    f"{lbl.ljust(6)[:6]}"
                    f"^{self.symtab.get(lbl,0):06X}"
                )

            self.records["D"] = "D^" + "^".join(d_parts)

        # --------------------------------------------------------------
        # REFERENCE
        # --------------------------------------------------------------
        if self.extref:

            self.records["R"] = (
                "R^" +
                "^".join(
                    [lbl.ljust(6)[:6] for lbl in self.extref]
                )
            )

        # --------------------------------------------------------------
        # END
        # --------------------------------------------------------------
        self.records["E"] = f"E^{self.start_address:06X}"

    # ==========================================================================
    # OBJECT FILE GENERATOR
    # ==========================================================================
    def _generate_object_file(self):

        content = [self.records["H"]]

        if self.records["D"]:
            content.append(self.records["D"])

        if self.records["R"]:
            content.append(self.records["R"])

        content.extend(self.records["T"])
        content.extend(self.records["M"])

        content.append(self.records["E"])

        return "\n".join(content)

    # ==========================================================================
    # SAVE SYMBOL TABLE
    # ==========================================================================
    def _save_symtab(self, path):

        with open(path, "w") as f:

            f.write(
                f"PROJE: {self.program_name}\n"
                f"ETIKET\t\tADRES\n"
                + "-" * 25 + "\n"
            )

            for k, v in self.symtab.items():

                f.write(
                    f"{k.ljust(10)}\t{v:06X}\n"
                )