# RRNS MPhil Experiments

This project provides a clean, reproducible Python and Verilog workspace for MPhil thesis experiments on a self-checking redundant residue number system (RRNS) MAC/checker for quantized fixed-point convolution-layer operations in Edge AI hardware accelerators.

No thesis results are pre-populated or assumed. Every table, figure, log, waveform, and raw output is generated only when the experiment scripts or Verilog testbenches are run.

## Project Layout

```text
rrns_mphil_experiments/
|-- README.md
|-- requirements.txt
|-- src/
|   |-- config.py
|   |-- convolution.py
|   |-- fault_injection.py
|   |-- hardware_metrics.py
|   |-- metrics.py
|   |-- plotting.py
|   |-- quantization.py
|   |-- rns.py
|   `-- rrns_checker.py
|-- experiments/
|   |-- 01_quantization_experiment.py
|   |-- 02_clean_rns_equivalence.py
|   |-- 03_rrns_fault_injection.py
|   |-- 04_false_positive_test.py
|   |-- 05_generate_tables_and_figures.py
|   `-- 06_verilog_hardware_evaluation.py
|-- results/
|   |-- figures/
|   |-- logs/
|   |-- raw_outputs/
|   `-- tables/
`-- verilog/
    |-- logs/
    |-- rtl/
    |-- tb/
    `-- waveforms/
```

## What The Code Covers

- Fixed-point quantization and dequantization
- Integer-domain convolution for quantized feature maps and kernels
- RNS encoding and CRT reconstruction
- Balanced signed decoding for signed integer recovery
- RRNS codeword checking with a redundant modulus
- Fault injection into integers and residue channels
- Error and detection-metric calculation
- Verilog-oriented hardware metrics derived from validated RTL systems
- Experiment scripts that save raw outputs, summary tables, figures, and logs for Chapter Four

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running The Python Experiments

Run from the project root:

```bash
python experiments/01_quantization_experiment.py
python experiments/02_clean_rns_equivalence.py
python experiments/03_rrns_fault_injection.py
python experiments/04_false_positive_test.py
python experiments/06_verilog_hardware_evaluation.py
python experiments/05_generate_tables_and_figures.py
```

`06_verilog_hardware_evaluation.py` reads the existing Verilog simulation logs and waveform files and converts them into thesis-style hardware-validation tables and figures.

The scripts write their outputs into:

- `results/raw_outputs/`
- `results/tables/`
- `results/figures/`
- `results/logs/`

## Running The Verilog Validation

From the project root in an environment where `iverilog` and `vvp` are available:

```bash
bash verilog/run_iverilog.sh
```

This generates:

- simulation logs in `verilog/logs/`
- waveform files in `verilog/waveforms/`

## Notes

- The convolution implementation follows the standard deep-learning cross-correlation convention.
- RRNS experiments choose a residue system large enough for the measured accumulator range in the generated workload.
- The Verilog stage currently provides functional hardware validation, not full synthesis, power, area, or timing closure.
