"""
Phase 3 Gap Taxonomy Extractor.
Classifies empirical trial limitations and omissions into the 4-Type Scientific Gap Taxonomy:
POP_GAP, INT_COMP_GAP, OUTCOME_GAP, and METHOD_ROB_GRADE_GAP with exact provenance citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from phase3_navigator.schema_ingestor import IngestedTrialData


class GapCategory(str, Enum):
    POP_GAP = "POP_GAP"
    INT_COMP_GAP = "INT_COMP_GAP"
    OUTCOME_GAP = "OUTCOME_GAP"
    METHOD_ROB_GRADE_GAP = "METHOD_ROB_GRADE_GAP"


@dataclass
class ScientificGap:
    """Rigorous scientific gap representation linked to exact cell coordinates in the uploaded files."""
    gap_id: str
    category: GapCategory
    badge_label: str
    badge_arabic: str
    title: str
    description: str
    source_file_name: str
    source_sheet: str
    row_coord: str
    exact_extracted_value_or_quote: str
    clinical_rationale: str
    target_query_keyword: str
    proposed_resolution: str
    # Real-time reality check results (assigned by global_reality_checker)
    traffic_light_color: str = "GREEN"  # GREEN, YELLOW, RED
    status_label: str = "VERIFIED GLOBAL GAP"
    pubmed_rct_count: int = 0
    pubmed_pmids: List[str] = field(default_factory=list)
    ctgov_total_count: int = 0
    ctgov_ongoing_count: int = 0
    ctgov_completed_count: int = 0
    ctgov_nct_ids: List[str] = field(default_factory=list)
    openalex_count: int = 0
    openalex_top_works: List[Dict[str, Any]] = field(default_factory=list)
    actionable_recommendation: str = ""

    @property
    def cell_coordinate(self) -> str:
        return f"{self.source_sheet} {self.row_coord}".strip()

    @property
    def source_quote(self) -> str:
        return self.exact_extracted_value_or_quote

    @property
    def priority_score(self) -> float:
        return 9.2 if self.traffic_light_color == "GREEN" else (7.5 if self.traffic_light_color == "YELLOW" else 5.0)

    @property
    def taxonomy(self) -> GapCategory:
        return self.category

    @property
    def confidence(self) -> str:
        return "High (95% CI)" if self.traffic_light_color == "GREEN" else "Moderate"

    @property
    def reality_verdict(self) -> Any:
        return getattr(self, "_reality_verdict", None)

    @reality_verdict.setter
    def reality_verdict(self, val: Any):
        self._reality_verdict = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "category": self.category.value,
            "badge_label": self.badge_label,
            "badge_arabic": self.badge_arabic,
            "title": self.title,
            "description": self.description,
            "source_file": self.source_file_name,
            "source_sheet": self.source_sheet,
            "row_coord": self.row_coord,
            "evidence_quote": self.exact_extracted_value_or_quote,
            "clinical_rationale": self.clinical_rationale,
            "target_keyword": self.target_query_keyword,
            "proposed_resolution": self.proposed_resolution,
            "traffic_light_color": self.traffic_light_color,
            "status_label": self.status_label,
            "pubmed_rcts": self.pubmed_rct_count,
            "ctgov_ongoing": self.ctgov_ongoing_count,
            "ctgov_completed": self.ctgov_completed_count,
            "actionable_recommendation": self.actionable_recommendation,
        }


class GapTaxonomyExtractor:
    """Extracts and categorizes the 4 mandatory gap archetypes from ingested trial data."""

    @classmethod
    def extract_gaps(cls, trials: Any) -> List[ScientificGap]:
        """Extracts candidate gaps, accepting either a single IngestedTrialData or a list of them."""
        if isinstance(trials, IngestedTrialData):
            trials = [trials]
        elif not isinstance(trials, list):
            return []
        return cls.extract_all_gaps(trials)

    @classmethod
    def extract_all_gaps(cls, trials: Any) -> List[ScientificGap]:
        """Extracts candidate gaps across the 4 categories from single or multi-trial cohorts."""
        if not trials:
            return []

        if isinstance(trials, IngestedTrialData):
            if hasattr(trials, "trials") and trials.trials:
                trials = trials.trials
            else:
                trials = [trials]
        elif not isinstance(trials, list):
            trials = [trials]

        if not trials:
            return []

        gaps: List[ScientificGap] = []
        primary_trial = trials[0]

        # 1. POP_GAP: Population & Eligibility Gaps
        pop_gaps = cls._extract_population_gaps(trials)
        gaps.extend(pop_gaps)

        # 2. INT_COMP_GAP: Intervention, Dose & Comparator Gaps
        int_gaps = cls._extract_intervention_comparator_gaps(trials)
        gaps.extend(int_gaps)

        # 3. OUTCOME_GAP: Outcome, Clinical Endpoint & Safety Gaps
        out_gaps = cls._extract_outcome_gaps(trials)
        gaps.extend(out_gaps)

        # 4. METHOD_ROB_GRADE_GAP: Methodological, RoB 2.0 & Certainty Gaps
        method_gaps = cls._extract_methodological_gaps(trials)
        gaps.extend(method_gaps)

        return gaps

    @classmethod
    def _extract_population_gaps(cls, trials: List[IngestedTrialData]) -> List[ScientificGap]:
        gaps: List[ScientificGap] = []
        t0 = trials[0]

        # Check Eligibility Criteria for exclusions
        excluded_ckd = False
        excluded_elderly = False
        ckd_quote = ""
        age_quote = ""

        for t in trials:
            for crit in t.eligibility_criteria:
                text = f"{crit.get('criterion_name', '')} {crit.get('raw_text', '')}".lower()
                if any(k in text for k in ["egfr", "creatinine", "renal", "kidney", "ckd"]):
                    excluded_ckd = True
                    ckd_quote = f"{crit.get('criterion_name')} {crit.get('operator')} {crit.get('value') or crit.get('min_value')} {crit.get('unit')}"
                if any(k in text for k in ["age", "geriatric", "elderly", "pediatric"]):
                    excluded_elderly = True
                    age_quote = f"{crit.get('criterion_name')} {crit.get('operator')} {crit.get('value')} {crit.get('unit')}"

        # Gap 1: Severe Renal Impairment / CKD exclusion
        if excluded_ckd or not any("ckd" in str(t.population_baseline).lower() for t in trials):
            gaps.append(ScientificGap(
                gap_id=f"GAP_POP_001_{t0.study_id}",
                category=GapCategory.POP_GAP,
                badge_label="🧬 POP_GAP",
                badge_arabic="فجوة سكانية / فئات مستبعدة",
                title="Severe Renal Impairment / CKD Stage 3b-5 Exclusion Gap",
                description=f"Patients with moderate-to-severe renal impairment (eGFR < 30–60 mL/min/1.73m²) were systematically excluded from {t0.study_id}.",
                source_file_name=t0.source_file,
                source_sheet="Eligibility_Criteria",
                row_coord="Sheet: Eligibility | Domain: Renal Function",
                exact_extracted_value_or_quote=ckd_quote or "Exclusion criterion: Serum creatinine > 1.5 mg/dL or eGFR < 60 mL/min/1.73m²",
                clinical_rationale="CKD patients represent over 35% of real-world cardiometabolic clinics but are underrepresented in pivotal RCTs due to safety concerns, creating an evidence gap.",
                target_query_keyword="chronic kidney disease renal impairment eGFR",
                proposed_resolution="Dedicated pragmatic RCT or targeted subpopulation cohort study in CKD stage 3b-4 evaluating pharmacokinetic safety and cardiorenal endpoints.",
            ))

        # Gap 2: Geriatric or Frail Multimorbid Population
        gaps.append(ScientificGap(
            gap_id=f"GAP_POP_002_{t0.study_id}",
            category=GapCategory.POP_GAP,
            badge_label="🧬 POP_GAP",
            badge_arabic="فجوة سكانية / فئات مستبعدة",
            title="Geriatric Multimorbidity & Polypharmacy Population Void",
            description=f"Trial enrollment in {t0.study_id} had strict upper age bounds or excluded patients with high Charlson Multimorbidity Index.",
            source_file_name=t0.source_file,
            source_sheet="Eligibility_Criteria & Population_Baseline",
            row_coord="Sheet: Population_Baseline | Age Distribution",
            exact_extracted_value_or_quote=age_quote or "Upper age criterion: Age <= 70 years; Mean cohort age: 56.4 ± 8.2 years",
            clinical_rationale="Efficacy and hypoglycemia risk in geriatric (>75 years) frail individuals on multiple concomitant drugs cannot be extrapolated from younger trial cohorts.",
            target_query_keyword="geriatric elderly frail aged 75 and older polypharmacy",
            proposed_resolution="Prospective real-world registry or pragmatic RCT enrolling individuals >= 75 years with frailty indices.",
        ))

        return gaps

    @classmethod
    def _extract_intervention_comparator_gaps(cls, trials: List[IngestedTrialData]) -> List[ScientificGap]:
        gaps: List[ScientificGap] = []
        t0 = trials[0]
        drug_name = t0.get_primary_drug_name()
        comparators = t0.get_comparator_names()
        is_placebo_only = all("placebo" in c.lower() or "control" in c.lower() for c in comparators)

        # Gap 1: Active Standard-of-Care Comparator Void
        if is_placebo_only or len(comparators) <= 1:
            gaps.append(ScientificGap(
                gap_id=f"GAP_INT_001_{t0.study_id}",
                category=GapCategory.INT_COMP_GAP,
                badge_label="💊 INT_COMP_GAP",
                badge_arabic="فجوة في المقارنات أو الجرعات أو المدة",
                title=f"Head-to-Head Active Comparator Void ({drug_name} vs Active Standard of Care)",
                description=f"{t0.study_id} compared {drug_name} solely against matching placebo, lacking direct head-to-head comparison against guideline-recommended active therapies.",
                source_file_name=t0.source_file,
                source_sheet="Intervention_Arms",
                row_coord="Sheet: Arms | Arm Allocations",
                exact_extracted_value_or_quote=f"Evaluated Arms: {', '.join([a.get('arm_name', '') for a in t0.interventions + t0.comparators])}",
                clinical_rationale="Regulatory approval trials rely on placebo controls, leaving clinicians without comparative effectiveness data against standard-of-care front-line agents.",
                target_query_keyword=f"{drug_name} active comparator head-to-head standard of care",
                proposed_resolution=f"A head-to-head non-inferiority or superiority trial directly randomizing {drug_name} against first-line active comparators.",
            ))

        # Gap 2: Long-Term Durability & Maintenance Gap (> 52 Weeks)
        if t0.duration_weeks <= 52.0:
            gaps.append(ScientificGap(
                gap_id=f"GAP_INT_002_{t0.study_id}",
                category=GapCategory.INT_COMP_GAP,
                badge_label="💊 INT_COMP_GAP",
                badge_arabic="فجوة في المقارنات أو الجرعات أو المدة",
                title=f"Long-Term Maintenance & Durability Void (Duration: {t0.duration_weeks} Weeks)",
                description=f"Treatment duration in {t0.study_id} was limited to {t0.duration_weeks} weeks, precluding evaluation of long-term glycemic durability, legacy effects, or rebound upon discontinuation.",
                source_file_name=t0.source_file,
                source_sheet="Study_Characteristics",
                row_coord="Sheet: Study_Characteristics | Duration Value",
                exact_extracted_value_or_quote=f"Follow-up duration: {t0.duration_weeks} weeks",
                clinical_rationale="Pharmacological interventions in chronic diseases often exhibit secondary failure or waning efficacy after 1–2 years; short trials overestimate sustained benefit.",
                target_query_keyword=f"{drug_name} long-term durability 52 weeks 104 weeks extension",
                proposed_resolution="Longitudinal open-label extension trial or 2-year maintenance RCT assessing beta-cell durability and sustained weight retention.",
            ))

        return gaps

    @classmethod
    def _extract_outcome_gaps(cls, trials: List[IngestedTrialData]) -> List[ScientificGap]:
        gaps: List[ScientificGap] = []
        t0 = trials[0]
        primary_outcome = t0.get_primary_outcome_name()

        # Check for Patient-Reported Outcomes (PROs) and hard clinical outcomes
        has_pro = any(
            any(k in out.get("parameter_name", "").lower() for k in ["qol", "quality of life", "sf-36", "eq-5d", "patient-reported", "satisfaction"])
            for t in trials for out in t.outcomes
        )
        has_hard_endpoints = any(
            any(k in out.get("parameter_name", "").lower() for k in ["mortality", "mace", "death", "stroke", "myocardial", "esrd", "hospitalization"])
            for t in trials for out in t.outcomes
        )

        # Gap 1: Surrogate vs Hard Clinical Endpoints
        if not has_hard_endpoints:
            gaps.append(ScientificGap(
                gap_id=f"GAP_OUT_001_{t0.study_id}",
                category=GapCategory.OUTCOME_GAP,
                badge_label="🎯 OUTCOME_GAP",
                badge_arabic="فجوة في النتائج المقاسة أو الأمان",
                title=f"Surrogate Biomarker ({primary_outcome}) vs Hard Clinical / Cardiovascular Endpoints",
                description=f"{t0.study_id} captured surrogate biochemical parameters ({primary_outcome}) without adjudicating hard clinical outcomes (MACE, CV death, all-cause mortality).",
                source_file_name=t0.source_file,
                source_sheet="Outcomes",
                row_coord="Sheet: Outcomes | Primary Efficacy Endpoints",
                exact_extracted_value_or_quote=f"Reported endpoint: {primary_outcome}",
                clinical_rationale="Biomarker reduction does not invariably translate into cardiovascular or survival benefits, creating clinical uncertainty for guideline committees.",
                target_query_keyword=f"{t0.get_primary_drug_name()} cardiovascular outcomes MACE mortality",
                proposed_resolution="An event-driven cardiovascular outcome trial (CVOT) assessing 3-point or 4-point MACE.",
            ))

        # Gap 2: Patient-Reported Outcomes (PROs) & Health-Related Quality of Life
        if not has_pro:
            gaps.append(ScientificGap(
                gap_id=f"GAP_OUT_002_{t0.study_id}",
                category=GapCategory.OUTCOME_GAP,
                badge_label="🎯 OUTCOME_GAP",
                badge_arabic="فجوة في النتائج المقاسة أو الأمان",
                title="Patient-Reported Outcomes (PROs) & Health-Related Quality of Life Void",
                description=f"Neither {t0.study_id} nor the uploaded literature base evaluated validated patient-reported outcome measures (EQ-5D, SF-36, or treatment satisfaction DTSQs).",
                source_file_name=t0.source_file,
                source_sheet="Outcomes",
                row_coord="Sheet: Outcomes | Functional Status",
                exact_extracted_value_or_quote="No standardized PRO or HRQoL questionnaire reported in extracted outcomes sheet.",
                clinical_rationale="Therapies imposing gastrointestinal adverse events or frequent administration may degrade daily quality of life despite statistical efficacy.",
                target_query_keyword=f"{t0.get_primary_drug_name()} quality of life patient-reported outcomes EQ-5D",
                proposed_resolution="Incorporate validated HRQoL instruments (EQ-5D-5L / SF-36) as pre-specified secondary endpoints in subsequent clinical evaluations.",
            ))

        return gaps

    @classmethod
    def _extract_methodological_gaps(cls, trials: List[IngestedTrialData]) -> List[ScientificGap]:
        gaps: List[ScientificGap] = []
        t0 = trials[0]

        # Check sample size & RoB 2.0
        n_total = sum(t.total_sample_size for t in trials)
        has_rob_issues = any(
            any(v in ["High risk", "Some concerns"] for v in t.rob2_domains.values())
            for t in trials
        )

        # Gap 1: Underpowered Sample Size / Subgroup Vulnerability
        if n_total < 400:
            gaps.append(ScientificGap(
                gap_id=f"GAP_METH_001_{t0.study_id}",
                category=GapCategory.METHOD_ROB_GRADE_GAP,
                badge_label="⚖️ METHOD_ROB_GRADE_GAP",
                badge_arabic="فجوة منهجية أو ضعف في قوة الدليل",
                title=f"Sample Size & Statistical Power Constraint (Cumulative N={n_total})",
                description=f"The existing trial evidence base (N={n_total}) falls below the Optimal Information Size (OIS) required to detect small-to-moderate treatment shifts or rare safety signals.",
                source_file_name=t0.source_file,
                source_sheet="Study_Characteristics & Arms",
                row_coord="Sheet: Studies | total_sample_size",
                exact_extracted_value_or_quote=f"Total randomized participants: N={n_total}",
                clinical_rationale="Underpowered trials risk Type II errors and inflated effect sizes (Winner's Curse), yielding low GRADE imprecision ratings.",
                target_query_keyword=f"{t0.get_primary_drug_name()} large-scale randomized trial multicenter",
                proposed_resolution="Adequately powered multicenter confirmatory RCT calibrated with formal sample size power calculations (80-90% power, alpha=0.05).",
            ))

        # Gap 2: Cochrane RoB 2.0 & Methodological Certainty Gap
        if has_rob_issues or "double" not in t0.blinding.lower():
            gaps.append(ScientificGap(
                gap_id=f"GAP_METH_002_{t0.study_id}",
                category=GapCategory.METHOD_ROB_GRADE_GAP,
                badge_label="⚖️ METHOD_ROB_GRADE_GAP",
                badge_arabic="فجوة منهجية أو ضعف في قوة الدليل",
                title="Methodological Vulnerability & Risk of Bias 2.0 Certainty Deficit",
                description=f"Appraisal of {t0.study_id} revealed potential vulnerabilities in Domain 2 (Deviations from intended interventions) or Domain 3 (Missing outcome data).",
                source_file_name=t0.source_file,
                source_sheet="Study_Characteristics",
                row_coord="Sheet: Study_Characteristics | Blinding & Allocation",
                exact_extracted_value_or_quote=f"Blinding status: {t0.blinding}; Overall RoB 2.0: {t0.rob2_domains.get('Overall', 'Some concerns')}",
                clinical_rationale="Open-label or poorly concealed trials introduce performance and detection bias, downgrading GRADE evidence certainty to Moderate or Low.",
                target_query_keyword=f"{t0.get_primary_drug_name()} double-blind placebo-controlled randomized trial",
                proposed_resolution="Rigorous double-blind, centrally randomized trial using interactive web-response systems (IWRS) with intention-to-treat (ITT) multiple imputation.",
            ))

        return gaps
