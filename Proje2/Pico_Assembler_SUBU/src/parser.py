# ==============================================================================
# parser.py
# ==============================================================================

import re
from encoder import Encoder


class Parser:

    @staticmethod
    def parse_line(line):

        line = line.split(";")[0].strip()

        if not line:
            return None, None, []

        parts = re.split(r'[\s,]+', line)

        label = None
        mnemonic = None
        args = []

        check_cmd = parts[0].upper()

        is_mnemonic = Encoder.is_valid_mnemonic(check_cmd)

        if not is_mnemonic:

            label = parts[0]

            if len(parts) > 1:

                mnemonic = parts[1].upper()
                args = parts[2:]

        else:

            mnemonic = parts[0].upper()
            args = parts[1:]

        return label, mnemonic, args