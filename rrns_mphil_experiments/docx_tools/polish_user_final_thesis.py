from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_DIR = PROJECT_ROOT / "docx_outputs" / "working_final"
SOURCE = DOCX_DIR / "MPHIL-FINAL-THESIS-PEH-ATTA-JOSEPH-UEMP1300125_working.docx"
OUTPUT = DOCX_DIR / "MPHIL-FINAL-THESIS-PEH-ATTA-JOSEPH-UEMP1300125_revised_v3.docx"


def set_run_font(run, size_pt: int = 12, bold: bool | None = None) -> None:
    run.font.name = "Times New Roman"
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


def set_paragraph_text(paragraph: Paragraph, text: str, size_pt: int = 12) -> None:
    style = paragraph.style
    alignment = paragraph.alignment
    before = paragraph.paragraph_format.space_before
    after = paragraph.paragraph_format.space_after
    line_spacing = paragraph.paragraph_format.line_spacing
    left_indent = paragraph.paragraph_format.left_indent
    first_line_indent = paragraph.paragraph_format.first_line_indent

    paragraph.clear()
    paragraph.style = style
    paragraph.alignment = alignment
    paragraph.paragraph_format.space_before = before
    paragraph.paragraph_format.space_after = after
    paragraph.paragraph_format.line_spacing = line_spacing
    paragraph.paragraph_format.left_indent = left_indent
    paragraph.paragraph_format.first_line_indent = first_line_indent

    if text:
        run = paragraph.add_run(text)
        set_run_font(run, size_pt=size_pt)


def find_paragraph_by_prefix(doc: Document, prefix: str) -> Paragraph:
    normalized_prefix = " ".join(prefix.split())
    for paragraph in doc.paragraphs:
        if " ".join(paragraph.text.split()).startswith(normalized_prefix):
            return paragraph
    raise ValueError(f"Paragraph not found for prefix: {prefix}")


def find_paragraph_containing(doc: Document, fragment: str) -> Paragraph:
    normalized_fragment = " ".join(fragment.split())
    for paragraph in doc.paragraphs:
        if normalized_fragment in " ".join(paragraph.text.split()):
            return paragraph
    raise ValueError(f"Paragraph not found containing: {fragment}")


def insert_paragraph_after(paragraph: Paragraph, text: str, size_pt: int = 12) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    new_para.style = paragraph.style
    new_para.alignment = paragraph.alignment
    new_para.paragraph_format.space_before = paragraph.paragraph_format.space_before
    new_para.paragraph_format.space_after = paragraph.paragraph_format.space_after
    new_para.paragraph_format.line_spacing = paragraph.paragraph_format.line_spacing
    new_para.paragraph_format.left_indent = paragraph.paragraph_format.left_indent
    new_para.paragraph_format.first_line_indent = paragraph.paragraph_format.first_line_indent
    if text:
        run = new_para.add_run(text)
        set_run_font(run, size_pt=size_pt)
    return new_para


