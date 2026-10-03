from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_DIR = PROJECT_ROOT / "docx_outputs"
SOURCE = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_formatted_clean.docx"
OUTPUT = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_safe_corrected.docx"


def set_paragraph_text(paragraph, text: str) -> None:
    style = paragraph.style
    paragraph.clear()
    paragraph.style = style
    if text:
        paragraph.add_run(text)


def remove_paragraph(paragraph) -> None:
    paragraph._element.getparent().remove(paragraph._element)


def replace_everywhere(doc: Document, replacements: dict[str, str]) -> None:
    for paragraph in doc.paragraphs:
        updated = paragraph.text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != paragraph.text:
            set_paragraph_text(paragraph, updated)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                updated = cell.text
                for old, new in replacements.items():
                    updated = updated.replace(old, new)
                if updated != cell.text:
                    cell.text = updated


def main() -> None:
    shutil.copy2(SOURCE, OUTPUT)
    doc = Document(OUTPUT)

    updates = {
        318: "The quantization stage was completed before the residue-domain experiments. The implemented fixed-point workflow used symmetric signed quantization with zero point 0, scale 2^f for each Q format, nearest-integer rounding, and saturation to the representable range. Chapter Four therefore reports the actual scaling factors, clipping counts, mean absolute error, and maximum absolute error for the tested Q4.4, Q5.5, and Q6.6 benchmark formats.",
        326: "The final experiment used two validated RRNS configurations rather than a single small base. System A, RRNS(17, 19, 23)+(29), provides an information dynamic range of 7429 and a balanced signed limit of ±3714, while System B, RRNS(29, 31, 37)+(41), provides an information dynamic range of 33263 and a balanced signed limit of ±16631. System A supported TC1, TC2, and TC4, whereas System B was selected for TC3 because of its larger accumulation range.",
        332: "The self-checking RRNS model adds one redundant modulus to the information base. In the validated experiments, the redundant modulus is 29 for System A and 41 for System B. The redundant channel receives the same activation and weight sequence and performs the equivalent modular MAC:",
        340: "The checker compares the predicted redundant residue with the independently accumulated redundant residue. The fault flag is defined as",
        344: "The principal Python campaign evaluated five residue-level fault patterns across the final workloads: single informative-channel faults, single redundant-channel faults, two informative-channel faults, informative-plus-redundant faults, and two-channel mixed faults. Each injected case records the affected moduli, MAC position, convolution-output location, corrupted residue tuple, checker decision, reconstructed faulty output, and output error.",
        345: "The conclusions are restricted to the implemented residue-level corruption patterns and directed clean-codeword validation. The study does not establish coverage of all simultaneous common-mode faults, timing violations, converter faults, checker faults, memory faults, control faults, or physical-device failures.",
        347: "1. Generate four reproducible convolution workloads TC1–TC4 with random seed 7, using feature maps of 6 × 6, 8 × 8, 9 × 9, and 10 × 10 together with 3 × 3 and 5 × 5 kernels.",
        348: "2. Quantize the floating-point benchmark data into the selected signed fixed-point formats Q4.4, Q5.5, Q6.6, and Q7.5 using symmetric scaling, nearest rounding, and saturation.",
        349: "3. Compute the valid-convolution outputs with the conventional quantized fixed-point baseline and record 141 clean scalar outputs.",
        350: "4. Select RRNS(17, 19, 23)+(29) for the workloads whose signed accumulation range fits System A and RRNS(29, 31, 37)+(41) for the larger-range workload requiring System B.",
        351: "5. Encode every activation and weight into the informative and redundant residue channels and perform modular multiplication and accumulation independently in each channel.",
        352: "6. Reconstruct the informative residue tuple by CRT, decode the balanced signed value, and verify exact equivalence with the conventional quantized fixed-point baseline.",
        353: "7. Inject the five defined residue-level fault patterns, producing 2,400 recorded fault cases across the two RRNS systems.",
        354: "8. Validate false-positive behaviour on 41,714 clean RRNS codewords and summarize the observed Python and Verilog evidence for Chapter Four.",
        356: "The final experiment contains four representative workloads, 141 clean scalar outputs, 2,400 residue-level fault injections, and 41,714 clean-codeword evaluations for false-positive validation. The appendix retains one small illustrative example for explanatory purposes, but the main evidence reported in Chapter Four comes from the consolidated TC1–TC4 study and the paired System A and System B Verilog simulations.",
        359: "The Verilog implementation provides simulation-focused RTL models of a self-checking RRNS MAC/checker component for quantized fixed-point convolution-layer MAC operations. It is not a complete CNN accelerator, but it does model both validated residue systems and the signed checker flow exercised in the Python study. Functional verification was completed with directed Icarus Verilog simulations, yielding 20 PASS checks and 0 FAIL checks for each system.",
        361: "The RTL stage implements the same two modulus systems used in the final Python experiments. System A uses informative moduli {17, 19, 23} with redundant modulus 29, while System B uses informative moduli {29, 31, 37} with redundant modulus 41. Their balanced signed limits remain ±3714 and ±16631 respectively, and the redundant modulus serves only for checking rather than for extending the valid informative payload range.",
        363: "The RTL comprises binary-to-residue conversion, one modular multiplier and clocked accumulator for each informative modulus, an independently operating redundant channel, CRT-based reconstruction, balanced signed decoding, expected redundant-residue generation, comparison logic, and a fault-flag output. Generic multiplication and remainder operators are used for functional clarity and are not presented as optimized hardware.",
        366: "The checker reconstructs from the informative residues, performs balanced signed decoding, calculates the expected redundant residue from the signed value, compares it with the independently accumulated redundant residue, and asserts the fault flag when they differ.",
        368: "Each RTL system was exercised with five directed cases: a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault example, and a clean multi-tap MAC window. The resulting simulator transcripts and waveform dumps therefore provide observed functional evidence for both correct clean arithmetic and the expected checker behaviour under the selected detected and undetected fault scenarios.",
        369: "The Verilog cases are now supported by independently executed Icarus Verilog simulation evidence. The observed simulator logs and waveform files confirm the clean-case outputs, fault-flag response, and known multi-channel limitation cases discussed later in Chapter Four and summarized again in Appendix B.",
        480: "Future work can extend the present component-level study by evaluating wider convolution layers, multi-channel feature maps, alternative modulus combinations, pipelined or sequential RRNS MAC organizations, fault localization or correction support, and the effect of arithmetic fault handling on higher-level inference behaviour. Such extensions should preserve the same careful distinction between functional arithmetic evidence and any later implementation-specific evaluation.",
        485: "• The Python findings apply to the four implemented TC1–TC4 workloads, the selected Q4.4 to Q7.5 formats, the stated residue systems, and the evaluated convolution windows rather than to every possible Edge AI layer configuration.",
        486: "• The fault campaign covers the implemented five-pattern residue-level corruption study and does not establish universal fault coverage across all possible multi-channel or physical fault mechanisms.",
        500: "",
        509: "",
        513: "This appendix preserves a small illustrative Python example used to explain the residue workflow. It supplements, rather than defines, the final Chapter Four evidence, which is based on the four TC1–TC4 workloads, 141 clean outputs, 2,400 fault injections, and 41,714 clean-codeword checks.",
    }
    for index, text in updates.items():
        set_paragraph_text(doc.paragraphs[index], text)

    table = doc.tables[18]
    rows = [
        ["Parameter", "Implemented value"],
        ["Random seed", "7"],
        ["Representative workloads", "TC1, TC2, TC3, and TC4"],
        ["Feature-map shapes", "6 × 6, 8 × 8, 9 × 9, and 10 × 10"],
        ["Kernel shapes", "3 × 3 and 5 × 5"],
        ["Fixed-point formats", "Q4.4, Q5.5, Q6.6, and Q7.5"],
        ["System A", "RRNS(17, 19, 23)+(29)"],
        ["System B", "RRNS(29, 31, 37)+(41)"],
        ["Clean outputs, fault injections, clean codewords", "141; 2,400; 41,714"],
    ]
    while len(table.rows) > len(rows):
        table._tbl.remove(table.rows[-1]._tr)
    while len(table.rows) < len(rows):
        table.add_row()
    for r_idx, row_values in enumerate(rows):
        for c_idx, value in enumerate(row_values):
            table.cell(r_idx, c_idx).text = value

    for index in range(490, 480, -1):
        remove_paragraph(doc.paragraphs[index])

    replace_everywhere(
        doc,
        {
            "multiply-andaccumulate": "multiply-and-accumulate",
            "selfchecking": "self-checking",
            "Selfchecking": "Self-checking",
            "fixedpoint": "fixed-point",
            "dynamicrange": "dynamic-range",
            "falsepositive": "false-positive",
            "Pythongenerated": "Python-generated",
            "FPGAbased": "FPGA-based",
            "performanceoriented": "performance-oriented",
            "no-localreuse": "no-local-reuse",
            "rowstationary": "row-stationary",
            "faultflag": "fault flag",
            "Â±": "±",
        },
    )

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
