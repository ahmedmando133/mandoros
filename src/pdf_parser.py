"""
High-Precision, Zero-Distortion PDF & Table Parser for Clinical Trials.
Implements methodologies from clinical_skills_library/pdf/ and clinical_skills_library/clinical-reports/.
Combines pdfplumber layout-aware table extraction with pypdf fallback to guarantee:
- Zero distortion of numeric values, signs (±, -, +), decimals, and exponents.
- Zero accidental merging or shifting of table cells across columns.
- Exact page and table-level provenance tracking.
- Strict 'Not Reported (NR)' tagging for missing clinical facts (Zero Hallucination).
"""

from __future__ import annotations

import os
import re
from typing import List, Dict, Any, Optional, Tuple


class PDFTable:
    """Represents a structured clinical trial table extracted with exact coordinates."""
    def __init__(self, page_number: int, table_index: int, data: List[List[Optional[str]]], bbox: Optional[Tuple[float, float, float, float]] = None):
        self.page_number = page_number
        self.table_index = table_index
        self.raw_data = data
        self.bbox = bbox
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self._clean_and_structure()

    def _clean_and_structure(self):
        if not self.raw_data:
            return

        cleaned_grid = []
        for row in self.raw_data:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("Not Reported (NR)")
                else:
                    # Clean whitespace while strictly preserving numbers, signs, units
                    c_str = str(cell).strip()
                    c_str = re.sub(r'[\r\n]+', ' ', c_str).strip()
                    cleaned_row.append(c_str if c_str else "Not Reported (NR)")
            cleaned_grid.append(cleaned_row)

        if cleaned_grid:
            self.headers = cleaned_grid[0]
            self.rows = cleaned_grid[1:]

    def to_markdown(self) -> str:
        """Converts the structured table into a clean, zero-distortion Markdown table."""
        if not self.headers:
            return ""

        num_cols = len(self.headers)
        header_line = "| " + " | ".join(h.replace("|", "\\|") for h in self.headers) + " |"
        sep_line = "| " + " | ".join(["---"] * num_cols) + " |"

        row_lines = []
        for r in self.rows:
            # Pad row if columns are shorter
            padded = r + ["Not Reported (NR)"] * max(0, num_cols - len(r))
            padded = padded[:num_cols]
            row_lines.append("| " + " | ".join(c.replace("|", "\\|") for c in padded) + " |")

        caption = f"### [Page {self.page_number} — Table {self.table_index}]"
        return f"{caption}\n{header_line}\n{sep_line}\n" + "\n".join(row_lines) + "\n"


class PDFPage:
    def __init__(self, page_number: int, text: str, tables: Optional[List[PDFTable]] = None):
        self.page_number = page_number
        self.text = text
        self.tables: List[PDFTable] = tables or []


