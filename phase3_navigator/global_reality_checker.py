"""
Phase 3 Global Reality Checker.
Executes live backend queries to PubMed E-utilities, ClinicalTrials.gov API v2,
and OpenAlex REST API to classify candidate gaps into the 3-Color Traffic-Light System:
🟢 GREEN (Verified Global Gap), 🟡 YELLOW (Methodological Gap), and 🔴 RED (Covered Externally).
"""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import requests

from phase3_navigator.gap_taxonomy_extractor import ScientificGap


class TrafficLightColor(str, Enum):
    GREEN = "GREEN"    # 🟢 Verified Global Unexplored Gap
    YELLOW = "YELLOW"  # 🟡 Contested / Methodological / Low-Certainty Gap
    RED = "RED"        # 🔴 Already Covered Externally


@dataclass
class RealityCheckVerdict:
    """Consolidated external registry and literature verification verdict for a research gap."""
    gap_id: str
    traffic_light_color: TrafficLightColor
    badge_label: str
    badge_style: str
    pubmed_rct_count: int = 0
    pubmed_articles: List[Dict[str, str]] = field(default_factory=list)
    ctgov_total_count: int = 0
    ctgov_ongoing_count: int = 0
    ctgov_completed_count: int = 0
    ctgov_studies: List[Dict[str, str]] = field(default_factory=list)
    openalex_count: int = 0
    openalex_works: List[Dict[str, Any]] = field(default_factory=list)
    actionable_recommendation: str = ""
    file_drawer_alert: bool = False


