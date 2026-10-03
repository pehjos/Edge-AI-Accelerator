from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph


SOURCE = Path(
    r"C:\Users\PehAttaJoseph\Documents\GitHub\Edge-AI-Accelerator\rrns_mphil_experiments\docx_outputs\MPhil_Thesis_Compilation_Working_Draft_v1_final_working.docx"
)
OUTPUT = Path(
    r"C:\Users\PehAttaJoseph\Documents\GitHub\Edge-AI-Accelerator\rrns_mphil_experiments\docx_outputs\MPhil_Thesis_Compilation_Working_Draft_v1_formatted.docx"
)


def set_run_font(run, name: str = "Times New Roman", size_pt: int = 11, bold: bool | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


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


def remove_paragraph(paragraph: Paragraph) -> None:
    p = paragraph._element
    p.getparent().remove(p)


def insert_paragraph_after(paragraph: Paragraph, text: str = "", style=None) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style is not None:
        new_para.style = style
    if text:
        new_para.add_run(text)
    return new_para


def has_page_break(paragraph: Paragraph) -> bool:
    for run in paragraph.runs:
        for br in run._element.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br"):
            if br.get(qn("w:type")) == "page":
                return True
    return False


def normalize_tables(doc: Document) -> None:
    for idx, table in enumerate(doc.tables):
        rows = len(table.rows)
        cols = len(table.columns)
        if rows < 2 or cols < 2:
            continue
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        mark_row_as_header(table.rows[0])
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if r_idx == 0:
                    shade_cell(cell, "D9E2F3")
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.line_spacing = 1.0
                    if r_idx == 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:
                        para.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
                    if not para.runs:
                        para.add_run("")
                    for run in para.runs:
                        set_run_font(run, size_pt=11, bold=(r_idx == 0))


def compress_blank_paragraphs(doc: Document) -> None:
    paragraphs = list(doc.paragraphs)
    blank_streak = 0
    for para in paragraphs:
        text = para.text.replace("\xa0", " ").strip()
        if text or has_page_break(para):
            blank_streak = 0
            continue
        blank_streak += 1
        if blank_streak > 1:
            remove_paragraph(para)


def clean_styles(doc: Document) -> None:
    for para in doc.paragraphs:
        text = para.text.strip()
        if para.style and para.style.name == "Update Required" and text:
            para.style = doc.styles["Normal"]
        if para.style and para.style.name == "Update Required" and not text:
            para.style = doc.styles["Normal"]
        if para.style and para.style.name == "Heading 2" and not text:
            para.style = doc.styles["Normal"]

    # Refresh a stale methodology sentence.
    if len(doc.paragraphs) > 403:
        para = doc.paragraphs[403]
        para.clear()
        para.add_run(
            "This chapter has defined a component-level methodology for evaluating conventional quantized fixed-point, non-redundant RNS, and self-checking RRNS convolution-layer MAC operations. The approach combines signed range analysis, exact residue arithmetic, CRT reconstruction, controlled residue-level fault injection, and Verilog functional modelling. The next chapter presents the consolidated Python and Verilog evidence produced from this methodology."
        )


def ensure_appendix_b(doc: Document) -> None:
    has_appendix_b = any(p.text.strip() == "Appendix B: Verilog Functional-Verification Evidence" for p in doc.paragraphs)
    if has_appendix_b:
        return
    # Insert after the Appendix A closing paragraph.
    anchor = None
    for para in doc.paragraphs:
        if para.text.strip().startswith(
            "The illustrative workbook reports nine detected faults"
        ):
            anchor = para
            break
    if anchor is None:
        return
    style_h2 = doc.styles["Heading 2"]
    style_body = doc.styles["Normal"]
    p = insert_paragraph_after(anchor, "Appendix B: Verilog Functional-Verification Evidence", style=style_h2)
    p = insert_paragraph_after(
        p,
        "The Verilog validation was executed with Icarus Verilog version 13.0 (stable). Both RRNS systems were compiled and simulated from the project workspace using the directed testbench flow. The key source files were rrns_channel_mac.sv, rrns_checker_system_a.sv, rrns_checker_system_b.sv, self_checking_rrns_mac_system_a.sv, self_checking_rrns_mac_system_b.sv, tb_self_checking_rrns_mac_system_a.sv, and tb_self_checking_rrns_mac_system_b.sv.",
        style=style_body,
    )
    p = insert_paragraph_after(
        p,
        "Representative commands executed for the verification stage were: iverilog -g2012 -o verilog/logs/tb_self_checking_rrns_mac_system_a.out verilog/rtl/rrns_channel_mac.sv verilog/rtl/rrns_checker_system_a.sv verilog/rtl/self_checking_rrns_mac_system_a.sv verilog/tb/tb_self_checking_rrns_mac_system_a.sv, followed by vvp verilog/logs/tb_self_checking_rrns_mac_system_a.out; and the corresponding System B command set using rrns_checker_system_b.sv and self_checking_rrns_mac_system_b.sv.",
        style=style_body,
    )
    p = insert_paragraph_after(
        p,
        "Observed simulation evidence confirmed the following directed cases for both systems: a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault example, and a clean multi-tap MAC window. System A and System B each recorded 20 PASS checks, 0 FAIL checks, and a generated VCD waveform file. The simulator logs are stored in verilog/logs, and the representative waveform files are stored in verilog/waveforms.",
        style=style_body,
    )
    insert_paragraph_after(
        p,
        "The waveform review focused on the binary dot-product output, the checked residues, the predicted redundant residue, the reconstructed signed value, the syndrome, and the checker-valid signal. The clean cases showed matching clean and checked residues with checker_valid asserted, while the detected fault cases showed checker_valid deasserted and a non-zero syndrome. The known multi-channel limitation case remained checker_valid while reconstructing to an incorrect signed value, matching the Python fault-analysis evidence.",
        style=style_body,
    )


def main() -> None:
    shutil.copy2(SOURCE, OUTPUT)
    doc = Document(OUTPUT)
    clean_styles(doc)
    ensure_appendix_b(doc)
    compress_blank_paragraphs(doc)
    normalize_tables(doc)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
