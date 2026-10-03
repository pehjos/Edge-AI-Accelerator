# Verilog Hardware Validation

This folder contains a first-pass RTL and testbench scaffold for the self-checking RRNS MAC/checker hardware path.

## Current Scope

The current RTL now targets two concrete RRNS configurations:

- `System A`
  - Informative moduli: `(17, 19, 23)`
  - Redundant modulus: `(29)`
- `System B`
  - Informative moduli: `(29, 31, 37)`
  - Redundant modulus: `(41)`

These match the Python-side systems already used in the Chapter Four experiments.

## Files

### RTL

- [rtl/rrns_channel_mac.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/rtl/rrns_channel_mac.sv)
  - Computes one modular MAC channel across a 9-tap window.
- [rtl/rrns_checker_system_a.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/rtl/rrns_checker_system_a.sv)
  - Reconstructs the informative value with CRT and checks the redundant residue.
- [rtl/self_checking_rrns_mac_system_a.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/rtl/self_checking_rrns_mac_system_a.sv)
  - Top-level wrapper that computes the clean residues, allows a faulted codeword override, and runs the checker.
- [rtl/rrns_checker_system_b.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/rtl/rrns_checker_system_b.sv)
  - Reconstructs the informative value for `System B` and checks the redundant residue.
- [rtl/self_checking_rrns_mac_system_b.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/rtl/self_checking_rrns_mac_system_b.sv)
  - Top-level wrapper for the `System B` modulus configuration.

### Testbench

- [tb/tb_self_checking_rrns_mac_system_a.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/tb/tb_self_checking_rrns_mac_system_a.sv)
  - Exercises:
    - a clean single-product MAC case
    - a detected single informative-channel fault
    - a detected single redundant-channel fault
    - a known undetected two-informative-fault limitation case
    - a clean 9-tap multi-product MAC window
- [tb/tb_self_checking_rrns_mac_system_b.sv](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/tb/tb_self_checking_rrns_mac_system_b.sv)
  - Exercises the same pattern for `System B`, including a known undetected two-informative-fault limitation case.

### Run Script

- [run_iverilog.sh](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/run_iverilog.sh)
  - Compiles and runs both `System A` and `System B` testbenches.

## What This Hardware Stage Proves

At this stage, the Verilog side is intended to support:

- functional agreement with the Python RRNS model for both chosen modulus sets
- clean-codeword acceptance
- single-fault detection behavior
- one explicit undetected multi-fault limitation case

This is functional validation, not yet area/power/timing proof.

## How To Run

### In Git Bash

From [rrns_mphil_experiments](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments):

```bash
cd "/c/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments"
bash verilog/run_iverilog.sh
```

### If You Prefer Manual Icarus Commands

```bash
iverilog -g2012 -o verilog/logs/tb_self_checking_rrns_mac_system_a.out \
  verilog/rtl/rrns_channel_mac.sv \
  verilog/rtl/rrns_checker_system_a.sv \
  verilog/rtl/self_checking_rrns_mac_system_a.sv \
  verilog/tb/tb_self_checking_rrns_mac_system_a.sv

vvp verilog/logs/tb_self_checking_rrns_mac_system_a.out | tee verilog/logs/tb_self_checking_rrns_mac_system_a.log

iverilog -g2012 -o verilog/logs/tb_self_checking_rrns_mac_system_b.out \
  verilog/rtl/rrns_channel_mac.sv \
  verilog/rtl/rrns_checker_system_b.sv \
  verilog/rtl/self_checking_rrns_mac_system_b.sv \
  verilog/tb/tb_self_checking_rrns_mac_system_b.sv

vvp verilog/logs/tb_self_checking_rrns_mac_system_b.out | tee verilog/logs/tb_self_checking_rrns_mac_system_b.log
```

## Waveform Evidence

Both testbenches now emit waveform files:

- [waveforms/tb_self_checking_rrns_mac_system_a.vcd](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/waveforms/tb_self_checking_rrns_mac_system_a.vcd)
- [waveforms/tb_self_checking_rrns_mac_system_b.vcd](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/verilog/waveforms/tb_self_checking_rrns_mac_system_b.vcd)

You can open these in GTKWave or another VCD viewer after running the testbenches locally.

## Current Limitation In This Session

No Verilog simulator is installed in the current Codex session, so the RTL could not be executed here yet. The files have been scaffolded and aligned to the Python model, but the next real check must happen in your local toolchain.

## Recommended Next Steps

1. Run the `System A` and `System B` testbenches locally.
2. Inspect the `.log` and `.vcd` files for hardware evidence.
3. Add a sequential MAC version if you want cycle-by-cycle hardware realism.
4. Move into synthesis and timing/resource reports after functional correctness is stable.
