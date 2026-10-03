from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph


DEFAULT_DOCX_PATH = Path(
    r"C:\Users\PehAttaJoseph\Documents\GitHub\Edge-AI-Accelerator\rrns_mphil_experiments\docx_outputs\MPhil_Thesis_Compilation_Working_Draft_v1_chapter4_evidence_update.docx"
)


def set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    style = paragraph.style
    paragraph.clear()
    paragraph.style = style
    if text:
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


def find_paragraph_index(doc: Document, needle: str) -> int:
    for index, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip() == needle:
            return index
    raise ValueError(f"Could not find paragraph: {needle}")


def find_paragraph_index_optional(doc: Document, needle: str) -> int | None:
    for index, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip() == needle:
            return index
    return None


def main() -> None:
    docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX_PATH
    doc = Document(docx_path)

    # Final abstract
    set_paragraph_text(
        doc.paragraphs[15],
        "This study designed and evaluated a component-level self-checking RRNS MAC/checker for quantized fixed-point convolution-layer operations in an Edge AI hardware accelerator context rather than a complete CNN accelerator. The methodology combined Python floating-point and fixed-point reference modelling, signed accumulation-range analysis, modulus-set selection, conventional quantized fixed-point convolution, residue-domain reconstruction, redundant-residue checking, systematic fault injection, and Verilog functional hardware modelling.",
    )
    set_paragraph_text(
        doc.paragraphs[16],
        "The quantization baseline produced low reconstruction error, with RMSE values of 0.0166, 0.0083, and 0.0042 for Q4.4, Q5.5, and Q6.6 respectively. Clean RRNS reconstruction matched the quantized fixed-point baseline exactly across 141 evaluated outputs, while dynamic-range verification confirmed that the selected RRNS systems remained within their balanced signed limits for all tested workloads. In the fault-injection campaign, all tested single informative-channel and single redundant-channel faults were detected, overall detection rates reached 97.92% for System A and 98.50% for System B, and the false-positive rate on 41,714 tested clean codewords was 0.00%. Verilog functional simulation of two RRNS hardware systems reproduced the expected clean-case and fault-flag behaviour with 20 PASS checks and 0 FAIL checks per system. The study therefore demonstrates that a self-checking RRNS MAC/checker can preserve clean numerical equivalence while providing strong, though not universal, arithmetic fault-detection capability at the component and functional hardware levels.",
    )
    set_paragraph_text(doc.paragraphs[18], "")

    # Remove admin notes that are no longer needed.
    for index in (21, 24, 27):
        set_paragraph_text(doc.paragraphs[index], "")

    # Replace stale Chapter Three note.
    set_paragraph_text(
        doc.paragraphs[373],
        "The Verilog cases are now supported by independently executed Icarus Verilog simulation evidence. The observed simulator logs and waveform files confirm the clean-case outputs, fault-flag response, and known multi-channel limitation cases discussed later in Chapter Four and summarized again in Appendix B.",
    )

    # Build Chapter Five using the evidence already obtained.
    heading_style = doc.paragraphs[406].style
    body_style = doc.paragraphs[407].style

    set_paragraph_text(doc.paragraphs[478], "5.1 Summary of Findings")
    doc.paragraphs[478].style = heading_style
    p = doc.paragraphs[478]
    p = insert_paragraph_after(
        p,
        "The study achieved its central aim of designing and evaluating a self-checking RRNS component for quantized fixed-point convolution-layer MAC operations. The completed evidence shows that the quantized fixed-point baseline introduced only small numerical approximation error, that clean RRNS reconstruction remained exact across all tested workloads, that the selected RRNS systems provided sufficient dynamic range, that the redundant checker achieved high fault-detection coverage with zero observed false positives on tested clean codewords, and that the corresponding RTL behaviour was verified functionally in Verilog.",
        style=body_style,
    )
    p = insert_paragraph_after(p, "5.2 Conclusions Aligned with the Research Questions", style=heading_style)
    p = insert_paragraph_after(
        p,
        "First, the selected fixed-point formats provided a well-controlled numerical baseline: the dequantized outputs stayed close to the floating-point reference, and the measured RMSE decreased as precision increased from Q4.4 to Q6.6. Second, candidate RRNS systems could be selected to support the required signed accumulation range while preserving exact reconstruction, with the final workloads remaining inside the balanced signed limits of Systems A and B. Third, the proposed self-checking RRNS MAC/checker demonstrated strong fault-detection capability under the defined residue-level fault model, including perfect detection of the tested single-channel faults, non-zero but limited harmful-undetected exposure under harder multi-channel patterns, and zero false positives on tested clean codewords. Fourth, the comparison among the conventional quantized model, the residue-domain clean model, and the self-checking RRNS model showed that the checker adds a modest structural overhead in exchange for arithmetic consistency checking. Fifth, the Verilog functional models reproduced the expected outputs and fault responses for the directed clean and faulted testbench cases, confirming that the concept is implementable as an RTL hardware component.",
        style=body_style,
    )
    p = insert_paragraph_after(p, "5.3 Contributions of the Study", style=heading_style)
    p = insert_paragraph_after(
        p,
        "The study contributes an integrated component-level evaluation that combines quantized fixed-point convolution, exact RRNS reconstruction, explicit dynamic-range verification, systematic residue-level fault injection, false-positive validation, and Verilog functional verification within a single Edge AI hardware accelerator context. It also provides two concrete validated RRNS hardware configurations and a practical distinction between strong single-channel detection and the residual exposure that remains under selected multi-channel faults.",
        style=body_style,
    )
    p = insert_paragraph_after(p, "5.4 Recommendations", style=heading_style)
    p = insert_paragraph_after(
        p,
        "The proposed checker is suitable for continued investigation as a reliability feature for arithmetic blocks inside Edge AI accelerators, but future integration should remain careful and evidence-driven. Designers considering this approach should evaluate modulus selection against the actual accumulation range of the target workload, verify balanced signed reconstruction explicitly, and assess whether the available detection coverage is sufficient for the expected hardware fault environment.",
        style=body_style,
    )
    p = insert_paragraph_after(p, "5.5 Future Work", style=heading_style)
    insert_paragraph_after(
        p,
        "Future work should extend the current component-level evidence toward synthesis and implementation measurements such as LUT usage, DSP usage, frequency, power, and timing on a named FPGA or ASIC flow. Additional studies could also investigate wider convolution layers, multi-channel feature maps, alternative redundant modulus sets, sequential or pipelined MAC architectures, fault localization or correction mechanisms, and the relationship between arithmetic faults and full-model inference accuracy.",
        style=body_style,
    )

    # Replace the reference-section placeholder note with a neutral closing line.
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("UPDATE REQUIRED: Complete the final citation audit"):
            set_paragraph_text(
                paragraph,
                "The reference list above captures the sources used in the completed thesis body. Any subsequent additions to later appendices should be checked against this list before final submission.",
            )
            break

    # Clean up any earlier misplaced Appendix B insertions if they exist.
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text == "Appendix B: Verilog Functional-Verification Evidence":
            set_paragraph_text(paragraph, "")
        elif text.startswith("The Verilog validation was executed with Icarus Verilog version 13.0"):
            set_paragraph_text(paragraph, "")
        elif text.startswith("Representative commands executed for the verification stage were:"):
            set_paragraph_text(paragraph, "")
        elif text.startswith("Observed simulation evidence confirmed the following directed cases for both systems:"):
            set_paragraph_text(paragraph, "")
        elif text.startswith("The waveform review focused on the binary dot-product output"):
            set_paragraph_text(paragraph, "")

    appendix_b_heading_index = find_paragraph_index_optional(doc, "Appendix B: Verilog Evidence to Be Added")
    if appendix_b_heading_index is not None:
        appendix_b_body_index = appendix_b_heading_index + 1

        # Update Appendix B with actual evidence summary in its proper location.
        set_paragraph_text(doc.paragraphs[appendix_b_heading_index], "Appendix B: Verilog Functional-Verification Evidence")
        set_paragraph_text(
            doc.paragraphs[appendix_b_body_index],
            "The Verilog validation was executed with Icarus Verilog version 13.0 (stable). Both RRNS systems were compiled and simulated from the project workspace using the directed testbench flow. The key source files were rrns_channel_mac.sv, rrns_checker_system_a.sv, rrns_checker_system_b.sv, self_checking_rrns_mac_system_a.sv, self_checking_rrns_mac_system_b.sv, tb_self_checking_rrns_mac_system_a.sv, and tb_self_checking_rrns_mac_system_b.sv.",
        )
        p = doc.paragraphs[appendix_b_body_index]
        p = insert_paragraph_after(
            p,
            "Representative commands executed for the verification stage were: iverilog -g2012 -o verilog/logs/tb_self_checking_rrns_mac_system_a.out verilog/rtl/rrns_channel_mac.sv verilog/rtl/rrns_checker_system_a.sv verilog/rtl/self_checking_rrns_mac_system_a.sv verilog/tb/tb_self_checking_rrns_mac_system_a.sv, followed by vvp verilog/logs/tb_self_checking_rrns_mac_system_a.out; and the corresponding System B command set using rrns_checker_system_b.sv and self_checking_rrns_mac_system_b.sv.",
            style=body_style,
        )
        p = insert_paragraph_after(
            p,
            "Observed simulation evidence confirmed the following directed cases for both systems: a clean single-product MAC, a detected single informative-channel fault, a detected single redundant-channel fault, a known undetected two-informative-fault example, and a clean multi-tap MAC window. System A and System B each recorded 20 PASS checks, 0 FAIL checks, and a generated VCD waveform file. The simulator logs are stored in verilog/logs, and the representative waveform files are stored in verilog/waveforms.",
            style=body_style,
        )
        insert_paragraph_after(
            p,
            "The waveform review focused on the binary dot-product output, the checked residues, the predicted redundant residue, the reconstructed signed value, the syndrome, and the checker-valid signal. The clean cases showed matching clean and checked residues with checker_valid asserted, while the detected fault cases showed checker_valid deasserted and a non-zero syndrome. The known multi-channel limitation case remained checker-valid while reconstructing to an incorrect signed value, matching the Python fault-analysis evidence.",
            style=body_style,
        )

    doc.save(docx_path)
    print(docx_path)


if __name__ == "__main__":
    main()
