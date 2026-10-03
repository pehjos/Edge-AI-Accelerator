# Thesis Template Distillation For Chapter Four

## Reference

- Reference DOCX: `C:\Users\PehAttaJoseph\Downloads\MPhil_Thesis_Compilation_Working_Draft_v1.docx`
- SHA-256: `d36d2329aa28cf4567ac05314cb5cd13fdd685111d515cc058b97836f1db8f1a`
- Evidence folder: [evidence](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/docx_style_reference/evidence)
- Structural snapshot: [template_structure.json](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/docx_style_reference/evidence/template_structure.json)
- Style lint snapshot: [template-style-evidence.json](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/docx_style_reference/evidence/template-style-evidence.json)
- Caption and role snapshot: [caption_and_roles.json](/C:/Users/PehAttaJoseph/Documents/GitHub/Edge-AI-Accelerator/rrns_mphil_experiments/docx_style_reference/evidence/caption_and_roles.json)
- Page count from DOCX properties: `74`
- Word count from DOCX properties: `16275`
- Paragraph count from DOCX properties: `217`

## Render Status

- Visual render QA could not be completed in this session.
- `render_docx.py` failed because the office conversion binary was unavailable.
- Word COM automation also failed in this environment.
- Result: this contract is based on DOCX package evidence and style metadata, not page-image inspection.

## Page System

- Section count: `3`
- All sections are `US Letter`, portrait, `8.5 x 11 in`
- Margins are consistent across sections: `1.0 in` on all sides
- Section 1:
  - `different_first_page = true`
  - header linked to previous
  - footer linked to previous
- Sections 2 and 3:
  - `different_first_page = false`
  - header linked to previous
  - footer not linked to previous
- Extracted footer content is page numbering only
- No header text was extracted from the package snapshot

## Core Typography

- Dominant font by character count: `Times New Roman`
- Body paragraph role is `Normal`
- `Normal` style tokens:
  - font: `Times New Roman`
  - size: `24 half-points = 12 pt`
  - alignment: `justified`
  - line spacing: `360 twips = 1.5 lines`
  - first-line indent: `720 twips = 0.5 in`
  - spacing after: `120 twips = 6 pt`
- Body text should therefore remain:
  - 12 pt Times New Roman
  - fully justified
  - first-line indented
  - 1.5-line spaced

## Heading Ladder

- `Heading1`:
  - size: `28 half-points = 14 pt`
  - bold
  - centered
  - black
  - spacing before: `200 twips = 10 pt`
  - no first-line indent
- `Heading2`:
  - based on `Normal`
  - bold
  - left-aligned
  - black
  - spacing before: `200 twips = 10 pt`
  - no first-line indent
- `Heading3`:
  - based on `Normal`
  - bold
  - left-aligned
  - black
  - spacing before: `200 twips = 10 pt`
  - no first-line indent

## Chapter Four Outline Contract

Use this exact structural pattern when adding or revising the experiment/results chapter:

- `Heading1`: `CHAPTER FOURRESULTS AND DISCUSSION`
- `Heading2`: `4.1 Introduction`
- `Heading2`: `4.2 Experimental Configuration`
- `Heading2`: `4.3 Quantized Fixed-Point Baseline Results`
- `Heading2`: `4.4 RNS Reconstruction and Exact Equivalence`
- `Heading2`: `4.5 Dynamic-Range Verification`
- `Heading2`: `4.6 RRNS Fault-Injection Results`
- `Heading3`: `4.6.1 Detection by Residue Channel`
- `Heading3`: `4.6.2 Detection by MAC Position and Convolution Window`
- `Heading2`: `4.7 Output-Error Magnitude and Undetected Faults`
- `Heading2`: `4.8 Redundant-Channel and Representation Overhead`
- `Heading2`: `4.9 Verilog Functional-Verification Status`
- `Heading2`: `4.10 Comparison of the Three Computational Models`
- `Heading2`: `4.11 Discussion in Relation to Prior Work`
- `Heading2`: `4.12 Limitations`
- `Heading2`: `4.13 Relationship of the Findings to the Research Gap`
- `Heading2`: `4.14 Chapter Summary`

## Captions And Display Items

- Caption roles are already defined in the document and should be reused, not recreated from scratch.
- `TableCaption`:
  - font: `Times New Roman`
  - size: `12 pt`
  - spacing before: `160 twips = 8 pt`
  - spacing after: `80 twips = 4 pt`
- `FigureCaption`:
  - font family inherits thesis defaults
  - centered
  - spacing before: `80 twips = 4 pt`
  - spacing after: `160 twips = 8 pt`
- The existing Chapter Four uses this caption pattern:
  - `Table 4.1 Python fault-injection experimental configuration`
  - `Table 4.2 Clean exact-equivalence results by test case`
  - `Figure 4.1 Observed maximum absolute convolution output by clean test case`
  - `Table 4.3 Information-range verification`
  - `Table 4.4 Aggregate RRNS fault-injection results`
  - `Table 4.5 Fault detection and output error by residue channel`
  - `Figure 4.2 Injected and detected faults by residue channel`
  - `Figure 4.3 Mean absolute reconstructed-output error by faulted residue channel`
  - `Table 4.6 Structural redundancy measures`
  - `Table 4.7 Expected Verilog functional cases`
  - `Table 4.8 Comparison of the conventional, RNS, and self-checking RRNS models`

## Tables

- The thesis contains `42` tables in total, including equation-layout tables and result tables.
- Result tables in Chapter Four are clearly numbered and introduced with table captions.
- Any new Chapter Four tables should:
  - stay within the existing Chapter Four numbering sequence
  - use the thesis `Table Caption` style
  - keep Times New Roman body text unless the source document already uses an exception
  - preserve the thesis’s formal report look rather than switching to spreadsheet-like styling

## Experiment Section Writing Pattern

When drafting or revising the experiment/results material, keep this pattern:

- Start each subsection with a short explanatory lead paragraph in thesis prose.
- Introduce each table or figure formally by number in the surrounding text.
- Present measured outcomes neutrally and academically.
- Do not overclaim beyond the actual generated data.
- Follow evidence with interpretation in prose, especially in `4.11`, `4.12`, and `4.13`.

## Safe Editing Rules For This Thesis

- Do not rebuild Chapter Four from a blank file.
- Edit inside a copy of the existing thesis document whenever the user asks for Word-document updates.
- Reuse the existing heading and caption styles already present in the DOCX.
- Preserve page numbering behavior and section structure unless the user explicitly asks to change them.
- Because the source uses substantial direct formatting, visually similar output may depend on editing in place rather than recreating styles from scratch.

## Mapping To The Python Experiment Project

The current Python project already aligns well with the extracted Chapter Four structure:

- `01_quantization_experiment.py` maps to `4.3 Quantized Fixed-Point Baseline Results`
- `02_clean_rns_equivalence.py` maps to `4.4 RNS Reconstruction and Exact Equivalence`
- `03_rrns_fault_injection.py` maps to `4.6 RRNS Fault-Injection Results`
- `04_false_positive_test.py` supports `4.7 Output-Error Magnitude and Undetected Faults`
- `05_generate_tables_and_figures.py` supports the summary material used in `4.10` and adjacent sections

## Unresolved Items

- Exact on-page visual spacing for cover-page direct formatting remains unresolved without page renders.
- Header placement and any invisible decorative elements could not be visually confirmed.
- Table border/fill specifics were not visually audited in this session.
- If a future task is to edit the DOCX itself, run a render-capable workflow before final delivery.
