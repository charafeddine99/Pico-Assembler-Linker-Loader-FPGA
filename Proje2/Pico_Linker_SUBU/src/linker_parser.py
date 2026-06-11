# ==============================================================================
# src/linker_parser.py
# OBJ DOSYASI OKUYUCU (PARSER) - PICORV32 / RV32I UYUMLU
# ==============================================================================

class ObjParser:
    """
    PicoAssembler tarafından üretilen:
        H, D, R, T, M, E

    kayıtlarını parse eder.
    """

    @staticmethod
    def parse_obj_file(filepath):

        parsed_data = {
            "H": {},
            "D": {},
            "R": [],
            "T": [],
            "M": [],
            "E": ""
        }

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            for line in lines:

                line = line.strip()

                if not line:
                    continue

                parts = line.split("^")
                record_type = parts[0]

                # ==========================================================
                # HEADER
                # ==========================================================
                if record_type == "H":

                    parsed_data["H"] = {
                        "name": parts[1].strip(),
                        "start_addr": int(parts[2], 16),
                        "length": int(parts[3], 16)
                    }

                # ==========================================================
                # DEFINE
                # ==========================================================
                elif record_type == "D":

                    for i in range(1, len(parts), 2):

                        label = parts[i].strip()
                        addr = int(parts[i + 1], 16)

                        parsed_data["D"][label] = addr

                # ==========================================================
                # REFERENCE
                # ==========================================================
                elif record_type == "R":

                    parsed_data["R"] = [
                        p.strip()
                        for p in parts[1:]
                    ]

                # ==========================================================
                # TEXT
                # ==========================================================
                elif record_type == "T":

                    parsed_data["T"].append({

                        "start_addr": int(parts[1], 16),
                        "length": int(parts[2], 16),
                        "code": parts[3].strip()
                    })

                # ==========================================================
                # MODIFICATION
                # Yeni format:
                #
                # M^000000^R_RISCV_JAL^GET42
                # ==========================================================
                elif record_type == "M":

                    parsed_data["M"].append({

                        "addr": int(parts[1], 16),

                        "rtype": parts[2].strip(),

                        "symbol": parts[3].strip()
                    })

                # ==========================================================
                # END
                # ==========================================================
                elif record_type == "E":

                    parsed_data["E"] = (
                        parts[1].strip()
                        if len(parts) > 1
                        else "000000"
                    )

            return parsed_data

        except Exception:
            return None