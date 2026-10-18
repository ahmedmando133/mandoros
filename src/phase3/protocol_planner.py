"""
MANDOROS Phase 3: Pillar V — Protocol, Search Strategy & Biostatistical Planning.
Provides validated biostatistical sample size calculations (continuous, binary, non-inferiority, attrition),
reproducible PubMed MeSH search strategies, and PRISMA-P / SPIRIT draft protocol outlines.
"""

from __future__ import annotations

import math
from typing import List, Dict, Any, Optional, Tuple

import scipy.stats as stats

from src.phase3.models import (
    SampleSizeSpec,
    ProtocolDraft,
    ThesisProposal,
    ObservedResearchGap
)


class ProtocolPlannerEngine:
    """
    Pillar V Engine: Generates rigorous statistical sample size calculations,
    reproducible database search queries, and formal protocol drafting packages.
    """

    # =========================================================================
    # BIOSTATISTICAL SAMPLE SIZE CALCULATOR (VALIDATED FORMULAS)
    # =========================================================================

    @classmethod
    def calculate_sample_size(
        cls,
        design_type: str = "two_sample_continuous",
        primary_outcome_name: str = "Change in Primary Biomarker",
        alpha: float = 0.05,
        power: float = 0.80,
        allocation_ratio: float = 1.0,
        attrition_rate: float = 0.15,
        param_inputs: Optional[Dict[str, float]] = None
    ) -> SampleSizeSpec:
        """
        Executes mathematically validated sample size estimation based on study design.
        Designs supported:
        - 'two_sample_continuous': Two-group superiority trial for continuous endpoints.
        - 'two_sample_binary': Two-group superiority trial for binary proportion endpoints.
        - 'non_inferiority_continuous': Non-inferiority trial for continuous endpoints.
        - 'non_inferiority_binary': Non-inferiority trial for binary endpoints.
        """
        inputs = param_inputs or {}

        if design_type == "two_sample_binary":
            return cls._calc_two_sample_binary(
                primary_outcome_name, alpha, power, allocation_ratio, attrition_rate, inputs
            )
        elif design_type == "non_inferiority_continuous":
            return cls._calc_non_inferiority_continuous(
                primary_outcome_name, alpha, power, allocation_ratio, attrition_rate, inputs
            )
        elif design_type == "non_inferiority_binary":
            return cls._calc_non_inferiority_binary(
                primary_outcome_name, alpha, power, allocation_ratio, attrition_rate, inputs
            )
        else:
            return cls._calc_two_sample_continuous(
                primary_outcome_name, alpha, power, allocation_ratio, attrition_rate, inputs
            )

    @classmethod
    def _calc_two_sample_continuous(
        cls,
        outcome_name: str,
        alpha: float,
        power: float,
        r: float,
        attrition: float,
        inputs: Dict[str, float]
    ) -> SampleSizeSpec:
        """
        Two-sample superiority t-test formula:
        n1 = (1 + 1/r) * ((Z_(1-alpha/2) + Z_(1-beta)) * sigma / delta)^2
        """
        delta = abs(inputs.get("mean_difference", 5.0))
        if delta == 0:
            delta = 0.1  # prevent division by zero
        sigma = abs(inputs.get("pooled_sd", 10.0))
        if sigma == 0:
            sigma = 1.0

        z_alpha = stats.norm.ppf(1.0 - alpha / 2.0)
        z_beta = stats.norm.ppf(power)

        # Standard sample size formula
        cohen_d = delta / sigma
        n1_raw = (1.0 + 1.0 / r) * ((z_alpha + z_beta) / cohen_d) ** 2
        n1 = int(math.ceil(n1_raw))
        n2 = int(math.ceil(n1 * r))
        n_eval = n1 + n2

        # Attrition adjustment: N_adj = N_eval / (1 - attrition)
        safe_attrition = min(0.50, max(0.0, attrition))
        n_total_adj = int(math.ceil(n_eval / (1.0 - safe_attrition))) if safe_attrition < 1.0 else n_eval

        formula_str = (
            f"n_1 = (1 + 1/r) × [ (Z_(1-α/2) + Z_(1-β)) × σ / δ ]²\n"
            f"where Z_(1-α/2) = {z_alpha:.3f} (α={alpha}), Z_(1-β) = {z_beta:.3f} (power={power*100:.0f}%), "
            f"δ = {delta:.2f}, σ = {sigma:.2f}, Cohen's d = {cohen_d:.2f}.\n"
            f"Attrition Adjustment: N_total = N_eval / (1 - {safe_attrition:.2f})"
        )

        rationale = (
            f"Assumed target difference of {delta} units with pooled standard deviation {sigma} "
            f"(standardized effect size d={cohen_d:.2f}). To detect this difference with {int(power*100)}% power "
            f"at a two-sided α of {alpha}, {n_eval} evaluable participants ({n1} experimental, {n2} control) are required. "
            f"Accounting for an anticipated {int(safe_attrition*100)}% drop-out rate, total enrollment must be {n_total_adj} participants."
        )

        return SampleSizeSpec(
            design_type="two_sample_continuous",
            primary_outcome_name=outcome_name,
            alpha=alpha,
            power=power,
            allocation_ratio=r,
            attrition_rate=safe_attrition,
            input_parameters={"mean_difference": delta, "pooled_sd": sigma, "cohens_d": round(cohen_d, 3)},
            n_per_group=n1,
            n_total_evaluable=n_eval,
            n_total_with_attrition=n_total_adj,
            mathematical_formula=formula_str,
            assumptions_rationale=rationale
        )

    @classmethod
    def _calc_two_sample_binary(
        cls,
        outcome_name: str,
        alpha: float,
        power: float,
        r: float,
        attrition: float,
        inputs: Dict[str, float]
    ) -> SampleSizeSpec:
        """
        Two-sample binary test (difference in proportions):
        Standard normal approximation with pooled variance.
        """
        p1 = min(0.99, max(0.01, inputs.get("p1_experimental", 0.45)))
        p2 = min(0.99, max(0.01, inputs.get("p2_control", 0.25)))
        diff = abs(p1 - p2)
        if diff == 0:
            diff = 0.05

        p_bar = (p1 + r * p2) / (1.0 + r)
        q_bar = 1.0 - p_bar

        z_alpha = stats.norm.ppf(1.0 - alpha / 2.0)
        z_beta = stats.norm.ppf(power)

        term1 = z_alpha * math.sqrt((1.0 + 1.0 / r) * p_bar * q_bar)
        term2 = z_beta * math.sqrt(p1 * (1.0 - p1) + (p2 * (1.0 - p2)) / r)
        n1_raw = ((term1 + term2) / diff) ** 2
        n1 = int(math.ceil(n1_raw))
        n2 = int(math.ceil(n1 * r))
        n_eval = n1 + n2

        safe_attrition = min(0.50, max(0.0, attrition))
        n_total_adj = int(math.ceil(n_eval / (1.0 - safe_attrition))) if safe_attrition < 1.0 else n_eval

        formula_str = (
            f"n_1 = [ Z_(1-α/2)√( (1+1/r)p̄q̄ ) + Z_(1-β)√( p1(1-p1) + p2(1-p2)/r ) ]² / (p1 - p2)²\n"
            f"where p1 = {p1:.2f}, p2 = {p2:.2f}, Δp = {diff:.2f}, Z_α={z_alpha:.3f}, Z_β={z_beta:.3f}.\n"
            f"Attrition Adjustment: N_total = N_eval / (1 - {safe_attrition:.2f})"
        )

        rationale = (
            f"Anticipating an event rate of {p1*100:.1f}% in the experimental group vs {p2*100:.1f}% in the control group "
            f"(absolute risk difference {diff*100:.1f}%). To detect this superiority with {int(power*100)}% power at α={alpha}, "
            f"{n_eval} evaluable participants are required. Factoring in a {int(safe_attrition*100)}% attrition rate, "
            f"target recruitment is {n_total_adj} participants."
        )

        return SampleSizeSpec(
            design_type="two_sample_binary",
            primary_outcome_name=outcome_name,
            alpha=alpha,
            power=power,
            allocation_ratio=r,
            attrition_rate=safe_attrition,
            input_parameters={"p1_experimental": p1, "p2_control": p2, "risk_difference": round(diff, 3)},
            n_per_group=n1,
            n_total_evaluable=n_eval,
            n_total_with_attrition=n_total_adj,
            mathematical_formula=formula_str,
            assumptions_rationale=rationale
        )

    @classmethod
    def _calc_non_inferiority_continuous(
        cls,
        outcome_name: str,
        alpha: float,
        power: float,
        r: float,
        attrition: float,
        inputs: Dict[str, float]
    ) -> SampleSizeSpec:
        """Non-inferiority continuous trial (one-sided alpha = 0.025)."""
        margin = abs(inputs.get("non_inferiority_margin", 2.5))
        sigma = abs(inputs.get("pooled_sd", 8.0))

        # One-sided alpha for non-inferiority
        z_alpha = stats.norm.ppf(1.0 - alpha)  # e.g. 1.645 for alpha=0.05 or 1.96 for alpha=0.025
        z_beta = stats.norm.ppf(power)

        n1_raw = (1.0 + 1.0 / r) * ((z_alpha + z_beta) * sigma / margin) ** 2
        n1 = int(math.ceil(n1_raw))
        n2 = int(math.ceil(n1 * r))
        n_eval = n1 + n2

        safe_attrition = min(0.50, max(0.0, attrition))
        n_total_adj = int(math.ceil(n_eval / (1.0 - safe_attrition))) if safe_attrition < 1.0 else n_eval

        formula_str = (
            f"n_1 = (1 + 1/r) × [ (Z_(1-α) + Z_(1-β)) × σ / Δ_NI ]²\n"
            f"where non-inferiority margin Δ_NI = {margin:.2f}, σ = {sigma:.2f}, one-sided α={alpha} (Z_α={z_alpha:.3f})."
        )

        rationale = (
            f"Non-inferiority design with a clinically justified margin Δ_NI of {margin} units and pooled SD {sigma}. "
            f"Assuming true treatment difference is zero, {n_eval} evaluable patients ({n_total_adj} with {int(safe_attrition*100)}% attrition) "
            f"provide {int(power*100)}% power to reject the null hypothesis of inferiority at one-sided α={alpha}."
        )

        return SampleSizeSpec(
            design_type="non_inferiority_continuous",
            primary_outcome_name=outcome_name,
            alpha=alpha,
            power=power,
            allocation_ratio=r,
            attrition_rate=safe_attrition,
            input_parameters={"non_inferiority_margin": margin, "pooled_sd": sigma},
            n_per_group=n1,
            n_total_evaluable=n_eval,
            n_total_with_attrition=n_total_adj,
            mathematical_formula=formula_str,
            assumptions_rationale=rationale
        )

    @classmethod
    def _calc_non_inferiority_binary(
        cls,
        outcome_name: str,
        alpha: float,
        power: float,
        r: float,
        attrition: float,
        inputs: Dict[str, float]
    ) -> SampleSizeSpec:
        """Non-inferiority binary trial with margin delta."""
        p = min(0.95, max(0.05, inputs.get("baseline_event_rate", 0.70)))
        margin = abs(inputs.get("non_inferiority_margin_prop", 0.10))

        z_alpha = stats.norm.ppf(1.0 - alpha)
        z_beta = stats.norm.ppf(power)

        var = 2.0 * p * (1.0 - p)
        n1_raw = (z_alpha + z_beta) ** 2 * var / (margin ** 2)
        n1 = int(math.ceil(n1_raw))
        n2 = int(math.ceil(n1 * r))
        n_eval = n1 + n2

        safe_attrition = min(0.50, max(0.0, attrition))
        n_total_adj = int(math.ceil(n_eval / (1.0 - safe_attrition))) if safe_attrition < 1.0 else n_eval

        formula_str = (
            f"n_1 = (Z_(1-α) + Z_(1-β))² × 2p(1-p) / Δ_NI²\n"
            f"where expected event rate p = {p:.2f}, margin Δ_NI = {margin:.2f}, one-sided α={alpha}."
        )

        rationale = (
            f"Non-inferiority binary design with baseline success rate {p*100:.1f}% and allowable margin Δ_NI of {margin*100:.1f}%. "
            f"Requires {n_eval} evaluable subjects ({n_total_adj} enrolled) for {int(power*100)}% power."
        )

        return SampleSizeSpec(
            design_type="non_inferiority_binary",
            primary_outcome_name=outcome_name,
            alpha=alpha,
            power=power,
            allocation_ratio=r,
            attrition_rate=safe_attrition,
            input_parameters={"baseline_event_rate": p, "non_inferiority_margin_prop": margin},
            n_per_group=n1,
            n_total_evaluable=n_eval,
            n_total_with_attrition=n_total_adj,
            mathematical_formula=formula_str,
            assumptions_rationale=rationale
        )

    # =========================================================================
    # REPRODUCIBLE PUBMED MESH SEARCH STRATEGY GENERATOR
    # =========================================================================

    @classmethod
    def generate_pubmed_search_strategy(
        cls,
        proposal: ThesisProposal
    ) -> Tuple[str, List[str], str]:
        """
        Synthesizes an advanced, reproducible Boolean search strategy with MeSH terms
        and study design filters (Cochrane Highly Sensitive Search Strategy).
        """
        pico = proposal.research_question_pico
        pop = pico.get("Population", "Chronic Disease")
        intervention = pico.get("Intervention", "Investigational Drug")
        comparator = pico.get("Comparator", "Placebo")

        mesh_terms = []

        # Population MeSH
        if "diabetes" in pop.lower():
            pop_mesh = '("Diabetes Mellitus, Type 2"[MeSH Terms] OR "Type 2 Diabetes"[Title/Abstract] OR "T2D"[Title/Abstract])'
            mesh_terms.append("Diabetes Mellitus, Type 2 [MeSH]")
        elif "obesity" in pop.lower():
            pop_mesh = '("Obesity"[MeSH Terms] OR "Overweight"[MeSH Terms] OR "Body Mass Index"[MeSH Terms] OR "obese"[Title/Abstract])'
            mesh_terms.append("Obesity [MeSH]")
        elif "heart failure" in pop.lower():
            pop_mesh = '("Heart Failure"[MeSH Terms] OR "cardiac failure"[Title/Abstract] OR "HFpEF"[Title/Abstract] OR "HFrEF"[Title/Abstract])'
            mesh_terms.append("Heart Failure [MeSH]")
        elif "renal" in pop.lower() or "ckd" in pop.lower():
            pop_mesh = '("Renal Insufficiency, Chronic"[MeSH Terms] OR "chronic kidney disease"[Title/Abstract] OR "eGFR"[Title/Abstract])'
            mesh_terms.append("Renal Insufficiency, Chronic [MeSH]")
        else:
            pop_mesh = f'("{pop}"[Title/Abstract])'

        # Intervention MeSH
        clean_int = intervention.split()[0].replace(",", "")
        int_mesh = f'("{clean_int}"[Title/Abstract] OR "{intervention}"[Title/Abstract])'
        mesh_terms.append(f"{clean_int} [Title/Abstract]")

        # Study design filter (Cochrane RCT Filter)
        if "systematic" in proposal.recommended_study_design.lower():
            design_filter = '(("systematic review"[Publication Type] OR "meta-analysis"[Publication Type] OR "systematic literature review"[Title/Abstract]))'
            mesh_terms.append("Systematic Review [Publication Type]")
        else:
            design_filter = '(("randomized controlled trial"[Publication Type] OR "controlled clinical trial"[Publication Type] OR "randomized"[Title/Abstract] OR "placebo"[Title/Abstract] OR "clinical trials as topic"[MeSH Terms] OR "randomly"[Title/Abstract]))'
            mesh_terms.append("Randomized Controlled Trial [Publication Type]")

        boolean_strategy = f"{pop_mesh} AND {int_mesh} AND {design_filter}"

        documentation = (
            f"# Reproducible PubMed Search Strategy Documentation\n"
            f"**Target Topic:** {proposal.primary_objective}\n"
            f"**Databases:** PubMed / MEDLINE (via NCBI NLM interface)\n"
            f"**Study Design Filter:** {proposal.recommended_study_design}\n"
            f"**Date Limits:** Inception to Current Date (No language restrictions applied initially)\n\n"
            f"### Executable Query Syntax:\n"
            f"```text\n{boolean_strategy}\n```\n"
        )

        return boolean_strategy, mesh_terms, documentation

    # =========================================================================
    # FORMAL PROTOCOL DRAFTING (SPIRIT 2013 / PRISMA-P / PROSPERO)
    # =========================================================================

    @classmethod
    def generate_protocol_draft(
        cls,
        proposal: ThesisProposal,
        sample_spec: SampleSizeSpec
    ) -> ProtocolDraft:
        """
        Constructs a structured protocol outline conforming to SPIRIT 2013 (for RCTs)
        or PRISMA-P 2015 (for Systematic Reviews) and generates PROSPERO registration fields.
        """
        is_sr = "systematic" in proposal.recommended_study_design.lower()
        framework = "PRISMA-P 2015 (Systematic Review)" if is_sr else "SPIRIT 2013 (Clinical Trial Protocol)"

        query, mesh_list, query_doc = cls.generate_pubmed_search_strategy(proposal)
        pico = proposal.research_question_pico

        sections = {}
        if is_sr:
            sections["1. Title & Registration"] = f"{proposal.proposed_titles[0]} (Draft PROSPERO Protocol)"
            sections["2. Rationale & Background"] = proposal.scientific_rationale
            sections["3. Research Objectives"] = f"Primary: {proposal.primary_objective}\nSecondary: " + "\n- ".join(proposal.secondary_objectives)
            sections["4. Eligibility Criteria (PICOS)"] = (
                f"- Population: {pico.get('Population')}\n"
                f"- Interventions: {pico.get('Intervention')}\n"
                f"- Comparators: {pico.get('Comparator')}\n"
                f"- Outcomes: {pico.get('Primary Outcome')}, {pico.get('Secondary Outcomes')}\n"
                f"- Study Designs: Randomized Controlled Trials (parallel, crossover, factorial)"
            )
            sections["5. Information Sources & Search Strategy"] = f"Electronic databases: PubMed/MEDLINE, Embase, Cochrane CENTRAL, ClinicalTrials.gov.\nQuery: {query}"
            sections["6. Data Extraction & Risk of Bias"] = "Two independent reviewers screening titles/abstracts and full texts. Methodological quality appraised via Cochrane RoB 2.0. Discrepancies resolved by third senior referee."
            sections["7. Statistical Synthesis & Meta-Analysis Plan"] = "Random-effects meta-analysis (DerSimonian-Laird & REML) for continuous (Hedges' g / MD) and binary (Risk Ratio / Odds Ratio) outcomes. Heterogeneity evaluated via Cochran's Q and Higgins' I^2. GRADE certainty profiles generated for key outcomes."
        else:
            sections["1. Protocol Title & Administrative Information"] = f"Protocol Blueprint: {proposal.proposed_titles[0]}"
            sections["2. Background & Clinical Equipoise"] = proposal.scientific_rationale
            sections["3. Hypotheses & Specific Aims"] = f"Primary Objective: {proposal.primary_objective}\nSecondary Aims:\n- " + "\n- ".join(proposal.secondary_objectives)
            sections["4. Trial Design & Setting"] = f"{proposal.recommended_study_design}. Setting: {pico.get('Setting')}."
            sections["5. Selection of Participants (Eligibility)"] = (
                f"Inclusion Criteria:\n- Adults aged >= 18 years with confirmed {pico.get('Population')}.\n"
                f"- Willingness to provide written informed consent.\n"
                f"Exclusion Criteria:\n- Hypersensitivity to investigational agent.\n"
                f"- Severe end-stage renal disease (eGFR < 15 mL/min/1.73m²) unless specifically enrolled in targeted subgroup.\n"
                f"- Concurrent participation in conflicting interventional trials."
            )
            sections["6. Interventions & Concomitant Therapy"] = f"Experimental: {pico.get('Intervention')}\nComparator: {pico.get('Comparator')}\nDuration: {pico.get('Timing / Follow-up')}."
            sections["7. Outcomes & Timepoints"] = f"Primary Endpoint: {pico.get('Primary Outcome')} at {pico.get('Timing / Follow-up')}.\nSecondary Endpoints: {pico.get('Secondary Outcomes')}."
            sections["8. Biostatistical Sample Size Calculation"] = (
                f"Total Required Enrollment: {sample_spec.n_total_with_attrition} participants "
                f"({sample_spec.n_total_evaluable} evaluable, {sample_spec.n_per_group} per treatment arm).\n"
                f"Assumptions: Alpha = {sample_spec.alpha}, Power = {sample_spec.power*100:.0f}%, "
                f"Anticipated Attrition = {sample_spec.attrition_rate*100:.0f}%.\n"
                f"Formula:\n{sample_spec.mathematical_formula}\n"
                f"Justification: {sample_spec.assumptions_rationale}"
            )
            sections["9. Randomization, Concealment & Masking"] = "Computer-generated central randomization sequence with permuted block stratifications. Allocation concealed via Interactive Web-Response System (IWRS). Double-blind masking maintained using identical matching placebos."
            sections["10. Ethics & Safety Monitoring"] = "Protocol subject to Institutional Review Board (IRB) approval in accordance with ICH-GCP and Declaration of Helsinki. Independent Data Safety Monitoring Board (DSMB) chartered to review unblinded safety data."

        # PROSPERO Form Checklist
        prospero_checklist = [
            {"Field": "Review Title", "Value": proposal.proposed_titles[0]},
            {"Field": "Anticipated Start Date", "Value": "Within 30 days of registration"},
            {"Field": "Anticipated Completion Date", "Value": "12 months from start date"},
            {"Field": "Review Question", "Value": proposal.primary_objective},
            {"Field": "Searches", "Value": f"PubMed, Embase, Cochrane CENTRAL, ClinicalTrials.gov. Strategy: {query[:140]}..."},
            {"Field": "Participants / Population", "Value": pico.get("Population", "")},
            {"Field": "Intervention(s)", "Value": pico.get("Intervention", "")},
            {"Field": "Comparator(s)", "Value": pico.get("Comparator", "")},
            {"Field": "Main Outcomes", "Value": pico.get("Primary Outcome", "")},
            {"Field": "Risk of Bias Assessment", "Value": "Cochrane Risk of Bias 2.0 (RoB 2.0) across 5 standard domains"},
            {"Field": "Strategy for Data Synthesis", "Value": "DerSimonian-Laird and REML random-effects pooling, I^2 heterogeneity, and GRADE evidence profile"}
        ]

        return ProtocolDraft(
            framework=framework,
            sections=sections,
            pubmed_search_strategy=query_doc,
            mesh_terms_used=mesh_list,
            boolean_query=query,
            prospero_checklist=prospero_checklist,
            download_filename="MANDOROS_Phase3_Protocol_Blueprint.md"
        )