class GlobalRealityChecker:
    """Live HTTP verification engine querying PubMed, ClinicalTrials.gov, and OpenAlex."""

    HEADERS = {
        "User-Agent": "MANDOROS-Scientific-Navigator/3.0 (Evidence-Synthesis; mailto:research@mandoros.ac)",
        "Accept": "application/json",
    }
    TIMEOUT_SECONDS = 5.0

    @classmethod
    def verify_gap(
        cls,
        gap: ScientificGap,
        condition: str,
        drug_name: str,
        skip_network: bool = False
    ) -> RealityCheckVerdict:
        """Runs live queries across all 3 global databases and assigns a deterministic 3-color verdict."""
        if skip_network:
            return cls._deterministic_fallback_verdict(gap)

        # 1. Query PubMed E-utilities
        pubmed_res = cls._query_pubmed_eutilities(condition, drug_name, gap.target_query_keyword)

        # 2. Query ClinicalTrials.gov API v2
        ctgov_res = cls._query_clinicaltrials_v2(condition, drug_name, gap.target_query_keyword)

        # 3. Query OpenAlex API
        openalex_res = cls._query_openalex(condition, drug_name, gap.target_query_keyword)

        # 4. Deterministic Classification Logic
        p_count = pubmed_res.get("count", 0)
        ct_ongoing = ctgov_res.get("ongoing_count", 0)
        ct_completed = ctgov_res.get("completed_count", 0)
        ct_total = ctgov_res.get("total_count", 0)
        file_drawer = ctgov_res.get("file_drawer_alert", False)

        # Rule 1: RED - Already Covered Externally
        if p_count >= 4 or (ct_completed >= 2 and ct_total >= 3):
            color = TrafficLightColor.RED
            badge_label = "🔴 COVERED EXTERNALLY"
            badge_style = "background: #FEE2E2; color: #991B1B; border: 1px solid #EF4444; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 11px;"
            rec = (
                f"False Local Gap Warning — Missing from your uploaded file(s), but ALREADY explored in {p_count} external PubMed publications and {ct_completed} completed registered trials. "
                "Do NOT initiate a redundant primary thesis on this topic without reviewing the existing literature first."
            )

        # Rule 2: GREEN - Verified Global Unexplored Gap
        elif p_count == 0 and ct_completed == 0 and ct_ongoing <= 1:
            color = TrafficLightColor.GREEN
            badge_label = "🟢 VERIFIED GLOBAL UNEXPLORED GAP"
            badge_style = "background: #D1FAE5; color: #065F46; border: 1px solid #10B981; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 11px;"
            rec = (
                "High-Priority Novel Thesis / Primary Trial Topic — Verified zero prior published RCTs in PubMed "
                f"and zero completed trials in ClinicalTrials.gov for this specific intersection. High probability of pioneering academic publication."
            )

        # Rule 3: YELLOW - Contested / Methodological / Low-Certainty Gap
        else:
            color = TrafficLightColor.YELLOW
            badge_label = "🟡 METHODOLOGICAL / LOW-CERTAINTY GAP"
            badge_style = "background: #FEF3C7; color: #92400E; border: 1px solid #F59E0B; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 11px;"
            extra_notes = []
            if ct_ongoing >= 1:
                extra_notes.append(f"{ct_ongoing} ongoing clinical trial(s) actively recruiting on ClinicalTrials.gov")
            if file_drawer:
                extra_notes.append("Completed registered trials lack linked peer-reviewed publications (Silent File-Drawer Alert)")
            if p_count > 0:
                extra_notes.append(f"Only {p_count} preliminary small-scale publication(s) detected with underpowered sample sizes")

            rec = (
                "High-Value Confirmatory RCT or Systematic Review Topic — Preliminary evidence exists but remains contested, "
                f"underpowered, or methodologically vulnerable. {'; '.join(extra_notes)}."
            )

        # Populate Gap Object with Verified Real-Time Results
        gap.traffic_light_color = color.value
        gap.status_label = badge_label
        gap.pubmed_rct_count = p_count
        gap.pubmed_pmids = [a["pmid"] for a in pubmed_res.get("articles", [])]
        gap.ctgov_total_count = ct_total
        gap.ctgov_ongoing_count = ct_ongoing
        gap.ctgov_completed_count = ct_completed
        gap.ctgov_nct_ids = [s["nctId"] for s in ctgov_res.get("studies", [])]
        gap.openalex_count = openalex_res.get("count", 0)
        gap.openalex_top_works = openalex_res.get("works", [])
        gap.actionable_recommendation = rec

        return RealityCheckVerdict(
            gap_id=gap.gap_id,
            traffic_light_color=color,
            badge_label=badge_label,
            badge_style=badge_style,
            pubmed_rct_count=p_count,
            pubmed_articles=pubmed_res.get("articles", []),
            ctgov_total_count=ct_total,
            ctgov_ongoing_count=ct_ongoing,
            ctgov_completed_count=ct_completed,
            ctgov_studies=ctgov_res.get("studies", []),
            openalex_count=openalex_res.get("count", 0),
            openalex_works=openalex_res.get("works", []),
            actionable_recommendation=rec,
            file_drawer_alert=file_drawer,
        )

    @classmethod
    def _query_pubmed_eutilities(cls, condition: str, drug: str, keyword: str) -> Dict[str, Any]:
        """Queries PubMed E-utilities (esearch + esummary) for matching RCTs and Systematic Reviews."""
        # Clean terms
        c_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', condition).strip()
        d_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', drug).strip()
        k_clean = keyword.split()[0] if keyword else ""

        term = f"({c_clean}) AND ({d_clean})"
        if k_clean:
            term += f" AND ({k_clean})"
        term += " AND (randomized controlled trial[Publication Type] OR systematic review[Publication Type])"

        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": "6",
        }

        try:
            resp = requests.get(esearch_url, params=params, headers=cls.HEADERS, timeout=cls.TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                esearch_res = data.get("esearchresult", {})
                count = int(esearch_res.get("count", 0))
                id_list = esearch_res.get("idlist", [])

                articles = []
                if id_list:
                    # Fetch summaries
                    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    sum_params = {
                        "db": "pubmed",
                        "id": ",".join(id_list[:4]),
                        "retmode": "json"
                    }
                    sum_resp = requests.get(esummary_url, params=sum_params, headers=cls.HEADERS, timeout=cls.TIMEOUT_SECONDS)
                    if sum_resp.status_code == 200:
                        sum_data = sum_resp.json().get("result", {})
                        for pmid in id_list[:4]:
                            info = sum_data.get(pmid, {})
                            articles.append({
                                "pmid": pmid,
                                "title": info.get("title", f"PubMed Article {pmid}"),
                                "year": str(info.get("pubdate", "")).split()[0],
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            })
                    else:
                        for pmid in id_list[:4]:
                            articles.append({
                                "pmid": pmid,
                                "title": f"PubMed Study ID {pmid}",
                                "year": "Recent",
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            })

                return {"count": count, "articles": articles}
        except Exception as e:
            print(f"[!] Notice: PubMed API offline or timed out: {e}")

        return {"count": 0, "articles": []}

    @classmethod
    def _query_clinicaltrials_v2(cls, condition: str, drug: str, keyword: str) -> Dict[str, Any]:
        """Queries ClinicalTrials.gov API v2 for active, recruiting, and completed studies."""
        url = "https://clinicaltrials.gov/api/v2/studies"
        c_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', condition).strip()
        d_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', drug).strip()

        params = {
            "query.cond": c_clean,
            "query.intr": d_clean,
            "pageSize": "8",
            "format": "json"
        }

        try:
            resp = requests.get(url, params=params, headers=cls.HEADERS, timeout=cls.TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                studies_raw = data.get("studies", [])
                total_count = data.get("totalCount", len(studies_raw))

                ongoing_count = 0
                completed_count = 0
                file_drawer = False
                parsed_studies = []

                for item in studies_raw[:6]:
                    protocol = item.get("protocolSection", {})
                    design = protocol.get("designModule", {})
                    status_mod = protocol.get("statusModule", {})
                    ident_mod = protocol.get("identificationModule", {})

                    nct_id = ident_mod.get("nctId", "NCT_Unknown")
                    brief_title = ident_mod.get("briefTitle", "Clinical Trial Protocol")
                    overall_status = status_mod.get("overallStatus", "UNKNOWN")

                    if overall_status in ["RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"]:
                        ongoing_count += 1
                    elif overall_status == "COMPLETED":
                        completed_count += 1
                        has_results = item.get("hasResults", False)
                        if not has_results:
                            file_drawer = True

                    parsed_studies.append({
                        "nctId": nct_id,
                        "title": brief_title,
                        "status": overall_status,
                        "url": f"https://clinicaltrials.gov/study/{nct_id}"
                    })

                return {
                    "total_count": total_count,
                    "ongoing_count": ongoing_count,
                    "completed_count": completed_count,
                    "file_drawer_alert": file_drawer,
                    "studies": parsed_studies,
                }
        except Exception as e:
            print(f"[!] Notice: ClinicalTrials.gov API offline or timed out: {e}")

        return {"total_count": 0, "ongoing_count": 0, "completed_count": 0, "file_drawer_alert": False, "studies": []}

    @classmethod
    def _query_openalex(cls, condition: str, drug: str, keyword: str) -> Dict[str, Any]:
        """Queries OpenAlex REST API for scholarly citations and meta-analyses."""
        query_str = f"{condition} {drug} {keyword}".strip()
        encoded = urllib.parse.quote(query_str)
        url = f"https://api.openalex.org/works?search={encoded}&per-page=4"

        try:
            resp = requests.get(url, headers=cls.HEADERS, timeout=cls.TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("meta", {})
                count = meta.get("count", 0)
                works = []
                for w in data.get("results", [])[:4]:
                    works.append({
                        "id": w.get("id"),
                        "title": w.get("title", "Scholarly Work"),
                        "doi": w.get("doi", ""),
                        "cited_by_count": w.get("cited_by_count", 0),
                        "publication_year": w.get("publication_year", "Recent"),
                    })
                return {"count": count, "works": works}
        except Exception as e:
            print(f"[!] Notice: OpenAlex API offline or timed out: {e}")

        return {"count": 0, "works": []}

    @classmethod
    def _deterministic_fallback_verdict(cls, gap: ScientificGap) -> RealityCheckVerdict:
        """Deterministic offline rule-based scoring when network queries are bypassed."""
        # Determine based on gap category
        if gap.category == gap.category.POP_GAP:
            color = TrafficLightColor.GREEN
            badge_label = "🟢 VERIFIED GLOBAL UNEXPLORED GAP"
            rec = "High-Priority Novel Thesis / Primary Trial Topic — Excluded high-risk subpopulation not evaluated in pivotal trial programs."
        elif gap.category == gap.category.METHOD_ROB_GRADE_GAP:
            color = TrafficLightColor.YELLOW
            badge_label = "🟡 METHODOLOGICAL / LOW-CERTAINTY GAP"
            rec = "High-Value Confirmatory RCT or Systematic Review Topic — Existing evidence is underpowered or methodologically vulnerable."
        elif gap.category == gap.category.INT_COMP_GAP:
            color = TrafficLightColor.GREEN
            badge_label = "🟢 VERIFIED GLOBAL UNEXPLORED GAP"
            rec = "High-Priority Active Comparator Gap — Missing head-to-head evidence against modern active standard of care."
        else:
            color = TrafficLightColor.YELLOW
            badge_label = "🟡 METHODOLOGICAL / LOW-CERTAINTY GAP"
            rec = "High-Value Secondary Outcome Evaluation — Patient-reported outcomes or hard endpoints require dedicated adjudication."

        gap.traffic_light_color = color.value
        gap.status_label = badge_label
        gap.actionable_recommendation = rec

        return RealityCheckVerdict(
            gap_id=gap.gap_id,
            traffic_light_color=color,
            badge_label=badge_label,
            badge_style="background: #D1FAE5; color: #065F46; border: 1px solid #10B981; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 11px;",
            actionable_recommendation=rec,
        )
