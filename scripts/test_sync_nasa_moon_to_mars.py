#!/usr/bin/env python3
from io import BytesIO

from openpyxl import Workbook

import sync_nasa_moon_to_mars as sync


def workbook_bytes(headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def source(kind, filename, digest, content):
    return sync.SourceFile(
        kind=kind,
        url=f"https://example.invalid/{filename}",
        filename=filename,
        sha256=digest,
        content=content,
    )


def main():
    ids = ["0801", "0201", "0301", "1107", "0103", "1104"] + [
        f"{1200 + i:04d}" for i in range(10)
    ]
    technology_rows = []
    for rank, gap_id in enumerate(ids, start=1):
        technology_rows.append(
            [
                gap_id,
                f"Gap {gap_id}",
                rank,
                1 if rank <= 6 else 2,
                "Description",
                "Impact",
                "State of the art",
                "Target",
                "Foundational Exploration",
                "Power Systems",
            ]
        )

    technology = source(
        "technology_gaps",
        "technology.xlsx",
        "tech-sha",
        workbook_bytes(
            [
                "Gap ID",
                "Gap Title",
                "Priority Rating",
                "Priority Bin",
                "Gap Description",
                "Architecture Impact",
                "Current State",
                "Performance Target",
                "Segments",
                "Sub-Architectures",
            ],
            technology_rows,
        ),
    )
    data_gaps = source(
        "data_gaps",
        "data.xlsx",
        "data-sha",
        workbook_bytes(
            ["Data Gap ID", "Data Gap", "Data Utility"],
            [["DN-001", "Terrain data", "Landing-site design"]],
        ),
    )
    objective_headers = ["Objective ID", "Objective", "Use Case", "Function"]
    objective_rows = [
        [f"O{i}", f"Objective {i}", f"Use {i}", f"Function {i}"]
        for i in range(1, 8)
    ]
    lunar = source(
        "lunar_objectives",
        "lunar.xlsx",
        "lunar-sha",
        workbook_bytes(objective_headers, objective_rows),
    )
    mars = source(
        "mars_objectives",
        "mars.xlsx",
        "mars-sha",
        workbook_bytes(objective_headers, objective_rows),
    )

    dataset, manifest = sync.build_dataset(
        {
            "technology_gaps": technology,
            "data_gaps": data_gaps,
            "lunar_objectives": lunar,
            "mars_objectives": mars,
        }
    )

    assert len(dataset["technology_gaps"]) == 16
    assert dataset["technology_gaps"][0]["id"] == "0801"
    assert dataset["technology_gaps"][0]["segments"] == ["Foundational Exploration"]
    assert dataset["technology_gaps"][0]["subarchitectures"] == ["Power Systems"]
    assert len(dataset["data_gaps"]) == 1
    assert len(dataset["objective_mappings"]["lunar"]) == 7
    assert len(dataset["objective_mappings"]["mars"]) == 7
    assert manifest["normalized_counts"]["technology_gaps"] == 16
    print("Moon-to-Mars XLSX parser tests: PASS")


if __name__ == "__main__":
    main()