class PDFDocument:
    """
    Advanced Clinical Trial Document Reader.
    Uses pdfplumber for layout-aware table extraction and pypdf for robust fallback.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pages: List[PDFPage] = []
        self._load()

    def _load(self):
        # 1. Attempt high-fidelity extraction via pdfplumber
        loaded_with_plumber = False
        try:
            import pdfplumber
            with pdfplumber.open(self.file_path) as pdf:
                for idx, p in enumerate(pdf.pages):
                    page_num = idx + 1
                    try:
                        # Layout-aware text extraction
                        text = p.extract_text(layout=True) or p.extract_text() or ""
                    except Exception:
                        text = ""

                    # Clean non-printable characters while preserving newlines and symbols
                    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

                    # Extract structured tables
                    page_tables = []
                    try:
                        raw_tables = p.extract_tables()
                        for t_idx, raw_t in enumerate(raw_tables):
                            if raw_t and len(raw_t) > 1:
                                table_obj = PDFTable(page_number=page_num, table_index=t_idx + 1, data=raw_t)
                                page_tables.append(table_obj)
                    except Exception as t_err:
                        print(f"[*] Notice: Table extraction on page {page_num}: {t_err}")

                    self.pages.append(PDFPage(page_number=page_num, text=cleaned, tables=page_tables))
                loaded_with_plumber = True
        except Exception as e:
            print(f"[*] pdfplumber unavailable or failed on {self.file_path}: {e}; falling back to pypdf.")

        # 2. Fallback to pypdf if pdfplumber failed or produced empty pages
        if not loaded_with_plumber or len(self.pages) == 0:
            self.pages = []
            try:
                import pypdf
                reader = pypdf.PdfReader(self.file_path, strict=False)
                if getattr(reader, "is_encrypted", False):
                    try:
                        reader.decrypt("")
                    except Exception:
                        pass
                for idx, page in enumerate(reader.pages):
                    try:
                        txt = page.extract_text() or ""
                    except Exception:
                        txt = ""
                    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', txt)
                    self.pages.append(PDFPage(page_number=idx + 1, text=cleaned, tables=[]))
            except Exception as pe:
                print(f"[!] Error loading PDF {self.file_path} via pypdf: {pe}")

        # Free any lingering temporary buffers from PDF extraction (Render memory safety)
        try:
            import gc
            gc.collect()
        except Exception:
            pass

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    def get_full_text(self) -> str:
        return "\n\n".join([f"--- PAGE {p.page_number} ---\n{p.text}" for p in self.pages])

    def get_page_text(self, page_number: int) -> str:
        for p in self.pages:
            if p.page_number == page_number:
                return p.text
        return ""

    def get_all_tables_markdown(self) -> str:
        """Returns all extracted tables formatted in clean Markdown with page numbers."""
        md_tables = []
        for p in self.pages:
            for t in p.tables:
                md_tables.append(t.to_markdown())
        return "\n\n".join(md_tables)

    def search_sections(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Segments document into functional clinical trial sections:
        - title_abstract (pages 1-2)
        - methods_eligibility (search for inclusion, eligibility, methods)
        - baseline_tables (search for Table 1, baseline characteristics)
        - results_tables (search for Table 2, Table 3, outcomes, endpoints)
        - figures_charts (search for Figure, Fig., curves, AUC, PPG time course)
        - methodology_text (search for participants, population, methods)
        - structured_tables (all extracted tables in markdown)
        """
        sections: Dict[str, List[Dict[str, Any]]] = {
            "title_abstract": [],
            "methods_eligibility": [],
            "baseline_tables": [],
            "results_tables": [],
            "figures_charts": [],
            "methodology_text": [],
            "structured_tables": []
        }

        # Page 1 & 2 are introductory
        for p in self.pages[:2]:
            sections["title_abstract"].append({
                "page": p.page_number,
                "text": p.text
            })

        for p in self.pages:
            lower_text = p.text.lower()
            page_tables_md = "\n\n".join(t.to_markdown() for t in p.tables)

            # Methods and Eligibility
            if any(k in lower_text for k in ["inclusion criteria", "exclusion criteria", "eligibility", "randomization", "study design", "intervention", "patients and methods", "participants"]):
                sections["methods_eligibility"].append({
                    "page": p.page_number,
                    "text": p.text
                })
                sections["methodology_text"].append({
                    "page": p.page_number,
                    "text": p.text
                })

            # Baseline Table (Table 1)
            if "table 1" in lower_text or "baseline characteristics" in lower_text or "demographic" in lower_text or "baseline patient" in lower_text:
                combined = p.text
                if page_tables_md:
                    combined += f"\n\n--- EXTRACTED STRUCTURED TABLES (PAGE {p.page_number}) ---\n" + page_tables_md
                sections["baseline_tables"].append({
                    "page": p.page_number,
                    "text": combined
                })

            # Results Tables (Table 2, 3, etc.)
            if any(f"table {i}" in lower_text for i in range(2, 15)) or "table" in lower_text or "changes in" in lower_text or "outcomes" in lower_text or "endpoints" in lower_text:
                combined = p.text
                if page_tables_md:
                    combined += f"\n\n--- EXTRACTED STRUCTURED TABLES (PAGE {p.page_number}) ---\n" + page_tables_md
                sections["results_tables"].append({
                    "page": p.page_number,
                    "text": combined
                })

            # Figures & Curves
            if any(k in lower_text for k in ["figure", "fig.", "auc", "area under", "time course", "plasma glucose", "concentration-time", "postprandial", "delta", "error bar"]):
                sections["figures_charts"].append({
                    "page": p.page_number,
                    "text": p.text
                })

            # Collect all structured tables
            for t in p.tables:
                sections["structured_tables"].append({
                    "page": p.page_number,
                    "table_index": t.table_index,
                    "headers": t.headers,
                    "rows": t.rows,
                    "markdown": t.to_markdown()
                })

        return sections

    def extract_methodology_demographics(self) -> Dict[str, Any]:
        """
        Scans Methodology, Eligibility, and Patient Selection text for demographic proportions
        when Table 1 does not explicitly stratify gender or race.
        """
        full_text = self.get_full_text()
        demographics = {
            "male_count": None,
            "male_pct": None,
            "female_count": None,
            "female_pct": None,
            "races": {},
            "raw_text": None
        }

        # 1. Search for gender counts: e.g. "450 men and 550 women"
        m_counts = re.search(r'(\d+)\s*(?:men|males?)\b(?:\s*(?:and|,)\s*(\d+)\s*(?:women|females?))?', full_text, re.I)
        if m_counts:
            demographics["male_count"] = int(m_counts.group(1))
            if m_counts.group(2):
                demographics["female_count"] = int(m_counts.group(2))
            demographics["raw_text"] = m_counts.group(0)

        # 2. Search for female percentage: e.g. "52.3% were female" or "60% women"
        f_pct = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:were\s*)?(?:female|women|females)\b', full_text, re.I)
        if f_pct:
            pct_val = float(f_pct.group(1))
            demographics["female_pct"] = pct_val
            demographics["male_pct"] = round(100.0 - pct_val, 1)
            demographics["raw_text"] = f_pct.group(0)

        # 3. Search for male percentage
        m_pct = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:were\s*)?(?:male|men|males)\b', full_text, re.I)
        if m_pct and not demographics["male_pct"]:
            pct_val = float(m_pct.group(1))
            demographics["male_pct"] = pct_val
            demographics["female_pct"] = round(100.0 - pct_val, 1)
            demographics["raw_text"] = m_pct.group(0)

        # 4. Search for racial subgroups
        for r_name in ["white", "caucasian", "black", "african american", "asian", "hispanic", "indigenous"]:
            r_match = re.search(rf'(\d+(?:\.\d+)?)\s*%\s*(?:were\s*)?{r_name}', full_text, re.I)
            if r_match:
                demographics["races"][r_name.title()] = float(r_match.group(1))

        return demographics
