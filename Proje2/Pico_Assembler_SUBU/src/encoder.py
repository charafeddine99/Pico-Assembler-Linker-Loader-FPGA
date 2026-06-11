# ==============================================================================
# encoder.py
# FULL RV32I ENCODER
# ==============================================================================

class Encoder:

    DIRECTIVES = {
        "START",
        "END",
        "CSECT",
        "EXTDEF",
        "EXTREF",
        "WORD",
        "RESW",
        ".TEXT",
        ".DATA",
        ".WORD",
        ".SPACE"
    }

    REGISTERS = {
        f"x{i}": i for i in range(32)
    }

    # ==========================================================================
    # OPCODES
    # ==========================================================================
    OPCODES = {

        "R-TYPE": 0x33,
        "I-TYPE": 0x13,

        "LW": 0x03,
        "SW": 0x23,

        "BRANCH": 0x63,

        "JAL": 0x6F
    }

    # ==========================================================================
    # FUNCT3
    # ==========================================================================
    FUNCT3 = {

        "ADD": 0x0,
        "SUB": 0x0,
        "AND": 0x7,
        "OR": 0x6,
        "XOR": 0x4,

        "ADDI": 0x0,
        "ANDI": 0x7,
        "ORI": 0x6,

        "LW": 0x2,
        "SW": 0x2,

        "BEQ": 0x0,
        "BNE": 0x1
    }

    # ==========================================================================
    # FUNCT7
    # ==========================================================================
    FUNCT7 = {

        "ADD": 0x00,
        "SUB": 0x20,

        "AND": 0x00,
        "OR": 0x00,
        "XOR": 0x00
    }

    # ==========================================================================
    # VALID MNEMONICS
    # ==========================================================================
    VALID_MNEMONICS = {

        "ADD",
        "SUB",
        "AND",
        "OR",
        "XOR",

        "ADDI",
        "ANDI",
        "ORI",

        "LW",
        "SW",

        "BEQ",
        "BNE",

        "JAL"
    }

    # ==========================================================================
    @classmethod
    def is_valid_register(cls, reg):

        return reg in cls.REGISTERS

    # ==========================================================================
    @classmethod
    def is_valid_mnemonic(cls, mnemonic):

        mnemonic = mnemonic.upper()

        return (
            mnemonic in cls.VALID_MNEMONICS or
            mnemonic in cls.DIRECTIVES
        )

    # ==========================================================================
    @classmethod
    def sign_extend(cls, value, bits):

        mask = (1 << bits) - 1
        return value & mask

    # ==========================================================================
    @classmethod
    def get_machine_code(cls, mnemonic, args, is_external=False):

        mnemonic = mnemonic.upper()

        machine_code = 0

        # ======================================================================
        # R-TYPE
        # ======================================================================
        if mnemonic in ["ADD", "SUB", "AND", "OR", "XOR"]:

            opcode = cls.OPCODES["R-TYPE"]

            funct3 = cls.FUNCT3[mnemonic]
            funct7 = cls.FUNCT7[mnemonic]

            rd = cls.REGISTERS.get(args[0], 0)
            rs1 = cls.REGISTERS.get(args[1], 0)
            rs2 = cls.REGISTERS.get(args[2], 0)

            machine_code = (
                (funct7 << 25) |
                (rs2 << 20) |
                (rs1 << 15) |
                (funct3 << 12) |
                (rd << 7) |
                opcode
            )

        # ======================================================================
        # I-TYPE ALU
        # ======================================================================
        elif mnemonic in ["ADDI", "ANDI", "ORI"]:

            opcode = cls.OPCODES["I-TYPE"]

            funct3 = cls.FUNCT3[mnemonic]

            rd = cls.REGISTERS.get(args[0], 0)
            rs1 = cls.REGISTERS.get(args[1], 0)

            imm = 0

            if not is_external:

                imm = int(args[2])

            imm = cls.sign_extend(imm, 12)

            machine_code = (
                (imm << 20) |
                (rs1 << 15) |
                (funct3 << 12) |
                (rd << 7) |
                opcode
            )

        # ======================================================================
        # LW
        # ======================================================================
        elif mnemonic == "LW":

            opcode = cls.OPCODES["LW"]
            funct3 = cls.FUNCT3["LW"]

            rd = cls.REGISTERS.get(args[0], 0)

            rs1 = 0
            imm = 0

            if "(" in args[1]:

                imm_str = args[1].split("(")[0]

                reg_str = (
                    args[1]
                    .split("(")[1]
                    .split(")")[0]
                )

                rs1 = cls.REGISTERS.get(reg_str, 0)

                if not is_external:
                    imm = int(imm_str)

            imm = cls.sign_extend(imm, 12)

            machine_code = (
                (imm << 20) |
                (rs1 << 15) |
                (funct3 << 12) |
                (rd << 7) |
                opcode
            )

        # ======================================================================
        # SW
        # ======================================================================
        elif mnemonic == "SW":

            opcode = cls.OPCODES["SW"]
            funct3 = cls.FUNCT3["SW"]

            rs2 = cls.REGISTERS.get(args[0], 0)

            rs1 = 0
            imm = 0

            if "(" in args[1]:

                imm_str = args[1].split("(")[0]

                reg_str = (
                    args[1]
                    .split("(")[1]
                    .split(")")[0]
                )

                rs1 = cls.REGISTERS.get(reg_str, 0)

                if not is_external:
                    imm = int(imm_str)

            imm = cls.sign_extend(imm, 12)

            imm_11_5 = (imm >> 5) & 0x7F
            imm_4_0 = imm & 0x1F

            machine_code = (
                (imm_11_5 << 25) |
                (rs2 << 20) |
                (rs1 << 15) |
                (funct3 << 12) |
                (imm_4_0 << 7) |
                opcode
            )

        # ======================================================================
        # BRANCH
        # ======================================================================
        elif mnemonic in ["BEQ", "BNE"]:

            opcode = cls.OPCODES["BRANCH"]

            funct3 = cls.FUNCT3[mnemonic]

            rs1 = cls.REGISTERS.get(args[0], 0)
            rs2 = cls.REGISTERS.get(args[1], 0)

            imm = 0

            if not is_external:
                imm = int(args[2])

            imm = cls.sign_extend(imm, 13)

            imm_12 = (imm >> 12) & 0x1
            imm_10_5 = (imm >> 5) & 0x3F
            imm_4_1 = (imm >> 1) & 0xF
            imm_11 = (imm >> 11) & 0x1

            machine_code = (
                (imm_12 << 31) |
                (imm_10_5 << 25) |
                (rs2 << 20) |
                (rs1 << 15) |
                (funct3 << 12) |
                (imm_4_1 << 8) |
                (imm_11 << 7) |
                opcode
            )

        # ======================================================================
        # JAL
        # ======================================================================
        elif mnemonic == "JAL":

            opcode = cls.OPCODES["JAL"]

            rd = cls.REGISTERS.get(args[0], 0)

            imm = 0

            if not is_external:
                imm = int(args[1])

            imm = cls.sign_extend(imm, 21)

            imm_20 = (imm >> 20) & 0x1
            imm_10_1 = (imm >> 1) & 0x3FF
            imm_11 = (imm >> 11) & 0x1
            imm_19_12 = (imm >> 12) & 0xFF

            machine_code = (
                (imm_20 << 31) |
                (imm_10_1 << 21) |
                (imm_11 << 20) |
                (imm_19_12 << 12) |
                (rd << 7) |
                opcode
            )

        return f"{machine_code:08X}"