def enable_update_fields_on_open(docx_path: Path) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        settings_xml = zin.read("word/settings.xml")

    if b"w:updateFields" in settings_xml:
        return

    patched = settings_xml.replace(b"</w:settings>", b'<w:updateFields w:val="true"/></w:settings>')

    tmp_path = docx_path.with_suffix(".settings.tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/settings.xml":
                zout.writestr(item, patched)
            else:
                zout.writestr(item, zin.read(item.filename))
    docx_path.unlink()
    tmp_path.rename(docx_path)


def replace_global_text(doc: Document) -> None:
    replacements = {
        "convolutionlayer": "convolution-layer",
        "Reducedprecision": "Reduced-precision",
        "architectureaware": "architecture-aware",
        "Pythongenerated": "Python-generated",
        "falsepositive": "false-positive",
        "dynamicrange": "dynamic-range",
        "selfchecking": "self-checking",
        "Ccase": "Case",
        "6x6": "6 x 6",
        "8x8": "8 x 8",
        "9x9": "9 x 9",
        "10x10": "10 x 10",
        "3x3": "3 x 3",
        "5x5": "5 x 5",
        "multiply-andaccumulate": "multiply-and-accumulate",
        "faultflag": "fault flag",
        "FPGAbased": "FPGA-based",
        "performanceoriented": "performance-oriented",
        "no-localreuse": "no-local-reuse",
    }

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

    replace_global_text(doc)

    para = find_paragraph_by_prefix(doc, "The quantization baseline produced low reconstruction error")
    set_paragraph_text(
        para,
        "The quantization baseline produced low reconstruction error, with RMSE values of 0.0166, 0.0083, and 0.0042 for Q4.4, Q5.5, and Q6.6 respectively. Clean RRNS reconstruction matched the quantized fixed-point baseline exactly across 141 evaluated outputs, while dynamic-range verification confirmed that the selected RRNS systems remained within their balanced signed limits for all tested workloads. In the fault-injection campaign, all tested single informative-channel and single redundant-channel faults were detected, overall detection rates reached 97.92% for System A and 98.50% for System B, and the false-positive rate on 41,714 clean-checker evaluations was 0.00%. Verilog functional simulation of two RRNS hardware systems reproduced the expected clean-case and fault-flag behaviour with 20 PASS checks and 0 FAIL checks per system. The study therefore demonstrates that a self-checking RRNS MAC/checker can preserve clean numerical equivalence while providing strong, though not universal, arithmetic fault-detection capability at the component and functional hardware levels.",
    )

    para = find_paragraph_by_prefix(doc, "For a multi-channel layer, the accumulation is extended across all input channels.")
    insert_paragraph_after(
        para,
        "In the benchmark workloads used in this thesis, no additional bias term was injected into the convolution windows, so the evaluated integer outputs reduce to signed multiply-and-accumulate sums over the selected kernel taps.",
    )

    para = find_paragraph_by_prefix(doc, "The quantization stage was completed before the residue-domain experiments.")
    insert_paragraph_after(
        para,
        "For the implemented symmetric signed formats, the integer code is obtained as x_q = round(x * 2^f) with zero point 0 and saturation to the signed Q-format bounds, while the dequantized value is x_hat = x_q / 2^f. When two quantized operands are multiplied, the raw integer product therefore carries 2f fractional bits. The convolution model accumulates these integer products directly and dequantizes only after accumulation by dividing the integer output by 2^(2f).",
    )

    para = find_paragraph_by_prefix(doc, "The final experiment used two validated RRNS configurations rather than a single small base.")
    insert_paragraph_after(
        para,
        "Candidate informative modulus sets screened in software were (17, 19, 23), (23, 29, 31), (29, 31, 37), and (37, 41, 43), each paired with the first available coprime redundant candidate from {29, 31, 37, 41, 43, 47}. The smallest balanced-signed system that supported the required clean workload magnitude was retained in order to limit residue width, which is why System A was used for TC1, TC2, and TC4, whereas TC3 required the larger System B.",
    )

    para = find_paragraph_by_prefix(doc, "The principal Python campaign evaluated five residue-level fault patterns across the final workloads")
    insert_paragraph_after(
        para,
        "For each RRNS system, a deterministic random generator initialized with DEFAULT_SEED + 50 + system_index produced 240 trials per fault pattern. A clean signed payload value was first sampled uniformly from the interval +/-0.75 of the balanced signed limit and encoded into its RRNS codeword. The faulted channel set was then selected by pattern: one informative channel, the redundant channel, two informative channels without replacement, one informative plus the redundant channel, or two channels chosen without replacement from the full informative-plus-redundant set.",
    )
    insert_paragraph_after(
        para,
        "Each selected channel was corrupted using one of three implemented modes cycled deterministically across trials: a non-zero modular delta, a random replacement residue forced to differ from the original value, or a bounded bit flip within the residue-channel width followed by modular reduction. A harmful undetected fault is defined in this thesis as a case in which the corrupted codeword reconstructs to a numerically different signed output while the checker still reports the residue tuple as valid.",
    )

    para = find_paragraph_by_prefix(doc, "8. Validate false-positive behaviour on 41,714 clean RRNS codewords")
    set_paragraph_text(
        para,
        "8. To validate false-positive behaviour on 41,714 clean-checker evaluations and summarize the observed Python and Verilog evidence for Chapter Four.",
    )
    para = find_paragraph_by_prefix(doc, "5. To develop and functionally verify a Verilog model of the selected RNS MAC")
    set_paragraph_text(
        para,
        "5. To develop and functionally verify a Verilog model of the selected RNS MAC and checker architecture by comparing their modular outputs, reconstructed results, fault-flag behaviour and directed-testbench observation delay with Python-generated reference vectors.",
    )
    para = find_paragraph_by_prefix(doc, "5. Does the Verilog functional model reproduce the Python reference outputs")
    set_paragraph_text(
        para,
        "5. Does the Verilog functional model reproduce the Python reference outputs, residue relationships, checker decisions and what observation delay is used in the directed functional testbench?",
    )
    para = find_paragraph_by_prefix(doc, "The use of Python and Verilog also provides complementary forms of evidence.")
    set_paragraph_text(
        para,
        "The use of Python and Verilog also provides complementary forms of evidence. Python will support numerical modelling, fixed-point analysis, RNS and RRNS arithmetic, reconstruction verification, dynamic-range testing, and systematic fault injection. Verilog will demonstrate that the modular MAC and checking operations can be expressed as a functional RTL component and verified using the same reference vectors, including functional response timing and testbench observation delay assessment for the directed cases.",
    )
    para = find_paragraph_by_prefix(doc, "Fifth, Verilog functional simulation demonstrates logical behaviour and cycle sequencing")
    set_paragraph_text(
        para,
        "Fifth, Verilog functional simulation demonstrates logical behaviour and directed-testbench response timing but does not provide FPGA area, physical timing, frequency or power results. No such hardware measurements will be claimed unless a separate synthesis study is conducted using a named target device, synthesis tool, constraint set, and implementation procedure.",
    )
    para = find_paragraph_by_prefix(doc, "The current study therefore draws architectural motivation from FPGA-based QNN accelerators")
    set_paragraph_text(
        para,
        "The current study therefore draws architectural motivation from FPGA-based QNN accelerators without attempting to reproduce a complete FINN-style toolchain or streaming accelerator. Verilog will be used only for component-level functional hardware modelling and functional verification and directed-testbench observation-delay assessment of the proposed RRNS MAC/checker. FPGA synthesis, LUT counts, DSP counts, power measurement, maximum clock frequency, and critical-path analysis are outside the study's scope.",
    )
    para = find_paragraph_containing(doc, "Verilog-supported component-level functional and cycle-level modelling.")
    set_paragraph_text(
        para,
        "Verilog-supported component-level functional modelling and observation-delay assessment.",
    )
    para = find_paragraph_by_prefix(doc, "The scope is deliberately bounded.")
    set_paragraph_text(
        para,
        "The scope is deliberately bounded. Python will be used for fixed-point modelling, modulus-set and signed-range analysis, exact RNS reconstruction verification, and systematic fault injection. Verilog will be used to model the functional behaviour and directed-testbench observation delay of the RRNS MAC/checker component. The study will not implement a complete CNN accelerator and will not report FPGA synthesis results, LUT or DSP counts, measured power, maximum frequency, critical-path delay, ASIC fabrication, or system-level accelerator performance.",
    )
    para = find_paragraph_by_prefix(doc, "Verilog will be used for functional hardware modelling of the modular multipliers")
    set_paragraph_text(
        para,
        "Verilog will be used for functional hardware modelling of the modular multipliers, modular accumulators, RNS MAC path, redundant residue path, checker, and fault flag. Verification will be based on Python-generated test vectors. The Verilog evaluation will report functional correctness, modular-output correctness, reconstructed-output agreement, fault-flag behaviour, and functional response timing and testbench observation delay.",
    )
    para = find_paragraph_by_prefix(doc, "6. A functionally verified Verilog model whose modular outputs")
    set_paragraph_text(
        para,
        "6. A functionally verified Verilog model whose modular outputs, reconstructed results, checker response, and directed-testbench observation delay are validated against Python-generated reference vectors.",
    )
    para = find_paragraph_by_prefix(doc, "The final experiment contains four representative workloads")
    set_paragraph_text(
        para,
        "The final experiment contains four representative workloads, 141 clean scalar outputs, 2,400 residue-level fault injections, and 41,714 clean-checker evaluations for false-positive validation. The appendix retains one small illustrative example for explanatory purposes, but the main evidence reported in Chapter Four comes from the consolidated TC1-TC4 study and the paired System A and System B Verilog simulations.",
    )

    para = find_paragraph_by_prefix(doc, "The evaluation uses metrics that are directly supported by Python numerical simulation")
    set_paragraph_text(
        para,
        "The evaluation uses metrics that are directly supported by Python numerical simulation and Verilog functional modelling. These include exact-equivalence rate, reconstruction mismatch rate, information-range sufficiency, overflow occurrence, fault-detection rate, undetected-fault rate, false-positive rate where fault-free checker records are available, output-error magnitude, residue-channel width, redundant-channel width, checker behaviour, and the observation delay used in the present directed RTL testbench.",
    )

    para = find_paragraph_by_prefix(doc, "The quantization experiment now provides the missing floating-point reference evidence.")
    insert_paragraph_after(
        para,
        "The implemented baseline used zero point 0, scale 2^f for each Q format, nearest-integer rounding, and saturation to the representable signed interval. Because the convolution integer outputs remain at product scale, the reported dequantized outputs were obtained by dividing the accumulated integer result by 2^(2f).",
    )

    para = find_paragraph_by_prefix(doc, "These margins show that the residue systems were not merely mathematically valid")
    set_paragraph_text(
        para,
        "These margins confirm that the selected residue systems were sufficient for the evaluated workload instances and that no clean-case range overflow occurred. None of the clean test cases approached the balanced signed boundary closely enough to risk ambiguity in signed decoding, and the minimum observed margin of 761 confirms that the exact-equivalence result was obtained without range overflow.",
    )
    insert_paragraph_after(
        para,
        "A conservative workload-screening expression may be written as A_screen = K max|a_q| max|w_q|, where K is the number of MAC terms and a_q and w_q are quantized integer operands. In the present study this expression was treated only as a loose screening heuristic because it assumes worst-case sign alignment across all terms. Final RRNS selection was therefore tied to the exact clean integer-output magnitudes generated by the reproducible workloads summarized in Chapter Four.",
    )

    para = find_paragraph_by_prefix(doc, "False-positive evaluation was completed explicitly on clean RRNS codewords.")
    set_paragraph_text(
        para,
        "False-positive evaluation was completed explicitly on clean-checker evaluations. System A accepted all 7,940 tested clean evaluations and System B accepted all 33,774 tested clean evaluations, yielding zero false positives in every validation regime and an overall false-positive rate of 0.00% for both systems.",
    )
    para = find_paragraph_by_prefix(doc, "False-positive screening was performed under three clean-codeword regimes")
    set_paragraph_text(
        para,
        "False-positive screening was performed under three clean-checker regimes for each system: 500 random interior values, 11 signed-edge values, and the full balanced signed range. Every valid clean RRNS tuple was accepted in all three regimes. This result is important because it shows that the checker does not create spurious alarms when the residue tuple is valid and in range.",
    )
    para = find_paragraph_by_prefix(doc, "The full-range validation is especially useful for the thesis because it tests")
    set_paragraph_text(
        para,
        "The full-range validation is especially useful for the thesis because it tests not only a random subset but the entire admissible signed payload space for each system. The absence of false positives across 7,429 unique clean payload values for System A and 33,263 unique clean payload values for System B supports the practical usability of the checker in clean operation.",
    )
    para = find_paragraph_by_prefix(doc, "The conclusions are restricted to the implemented residue-level corruption patterns and directed clean-codeword validation.")
    set_paragraph_text(
        para,
        "The conclusions are restricted to the implemented residue-level corruption patterns and directed clean-checker validation. The study does not establish coverage of all simultaneous common-mode faults, timing violations, converter faults, checker faults, memory faults, control faults, or physical-device failures.",
    )

    para = find_paragraph_by_prefix(doc, "Figure 4.4 False-positive validation of the RRNS checker on clean codewords")
    set_paragraph_text(
        para,
        "Figure 4.4 False-positive validation of the RRNS checker on clean-checker evaluations Note. No false positives were observed in any validation regime for either RRNS system, while the right-hand panel shows the much larger clean-evaluation coverage achieved when the full balanced signed range is exercised.",
    )
    para = find_paragraph_by_prefix(doc, "4.6.2 False-Positive Validation on Clean Codewords")
    set_paragraph_text(para, "4.6.2 False-Positive Validation on Clean RRNS Evaluations")

    para = find_paragraph_by_prefix(doc, "The structural overhead is modest but measurable.")
    set_paragraph_text(
        para,
        "The additional redundant channel produces a 33.33% channel-count overhead and a 33.33%-37.50% residue-representation-width overhead in the evaluated systems. These values characterize encoded structural cost only; they do not represent synthesized hardware area, power, timing, energy, or throughput overhead.",
    )

    para = find_paragraph_by_prefix(doc, "The Verilog stage is now supported by independently executed simulation evidence")
    set_paragraph_text(
        para,
        "The Verilog stage is now supported by independently executed simulation evidence rather than arithmetic expectation alone. Both System A and System B were compiled and run in Icarus Verilog, each with five directed testbench cases covering a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault limitation case, and a clean multi-tap MAC window. Each RTL system recorded 20 PASS checks, zero FAIL checks, and an available VCD waveform dump. The present RTL models are combinational rather than pipelined, and the testbench samples outputs one simulation time unit after each stimulus update, so the timing evidence is an observation delay rather than a multi-cycle pipeline latency figure.",
    )
    para = find_paragraph_by_prefix(doc, "The RTL comprises binary-to-residue conversion, one modular multiplier and clocked accumulator for each informative modulus")
    set_paragraph_text(
        para,
        "The RTL comprises binary-to-residue conversion, one modular multiplier and modular accumulation logic for each informative modulus, an independently operating redundant channel, CRT-based reconstruction, balanced signed decoding, expected redundant-residue generation, comparison logic, and a fault-flag output. Generic multiplication and remainder operators are used for functional clarity and are not presented as optimized hardware.",
    )

    para = find_paragraph_by_prefix(doc, "First, the selected fixed-point formats provided a well-controlled numerical baseline")
    set_paragraph_text(
        para,
        "First, the selected fixed-point formats provided a well-controlled numerical baseline: the dequantized outputs stayed close to the floating-point reference, and the measured RMSE decreased as precision increased from Q4.4 to Q6.6. Second, candidate RRNS systems could be selected to support the required signed accumulation range while preserving exact reconstruction, with the final workloads remaining inside the balanced signed limits of Systems A and B. Third, the proposed self-checking RRNS MAC/checker demonstrated strong fault-detection capability under the defined residue-level fault model, including perfect detection of the tested single-channel faults, non-zero but limited harmful-undetected exposure under harder multi-channel patterns, and zero false positives on tested clean-checker evaluations. Fourth, the comparison among the conventional quantized model, the residue-domain clean model, and the self-checking RRNS model showed that the additional redundant channel introduces a 33.33% channel-count overhead and a 33.33%-37.50% residue-representation-width overhead in exchange for arithmetic consistency checking. Fifth, the Verilog functional models reproduced the expected outputs and fault responses for the directed clean and faulted testbench cases, confirming the functional realizability of the concept as a simulation-level RTL component.",
    )

    para = find_paragraph_by_prefix(doc, "The study presents an integrated component-level evaluation")
    set_paragraph_text(
        para,
        "The study presents an integrated component-level evaluation that combines quantized fixed-point convolution, exact RRNS reconstruction, explicit dynamic-range verification, systematic residue-level fault injection, false-positive validation, and Verilog functional verification within an edge AI hardware-accelerator context. It also provides two concrete validated RRNS hardware configurations and a practical distinction between strong single-channel detection and the residual exposure that remains under selected multi-channel faults.",
    )

    para = find_paragraph_by_prefix(doc, "The completed Chapter Four evidence now addresses the research gap more directly.")
    set_paragraph_text(
        para,
        "The completed Chapter Four evidence now addresses the research gap more directly. The study provides empirical support for quantized fixed-point baseline behaviour, exact clean RRNS equivalence, explicit dynamic-range sufficiency, high-coverage fault detection with documented multi-channel limitations, zero false positives on tested clean-checker evaluations, and functionally validated RTL behaviour for two RRNS hardware configurations.",
    )

    para = find_paragraph_by_prefix(doc, "Chapter Four shows that the quantized fixed-point baseline introduces only a small numerical approximation error")
    set_paragraph_text(
        para,
        "Chapter Four shows that the quantized fixed-point baseline introduces only a small numerical approximation error, that clean RRNS reconstruction remained exact across 141 outputs and four representative workloads, and that the validated RRNS systems preserved positive dynamic-range margins for the evaluated workloads, with a minimum observed margin of 761. The self-checking RRNS checker detected every tested single-channel fault, achieved overall detection rates of 97.92% and 98.50% for Systems A and B, respectively, recorded zero false positives across 41,714 clean-checker evaluations, and was functionally verified in Verilog with two independently executed RTL systems. These results support the thesis claim at the component and functional-hardware levels while keeping the interpretation honestly bounded away from unmeasured synthesis or power claims.",
    )
    para = find_paragraph_containing(doc, "The clean-codeword false-positive rate was reduced to zero in the tested regimes")
    set_paragraph_text(
        para,
        "The clean-checker false-positive rate was reduced to zero in the tested regimes, but this evidence is still bounded to the two validated RRNS systems and the implemented balanced signed checker.",
    )

    para = find_paragraph_by_prefix(doc, "The study achieved its central aim of designing and evaluating a self-checking RRNS component")
    set_paragraph_text(
        para,
        "The study achieved its central aim of designing and evaluating a self-checking RRNS component for quantized fixed-point convolution-layer MAC operations. The completed evidence shows that the quantized fixed-point baseline introduced only small numerical approximation error, that clean RRNS reconstruction remained exact across all tested workloads, that the selected RRNS systems provided sufficient dynamic range, that the redundant checker achieved high fault-detection coverage with zero observed false positives on tested clean-checker evaluations, and that the corresponding RTL behaviour was verified functionally in Verilog.",
    )
    para = find_paragraph_by_prefix(doc, "This appendix preserves a small illustrative Python example used to explain the residue workflow.")
    set_paragraph_text(
        para,
        "This appendix preserves a small illustrative Python example used to explain the residue workflow. It supplements, rather than defines, the final Chapter Four evidence, which is based on the four TC1-TC4 workloads, 141 clean outputs, 2,400 fault injections, and 41,714 clean-checker evaluations.",
    )

    table = doc.tables[3]
    table.cell(0, 0).text = "Case"

    config_table = doc.tables[1]
    config_table.cell(8, 0).text = "Clean outputs, fault injections and clean-checker evaluations"

    if len(doc.tables) > 2:
        verified_table = doc.tables[2]
        verified_table.cell(2, 1).text = "4 representative workloads (TC1-TC4)"
        verified_table.cell(3, 1).text = "6 x 6, 8 x 8, 9 x 9, and 10 x 10"
        verified_table.cell(4, 1).text = "3 x 3 and 5 x 5"
        verified_table.cell(11, 0).text = "Clean-checker evaluations"
        verified_table.cell(11, 1).text = "41,714 across both systems"
    if len(doc.tables) > 9:
        doc.tables[9].cell(5, 3).text = "0.00% across all tested clean-checker evaluation regimes"

    doc.save(OUTPUT)
    enable_update_fields_on_open(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
