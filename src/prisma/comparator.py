"""
PRISMA Trial Comparator.
Generates side-by-side multi-trial comparison matrices, detects methodological divergences,
and filters evidence by interventions, comparators, and endpoints.
"""

from typing import Any, Optional
import pandas as pd

from src.prisma.models import PrismaTrial


class PrismaTrialComparator:
    """Analytical service for side-by-side clinical trial comparison and divergence auditing."""

    def __init__(self, trials: dict[str, PrismaTrial]):
        self.trials = trials

    def get_filter_options(self) -> dict[str, list[str]]:
        """Extracts available filter categories across all loaded trials."""
        trial_keys = list(self.trials.keys())
        interventions = set()
        comparators = set()
        conditions = set()
        outcomes = set()
        years = set()

        for t in self.trials.values():
            if t.publication_year:
                years.add(str(t.publication_year))
            if t.condition_studied:
                conditions.add(t.condition_studied)
            for a in t.arms:
                if a.intervention_type == "experimental" and a.drug_name:
                    interventions.add(a.drug_name)
                elif a.intervention_type in ["placebo", "control", "active_comparator"]:
                    comparators.add(a.drug_name or a.arm_name)
            for o in t.outcomes:
                if o.parameter_name:
                    outcomes.add(o.parameter_name)

        return {
            "trials": sorted(trial_keys),
            "interventions": sorted(list(interventions)) or ["All Interventions"],
            "comparators": sorted(list(comparators)) or ["All Comparators"],
            "conditions": sorted(list(conditions)) or ["All Conditions"],
            "outcomes": sorted(list(outcomes)) or ["All Outcomes"],
            "years": sorted(list(years), reverse=True) or ["All Years"],
        }

    def filter_trials(
        self,
        selected_trials: Optional[list[str]] = None,
        intervention: Optional[str] = None,
        comparator: Optional[str] = None,
        outcome: Optional[str] = None,
        year: Optional[str] = None,
    ) -> dict[str, PrismaTrial]:
        """Filters trials based on user-selected criteria."""
        filtered = {}
        for s_id, t in self.trials.items():
            if selected_trials and s_id not in selected_trials:
                continue
            if year and year not in ["All Years", ""] and str(t.publication_year) != str(year):
                continue
            if intervention and intervention not in ["All Interventions", ""]:
                drug_match = any(
                    a.intervention_type == "experimental" and intervention.lower() in (a.drug_name or "").lower()
                    for a in t.arms
                )
                if not drug_match:
                    continue
            if comparator and comparator not in ["All Comparators", ""]:
                comp_match = any(
                    a.intervention_type in ["placebo", "control", "active_comparator"]
                    and comparator.lower() in (a.drug_name or a.arm_name).lower()
                    for a in t.arms
                )
                if not comp_match:
                    continue
            if outcome and outcome not in ["All Outcomes", ""]:
                out_match = any(outcome.lower() in (o.parameter_name or "").lower() for o in t.outcomes)
                if not out_match:
                    continue

            filtered[s_id] = t

        return filtered if filtered else self.trials

    def build_side_by_side_matrix(self, selected_trial_ids: Optional[list[str]] = None) -> pd.DataFrame:
        """
        Builds a structured side-by-side comparison table where rows are clinical attributes
        and columns are the individual clinical trials.
        """
        target_trials = (
            {k: v for k, v in self.trials.items() if k in selected_trial_ids}
            if selected_trial_ids
            else self.trials
        )

        if not target_trials:
            return pd.DataFrame({"Attribute": ["No trials loaded or selected."]})

        trial_cols = list(target_trials.keys())
        rows: list[dict[str, Any]] = []

        def add_attr(category: str, attribute: str, extractor_fn):
            r = {"Category": category, "Clinical Parameter": attribute}
            for tid, trial in target_trials.items():
                val = extractor_fn(trial)
                r[tid] = str(val) if val is not None and str(val).strip() != "" else "Not Reported"
            rows.append(r)

        # 1. Study Characteristics
        add_attr("Study Design", "Study Title", lambda t: t.title or t.study_id)
        add_attr("Study Design", "Citation / Authors", lambda t: f"{t.authors} ({t.publication_year or 'ND'})")
        add_attr("Study Design", "Journal & DOI", lambda t: f"{t.journal} | {t.doi}".strip(" |"))
        add_attr("Study Design", "Design & Blinding", lambda t: t.study_design or "RCT")
        add_attr("Study Design", "Study Phase", lambda t: t.study_phase or "Not explicitly reported")
        add_attr("Study Design", "Condition Studied", lambda t: t.condition_studied or "Cardiometabolic")
        add_attr("Study Design", "Treatment Duration", lambda t: t.duration_label())

        # 2. Sample Size & Populations
        add_attr("Sample Size", "Total Randomized (N)", lambda t: t.total_sample_size)
        add_attr(
            "Sample Size",
            "Arm Allocations (N)",
            lambda t: "; ".join([f"{a.arm_name}: N={a.sample_size_analyzed or a.sample_size_allocated or 'NR'}" for a in t.arms])
        )

        # 3. Interventions & Regimens
        add_attr(
            "Interventions",
            "Experimental Drug & Dose",
            lambda t: "; ".join([
                f"{a.arm_name} ({a.dose_value} {a.dose_unit} {a.frequency_number} {a.frequency_unit})".strip()
                for a in t.arms if a.intervention_type == "experimental"
            ]) or "None"
        )
        add_attr(
            "Interventions",
            "Comparator / Control Arm",
            lambda t: "; ".join([
                f"{a.arm_name} ({a.intervention_type})"
                for a in t.arms if a.intervention_type in ["placebo", "control", "active_comparator"]
            ]) or "None"
        )

        # 4. Key Outcomes Extracted
        add_attr(
            "Key Outcomes",
            "Reported Efficacy Endpoints",
            lambda t: "; ".join(sorted(list({o.parameter_name for o in t.outcomes if o.domain.lower() == "efficacy" and o.parameter_name}))) or "None"
        )
        add_attr(
            "Key Outcomes",
            "Reported Safety Endpoints",
            lambda t: "; ".join(sorted(list({o.parameter_name for o in t.outcomes if o.domain.lower() == "safety" and o.parameter_name}))) or "None"
        )

        # 5. Methodological & Completeness Score
        add_attr("Quality & Validation", "Validation Findings Count", lambda t: len(t.validation_findings))
        add_attr("Quality & Validation", "Critical Warnings", lambda t: sum(1 for f in t.validation_findings if f.severity == "critical"))
        add_attr("Quality & Validation", "Source Workbook", lambda t: t.source_file)

        df = pd.DataFrame(rows)
        return df

    def detect_trial_divergences(self, selected_trial_ids: Optional[list[str]] = None) -> list[dict[str, str]]:
        """
        Detects methodological and clinical divergences across the selected trials.
        Flags dosage variations, duration discrepancies, and population differences.
        """
        target_trials = (
            {k: v for k, v in self.trials.items() if k in selected_trial_ids}
            if selected_trial_ids
            else self.trials
        )

        if len(target_trials) < 2:
            return [{
                "Category": "Single Study Loaded",
                "Divergence Description": "At least two clinical trials are required to compute cross-trial divergence metrics.",
                "Clinical Interpretation": "Load or select multiple RCT workbooks to evaluate comparative heterogeneity.",
                "Actionable Advice": "Upload additional RCT workbooks.",
            }]

        divergences = []
        trial_list = list(target_trials.values())

        # 1. Duration Divergence Check
        durations = {}
        for t in trial_list:
            if t.duration_value is not None:
                durations[t.study_id] = f"{t.duration_value} {t.duration_unit}".strip()

        if len(set(durations.values())) > 1:
            div_desc = ", ".join([f"{tid}: {d}" for tid, d in durations.items()])
            divergences.append({
                "Category": "Duration Divergence",
                "Divergence Description": f"Heterogeneous trial durations observed across cohort: {div_desc}",
                "Clinical Interpretation": "Different follow-up horizons can introduce time-dependent bias. Short-term trials may overestimate acute pharmacodynamic effects while underreporting long-term safety.",
                "Actionable Advice": "Subgroup by treatment duration (e.g. <=12 weeks vs >24 weeks) or perform meta-regression on duration.",
            })

        # 2. Dosage / Regimen Divergence
        doses = {}
        for t in trial_list:
            exp_arms = [a for a in t.arms if a.intervention_type == "experimental" and a.dose_value is not None]
            if exp_arms:
                doses[t.study_id] = "/".join([f"{a.dose_value}{a.dose_unit}" for a in exp_arms])

        if len(set(doses.values())) > 1:
            div_desc = ", ".join([f"{tid}: {d}" for tid, d in doses.items()])
            divergences.append({
                "Category": "Dosing & Regimen Divergence",
                "Divergence Description": f"Disparate dose regimens extracted across trials: {div_desc}",
                "Clinical Interpretation": "Dose-dependent efficacy may inflate between-study variance (tau^2) if pooled under an unstratified model.",
                "Actionable Advice": "Stratify meta-analysis by dose level (low vs standard vs high dose) or fit a longitudinal dose-response curve.",
            })

        # 3. Comparator Divergence
        comparators = {}
        for t in trial_list:
            comp_arms = [a.arm_name for a in t.arms if a.intervention_type in ["placebo", "control", "active_comparator"]]
            if comp_arms:
                comparators[t.study_id] = ", ".join(comp_arms)

        active_comps = [c for c in comparators.values() if "placebo" not in c.lower()]
        placebo_comps = [c for c in comparators.values() if "placebo" in c.lower()]
        if active_comps and placebo_comps:
            divergences.append({
                "Category": "Comparator Type Divergence",
                "Divergence Description": "Mixture of Placebo-controlled and Active-comparator RCT designs.",
                "Clinical Interpretation": "Pooling placebo-controlled and active-comparator trials directly violates exchangeability assumptions.",
                "Actionable Advice": "Separate indirect network meta-analysis (NMA) or synthesize placebo and active-controlled cohorts independently.",
            })

        # 4. Condition / Population Nuances
        conditions = {t.study_id: t.condition_studied for t in trial_list if t.condition_studied}
        if len(set(conditions.values())) > 1:
            divergences.append({
                "Category": "Target Population Divergence",
                "Divergence Description": f"Heterogeneous conditions studied across cohort: {', '.join(set(conditions.values()))}",
                "Clinical Interpretation": "Baseline clinical risk and disease severity may modify relative treatment effect sizes.",
                "Actionable Advice": "Evaluate subgroup heterogeneity (Cochran's Q_between) across clinical condition strata.",
            })

        if not divergences:
            divergences.append({
                "Category": "Cohort Harmonization",
                "Divergence Description": "No severe methodological divergences detected across selected trials. Designs and durations are aligned.",
                "Clinical Interpretation": "The cohort exhibits high methodological exchangeability suitable for standard random-effects synthesis.",
                "Actionable Advice": "Proceed to Outcome Explorer for endpoint synthesis readiness checks.",
            })

        return divergences

    def build_arms_comparison_df(self, selected_trial_ids: Optional[list[str]] = None) -> pd.DataFrame:
        """Flattens all arms across trials into a standardized comparison DataFrame."""
        rows = []
        target_trials = (
            {k: v for k, v in self.trials.items() if k in selected_trial_ids}
            if selected_trial_ids
            else self.trials
        )

        for tid, trial in target_trials.items():
            for arm in trial.arms:
                rows.append({
                    "Trial ID": tid,
                    "Study Source": trial.source_file,
                    "Arm ID": arm.arm_id,
                    "Arm Name": arm.arm_name,
                    "Type": arm.intervention_type.title(),
                    "Drug": arm.drug_name or "Not Specified",
                    "Dose": f"{arm.dose_value or ''} {arm.dose_unit}".strip() or "NR",
                    "Frequency": f"{arm.frequency_number or ''} {arm.frequency_unit}".strip() or "NR",
                    "Allocated N": arm.sample_size_allocated or "NR",
                    "Analyzed N": arm.sample_size_analyzed or "NR",
                    "Provenance": arm.provenance.citation(),
                })

        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": ["No arms found."]})

    def build_eligibility_comparison_df(self, selected_trial_ids: Optional[list[str]] = None) -> pd.DataFrame:
        """Flattens eligibility criteria across trials to evaluate inclusion/exclusion overlap."""
        rows = []
        target_trials = (
            {k: v for k, v in self.trials.items() if k in selected_trial_ids}
            if selected_trial_ids
            else self.trials
        )

        for tid, trial in target_trials.items():
            for e in trial.eligibility:
                rows.append({
                    "Trial ID": tid,
                    "Type": e.criterion_type.upper(),
                    "Domain": e.domain or "General",
                    "Criterion": e.criterion_name,
                    "Condition / Range": e.formatted_condition(),
                    "Raw Excerpt": e.raw_source_text or "NR",
                    "Provenance": e.provenance.citation(),
                })

        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": ["No eligibility criteria found."]})
