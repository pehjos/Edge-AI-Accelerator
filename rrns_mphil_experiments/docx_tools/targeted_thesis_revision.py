from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.shared import Inches, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_DIR = PROJECT_ROOT / "docx_outputs"
SOURCE = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_formatted_clean.docx"
OUTPUT = DOCX_DIR / "MPhil_Thesis_Compilation_Working_Draft_v1_targeted_revision_v3.docx"


def set_run_font(run, size_pt: int = 11, bold: bool | None = None) -> None:
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
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


def normalized(text: str) -> str:
    return " ".join(text.split())


def find_table_by_header(doc: Document, header: list[str]) -> Table:
    for table in doc.tables:
        if len(table.rows) < 1 or len(table.columns) != len(header):
            continue
        values = [normalized(cell.text) for cell in table.rows[0].cells]
        if values == header:
            return table
    raise ValueError(f"Table not found for header: {header!r}")


def iter_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def replace_paragraph_by_prefix(doc: Document, prefix: str, new_text: str) -> None:
    for paragraph in doc.paragraphs:
        if normalized(paragraph.text).startswith(prefix):
            set_paragraph_text(paragraph, new_text)
            return
    raise ValueError(f"Paragraph not found: {prefix}")


def build_generic_architecture_png(destination: Path) -> None:
    width, height = 2200, 2450
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    def load_font(size: int, bold: bool = False):
        candidates = [
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size=size)
        return ImageFont.load_default()

    title_font = load_font(54, bold=True)
    box_font = load_font(36, bold=True)
    body_font = load_font(30)
    footer_font = load_font(24)

    def draw_box(x1: int, y1: int, x2: int, y2: int, text: str) -> None:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=24, outline="black", fill="#eef4ff", width=5)
        bbox = draw.multiline_textbbox((0, 0), text, font=body_font, align="center", spacing=10)
        tx = x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2
        ty = y1 + (y2 - y1 - (bbox[3] - bbox[1])) / 2
        draw.multiline_text((tx, ty), text, fill="black", font=body_font, align="center", spacing=10)

    def draw_arrow(x1: int, y1: int, x2: int, y2: int) -> None:
        draw.line((x1, y1, x2, y2), fill="black", width=6)
        if y2 > y1:
            draw.polygon([(x2, y2), (x2 - 18, y2 - 30), (x2 + 18, y2 - 30)], fill="black")
        elif y2 < y1:
            draw.polygon([(x2, y2), (x2 - 18, y2 + 30), (x2 + 18, y2 + 30)], fill="black")
        elif x2 > x1:
            draw.polygon([(x2, y2), (x2 - 30, y2 - 18), (x2 - 30, y2 + 18)], fill="black")
        else:
            draw.polygon([(x2, y2), (x2 + 30, y2 - 18), (x2 + 30, y2 + 18)], fill="black")

    title = "Generic Architecture of the Self-Checking RRNS MAC/Checker"
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((width - (title_box[2] - title_box[0])) / 2, 50), title, fill="black", font=title_font)

    draw_box(300, 150, 1900, 320, "Quantized fixed-point feature-map samples\nand kernel weights")
    draw_box(300, 430, 1900, 600, "Binary-to-RRNS conversion for informative residues\nplus one redundant residue")
    draw_arrow(1100, 320, 1100, 430)
    draw_arrow(1100, 600, 1100, 710)

    draw.rounded_rectangle((150, 710, 2050, 1220), radius=28, outline="black", width=5)
    engine_label = "Parallel modular MAC engine"
    engine_box = draw.textbbox((0, 0), engine_label, font=box_font)
    draw.text(((width - (engine_box[2] - engine_box[0])) / 2, 745), engine_label, fill="black", font=box_font)
    draw_box(220, 845, 620, 1110, "Informative\nchannel MAC 1")
    draw_box(670, 845, 1070, 1110, "Informative\nchannel MAC 2")
    draw_box(1120, 845, 1520, 1110, "Informative\nchannel MAC 3")
    draw_box(1570, 845, 1980, 1110, "Redundant\nchannel MAC")

    draw_arrow(1100, 1220, 1100, 1320)
    draw_box(220, 1360, 980, 1550, "CRT reconstruction from the informative\nresidue channels")
    draw_box(1220, 1360, 1980, 1550, "Independent redundant-channel accumulation")
    draw_box(220, 1660, 980, 1850, "Balanced signed decoding and expected\nredundant-residue prediction")
    draw_box(1220, 1660, 1980, 1850, "Checker comparison between predicted and\nobserved redundant residues")
    draw_box(220, 1960, 980, 2140, "Recovered quantized fixed-point\nconvolution output")
    draw_box(1220, 1960, 1980, 2140, "Self-checking fault flag")

    draw_arrow(600, 1550, 600, 1660)
    draw_arrow(1600, 1550, 1600, 1660)
    draw_arrow(980, 1755, 1220, 1755)
    draw_arrow(600, 1850, 600, 1960)
    draw_arrow(1600, 1850, 1600, 1960)

    footer = (
        "Applies generically to the validated System A RRNS(17, 19, 23)+(29) and "
        "System B RRNS(29, 31, 37)+(41) component-level implementations."
    )
    footer_box = draw.multiline_textbbox((0, 0), footer, font=footer_font, align="center", spacing=6)
    draw.multiline_text(
        ((width - (footer_box[2] - footer_box[0])) / 2, height - 120),
        footer,
        fill="black",
        font=footer_font,
        align="center",
        spacing=6,
    )
    image.save(destination, dpi=(300, 300))


