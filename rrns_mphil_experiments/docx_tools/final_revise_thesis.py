from __future__ import annotations

import html
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.shared import Inches, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_DIR = PROJECT_ROOT / "docx_outputs"
SOURCE = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_formatted_clean.docx"
OUTPUT = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_final_revised.docx"


def set_run_font(run, name: str = "Times New Roman", size_pt: int = 11, bold: bool | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


def set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    style = paragraph.style
    paragraph.clear()
    paragraph.style = style
    if text:
        run = paragraph.add_run(text)
        set_run_font(run)


def remove_paragraph(paragraph: Paragraph) -> None:
    paragraph._element.getparent().remove(paragraph._element)


def remove_table(table: Table) -> None:
    table._element.getparent().remove(table._element)


def iter_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def find_paragraph_start(doc: Document, prefix: str, occurrence: int = 1) -> Paragraph:
    count = 0
    for paragraph in doc.paragraphs:
        if " ".join(paragraph.text.split()).startswith(prefix):
            count += 1
            if count == occurrence:
                return paragraph
    raise ValueError(f"Could not find paragraph starting with: {prefix!r}")


def find_table_by_header(doc: Document, header: list[str]) -> Table:
    for table in doc.tables:
        if len(table.rows) < 1 or len(table.columns) != len(header):
            continue
        values = [" ".join(cell.text.split()) for cell in table.rows[0].cells]
        if values == header:
            return table
    raise ValueError(f"Could not find table header: {header!r}")


def resize_table(table: Table, rows_needed: int, cols_needed: int) -> None:
    while len(table.rows) < rows_needed:
        table.add_row()
    while len(table.rows) > rows_needed:
        table._tbl.remove(table.rows[-1]._tr)
    if len(table.columns) != cols_needed:
        raise ValueError("Unexpected column count while resizing table.")


def fill_table(table: Table, rows: list[list[str]]) -> None:
    resize_table(table, len(rows), len(rows[0]))
    for r_idx, row in enumerate(rows):
        for c_idx, value in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = value


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def mark_row_as_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    hdr = tr_pr.find(qn("w:tblHeader"))
    if hdr is None:
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        tr_pr.append(hdr)


def set_cell_width(cell, width_inches: float) -> None:
    width = Inches(width_inches)
    cell.width = width
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:type"), "dxa")
    tc_w.set(qn("w:w"), str(int(width)))


def format_table(
    table: Table,
    widths: list[float] | None = None,
    header_fill: str = "D9E2F3",
    body_font_size: int = 10,
    header_font_size: int = 10,
) -> None:
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if widths is not None:
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                set_cell_width(cell, width)
    mark_row_as_header(table.rows[0])
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if r_idx == 0:
                shade_cell(cell, header_fill)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                if r_idx == 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif c_idx == 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if not paragraph.runs:
                    paragraph.add_run("")
                for run in paragraph.runs:
                    set_run_font(
                        run,
                        size_pt=header_font_size if r_idx == 0 else body_font_size,
                        bold=(r_idx == 0),
                    )


def set_caption_spacing(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if paragraph.style and paragraph.style.name == "Table Caption":
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.keep_with_next = True
        elif paragraph.style and paragraph.style.name == "Figure Caption":
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(3)


def replace_words_everywhere(doc: Document, replacements: dict[str, str]) -> None:
    def clean_text(text: str) -> str:
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        return updated

    for paragraph in doc.paragraphs:
        old = paragraph.text
        new = clean_text(old)
        if new != old:
            set_paragraph_text(paragraph, new)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                old = cell.text
                new = clean_text(old)
                if new != old:
                    cell.text = new


def update_specific_paragraphs(doc: Document) -> None:
    updates = {
        "The current supplied fault-injection experiment operates directly on bounded signed integer activations and weights.": (
            "The quantization stage was completed before the residue-domain experiments. The implemented fixed-point workflow used symmetric signed quantization with zero point 0, scale 2^f for each Q format, nearest-integer rounding, and saturation to the representable range. Chapter Four therefore reports the actual scaling factors, clipping counts, mean absolute error, and maximum absolute error for the tested Q4.4, Q5.5, and Q6.6 benchmark formats."
        ),
        "For the implemented information base, Mᵢ = 7 × 11 × 13 = 1001 and the balanced signed range is −500 to 500 inclusive.": (
            "The final experiment used two validated RRNS configurations rather than a single small base. System A, RRNS(17, 19, 23)+(29), provides an information dynamic range of 7429 and a balanced signed limit of ±3714, while System B, RRNS(29, 31, 37)+(41), provides an information dynamic range of 33263 and a balanced signed limit of ±16631. System A supported TC1, TC2, and TC4, whereas System B was selected for TC3 because of its larger accumulation range."
        ),
        "The self-checking RRNS model adds redundant modulus mᵣ = 17 to the information base.": (
            "The self-checking RRNS model augments the informative residue channels with one redundant modulus mᵣ. In the validated experiments, mᵣ = 29 for System A and mᵣ = 41 for System B. The redundant channel receives the same activation and weight sequence and performs the equivalent modular MAC:"
        ),
        "Let X̂ denote the canonical CRT reconstruction from the information residues in [0, Mᵢ − 1].": (
            "Let X̂ denote the canonical CRT reconstruction from the information residues in [0, Mᵢ − 1]. The balanced signed result Xₛ is obtained by"
        ),
        "The expected redundant residue is then": (
            "The expected redundant residue is then"
        ),
        "The checker compares r̂₁₇ with the independently accumulated residue r₁₇.": (
            "The checker compares the predicted redundant residue r̂ᵣ with the independently accumulated redundant residue rᵣ. The fault flag is defined as"
        ),
        "The principal Python campaign injects one residue-channel fault at a time into a selected MAC position.": (
            "The principal Python campaign evaluated five residue-level fault patterns across the final workloads: single informative-channel faults, single redundant-channel faults, two informative-channel faults, informative-plus-redundant faults, and two-channel mixed faults. Each injected case records the affected moduli, MAC position, convolution-output location, corrupted residue tuple, checker decision, reconstructed faulty output, and output error."
        ),
        "The conclusions are restricted to the implemented single-residue corruption model.": (
            "The conclusions are restricted to the implemented residue-level corruption patterns and directed clean-codeword validation. The study does not establish coverage of all simultaneous common-mode faults, timing violations, converter faults, checker faults, memory faults, control faults, or physical-device failures."
        ),
        "The Verilog implementation provides a small, simulation-focused model of a self-checking RRNS MAC/checker component for quantized fixed-point convolution-layer MAC operations.": (
            "The Verilog implementation provides simulation-focused RTL models of the self-checking RRNS MAC/checker component for quantized fixed-point convolution-layer MAC operations. It is not a complete CNN accelerator, but it does model both validated residue systems and the signed checker flow exercised in the Python study. Functional verification was completed with directed Icarus Verilog simulations, yielding 20 PASS checks and 0 FAIL checks for each system."
        ),
        "The Verilog proof-of-concept uses information moduli {3, 5, 7}, giving Mᵢ = 105 and balanced signed range −52 to 52, together with redundant modulus 11.": (
            "The RTL stage implements the same two modulus systems used in the final Python experiments. System A uses informative moduli {17, 19, 23} with redundant modulus 29, while System B uses informative moduli {29, 31, 37} with redundant modulus 41. Their balanced signed limits remain ±3714 and ±16631 respectively, and the redundant modulus serves only for checking rather than for extending the valid informative payload range."
        ),
        "The RTL comprises binary-to-residue conversion, one modular multiplier and clocked accumulator for each information modulus, an independently operating modulus-11 redundant channel, CRT-based reconstruction, balanced signed decoding, expected redundant-residue generation, comparison logic, and a fault-flag output.": (
            "The RTL comprises binary-to-residue conversion, one modular multiplier and clocked accumulator for each informative modulus, an independently operating redundant channel, CRT-based reconstruction, balanced signed decoding, expected redundant-residue generation, comparison logic, and a fault-flag output. Generic multiplication and remainder operators are used for functional clarity and are not presented as optimized hardware."
        ),
        "The checker reconstructs from the information residues, performs balanced signed decoding, calculates the expected modulus-11 residue from the signed value, compares it with the independently accumulated redundant residue, and asserts the fault flag when they differ.": (
            "The checker reconstructs from the informative residues, performs balanced signed decoding, calculates the expected redundant residue from the signed value, compares it with the independently accumulated redundant residue, and asserts the fault flag when they differ."
        ),
        "The fault-free demonstration applies activation/weight pairs (4,5), (3,2), and (7,1), producing the accumulated result 33 and information tuple (0,3,5).": (
            "Each RTL system was exercised with five directed cases: a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault example, and a clean multi-tap MAC window. The resulting simulator transcripts and waveform dumps therefore provide observed functional evidence for both correct clean arithmetic and the expected checker behaviour under the selected detected and undetected fault scenarios."
        ),
        "Future work should extend the current component-level evidence toward synthesis and implementation measurements such as LUT usage, DSP usage, frequency, power, and timing on a named FPGA or ASIC flow.": (
            "Future work can extend the present component-level study by evaluating wider convolution layers, multi-channel feature maps, alternative modulus combinations, pipelined or sequential RRNS MAC organizations, fault localization or correction support, and the effect of arithmetic fault handling on higher-level inference behaviour. Such extensions should preserve the same careful distinction between functional arithmetic evidence and any later implementation-specific evaluation."
        ),
        "This appendix reproduces the supplied illustrative 5 × 5 input feature map, 3 × 3 kernel, nine clean output comparisons, and first-window modular trace.": (
            "This appendix preserves a small illustrative Python example used to explain the residue workflow. It supplements, rather than defines, the final Chapter Four evidence, which is based on the four TC1–TC4 workloads, 141 clean outputs, 2,400 fault injections, and 41,714 clean-codeword checks."
        ),
    }
    for prefix, text in updates.items():
        set_paragraph_text(find_paragraph_start(doc, prefix), text)

    # Rewrite the stepwise methodology so Chapter Three reflects the final campaign.
    step_updates = [
        "1. Generate four reproducible convolution workloads TC1–TC4 with random seed 7, using feature maps of 6 × 6, 8 × 8, 9 × 9, and 10 × 10 together with 3 × 3 and 5 × 5 kernels.",
        "2. Quantize the floating-point benchmark data into the selected signed fixed-point formats Q4.4, Q5.5, Q6.6, and Q7.5 using symmetric scaling, nearest rounding, and saturation.",
        "3. Compute the valid-convolution outputs with the conventional quantized fixed-point baseline and record 141 clean scalar outputs.",
        "4. Select RRNS(17, 19, 23)+(29) for the workloads whose signed accumulation range fits System A and RRNS(29, 31, 37)+(41) for the larger-range workload requiring System B.",
        "5. Encode every activation and weight into the informative and redundant residue channels and perform modular multiplication and accumulation independently in each channel.",
        "6. Reconstruct the informative residue tuple by CRT, decode the balanced signed value, and verify exact equivalence with the conventional quantized fixed-point baseline.",
        "7. Inject the five defined residue-level fault patterns, producing 2,400 recorded fault cases across the two RRNS systems.",
        "8. Validate false-positive behaviour on 41,714 clean RRNS codewords and summarize the observed Python and Verilog evidence for Chapter Four.",
    ]
    heading_310 = find_paragraph_start(doc, "3.10 Python Numerical Simulation")
    paragraphs = list(doc.paragraphs)
    start_idx = next(index for index, paragraph in enumerate(paragraphs) if paragraph._element == heading_310._element)
    for offset, text in enumerate(step_updates, start=1):
        set_paragraph_text(paragraphs[start_idx + offset], text)

    set_paragraph_text(
        find_paragraph_start(doc, "The supplied large-scale experiment contains 10 independent input/kernel cases"),
        "The final experiment contains four representative workloads, 141 clean scalar outputs, 2,400 residue-level fault injections, and 41,714 clean-codeword evaluations for false-positive validation. The appendix retains one small illustrative example for explanatory purposes, but the main evidence reported in Chapter Four comes from the consolidated TC1–TC4 study and the paired System A and System B Verilog simulations.",
    )
    set_paragraph_text(
        find_paragraph_start(doc, "• The Python findings apply to 5 × 5 single-channel inputs"),
        "• The Python findings apply to the four implemented TC1–TC4 workloads, the selected Q4.4 to Q7.5 formats, the stated residue systems, and the evaluated convolution windows rather than to every possible Edge AI layer configuration.",
    )
    set_paragraph_text(
        find_paragraph_start(doc, "• The fault campaign covers the implemented single-residue corruption model"),
        "• The fault campaign covers the implemented five-pattern residue-level corruption study and does not establish universal fault coverage across all possible multi-channel or physical fault mechanisms.",
    )


def update_table_3_1(doc: Document) -> None:
    table = find_table_by_header(doc, ["Parameter", "Implemented value"])
    rows = [
        ["Parameter", "Implemented value"],
        ["Random seed", "7"],
        ["Representative workloads", "TC1, TC2, TC3, and TC4"],
        ["Feature-map shapes", "6 × 6, 8 × 8, 9 × 9, and 10 × 10"],
        ["Kernel shapes", "3 × 3 and 5 × 5"],
        ["Fixed-point formats", "Q4.4, Q5.5, Q6.6, and Q7.5"],
        ["System A", "RRNS(17, 19, 23)+(29)"],
        ["System B", "RRNS(29, 31, 37)+(41)"],
        ["Clean outputs evaluated", "141"],
        ["Injected fault trials", "2,400"],
        ["Clean codewords for false-positive validation", "41,714"],
    ]
    fill_table(table, rows)


def remove_duplicate_chapter_five(doc: Document) -> None:
    paragraphs = list(doc.paragraphs)
    matches = [
        index
        for index, paragraph in enumerate(paragraphs)
        if " ".join(paragraph.text.split()).startswith("5.2 Conclusions Aligned with the Research Questions")
    ]
    if len(matches) < 2:
        return

    start_index = matches[1]
    if start_index > 0 and "The study achieved its central aim" in " ".join(paragraphs[start_index - 1].text.split()):
        start_index -= 1

    end_index = next(
        index
        for index, paragraph in enumerate(paragraphs)
        if " ".join(paragraph.text.split()).startswith("REFERENCES")
    )

    for paragraph in reversed(paragraphs[start_index:end_index]):
        remove_paragraph(paragraph)


def clean_references_and_appendix(doc: Document) -> None:
    for paragraph in list(doc.paragraphs):
        if " ".join(paragraph.text.split()).startswith("The reference list above captures the sources used in the completed thesis body."):
            remove_paragraph(paragraph)


def update_equation_source_tables(doc: Document) -> None:
    replacements = {
        "(3.9)": "Xₛ = X̂ if 0 ≤ X̂ ≤ ⌊Mᵢ/2⌋; X̂ − Mᵢ if ⌊Mᵢ/2⌋ < X̂ < Mᵢ",
        "(3.10)": "r̂ᵣ = ⟨Xₛ⟩ₘᵣ",
        "(3.11)": "fault_flag = 0 if rᵣ = r̂ᵣ; 1 if rᵣ ≠ r̂ᵣ",
        "(3.12)": "X̂ = ⟨Σ(i=1 to k) rᵢMᵢNᵢ⟩Mᵢ",
        "(3.13)": "Xₛ = X̂ if 0 ≤ X̂ ≤ ⌊Mᵢ/2⌋; X̂ − Mᵢ if ⌊Mᵢ/2⌋ < X̂ < Mᵢ",
        "(3.14)": "r̂ᵣ = ⟨Xₛ⟩ₘᵣ",
    }
    for table in doc.tables:
        if len(table.columns) != 3:
            continue
        for row in table.rows:
            eq_number = " ".join(row.cells[2].text.split())
            if eq_number in replacements:
                row.cells[1].text = replacements[eq_number]


def build_equation_paragraph(formula_text: str, number_text: str) -> OxmlElement:
    paragraph = OxmlElement("w:p")

    p_pr = OxmlElement("w:pPr")
    p_style = OxmlElement("w:pStyle")
    p_style.set(qn("w:val"), "Normal")
    p_pr.append(p_style)

    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    p_pr.append(spacing)

    tabs = OxmlElement("w:tabs")
    center_tab = OxmlElement("w:tab")
    center_tab.set(qn("w:val"), "center")
    center_tab.set(qn("w:pos"), "4680")
    tabs.append(center_tab)
    right_tab = OxmlElement("w:tab")
    right_tab.set(qn("w:val"), "right")
    right_tab.set(qn("w:pos"), "9360")
    tabs.append(right_tab)
    p_pr.append(tabs)
    paragraph.append(p_pr)

    start_run = OxmlElement("w:r")
    start_tab = OxmlElement("w:tab")
    start_run.append(start_tab)
    paragraph.append(start_run)

    escaped_formula = html.escape(formula_text)
    omath = parse_xml(
        f'<m:oMath {nsdecls("m")}><m:r><m:t>{escaped_formula}</m:t></m:r></m:oMath>'
    )
    paragraph.append(omath)

    end_run = OxmlElement("w:r")
    end_tab = OxmlElement("w:tab")
    end_run.append(end_tab)
    paragraph.append(end_run)

    number_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    r_fonts = OxmlElement("w:rFonts")
    r_fonts.set(qn("w:ascii"), "Times New Roman")
    r_fonts.set(qn("w:hAnsi"), "Times New Roman")
    r_pr.append(r_fonts)
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "22")
    r_pr.append(size)
    number_run.append(r_pr)
    number_text_el = OxmlElement("w:t")
    number_text_el.text = number_text
    number_run.append(number_text_el)
    paragraph.append(number_run)
    return paragraph


def convert_equation_tables(doc: Document) -> None:
    chapter_four = find_paragraph_start(doc, "CHAPTER FOUR RESULTS AND DISCUSSION")
    chapter_four_seen = False

    for block in list(iter_blocks(doc)):
        if isinstance(block, Paragraph) and block._element == chapter_four._element:
            chapter_four_seen = True
        if chapter_four_seen:
            break
        if not isinstance(block, Table):
            continue
        if len(block.columns) != 3:
            continue

        rows = []
        is_equation_table = True
        for row in block.rows:
            values = [" ".join(cell.text.split()) for cell in row.cells]
            if len(values) != 3 or not values[2].startswith("("):
                is_equation_table = False
                break
            rows.append(values)
        if not is_equation_table:
            continue

        for values in rows:
            paragraph_xml = build_equation_paragraph(values[1], values[2])
            block._element.addprevious(paragraph_xml)
        remove_table(block)


def apply_table_layouts(doc: Document) -> None:
    format_table(
        find_table_by_header(
            doc,
            ["Source", "Primary focus", "Representation / mechanism", "Main relevance to this study", "Principal distinction"],
        ),
        widths=[1.05, 1.05, 1.25, 1.45, 1.7],
        body_font_size=9,
        header_font_size=9,
    )
    format_table(
        find_table_by_header(
            doc,
            ["Fault pattern", "System A detection", "System B detection", "System A harmful undetected", "System B harmful undetected", "System A mean |error|", "System B mean |error|"],
        ),
        widths=[1.35, 0.78, 0.78, 0.95, 0.95, 0.84, 0.85],
        body_font_size=9,
        header_font_size=9,
    )
    format_table(
        find_table_by_header(
            doc,
            ["System", "RRNS configuration", "Testbench cases", "PASS checks", "FAIL checks", "Waveform available", "Verdict"],
        ),
        widths=[0.85, 1.45, 0.75, 0.7, 0.7, 0.95, 0.7],
        body_font_size=9,
        header_font_size=9,
    )
    format_table(
        find_table_by_header(
            doc,
            ["Criterion", "Conventional quantized fixed-point baseline", "Residue-domain clean model", "Self-checking RRNS MAC/checker"],
        ),
        widths=[1.2, 1.8, 1.55, 1.95],
        body_font_size=9,
        header_font_size=9,
    )
    format_table(
        find_table_by_header(
            doc,
            ["Row", "Col", "Baseline", "Information residues", "RNS output", "Faulted modulus", "Fault magnitude", "Faulty output", "Status", "Output error"],
        ),
        widths=[0.35, 0.35, 0.55, 0.95, 0.6, 0.65, 0.6, 0.72, 0.58, 0.75],
        body_font_size=8,
        header_font_size=8,
    )
    format_table(
        find_table_by_header(doc, ["Parameter", "Implemented value"]),
        widths=[2.15, 4.05],
        body_font_size=10,
        header_font_size=10,
    )


def normalize_paragraph_fonts(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if paragraph.style and paragraph.style.name in {"Heading 1", "Heading 2", "Heading 3"}:
            continue
        for run in paragraph.runs:
            if run.text.strip():
                set_run_font(run)


def main() -> None:
    shutil.copy2(SOURCE, OUTPUT)
    doc = Document(OUTPUT)

    update_specific_paragraphs(doc)
    update_table_3_1(doc)
    remove_duplicate_chapter_five(doc)
    clean_references_and_appendix(doc)
    update_equation_source_tables(doc)

    replacements = {
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
    }
    replace_words_everywhere(doc, replacements)

    convert_equation_tables(doc)
    set_caption_spacing(doc)
    apply_table_layouts(doc)
    normalize_paragraph_fonts(doc)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
