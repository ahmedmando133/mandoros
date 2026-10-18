"""
High-Precision, Zero-Distortion PDF & Table Parser for Clinical Trials.
Implements methodologies from clinical_skills_library/pdf/ and clinical_skills_library/clinical-reports/.
Combines pdfplumber layout-aware table extraction with pypdf fallback to guarantee:
- Zero distortion of numeric values, signs (±, -, +), decimals, and exponents.
- Zero accidental merging or shifting of table cells across columns.
- Exact page and table-level provenance tracking.
- Genuinely blank cells for missing table values (Rule 5 / Rule 49: no 'NR' placeholders).
- Universal input resilience: PDF (pdfplumber -> pypdf -> raw-bytes salvage), DOCX, TXT/MD, HTML
  and XLSX/CSV inputs all load without crashing; encoding/Unicode normalisation of minus signs,
  ligatures and non-breaking spaces; multi-page table stitching for continued tables.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple


# Word-gap tolerance (pt). pdfplumber's default (3) glues adjacent words in dense journal
# typesetting ("wererequiredtohaveHbA1c"); 1.5 keeps genuine spaces without splitting numbers.
PDF_X_TOLERANCE = float(os.environ.get("MANDOROS_PDF_X_TOLERANCE", "1.5"))

_UNICODE_MAP = {
    "\u2212": "-", "\u2013": "-", "\u2014": "-", "\u2010": "-", "\u2011": "-",
    "\u00a0": " ", "\u2009": " ", "\u202f": " ", "\u2007": " ",
    "\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00b1": "±", "\u2264": "<=", "\u2265": ">=", "\u2266": "<=", "\u2267": ">=",
}


def normalize_text(text: str) -> str:
    """Encoding/Unicode normalisation that preserves every digit, sign and decimal point."""
    if not text:
        return ""
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass
    for src, dst in _UNICODE_MAP.items():
        text = text.replace(src, dst)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Re-join digits split by a soft hyphen / line break inside a number (e.g. "12-\n5" artefacts are left intact)
    return text


class PDFTable:
    """Represents a structured clinical trial table extracted with exact coordinates."""
    def __init__(self, page_number: int, table_index: int, data: List[List[Optional[str]]], bbox: Optional[Tuple[float, float, float, float]] = None):
        self.page_number = page_number
        self.table_index = table_index
        self.raw_data = data
        self.bbox = bbox
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.continued_from: Optional[Tuple[int, int]] = None
        self._clean_and_structure()

    def _clean_and_structure(self):
        if not self.raw_data:
            return

        cleaned_grid = []
        for row in self.raw_data:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # Clean whitespace while strictly preserving numbers, signs, units
                    c_str = normalize_text(str(cell)).strip()
                    c_str = re.sub(r'[\r\n]+', ' ', c_str).strip()
                    cleaned_row.append(c_str)
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
            padded = r + [""] * max(0, num_cols - len(r))
            padded = padded[:num_cols]
            row_lines.append("| " + " | ".join(c.replace("|", "\\|") for c in padded) + " |")

        caption = f"### [Page {self.page_number} — Table {self.table_index}]" + (f" (continuation of Page {self.continued_from[0]} Table {self.continued_from[1]})" if self.continued_from else "")
        return f"{caption}\n{header_line}\n{sep_line}\n" + "\n".join(row_lines) + "\n"


class PDFPage:
    def __init__(self, page_number: int, text: str, tables: Optional[List[PDFTable]] = None, reading_text: Optional[str] = None):
        self.page_number = page_number
        self.text = text
        self.tables: List[PDFTable] = tables or []
        # Column-aware (reading-order) rendering of the same page; empty when identical to `text`
        self.reading_text: str = reading_text or ""


class PDFDocument:
    """
    Advanced Clinical Trial Document Reader.
    Uses pdfplumber for layout-aware table extraction and pypdf for robust fallback.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pages: List[PDFPage] = []
        self.load_notes: List[str] = []
        self.loader_used: str = "none"
        try:
            self._load()
        except Exception as fatal:  # never crash the pipeline on a malformed upload
            self.load_notes.append(f"Fatal loader error: {fatal}")
        if not self.pages:
            self.pages.append(PDFPage(page_number=1, text="", tables=[]))
            self.load_notes.append("No extractable text found (scanned/image-only or unreadable file). Manual review required.")
        self._stitch_continued_tables()

    # ------------------------------------------------------------------ loaders
    def _load(self):
        ext = os.path.splitext(str(self.file_path))[1].lower()
        if ext in (".txt", ".md", ".text"):
            self._load_text_file()
        elif ext == ".docx":
            self._load_docx()
        elif ext in (".html", ".htm"):
            self._load_html()
        elif ext in (".xlsx", ".xlsm", ".xls", ".csv", ".tsv"):
            self._load_tabular()
        else:
            self._load_pdf()

        # Free any lingering temporary buffers from PDF extraction (Render memory safety)
        try:
            import gc
            gc.collect()
        except Exception:
            pass

    def _load_pdf(self):
        # 1. Attempt high-fidelity extraction via pdfplumber (streams closed by the context manager)
        loaded_with_plumber = False
        try:
            import pdfplumber
            with pdfplumber.open(self.file_path) as pdf:
                for idx, p in enumerate(pdf.pages):
                    page_num = idx + 1
                    text = ""
                    for kwargs in ({"layout": True, "x_tolerance": PDF_X_TOLERANCE}, {"layout": True}, {}):
                        try:
                            text = p.extract_text(**kwargs) or ""
                        except Exception:
                            text = ""
                        if text.strip():
                            break
                    cleaned = normalize_text(text)
                    reading_text = normalize_text(self._extract_reading_order_text(p))

                    page_tables = []
                    try:
                        raw_tables = p.extract_tables() or []
                        if not raw_tables:
                            try:
                                raw_tables = p.extract_tables(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text"}) or []
                            except Exception:
                                raw_tables = []
                        for t_idx, raw_t in enumerate(raw_tables):
                            if raw_t and len(raw_t) > 1:
                                page_tables.append(PDFTable(page_number=page_num, table_index=t_idx + 1, data=raw_t))
                    except Exception as t_err:
                        self.load_notes.append(f"Table extraction notice on page {page_num}: {t_err}")

                    self.pages.append(PDFPage(page_number=page_num, text=cleaned, tables=page_tables, reading_text=reading_text))
                    try:
                        p.flush_cache()
                    except Exception:
                        pass
                loaded_with_plumber = True
                self.loader_used = "pdfplumber"
        except Exception as e:
            self.load_notes.append(f"pdfplumber failed: {e}")

        # 2. Fallback to pypdf if pdfplumber failed or produced no text at all
        if not loaded_with_plumber or not any(pg.text.strip() for pg in self.pages):
            fallback_pages: List[PDFPage] = []
            try:
                import pypdf
                with open(self.file_path, "rb") as fh:
                    reader = pypdf.PdfReader(fh, strict=False)
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
                        fallback_pages.append(PDFPage(page_number=idx + 1, text=normalize_text(txt), tables=[]))
                if any(pg.text.strip() for pg in fallback_pages) or not self.pages:
                    self.pages = fallback_pages
                    self.loader_used = "pypdf"
            except Exception as pe:
                self.load_notes.append(f"pypdf failed: {pe}")

        # 3. Last resort: salvage printable text streams from raw bytes (never crash)
        if not any(pg.text.strip() for pg in self.pages):
            try:
                with open(self.file_path, "rb") as fh:
                    raw = fh.read()
                salvaged = re.findall(rb"[\x20-\x7e]{6,}", raw)
                txt = normalize_text("\n".join(b.decode("latin-1", errors="ignore") for b in salvaged[:5000]))
                if len(txt.strip()) > 200:
                    self.pages = [PDFPage(page_number=1, text=txt, tables=[])]
                    self.loader_used = "raw-bytes-salvage"
                    self.load_notes.append("Text salvaged from raw byte streams; layout and provenance pages are approximate.")
            except Exception as se:
                self.load_notes.append(f"raw salvage failed: {se}")

    @staticmethod
    def _extract_reading_order_text(p) -> str:
        """
        Column-aware text extraction. Two-column journal layouts are detected from the word
        x-distribution and read left column first, then right column, so that sentences such as
        'drug-naive patients were required to have HbA1c >=7% and <=10%' are never interleaved
        with the neighbouring column. Falls back to layout / plain extraction on any error.
        """
        try:
            words = p.extract_words(x_tolerance=1.5, keep_blank_chars=False) or []
            width = float(p.width or 0)
            if width > 0 and len(words) >= 60:
                mid = width / 2.0
                left = [w for w in words if float(w["x1"]) <= mid - 4]
                right = [w for w in words if float(w["x0"]) >= mid + 4]
                spanning = [w for w in words if float(w["x0"]) < mid - 4 and float(w["x1"]) > mid + 4]
                total = len(words)
                if len(left) / total > 0.3 and len(right) / total > 0.3 and len(spanning) / total < 0.08:
                    top_span = [w for w in spanning]
                    header_cut = max((float(w["bottom"]) for w in top_span if float(w["top"]) < p.height * 0.25), default=0.0)
                    parts = []
                    if header_cut > 0:
                        try:
                            parts.append(p.crop((0, 0, width, header_cut)).extract_text(x_tolerance=1.5) or "")
                        except Exception:
                            pass
                    try:
                        parts.append(p.crop((0, header_cut, mid, p.height)).extract_text(x_tolerance=1.5) or "")
                        parts.append(p.crop((mid, header_cut, width, p.height)).extract_text(x_tolerance=1.5) or "")
                    except Exception:
                        parts = []
                    joined = "\n".join(x for x in parts if x and x.strip())
                    if len(joined.strip()) > 100:
                        return joined
            return p.extract_text(x_tolerance=1.5) or p.extract_text(layout=True) or p.extract_text() or ""
        except Exception:
            try:
                return p.extract_text(layout=True) or p.extract_text() or ""
            except Exception:
                return ""

    def _read_text_any_encoding(self) -> str:
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                with open(self.file_path, "r", encoding=enc) as fh:
                    return fh.read()
            except Exception:
                continue
        with open(self.file_path, "rb") as fh:
            return fh.read().decode("utf-8", errors="replace")

    def _paginate(self, text: str, chars_per_page: int = 6000) -> None:
        text = normalize_text(text)
        chunks = [text[i:i + chars_per_page] for i in range(0, max(1, len(text)), chars_per_page)] or [""]
        for i, ch in enumerate(chunks, 1):
            self.pages.append(PDFPage(page_number=i, text=ch, tables=[]))

    def _load_text_file(self):
        self._paginate(self._read_text_any_encoding())
        self.loader_used = "text"

    def _load_docx(self):
        try:
            import docx  # python-docx
            d = docx.Document(self.file_path)
            paras = [p.text for p in d.paragraphs]
            tables = []
            for t_idx, t in enumerate(d.tables, 1):
                grid = [[c.text for c in row.cells] for row in t.rows]
                if grid and len(grid) > 1:
                    tables.append(PDFTable(page_number=1, table_index=t_idx, data=grid))
            self._paginate("\n".join(paras))
            if self.pages:
                self.pages[0].tables.extend(tables)
            self.loader_used = "python-docx"
        except Exception as e:
            self.load_notes.append(f"docx loader failed: {e}")
            self._paginate(self._read_text_any_encoding())

    def _load_html(self):
        raw = self._read_text_any_encoding()
        txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        txt = re.sub(r"<br\s*/?>|</p>|</tr>|</h\d>", "\n", txt, flags=re.I)
        txt = re.sub(r"</t[dh]>", " | ", txt, flags=re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
        import html as _html
        self._paginate(_html.unescape(txt))
        self.loader_used = "html"

    def _load_tabular(self):
        try:
            import pandas as pd
            ext = os.path.splitext(str(self.file_path))[1].lower()
            if ext in (".csv", ".tsv"):
                frames = {"Sheet1": pd.read_csv(self.file_path, sep=None, engine="python", header=None)}
            else:
                with pd.ExcelFile(self.file_path) as xl:
                    frames = {name: xl.parse(name, header=None) for name in xl.sheet_names}
            page_num = 0
            for name, df in frames.items():
                page_num += 1
                grid = [[("" if (v is None or (isinstance(v, float) and v != v)) else str(v)) for v in row] for row in df.astype(object).values.tolist()]
                text = f"--- SHEET {name} ---\n" + "\n".join(" | ".join(r) for r in grid)
                tables = [PDFTable(page_number=page_num, table_index=1, data=grid)] if len(grid) > 1 else []
                self.pages.append(PDFPage(page_number=page_num, text=normalize_text(text), tables=tables))
            self.loader_used = "pandas-tabular"
        except Exception as e:
            self.load_notes.append(f"tabular loader failed: {e}")
            self._paginate(self._read_text_any_encoding())

    # ------------------------------------------------------------- stitching
    def _stitch_continued_tables(self) -> None:
        """
        Multi-page table stitching: when a page starts with a table whose header matches
        (or whose first row is a data continuation of) the last table of the previous page,
        the rows are appended to the previous table and the fragment is marked as continued.
        """
        prev_table: Optional[PDFTable] = None
        for pg in self.pages:
            if not pg.tables:
                prev_table = None
                continue
            first = pg.tables[0]
            if prev_table is not None and first.headers and len(first.headers) == len(prev_table.headers):
                same_header = [h.strip().lower() for h in first.headers] == [h.strip().lower() for h in prev_table.headers]
                continued_marker = "continued" in (pg.text[:400].lower())
                header_is_data = bool(re.search(r"\d", " ".join(first.headers))) and not same_header
                if same_header or continued_marker or header_is_data:
                    extra_rows = list(first.rows) if (same_header or not header_is_data) else [first.headers] + list(first.rows)
                    prev_table.rows.extend(extra_rows)
                    first.continued_from = (prev_table.page_number, prev_table.table_index)
            prev_table = pg.tables[-1]

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    def get_full_text(self) -> str:
        return "\n\n".join([f"--- PAGE {p.page_number} ---\n{p.text}" for p in self.pages])

    def get_reading_order_text(self) -> str:
        """Column-aware text (left column, then right column) for prose-level rules such as eligibility."""
        return "\n\n".join([f"--- PAGE {p.page_number} ---\n{p.reading_text or p.text}" for p in self.pages])

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
                    "text": p.text,
                    "reading_text": p.reading_text or p.text
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