def replace_first_media_image(docx_path: Path, image_path: Path) -> None:
    tmp_path = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/media/image1.png":
                zout.writestr(item, image_path.read_bytes())
            else:
                zout.writestr(item, zin.read(item.filename))
    docx_path.unlink()
    tmp_path.rename(docx_path)


def enable_update_fields_on_open(docx_path: Path) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        settings_xml = zin.read("word/settings.xml")

    settings_root = parse_xml(settings_xml)
    if settings_root.find(qn("w:updateFields")) is None:
        update_fields = OxmlElement("w:updateFields")
        update_fields.set(qn("w:val"), "true")
        settings_root.append(update_fields)

    tmp_path = docx_path.with_suffix(".settings.tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/settings.xml":
                zout.writestr(item, settings_root.xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    docx_path.unlink()
    tmp_path.rename(docx_path)


def build_equation_paragraph(formula_text: str, number_text: str) -> OxmlElement:
    paragraph = OxmlElement("w:p")
    p_pr = OxmlElement("w:pPr")
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
    start_run.append(OxmlElement("w:tab"))
    paragraph.append(start_run)

    formula_run = OxmlElement("w:r")
    formula_rpr = OxmlElement("w:rPr")
    formula_fonts = OxmlElement("w:rFonts")
    formula_fonts.set(qn("w:ascii"), "Cambria Math")
    formula_fonts.set(qn("w:hAnsi"), "Cambria Math")
    formula_rpr.append(formula_fonts)
    formula_size = OxmlElement("w:sz")
    formula_size.set(qn("w:val"), "22")
    formula_rpr.append(formula_size)
    formula_run.append(formula_rpr)
    formula_text_element = OxmlElement("w:t")
    formula_text_element.text = formula_text
    formula_run.append(formula_text_element)
    paragraph.append(formula_run)

    end_run = OxmlElement("w:r")
    end_run.append(OxmlElement("w:tab"))
    paragraph.append(end_run)

    num_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    r_fonts = OxmlElement("w:rFonts")
    r_fonts.set(qn("w:ascii"), "Times New Roman")
    r_fonts.set(qn("w:hAnsi"), "Times New Roman")
    r_pr.append(r_fonts)
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "22")
    r_pr.append(size)
    num_run.append(r_pr)
    t = OxmlElement("w:t")
    t.text = number_text
    num_run.append(t)
    paragraph.append(num_run)
    return paragraph


def remove_image_paragraphs_by_media_targets(docx_path: Path, targets: set[str]) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        rels = zipfile.ZipFile(docx_path, "r").read("word/_rels/document.xml.rels")
        document_xml = zipfile.ZipFile(docx_path, "r").read("word/document.xml")

    rel_root = parse_xml(rels)
    rel_map = {rel.get("Id"): rel.get("Target") for rel in rel_root}
    document_root = parse_xml(document_xml)
    body = document_root.find(qn("w:body"))
    to_remove = []
    for child in list(body):
        if child.tag != qn("w:p"):
            continue
        blips = child.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
        child_targets = {
            rel_map.get(blip.get(qn("r:embed")))
            for blip in blips
            if rel_map.get(blip.get(qn("r:embed")))
        }
        if child_targets & targets:
            to_remove.append(child)
    for child in to_remove:
        body.remove(child)

    tmp_path = docx_path.with_suffix(".trim.tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, document_root.xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    docx_path.unlink()
    tmp_path.rename(docx_path)


def set_cell_margins(cell, top: int = 35, start: int = 55, bottom: int = 35, end: int = 55) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        element = tc_mar.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            tc_mar.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def format_table(table: Table, widths: list[float], body_font_size: int, header_font_size: int) -> None:
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:type"), "dxa")
            tc_w.set(qn("w:w"), str(int(width * 1440)))
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            for para in cell.paragraphs:
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = 1.0
                if r_idx == 0:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif c_idx == 0:
                    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                else:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if not para.runs:
                    para.add_run("")
                for run in para.runs:
                    set_run_font(run, size_pt=header_font_size if r_idx == 0 else body_font_size, bold=(r_idx == 0))


def refine_table_labels(doc: Document) -> None:
    clean_table = find_table_by_header(
        doc,
        ["Case", "Workload", "RRNS system", "Exact match rate", "Checker acceptance rate"],
    )
    clean_table.rows[0].cells[2].text = "RRNS\nsystem"

    fault_table = find_table_by_header(
        doc,
        [
            "Fault pattern",
            "System A detection",
            "System B detection",
            "System A harmful undetected",
            "System B harmful undetected",
            "System A mean |error|",
            "System B mean |error|",
        ],
    )
    fault_table.rows[0].cells[1].text = "System A\ndetection (%)"
    fault_table.rows[0].cells[2].text = "System B\ndetection (%)"
    fault_table.rows[0].cells[3].text = "System A harmful\nundetected (%)"
    fault_table.rows[0].cells[4].text = "System B harmful\nundetected (%)"
    fault_table.rows[0].cells[5].text = "System A mean\nabsolute error"
    fault_table.rows[0].cells[6].text = "System B mean\nabsolute error"

    rtl_table = find_table_by_header(
        doc,
        ["System", "RRNS configuration", "Testbench cases", "PASS checks", "FAIL checks", "Waveform available", "Verdict"],
    )
    rtl_table.rows[0].cells[1].text = "RRNS\nconfiguration"
    rtl_table.rows[0].cells[2].text = "Testbench\ncases"
    rtl_table.rows[0].cells[3].text = "PASS\nchecks"
    rtl_table.rows[0].cells[4].text = "FAIL\nchecks"
    rtl_table.rows[0].cells[5].text = "Waveform\navailable"

    appendix_table = find_table_by_header(
        doc,
        ["Row", "Col", "Baseline", "Information residues", "RNS output", "Faulted modulus", "Fault magnitude", "Faulty output", "Status", "Output error"],
    )
    appendix_table.rows[0].cells[3].text = "Info\nresidues"
    appendix_table.rows[0].cells[5].text = "Faulted\nmodulus"
    appendix_table.rows[0].cells[6].text = "Fault\nmag."
    appendix_table.rows[0].cells[8].text = "Status"
    appendix_table.rows[0].cells[9].text = "Out.\nerror"


def main() -> None:
    shutil.copy2(SOURCE, OUTPUT)
    doc = Document(OUTPUT)

    # Direct text updates in Chapters Three and Four.
    updates = {
        318: "The quantization stage was completed before the residue-domain experiments. The implemented fixed-point workflow used symmetric signed quantization with zero point 0, scale 2^f for each Q format, nearest-integer rounding, and saturation to the representable range. Chapter Four therefore reports the actual scaling factors, clipping counts, mean absolute error, and maximum absolute error for the tested Q4.4, Q5.5, and Q6.6 benchmark formats.",
        322: "For balanced signed interpretation, the admissible interval is",
        326: "The final experiment used two validated RRNS configurations rather than a single small base. System A, RRNS(17, 19, 23)+(29), provides an information dynamic range of 7429 and a balanced signed limit of ±3714, while System B, RRNS(29, 31, 37)+(41), provides an information dynamic range of 33263 and a balanced signed limit of ±16631. System A supported TC1–TC4 except for the highest-range workload, which used System B.",
        332: "The self-checking RRNS model adds one redundant modulus to the information base. In the validated experiments, the redundant modulus is 29 for System A and 41 for System B. The redundant channel receives the same activation and weight sequence and performs the equivalent modular MAC:",
        336: "Let X̂ denote the canonical CRT reconstruction from the information residues in [0, Mᵢ − 1]. The balanced signed result Xₛ is obtained by",
        338: "The expected redundant residue is then",
        340: "The checker compares the predicted redundant residue r̂ᵣ with the independently accumulated redundant residue rᵣ. The fault flag is defined as",
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
        368: "For both validated RTL systems, the same checker sequence is used: reconstruct from the informative residues, decode into the balanced signed interval, compute the expected redundant residue under the active modulus set, and compare it with the independently accumulated redundant residue. This description supersedes the earlier small proof-of-concept arithmetic example and matches the final System A and System B verification flow.",
        369: "The Verilog cases are now supported by independently executed Icarus Verilog simulation evidence. The observed simulator logs and waveform files confirm the clean-case outputs, fault-flag response, and known multi-channel limitation cases discussed later in Chapter Four and summarized again in Appendix B.",
        480: "Future work can extend the present component-level study by evaluating wider convolution layers, multi-channel feature maps, alternative modulus combinations, pipelined or sequential RRNS MAC organizations, fault localization or correction support, and the effect of arithmetic fault handling on higher-level inference behaviour. Such extensions should preserve the same careful distinction between functional arithmetic evidence and any later implementation-specific evaluation.",
        485: "• The Python findings apply to the four representative workloads TC1–TC4, the selected feature-map and kernel sizes, the evaluated Q formats, the validated System A and System B modulus sets, and the implemented residue-level fault patterns rather than to every possible Edge AI layer configuration.",
        486: "• The fault campaign covers the implemented five-pattern residue-level corruption study and does not establish universal fault coverage across all possible multi-channel or physical fault mechanisms.",
        500: "",
        509: "",
        513: "This appendix preserves a small illustrative Python example used to explain the residue workflow. It supplements, rather than defines, the final Chapter Four evidence, which is based on the four TC1–TC4 workloads, 141 clean outputs, 2,400 fault injections, and 41,714 clean-codeword checks.",
    }
    for index, text in updates.items():
        set_paragraph_text(doc.paragraphs[index], text)

    # Update configuration table.
    config_rows = [
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
    table = doc.tables[18]
    while len(table.rows) > len(config_rows):
        table._tbl.remove(table.rows[-1]._tr)
    while len(table.rows) < len(config_rows):
        table.add_row()
    for r_idx, row_values in enumerate(config_rows):
        for c_idx, value in enumerate(row_values):
            table.cell(r_idx, c_idx).text = value

    # Update formula source text before converting equation tables.
    replacements = {
        22: ["", "Xₛ = X̂ if 0 ≤ X̂ ≤ ⌊Mᵢ/2⌋; X̂ − Mᵢ if ⌊Mᵢ/2⌋ < X̂ < Mᵢ", "(3.9)"],
        23: ["", "r̂ᵣ = ⟨Xₛ⟩ₘᵣ", "(3.10)"],
        24: ["", "fault_flag = 0 if rᵣ = r̂ᵣ; 1 if rᵣ ≠ r̂ᵣ", "(3.11)"],
        25: ["", "X̂ = ⟨Σ(i=1 to k) rᵢMᵢNᵢ⟩Mᵢ", "(3.12)"],
        26: [
            ["", "Xₛ = X̂ if 0 ≤ X̂ ≤ ⌊Mᵢ/2⌋; X̂ − Mᵢ if ⌊Mᵢ/2⌋ < X̂ < Mᵢ", "(3.13)"],
            ["", "r̂ᵣ = ⟨Xₛ⟩ₘᵣ", "(3.14)"],
        ],
    }
    for idx, values in replacements.items():
        target = doc.tables[idx]
        if idx == 26:
            for ridx, rowvals in enumerate(values):
                for cidx, value in enumerate(rowvals):
                    target.cell(ridx, cidx).text = value
        else:
            for cidx, value in enumerate(values):
                target.cell(0, cidx).text = value

    # Remove duplicated Chapter Five block.
    for idx in range(490, 480, -1):
        remove_paragraph(doc.paragraphs[idx])

    # Convert Chapter 2 and 3 equation tables to Word equation paragraphs.
    chapter_four_index = 399
    equation_table_indices = list(range(0, 12)) + [13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
    tables_to_convert = [doc.tables[i] for i in equation_table_indices]
    for table in tables_to_convert:
        rows = [[" ".join(cell.text.split()) for cell in row.cells] for row in table.rows]
        for values in rows:
            para_xml = build_equation_paragraph(values[1], values[2])
            table._element.addprevious(para_xml)
        remove_table(table)

    # Global word repairs.
    global_replacements = {
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
        "convolutionlayer": "convolution-layer",
        "Reducedprecision": "Reduced-precision",
        "architectureaware": "architecture-aware",
        "TC1?TC4": "TC1–TC4",
        "TC1?TC4": "TC1–TC4",
        "6 ? 6": "6 × 6",
        "8 ? 8": "8 × 8",
        "9 ? 9": "9 × 9",
        "10 ? 10": "10 × 10",
        "3 ? 3": "3 × 3",
        "5 ? 5": "5 × 5",
        "?3714": "±3714",
        "?16631": "±16631",
        "Â±": "±",
    }
    for paragraph in doc.paragraphs:
        updated = paragraph.text
        for old, new in global_replacements.items():
            updated = updated.replace(old, new)
        if updated != paragraph.text:
            set_paragraph_text(paragraph, updated)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                updated = cell.text
                for old, new in global_replacements.items():
                    updated = updated.replace(old, new)
                if updated != cell.text:
                    cell.text = updated

    replace_paragraph_by_prefix(
        doc,
        "• The Python findings apply to 5 × 5 single-channel inputs",
        "• The Python findings apply to the four representative workloads TC1–TC4, the selected feature-map and kernel sizes, the evaluated Q formats, the validated System A and System B modulus sets, and the implemented residue-level fault patterns rather than to every possible Edge AI layer configuration.",
    )
    replace_paragraph_by_prefix(
        doc,
        "• The fault campaign covers the implemented single-residue corruption model",
        "• The fault campaign covers the implemented five-pattern residue-level corruption study and does not establish universal fault coverage across all possible multi-channel or physical fault mechanisms.",
    )

    # Tune only the problematic tables.
    format_table(
        find_table_by_header(doc, ["Case", "Workload", "RRNS system", "Exact match rate", "Checker acceptance rate"]),
        widths=[0.55, 1.75, 1.1, 1.45, 1.6],
        body_font_size=9,
        header_font_size=9,
    )
    format_table(
        find_table_by_header(doc, ["Parameter", "Implemented value"]),
        widths=[2.2, 4.0],
        body_font_size=10,
        header_font_size=10,
    )
    format_table(
        find_table_by_header(
            doc,
            ["Fault pattern", "System A detection", "System B detection", "System A harmful undetected", "System B harmful undetected", "System A mean |error|", "System B mean |error|"],
        ),
        widths=[1.55, 0.78, 0.78, 0.98, 0.98, 0.9, 0.9],
        body_font_size=8,
        header_font_size=8,
    )
    format_table(
        find_table_by_header(doc, ["System", "RRNS configuration", "Testbench cases", "PASS checks", "FAIL checks", "Waveform available", "Verdict"]),
        widths=[0.8, 1.8, 0.65, 0.65, 0.65, 0.8, 0.75],
        body_font_size=8,
        header_font_size=8,
    )
    format_table(
        find_table_by_header(doc, ["Criterion", "Conventional quantized fixed-point baseline", "Residue-domain clean model", "Self-checking RRNS MAC/checker"]),
        widths=[0.9, 1.7, 1.45, 2.0],
        body_font_size=8,
        header_font_size=8,
    )
    format_table(
        find_table_by_header(doc, ["Row", "Col", "Baseline", "Information residues", "RNS output", "Faulted modulus", "Fault magnitude", "Faulty output", "Status", "Output error"]),
        widths=[0.32, 0.32, 0.45, 0.9, 0.5, 0.58, 0.5, 0.58, 0.48, 0.58],
        body_font_size=7,
        header_font_size=7,
    )
    refine_table_labels(doc)

    doc.save(OUTPUT)

    # Replace Figure 3.1 with a generic architecture image.
    figure_path = DOCX_DIR / "figure_3_1_generic.png"
    build_generic_architecture_png(figure_path)
    replace_first_media_image(OUTPUT, figure_path)
    remove_image_paragraphs_by_media_targets(OUTPUT, {"media/image3.png", "media/image5.png"})
    enable_update_fields_on_open(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
