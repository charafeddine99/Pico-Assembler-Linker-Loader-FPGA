# ==============================================================================
# hata_yonetimi.py
# ==============================================================================

class AssemblerError(Exception):

    def __init__(self, line_num, message):

        self.line_num = line_num

        self.message = (
            f"Hata (Satır {line_num}): {message}"
        )

        super().__init__(self.message)