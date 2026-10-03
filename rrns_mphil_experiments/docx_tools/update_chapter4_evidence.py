from __future__ import annotations

import csv
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Inches
from docx.text.paragraph import Paragraph


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
OUTPUT_DIR = PROJECT_ROOT / "docx_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_DOCX = Path(r"C:\Users\PehAttaJoseph\Downloads\MPhil_Thesis_Compilation_Working_Draft_v1.docx")
OUTPUT_DOCX = OUTPUT_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_chapter4_evidence_update.docx"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt_percent(value: str | float, digits: int = 2) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def fmt_float(value: str | float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    style = paragraph.style
    paragraph.clear()
    paragraph.style = style
    paragraph.add_run(text)


def insert_paragraph_after(paragraph: Paragraph, text: str = "", style=None) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style is not None:
        new_para.style = style
    if text:
        new_para.add_run(text)
    return new_para


def insert_figure_after(paragraph: Paragraph, image_path: Path, width_inches: float = 6.2) -> Paragraph:
    figure_para = insert_paragraph_after(paragraph)
    figure_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = figure_para.add_run()
    run.add_picture(str(image_path), width=Inches(width_inches))
    return figure_para


def resize_table(table, rows_needed: int, cols_needed: int) -> None:
    while len(table.rows) < rows_needed:
        table.add_row()
    while len(table.rows) > rows_needed:
        table._tbl.remove(table.rows[-1]._tr)
    if len(table.columns) != cols_needed:
        raise ValueError(f"Expected {cols_needed} columns but found {len(table.columns)}.")


def fill_table(table, rows: list[list[str]]) -> None:
    resize_table(table, len(rows), len(rows[0]))
    for r_idx, row in enumerate(rows):
        for c_idx, value in enumerate(row):
            table.cell(r_idx, c_idx).text = value


