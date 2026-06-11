# FPGA-Based UART Loader System with PicoRV32

## Project Overview

This project implements a complete FPGA-based program loading infrastructure using a custom UART Loader architecture and the PicoRV32 RISC-V processor core.

The system enables executable programs generated on a host computer to be transmitted over UART and dynamically loaded into FPGA memory (BRAM). The design integrates both hardware and software components including a custom Host Loader application, UART Receiver, Loader FSM, BRAM memory subsystem, and PicoRV32 processor.

The project demonstrates a practical Hardware-Software Co-Design approach for embedded systems and FPGA-based computing platforms.

---

## Project Objectives

- Develop a UART-based program loading mechanism.
- Implement a custom Loader FSM on FPGA.
- Enable dynamic program transfer from a host computer.
- Verify data integrity using checksum validation.
- Integrate PicoRV32 RISC-V processor with BRAM memory.
- Demonstrate MMIO-based peripheral control.
- Validate the complete toolchain through FPGA implementation.

---

## System Architecture

The system consists of the following components:

### Host Side

- Assembly Program
- Custom Assembler
- Custom Linker
- Host Loader Application
- UART Communication Interface

### FPGA Side

- UART Receiver
- Loader Finite State Machine (FSM)
- Checksum Verification Unit
- BRAM Memory
- PicoRV32 Processor
- MMIO Peripheral Interface

Data Flow:

```text
Assembly Program
        ↓
Assembler
        ↓
Linker
        ↓
output.mem
        ↓
Host Loader
        ↓ UART
FPGA Loader FSM
        ↓
BRAM
        ↓
PicoRV32
        ↓
MMIO Devices




Hardware Requirements
Tang Nano 9K FPGA Board
Gowin FPGA Development Environment
USB-UART Interface
Personal Computer
Software Requirements
FPGA Development
Gowin FPGA Designer
Gowin Programmer
Host Side
Python 3.x
Serial Communication Library (PySerial)



Project/
│
├── src/
│   ├── top.v
│   ├── uart_rx.v
│   ├── loader_fsm.v
│   ├── memory_controller.v
│   └── picorv32.v
│
├── software/
│   ├── assembler
│   ├── linker
│   └── host_loader.py
│
├── build/
│   └── output.mem
│
├── docs/
│   └── Project_Report.pdf
│
└── README.md