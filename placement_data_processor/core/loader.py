"""Load Excel workbooks once into DataFrames. Identify columns by header names."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import BinaryIO

import pandas as pd

from utils.headers import HeaderMapper, HeaderMapping


@dataclass
class LoadedWorkbook:
    name: str
    dataframe: pd.DataFrame
    headers: list[str]
    mapping: HeaderMapping
    sheet_name: str | None = None


@dataclass
class LoadedInputs:
    responses: LoadedWorkbook
    placement: LoadedWorkbook
    internship: LoadedWorkbook | None = None
    warnings: list[str] = field(default_factory=list)


def _read_excel(source: bytes | BinaryIO | str, name: str) -> pd.DataFrame:
    if isinstance(source, (bytes, bytearray)):
        buffer = BytesIO(source)
        df = pd.read_excel(buffer, engine="openpyxl", dtype=object)
    else:
        df = pd.read_excel(source, engine="openpyxl", dtype=object)
    df.columns = [str(c).strip() if pd.notna(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed", na=False)]
    if df.empty:
        raise ValueError(f"{name} workbook has no data rows.")
    return df.reset_index(drop=True)


def load_workbook(source: bytes | BinaryIO | str, name: str, mapper: HeaderMapper | None = None) -> LoadedWorkbook:
    mapper = mapper or HeaderMapper()
    df = _read_excel(source, name)
    headers = list(df.columns)
    mapping = mapper.map_headers(headers)
    return LoadedWorkbook(name=name, dataframe=df, headers=headers, mapping=mapping)


def load_inputs(
    responses: bytes | BinaryIO | str,
    placement: bytes | BinaryIO | str,
    internship: bytes | BinaryIO | str | None = None,
) -> LoadedInputs:
    mapper = HeaderMapper()
    warnings: list[str] = []
    responses_wb = load_workbook(responses, "Responses", mapper)
    placement_wb = load_workbook(placement, "Studentwise Placement", mapper)
    internship_wb = None
    if internship is not None:
        internship_wb = load_workbook(internship, "Studentwise Internship", mapper)
        if "roll_no" not in internship_wb.mapping.field_to_column:
            warnings.append(
                "Internship workbook did not contain an identifiable College Roll No. column. "
                "Internship matching will use only safe email/mobile matches."
            )
    return LoadedInputs(
        responses=responses_wb,
        placement=placement_wb,
        internship=internship_wb,
        warnings=warnings,
    )
