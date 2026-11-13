# FPGA UART Program Loader for PicoRV32

A complete toolchain that takes a RISC-V assembly program from source code to execution on an FPGA. A custom assembler and linker produce a memory image. A Python host loader sends it over UART. A Verilog loader FSM verifies every packet and writes it into BRAM, then starts a **PicoRV32** RISC-V core on a **Tang Nano 9K**.

> Team project (4 students) for the *System Programming* course (BIL302), Sakarya University of Applied Sciences. The report and a demo video are in `Proje2/`.

## Pipeline

```text
Assembly (.asm) ──► Assembler ──► .obj ──► Linker ──► output.mem
                                                         │
                                         host_loader.py  │  UART 115200 baud
                                                         ▼
                          Tang Nano 9K:  UART RX ─► Loader FSM (XOR checksum) ─► BRAM ─► PicoRV32 ─► LEDs (MMIO)
```

## Features

### Host side (Python)
- **Assembler and linker** with Tkinter GUIs. They support a subset of RV32I (`ADD`, `SUB`, `AND`, `OR`, `XOR`, `ADDI`, `ANDI`, `ORI`, `LW`, `SW`, `BEQ`, `BNE`, `JAL`) and multi-module linking through `EXTDEF`/`EXTREF`, ESTAB and relocation.
- **`host_loader.py`** reads `output.mem`, including its `@address` markers, and builds a 4 KB RAM image. It sends the image as 5-byte packets: 4 data bytes (little-endian) plus 1 XOR checksum byte.
- **`test_uart.py`** is a small interactive serial test.

### FPGA side (Verilog)
- **`uart_rx.v`:** a UART receiver at 115200 baud from the board's 27 MHz clock.
- **Loader FSM in `top.v`:**
  - It assembles 32-bit words and checks the checksum of each packet.
  - Only valid words are written to BRAM.
  - After a period of UART silence (timeout) it releases the CPU from reset.
- **BRAM:** 4 KB, organised as four byte lanes, so byte-wise writes from the CPU (`mem_wstrb`) work.
- **MMIO:** a store to address `0x80` drives the six on-board LEDs.

## Screenshots

<!-- Add a photo of the board or a frame from the demo video here. -->

## Getting started

**Hardware:** Tang Nano 9K board connected over USB (UART).
**Software:** Gowin FPGA Designer and Programmer, Python 3.10+ and `pyserial`.

```bash
git clone https://github.com/charafeddine99/Pico-Assembler-Linker-Loader-FPGA.git
cd Pico-Assembler-Linker-Loader-FPGA/Proje2
pip install pyserial

# 1. Assemble and link (GUIs)
python Pico_Assembler_SUBU/launcher.py
python Pico_Linker_SUBU/launcher.py      # writes build/output/output.mem

# 2. Synthesize Pico_Linker_SUBU/FPGA/*.v in Gowin and program the board.
#    Pin constraints: tangnano9k.cst

# 3. Send the program (set PORT in host_loader.py to your COM port first)
python host_loader.py
```

## Project structure

```text
Proje2/
├── Pico_Assembler_SUBU/      # assembler: GUI launcher + src/
├── Pico_Linker_SUBU/
│   ├── src/                  # linker core and object parser
│   └── FPGA/                 # top.v (loader FSM, BRAM, MMIO), uart_rx.v, picorv32.v, tangnano9k.cst
├── host_loader.py            # UART program loader
├── test_uart.py              # serial test utility
├── README.txt                # original project notes
└── BIL302_PROJE3_*.pdf/.mp4  # report and demo video
```

## Related

[riscv-assembler-linker](https://github.com/charafeddine99/riscv-assembler-linker) is the previous project. It covers the assembler and linker on their own, plus Verilog simulation.

## Credits

The PicoRV32 core (`picorv32.v`) is by Claire Xenia Wolf ([YosysHQ/picorv32](https://github.com/YosysHQ/picorv32)), under the ISC license.

## License

[MIT](LICENSE). This covers the project's own code.
