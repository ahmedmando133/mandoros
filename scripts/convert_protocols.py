import os
import shutil
from pathlib import Path
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_PROTOCOLS_DIR = BASE_DIR / "master_protocols"
BACKEND_INSTRUCTIONS_DIR = BASE_DIR / "backend instructions"

MASTER_PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Copy the 4 original files
files_to_copy = [
    "Phase 1 extraction.json",
    "Phase 1 Prompt.docx",
    "Phase 2 Meta-analysis.docx",
    "Phase 2 meta-analysis.json"
]

for fname in files_to_copy:
    src = BACKEND_INSTRUCTIONS_DIR / fname
    dst = MASTER_PROTOCOLS_DIR / fname
    shutil.copy2(src, dst)
    print(f"Copied {fname} -> {dst}")

def table_to_markdown(table: Table) -> str:
    rows = []
    for r in table.rows:
        row_cells = []
        for cell in r.cells:
            # clean cell text, replace internal newlines with <br>
            cell_txt = cell.text.strip().replace("\r\n", "<br>").replace("\n", "<br>").replace("|", "\\|")
            row_cells.append(cell_txt)
        rows.append(row_cells)
    
    if not rows:
        return ""
    
    # Deduplicate repeated identical cells across columns (common in merged cells in docx)
    num_cols = max(len(r) for r in rows)
    # Ensure all rows have num_cols
    for r in rows:
        while len(r) < num_cols:
            r.append("")
            
    header = rows[0]
    separator = ["---"] * num_cols
    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |"
    ]
    for r in rows[1:]:
        md_lines.append("| " + " | ".join(r) + " |")
        
    return "\n" + "\n".join(md_lines) + "\n\n"

def paragraph_to_markdown(p: Paragraph) -> str:
    text = p.text.strip()
    if not text:
        return ""
    
    style_name = p.style.name.lower() if p.style else ""
    
    # Format runs (bold, italic)
    formatted_runs = []
    for r in p.runs:
        r_text = r.text
        if not r_text:
            continue
        if r.bold and r.italic:
            formatted_runs.append(f"***{r_text}***")
        elif r.bold:
            formatted_runs.append(f"**{r_text}**")
        elif r.italic:
            formatted_runs.append(f"*{r_text}*")
        else:
            formatted_runs.append(r_text)
    
    run_text = "".join(formatted_runs).strip()
    if not run_text:
        run_text = text
        
    if "heading 1" in style_name:
        return f"\n# {run_text}\n\n"
    elif "heading 2" in style_name:
        return f"\n## {run_text}\n\n"
    elif "heading 3" in style_name:
        return f"\n### {run_text}\n\n"
    elif "heading 4" in style_name:
        return f"\n#### {run_text}\n\n"
    elif "bullet" in style_name or "list" in style_name:
        return f"- {run_text}\n"
    
    # Check if the paragraph text itself looks like a major header (e.g. ALL CAPS and short)
    if text.isupper() and len(text) < 80 and not text.endswith("."):
        return f"\n## {text}\n\n"
    elif text.endswith(":") and len(text) < 80 and text.isupper():
        return f"\n### {text}\n\n"
        
    return f"{run_text}\n\n"

def convert_docx_to_markdown(docx_path: Path, output_md_path: Path):
    doc = docx.Document(docx_path)
    output_parts = []
    
    for child in doc.element.body:
        if child.tag.endswith('p'):
            p = Paragraph(child, doc)
            md_p = paragraph_to_markdown(p)
            if md_p:
                output_parts.append(md_p)
        elif child.tag.endswith('tbl'):
            t = Table(child, doc)
            md_t = table_to_markdown(t)
            if md_t:
                output_parts.append(md_t)
                
    content = "".join(output_parts)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Generated {output_md_path} ({len(content)} characters, {len(content.splitlines())} lines).")

if __name__ == "__main__":
    p1_docx = MASTER_PROTOCOLS_DIR / "Phase 1 Prompt.docx"
    p1_md = MASTER_PROTOCOLS_DIR / "phase1_master_instructions.md"
    convert_docx_to_markdown(p1_docx, p1_md)

    p2_docx = MASTER_PROTOCOLS_DIR / "Phase 2 Meta-analysis.docx"
    p2_md = MASTER_PROTOCOLS_DIR / "phase2_master_instructions.md"
    convert_docx_to_markdown(p2_docx, p2_md)
    print("Task 1 docx conversion completed.")
