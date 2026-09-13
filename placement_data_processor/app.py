"""Streamlit UI for the TPC placement data processor. No business logic here."""

from __future__ import annotations

from datetime import datetime
import os
import re

import pandas as pd
import streamlit as st


from config.settings import DriveRules
from core.loader import load_inputs
from core.processor import ProcessResult, run_pipeline
from core.validator import validate_inputs
from output.workbook import build_workbook

st.set_page_config(
    page_title="Student Placement Data Processor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_state() -> None:
    defaults = {
        "responses_bytes": None,
        "placement_bytes": None,
        "internship_bytes": None,
        "responses_name": "",
        "placement_name": "",
        "internship_name": "",
        "validation": None,
        "result": None,
        "workbook_bytes": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _rules_from_widgets(
    placement_mode: str,
    custom_max: int,
    academic_mode: str,
    tenth: float,
    twelfth: float,
    cgpa: float,
    live_kt_allowed: bool,
    remove_internship: bool,
    include_job_role: bool,
) -> DriveRules:
    if placement_mode == "No offers allowed":
        max_offers = 0
    elif placement_mode == "Single-placed students allowed":
        max_offers = 1
    else:
        max_offers = int(custom_max)
    payload = {
        "placement": {"max_offers": max_offers},
        "academic": {
            "mode": "open" if academic_mode == "Open" else "threshold",
            "tenth": None if academic_mode == "Open" else tenth,
            "twelfth": None if academic_mode == "Open" else twelfth,
            "cgpa": None if academic_mode == "Open" else cgpa,
        },
        "live_kt": {"allowed": live_kt_allowed},
        "internship": {"remove": remove_internship},
        "output": {"include_job_role": include_job_role},
    }
    return DriveRules.from_dict(payload)


def _show_validation(validation) -> None:
    counts = validation.record_counts
    c1, c2, c3 = st.columns(3)
    c1.metric("Response rows", f"{counts.get('responses', 0):,}")
    c2.metric("Placement rows", f"{counts.get('placement', 0):,}")
    c3.metric("Internship rows", f"{counts.get('internship', 0):,}")

    st.markdown("**Detected columns**")
    for source, mapping in validation.detected_columns.items():
        with st.expander(source.title(), expanded=source == "responses"):
            if mapping:
                st.dataframe(
                    pd.DataFrame(
                        [{"Field": field, "Workbook column": column} for field, column in mapping.items()]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No known columns detected.")

    if validation.errors:
        st.error("Cannot process")
        for err in validation.errors:
            st.error(err)
    else:
        st.success("Required fields were identified. You can process this drive.")

    for warning in validation.warnings:
        st.warning(warning)


def _show_preview(result: ProcessResult) -> None:
    st.markdown("### Processing preview")
    s = result.summary
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total students", f"{s.input_response_count:,}")
    m2.metric("Duplicates", f"{s.duplicate_count:,}")
    m3.metric("Placement removed", f"{s.placement_removals:,}")
    m4.metric("Final eligible", f"{s.final_eligible_count:,}")
    n1, n2, n3 = st.columns(3)
    n1.metric("Academic removed", f"{s.academic_removals:,}")
    n2.metric("KT removed", f"{s.kt_removals:,}")
    n3.metric("Internship removed", f"{s.internship_removals:,}")

    st.code("\n".join(s.as_display_lines()), language=None)
    for warning in result.warnings:
        st.warning(warning)

    st.markdown("**Eligible students (preview)**")
    preview_cols = [c for c in ["roll_no", "name", "email", "mobile", "branch", "college", "offer_count"] if c in result.eligible.columns]
    st.dataframe(result.eligible[preview_cols].head(25), hide_index=True, use_container_width=True)
    st.caption("College Roll No. is included as column 2 in the RAIT and Remove sheets for internal verification.")


def clean_download_filename(raw_name: str) -> str:
    """Generate output filename matching the uploaded raw responses filename without '(Responses)'."""
    if not raw_name:
        return "RAIT_eligible.xlsx"
    name, ext = os.path.splitext(raw_name)
    if not ext:
        ext = ".xlsx"
    cleaned = re.sub(r"\s*\(\s*responses\s*\)\s*", " ", name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f"{cleaned}{ext}"


def main() -> None:
    _init_state()
    st.title("Student Placement Data Processor")

    st.caption("Upload → Configure → Validate → Process → Preview → Download")

    with st.sidebar:
        st.header("Workflow")
        st.markdown(
            "1. Upload files\n"
            "2. Set drive rules\n"
            "3. Validate\n"
            "4. Process\n"
            "5. Preview\n"
            "6. Download"
        )
        st.divider()
        st.markdown("Student files stay in this session only. They are not written to disk or sent to external services.")
        if st.button("Clear session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("## Step 1 — Upload files")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        responses_file = st.file_uploader("Responses workbook", type=["xlsx", "xlsm"], key="up_responses")
    with col_b:
        placement_file = st.file_uploader("Studentwise placement workbook", type=["xlsx", "xlsm"], key="up_placement")
    with col_c:
        internship_file = st.file_uploader(
            "Studentwise internship workbook",
            type=["xlsx", "xlsm"],
            key="up_internship",
            help="Optional",
        )

    def _store_upload(file, bytes_key: str, name_key: str) -> None:
        if file is None:
            return
        payload = file.getvalue()
        if st.session_state.get(bytes_key) == payload:
            return
        st.session_state[bytes_key] = payload
        st.session_state[name_key] = file.name
        st.session_state.validation = None
        st.session_state.result = None
        st.session_state.workbook_bytes = None

    _store_upload(responses_file, "responses_bytes", "responses_name")
    _store_upload(placement_file, "placement_bytes", "placement_name")
    _store_upload(internship_file, "internship_bytes", "internship_name")

    st.markdown("## Step 2 — Drive rules")
    st.caption("Eligibility is never assumed. Set the rule for this drive before processing.")

    r1, r2 = st.columns(2)
    with r1:
        placement_mode = st.radio(
            "Placement rule",
            ["No offers allowed", "Single-placed students allowed", "Custom maximum offer count"],
            index=0,
        )
        custom_max = st.number_input(
            "Maximum offers allowed",
            min_value=0,
            max_value=8,
            value=0,
            disabled=placement_mode != "Custom maximum offer count",
        )
        live_kt_allowed = st.radio(
            "Live KTs allowed?",
            ["No", "Yes"],
            index=1,
            horizontal=True,
        ) == "Yes"
        remove_internship = st.radio(
            "Remove existing internship students?",
            ["No", "Yes"],
            index=0,
            horizontal=True,
        ) == "Yes"

    with r2:
        academic_mode = st.radio(
            "Academic rule",
            ["Open", "Threshold"],
            index=0,
        )
        st.caption("Threshold example: 70% throughout → 10th ≥ 70, 12th ≥ 70, CGPA ≥ 7.0")
        tenth = st.number_input(
            "10th percentage",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            disabled=academic_mode == "Open",
        )
        twelfth = st.number_input(
            "12th/Diploma percentage",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            disabled=academic_mode == "Open",
        )
        cgpa = st.number_input(
            "BTech/BE CGPA",
            min_value=0.0,
            max_value=10.0,
            value=7.0,
            step=0.1,
            disabled=academic_mode == "Open",
        )
        include_job_role = st.checkbox(
            "Include Job role values in RAIT",
            value=True,
        )

    rules = _rules_from_widgets(
        placement_mode,
        int(custom_max),
        academic_mode,
        float(tenth),
        float(twelfth),
        float(cgpa),
        live_kt_allowed,
        remove_internship,
        include_job_role,
    )
    config_errors = rules.validate()
    if config_errors:
        for err in config_errors:
            st.error(err)

    st.markdown("## Step 3 — Validate")
    can_validate = (
        st.session_state.responses_bytes is not None
        and st.session_state.placement_bytes is not None
        and not config_errors
    )
    if st.button("Validate uploads", type="primary", disabled=not can_validate):
        try:
            inputs = load_inputs(
                st.session_state.responses_bytes,
                st.session_state.placement_bytes,
                st.session_state.internship_bytes,
            )
            st.session_state.validation = validate_inputs(inputs)
            st.session_state.result = None
            st.session_state.workbook_bytes = None
        except Exception as exc:  # noqa: BLE001 — show a clean UI error, never crash the page
            st.session_state.validation = None
            st.error(f"Cannot process\n\n{exc}")

    if not can_validate:
        st.info("Upload the Responses and Studentwise Placement workbooks, then set valid drive rules.")

    if st.session_state.validation is not None:
        _show_validation(st.session_state.validation)

    st.markdown("## Step 4 — Process")
    can_process = (
        st.session_state.validation is not None
        and st.session_state.validation.ok
        and not config_errors
    )
    if st.button("Process data", disabled=not can_process):
        try:
            inputs = load_inputs(
                st.session_state.responses_bytes,
                st.session_state.placement_bytes,
                st.session_state.internship_bytes,
            )
            st.session_state.result = run_pipeline(inputs, rules)
            st.session_state.workbook_bytes = None
        except Exception as exc:  # noqa: BLE001
            st.error(f"Cannot process\n\n{exc}")

    st.markdown("## Step 5 — Preview")
    if st.session_state.result is not None:
        _show_preview(st.session_state.result)
    else:
        st.caption("Process data to see eligibility counts and a sample of the RAIT list.")

    st.markdown("## Step 6 — Export")
    if st.session_state.result is None:
        st.caption("Generate the workbook only after you have reviewed the preview.")
        return

    if st.button("Generate workbook"):
        st.session_state.workbook_bytes = build_workbook(st.session_state.result)


    if st.session_state.workbook_bytes:
        download_name = clean_download_filename(st.session_state.get("responses_name", ""))
        st.download_button(
            "Download final workbook",
            data=st.session_state.workbook_bytes,
            file_name=download_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
        st.success("Workbook generated. Sheets: RAIT, Remove, Audit, Run Info.")



if __name__ == "__main__":
    main()