def main() -> None:
    shutil.copy2(SOURCE_DOCX, OUTPUT_DOCX)
    doc = Document(OUTPUT_DOCX)
    paragraphs = list(doc.paragraphs)
    tables = list(doc.tables)

    quant_rows = read_csv(TABLES_DIR / "01_quantization_summary.csv")
    clean_rows = read_csv(TABLES_DIR / "02_clean_rns_equivalence_summary.csv")
    fault_rows = read_csv(TABLES_DIR / "03_rrns_fault_injection_summary.csv")
    fp_rows = read_csv(TABLES_DIR / "04_false_positive_test_summary.csv")
    hw_rows = read_csv(TABLES_DIR / "06_verilog_hardware_evaluation_summary.csv")

    fault_overall = [row for row in fault_rows if row["Fault Pattern"] == "Overall"]
    fp_overall = [row for row in fp_rows if row["Validation Regime"] == "Overall"]

    total_clean_outputs = sum(int(row["Number of Outputs"]) for row in clean_rows)
    min_range_margin = min(int(row["Range Margin"]) for row in clean_rows)
    max_observed_output = max(int(row["Observed Max |Output|"]) for row in clean_rows)
    total_fault_trials = sum(int(row["Trials"]) for row in fault_overall)
    total_detected = sum(int(row["Detected Faults"]) for row in fault_overall)
    total_harmful_undetected = sum(int(row["Harmful Undetected Faults"]) for row in fault_overall)

    # Section text updates
    set_paragraph_text(
        paragraphs[407],
        "This chapter presents the consolidated Python and Verilog evidence for the conventional quantized fixed-point baseline, the residue-domain reconstruction flow, and the proposed self-checking RRNS MAC/checker. The results are organised around quantization accuracy, clean-case exact equivalence, dynamic-range sufficiency, fault-detection behaviour, false-positive screening, structural redundancy overhead, and RTL functional verification.",
    )
    set_paragraph_text(paragraphs[409], "Table 4.1\nChapter Four experimental configuration summary")
    set_paragraph_text(
        paragraphs[410],
        "The Python study covered four representative convolution workloads, spanning 141 clean output values across Q4.4, Q5.5, Q6.6, and Q7.5 formats. Two RRNS systems were exercised: System A, RRNS(17, 19, 23)+(29), and System B, RRNS(29, 31, 37)+(41). Fault evaluation used five residue-level fault patterns with 240 trials per pattern per system, while the Verilog stage validated both RTL systems with five directed testbench cases each.",
    )
    set_paragraph_text(
        paragraphs[412],
        "The quantization experiment now provides the missing floating-point reference evidence. Across the tested formats, the dequantized response remained tightly aligned with the original floating-point values, with RMSE values of 0.0166 for Q4.4, 0.0083 for Q5.5, and 0.0042 for Q6.6. The corresponding mean absolute errors were 0.0134, 0.0069, and 0.0035 respectively, with no clipped samples reported in the generated benchmark. This confirms that the numerical baseline entering the residue-domain experiments is already a well-controlled low-error approximation of the floating-point convolution reference.",
    )
    set_paragraph_text(
        paragraphs[414],
        f"Clean RRNS reconstruction remained exact across all four representative workloads. In total, {total_clean_outputs} clean output values were evaluated, and every RRNS reconstruction matched the conventional quantized fixed-point output exactly while every checker decision remained valid. The clean exact-match rate and clean checker-acceptance rate were therefore both 100% for every test case.",
    )
    set_paragraph_text(paragraphs[417], "Figure 4.2\nClean RRNS reconstruction across representative convolution workloads\nNote. The left panel compares the observed maximum output magnitude with the balanced signed limit for each workload, while the right panel confirms exact reconstruction and checker validity for all four clean test cases.")
    set_paragraph_text(
        paragraphs[419],
        "Dynamic-range verification was completed against the actual RRNS systems selected for the workloads. System A, RRNS(17, 19, 23)+(29), provides an informative dynamic range of 7429 and a balanced signed limit of ±3714; it was used for TC1, TC2, and TC4. System B, RRNS(29, 31, 37)+(41), provides a dynamic range of 33263 and a balanced signed limit of ±16631; it was used for TC3. The largest observed clean output magnitude across all workloads was 14489 in TC3, which still remained 2142 counts below the System B boundary, while the smallest recorded margin across the study was 761 counts in TC4 under System A.",
    )
    set_paragraph_text(
        paragraphs[420],
        f"These margins show that the residue systems were not merely mathematically valid but also comfortably safe for the evaluated workloads. None of the clean test cases approached the balanced signed boundary closely enough to risk ambiguity in signed decoding, and the minimum observed margin of {min_range_margin} confirms that the exact-equivalence result was obtained without range overflow.",
    )
    set_paragraph_text(
        paragraphs[423],
        f"The RRNS fault-injection campaign covered {total_fault_trials} residue-level injections across two systems and five fault patterns. Single informative-channel faults and single redundant-channel faults were detected in every tested case. When the fault model was extended to harder multi-channel corruptions, detection remained high but was no longer perfect: System A achieved an overall detection rate of {fmt_percent(fault_overall[0]['Detection Rate'])}, while System B achieved {fmt_percent(fault_overall[1]['Detection Rate'])}. Harmful undetected outcomes were therefore observed only in the harder multi-channel patterns.",
    )
    set_paragraph_text(
        paragraphs[424],
        "This outcome is more realistic and more defensible than a universal-coverage claim. The checker is very strong for the tested single-channel faults, but the experiments also document the residual exposure that remains under selected multi-channel corruptions.",
    )
    set_paragraph_text(
        paragraphs[426],
        f"False-positive evaluation was completed explicitly on clean RRNS codewords. System A accepted all 7,940 tested clean codewords and System B accepted all 33,774 tested clean codewords, yielding zero false positives in every validation regime and an overall false-positive rate of 0.00% for both systems.",
    )
    set_paragraph_text(paragraphs[427], "4.6.1 Detection by Fault Pattern and RRNS System")
    set_paragraph_text(paragraphs[428], "Table 4.5\nFault detection and output error by fault pattern")
    set_paragraph_text(paragraphs[430], "Figure 4.3\nRRNS checker behaviour under single- and multi-channel fault patterns\nNote. Single-channel faults were detected in every tested case for both systems, whereas the multi-channel patterns expose the non-zero harmful-undetected rates reported in the right-hand panel.")
    set_paragraph_text(paragraphs[432], "Figure 4.4\nFalse-positive validation of the RRNS checker on clean codewords\nNote. No false positives were observed in any validation regime for either RRNS system, while the right-hand panel shows the much larger clean-codeword coverage achieved when the full balanced signed range is exercised.")
    set_paragraph_text(
        paragraphs[433],
        "The detection profiles show the expected asymmetry between easy and hard fault classes. Single informative-channel faults and single redundant-channel faults were always detected, but multi-channel patterns could alias to another valid RRNS codeword. This is why the harmful-undetected rate becomes visible only once two channels are corrupted simultaneously.",
    )
    set_paragraph_text(paragraphs[434], "4.6.2 False-Positive Validation on Clean Codewords")
    set_paragraph_text(
        paragraphs[435],
        "False-positive screening was performed under three clean-codeword regimes for each system: 500 random interior values, 11 signed-edge values, and the full balanced signed range. Every clean codeword was accepted in all three regimes. This result is important because it shows that the checker does not create spurious alarms when the residue tuple is valid and in range.",
    )
    set_paragraph_text(
        paragraphs[436],
        "The full-range validation is especially useful for the thesis because it tests not only a random subset but the entire admissible signed payload space for each system. The absence of false positives across 7,429 clean values for System A and 33,263 clean values for System B supports the practical usability of the checker in clean operation.",
    )
    set_paragraph_text(
        paragraphs[438],
        f"The numerical consequence of a detected or undetected fault depends strongly on the system and pattern. Across all injected faults, the mean absolute reconstructed-output error was 1791.9742 for System A and 8153.2358 for System B, with maximum absolute errors of 6308 and 28675 respectively. These averages include redundant-channel faults, which are detected but leave the informative reconstruction unchanged.",
    )
    set_paragraph_text(
        paragraphs[439],
        f"The undetected-fault population is no longer empty in the updated experiments. Harmful undetected rates reached 4.17% for System A under informative-plus-redundant faults, 4.58% for System B under two informative-channel faults, and lower but non-zero values for the other hard multi-channel patterns. Consequently, the checker should be presented as a high-coverage detection mechanism rather than a universal guarantee against every multi-channel residue corruption.",
    )
    set_paragraph_text(
        paragraphs[441],
        "The structural overhead is modest but measurable. Both validated RRNS systems add one redundant channel to three informative channels, corresponding to a 33.33% channel-count overhead. In residue-bit terms, System A expands from 15 informative bits to 20 total residue bits, a 33.33% overhead, whereas System B expands from 16 informative bits to 22 total residue bits, a 37.50% overhead. These figures quantify representation cost without overstating them as physical area or power results.",
    )
    set_paragraph_text(
        paragraphs[445],
        "The Verilog stage is now supported by independently executed simulation evidence rather than arithmetic expectation alone. Both System A and System B were compiled and run in Icarus Verilog, each with five directed testbench cases covering a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault limitation case, and a clean multi-tap MAC window. Each RTL system recorded 20 PASS checks, zero FAIL checks, and an available VCD waveform dump.",
    )
    set_paragraph_text(paragraphs[446], "Table 4.7\nObserved Verilog functional-verification summary")
    set_paragraph_text(
        paragraphs[447],
        "The RTL results therefore support the Python findings at the functional hardware level. They confirm clean-case correctness, fault-flag behaviour for detected cases, and the existence of a known undetected multi-channel limitation case in both validated residue systems. The evidence remains functional rather than synthesis-level: no FPGA resource, timing, or power measurements are claimed.",
    )
    set_paragraph_text(
        paragraphs[451],
        "The exact clean equivalence observed in the updated Python experiments remains consistent with the mathematical expectation that residue-domain multiplication and addition preserve the quantized fixed-point result when the informative dynamic range is sufficient. The contribution here is narrower than a full accelerator claim, but stronger than a purely conceptual proposal because the equivalence is now shown across four representative workloads and two concrete RRNS systems.",
    )
    set_paragraph_text(
        paragraphs[452],
        "The fault results also align with the self-checking motivation in the prior work, but the updated evidence adds an important nuance: the checker achieved 100% detection for the tested single-channel faults while still exhibiting non-zero harmful-undetected rates under some multi-channel patterns. This is a more credible and research-useful result than an unqualified statement of universal detection.",
    )
    set_paragraph_text(
        paragraphs[453],
        "The Verilog evidence now complements the Python model in a way that the earlier draft could not. The same self-checking concept has been exercised at both the algorithmic level and the RTL functional level, which strengthens the thesis claim that the proposed RRNS checker is relevant to Edge AI hardware accelerator arithmetic rather than being only a software abstraction.",
    )
    set_paragraph_text(paragraphs[458], "•\tThe study evaluates quantized fixed-point arithmetic and checker behaviour, but not end-to-end neural-network accuracy or application-level inference quality.")
    set_paragraph_text(paragraphs[459], "•\tThe clean-codeword false-positive rate was reduced to zero in the tested regimes, but this evidence is still bounded to the two validated RRNS systems and the implemented balanced signed checker.")
    set_paragraph_text(paragraphs[460], "•\tThe Verilog evidence is now functionally observed rather than provisional, but it remains limited to directed simulation and does not yet include synthesis, physical timing, or device-level implementation.")
    set_paragraph_text(
        paragraphs[464],
        "The completed Chapter Four evidence now addresses the research gap more directly. The study provides empirical support for quantized fixed-point baseline behaviour, exact clean RRNS equivalence, explicit dynamic-range sufficiency, high-coverage fault detection with documented multi-channel limitations, zero false positives on tested clean codewords, and functionally validated RTL behaviour for two RRNS hardware configurations.",
    )
    set_paragraph_text(
        paragraphs[465],
        "What remains outside the current gap closure is synthesis-level hardware evaluation. The thesis can therefore claim correctness, self-checking behaviour, and functional hardware validation for the targeted convolution-layer MAC/checker component, but not full accelerator implementation metrics such as LUT count, clock frequency, power, energy, or thermal behaviour.",
    )
    set_paragraph_text(
        paragraphs[467],
        f"Chapter Four now shows that the quantized fixed-point baseline introduces only small numerical approximation error, that clean RRNS reconstruction remained exact across {total_clean_outputs} outputs and four representative workloads, and that the validated RRNS systems preserved comfortable dynamic-range margins with a minimum observed margin of {min_range_margin}. The self-checking RRNS checker detected every tested single-channel fault, achieved overall detection rates of {fmt_percent(fault_overall[0]['Detection Rate'])} and {fmt_percent(fault_overall[1]['Detection Rate'])} for Systems A and B respectively, recorded zero false positives across 41,714 tested clean codewords, and was functionally verified in Verilog with two independently executed RTL systems. These results support the thesis claim at the component and functional-hardware levels while keeping the interpretation honestly bounded away from unmeasured synthesis or power claims.",
    )
    set_paragraph_text(paragraphs[468], "")

    # Figures
    quant_caption = insert_paragraph_after(
        paragraphs[412],
        "Figure 4.1\nQuantization precision and reconstruction accuracy\nNote. Dequantized responses for Q4.4, Q5.5, and Q6.6 stay close to the floating-point reference line, and the annotated RMSE and mean absolute error values decrease as the fractional precision increases.",
        style=paragraphs[417].style,
    )
    insert_figure_after(quant_caption, FIGURES_DIR / "01_quantization_scatter.png")
    insert_figure_after(paragraphs[417], FIGURES_DIR / "02_clean_rns_equivalence_stress_summary.png")
    insert_figure_after(paragraphs[430], FIGURES_DIR / "03_rrns_fault_injection_detection_profiles.png")
    insert_figure_after(paragraphs[432], FIGURES_DIR / "04_false_positive_test_profiles.png")

    hw_caption = insert_paragraph_after(
        paragraphs[447],
        "Figure 4.5\nVerilog hardware evaluation of the self-checking RRNS MAC/checker\nNote. The left panel summarizes the informative and total residue-bit widths of the two validated RTL systems, while the right panel shows that both simulations passed all directed checks with moderate structural redundancy overhead.",
        style=paragraphs[417].style,
    )
    insert_figure_after(hw_caption, FIGURES_DIR / "06_verilog_hardware_evaluation_summary.png")

    # Table updates
    fill_table(
        tables[31],
        [
            ["Parameter", "Verified value"],
            ["Random seed", "7"],
            ["Convolution workloads", "4 representative workloads (TC1-TC4)"],
            ["Feature-map sizes", "6x6, 8x8, 9x9, and 10x10"],
            ["Kernel sizes", "3x3 and 5x5"],
            ["Fixed-point formats", "Q4.4, Q5.5, Q6.6, and Q7.5"],
            ["RRNS systems", "System A: RRNS(17, 19, 23)+(29); System B: RRNS(29, 31, 37)+(41)"],
            ["Clean outputs checked", str(total_clean_outputs)],
            ["Fault patterns", "5 residue-level patterns, 240 trials per pattern per system"],
            ["Total fault injections", str(total_fault_trials)],
            ["False-positive regimes", "Random interior, signed-edge, and full balanced range"],
            ["Clean codewords tested", "41,714 across both systems"],
            ["Verilog validation", "2 RTL systems, 5 cases each, 20 PASS and 0 FAIL per system"],
        ],
    )

    fill_table(
        tables[32],
        [
            ["Case", "Workload", "RRNS system", "Exact match rate", "Checker acceptance rate"],
            ["TC1", "Small workload (Q4.4)", "System A", "100.00%", "100.00%"],
            ["TC2", "Medium workload (Q5.5)", "System A", "100.00%", "100.00%"],
            ["TC3", "Large-kernel workload (Q6.6)", "System B", "100.00%", "100.00%"],
            ["TC4", "Near-range stress workload (Q7.5)", "System A", "100.00%", "100.00%"],
        ],
    )

    fill_table(
        tables[33],
        [
            ["Measure", "Result"],
            ["System A informative moduli", "{17, 19, 23}"],
            ["System A balanced signed limit", "±3714"],
            ["System A largest observed |output|", "2953"],
            ["System A minimum range margin", "761"],
            ["System B informative moduli", "{29, 31, 37}"],
            ["System B balanced signed limit", "±16631"],
            ["System B largest observed |output|", str(max_observed_output)],
            ["System B minimum range margin", "2142"],
        ],
    )

    fill_table(
        tables[34],
        [
            ["Metric", "Result"],
            ["System A total injected faults", "1200"],
            ["System A detected faults", f"1175 ({fmt_percent(fault_overall[0]['Detection Rate'])})"],
            ["System A harmful undetected faults", f"25 ({fmt_percent(fault_overall[0]['Harmful Undetected Rate'])})"],
            ["System A maximum absolute output error", "6308"],
            ["System B total injected faults", "1200"],
            ["System B detected faults", f"1182 ({fmt_percent(fault_overall[1]['Detection Rate'])})"],
            ["System B harmful undetected faults", f"18 ({fmt_percent(fault_overall[1]['Harmful Undetected Rate'])})"],
            ["System B maximum absolute output error", "28675"],
        ],
    )

    fill_table(
        tables[35],
        [
            [
                "Fault pattern",
                "System A detection",
                "System B detection",
                "System A harmful undetected",
                "System B harmful undetected",
                "System A mean |error|",
                "System B mean |error|",
            ],
            ["Single informative-channel fault", "100.00%", "100.00%", "0.00%", "0.00%", "2249.30", "11109.46"],
            ["Single redundant-channel fault", "100.00%", "100.00%", "0.00%", "0.00%", "0.00", "0.00"],
            ["Two informative-channel faults", "95.83%", "95.42%", "4.17%", "4.58%", "2084.39", "9304.54"],
            ["Informative + redundant fault", "95.83%", "98.33%", "4.17%", "1.67%", "2290.97", "10875.48"],
            ["Two-channel mixed fault", "97.92%", "98.75%", "2.08%", "1.25%", "2335.22", "9476.70"],
        ],
    )

    fill_table(
        tables[36],
        [
            ["Measure", "Result", "Interpretation"],
            ["System A channel overhead", "33.33%", "1 redundant channel added to 3 informative channels"],
            ["System A residue-bit overhead", "33.33%", "15 informative bits expanded to 20 total residue bits"],
            ["System A coding efficiency", "64.29%", "Payload information per encoded residue bit"],
            ["System B channel overhead", "33.33%", "1 redundant channel added to 3 informative channels"],
            ["System B residue-bit overhead", "37.50%", "16 informative bits expanded to 22 total residue bits"],
            ["System B coding efficiency", "68.28%", "Higher dynamic range at a slightly larger total width"],
        ],
    )

    fill_table(
        tables[37],
        [
            ["System", "RRNS configuration", "Testbench cases", "PASS checks", "FAIL checks", "Waveform available", "Verdict"],
            ["System A", "RRNS(17, 19, 23)+(29)", "5", "20", "0", "Yes", "PASS"],
            ["System B", "RRNS(29, 31, 37)+(41)", "5", "20", "0", "Yes", "PASS"],
        ],
    )

    fill_table(
        tables[38],
        [
            ["Criterion", "Conventional quantized fixed-point baseline", "Residue-domain clean model", "Self-checking RRNS MAC/checker"],
            ["Arithmetic domain", "Signed fixed-point / integer convolution", "Residue-domain reconstruction of the same workload", "Residue-domain computation with redundant checking"],
            ["Quantization evidence", "RMSE 0.0166 to 0.0042 across Q4.4 to Q6.6", "Uses the same quantized integer inputs", "Uses the same quantized integer inputs"],
            ["Clean exact equivalence", "Reference baseline", "100.00% exact match across all clean outputs", "100.00% exact match and 100.00% clean checker acceptance"],
            ["Fault-detection capability", "None", "None", "100% on tested single-channel faults; high but non-perfect on harder multi-channel faults"],
            ["False-positive behaviour", "Not applicable", "Not applicable", "0.00% across all tested clean-codeword regimes"],
            ["Hardware validation", "Software baseline only", "Used as Python comparison model", "Two RTL systems simulated with 20 PASS and 0 FAIL each"],
            ["Current limitation", "No end-to-end model accuracy claim", "No built-in error checking", "No synthesis, timing, power, or thermal measurements yet"],
        ],
    )

    doc.save(OUTPUT_DOCX)
    print(OUTPUT_DOCX)


if __name__ == "__main__":
    main()
