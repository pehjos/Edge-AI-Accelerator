#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RTL_DIR="$ROOT_DIR/rtl"
TB_DIR="$ROOT_DIR/tb"
LOG_DIR="$ROOT_DIR/logs"
WAVE_DIR="$ROOT_DIR/waveforms"

mkdir -p "$LOG_DIR" "$WAVE_DIR"

if ! command -v iverilog >/dev/null 2>&1; then
  echo "iverilog is not installed or not on PATH."
  echo "Install Icarus Verilog, then rerun this script."
  exit 1
fi

iverilog -g2012 \
  -o "$LOG_DIR/tb_self_checking_rrns_mac_system_a.out" \
  "$RTL_DIR/rrns_channel_mac.sv" \
  "$RTL_DIR/rrns_checker_system_a.sv" \
  "$RTL_DIR/self_checking_rrns_mac_system_a.sv" \
  "$TB_DIR/tb_self_checking_rrns_mac_system_a.sv"

vvp "$LOG_DIR/tb_self_checking_rrns_mac_system_a.out" | tee "$LOG_DIR/tb_self_checking_rrns_mac_system_a.log"

iverilog -g2012 \
  -o "$LOG_DIR/tb_self_checking_rrns_mac_system_b.out" \
  "$RTL_DIR/rrns_channel_mac.sv" \
  "$RTL_DIR/rrns_checker_system_b.sv" \
  "$RTL_DIR/self_checking_rrns_mac_system_b.sv" \
  "$TB_DIR/tb_self_checking_rrns_mac_system_b.sv"

vvp "$LOG_DIR/tb_self_checking_rrns_mac_system_b.out" | tee "$LOG_DIR/tb_self_checking_rrns_mac_system_b.log"
