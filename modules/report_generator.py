from pathlib import Path
from datetime import datetime
import html
import json

import pandas as pd


def is_empty_value(value):
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    text = str(value).strip()

    return text in ["", "nan", "NaN", "None", "N/A"]


def safe_text(value, default="N/A"):
    if is_empty_value(value):
        return default

    return str(value)


def safe_number(value, decimals=3, unit=""):
    if is_empty_value(value):
        return "N/A"

    try:
        numeric_value = float(value)

        if unit:
            return f"{numeric_value:.{decimals}f} {unit}"

        return f"{numeric_value:.{decimals}f}"

    except Exception:
        return safe_text(value)


def read_json_file(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def read_first_csv_row(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        return {}

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            return {}

        row = df.iloc[0].to_dict()
        clean_row = {}

        for key, value in row.items():
            if is_empty_value(value):
                clean_row[key] = ""
            else:
                clean_row[key] = value

        return clean_row

    except Exception:
        return {}


def read_csv_dataframe(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame()


def list_files(folder_path, extension):
    folder_path = Path(folder_path)

    if not folder_path.exists():
        return []

    return sorted(folder_path.glob(extension))


def get_summary_value(summary_data, metadata, key, default="N/A"):
    if key in summary_data and not is_empty_value(summary_data.get(key)):
        return summary_data.get(key)

    if key in metadata and not is_empty_value(metadata.get(key)):
        return metadata.get(key)

    return default


def build_session_info(summary_data, metadata, fallback_info):
    return {
        "sport": get_summary_value(
            summary_data,
            metadata,
            "sport",
            fallback_info.get("sport", "N/A")
        ),
        "exercise": get_summary_value(
            summary_data,
            metadata,
            "exercise",
            fallback_info.get("exercise", "N/A")
        ),
        "camera_view": get_summary_value(
            summary_data,
            metadata,
            "camera_view",
            fallback_info.get("camera_view", "N/A")
        ),
        "input_mode": get_summary_value(
            summary_data,
            metadata,
            "input_mode",
            fallback_info.get("input_mode", "N/A")
        ),
        "source_file": get_summary_value(
            summary_data,
            metadata,
            "source_file",
            fallback_info.get("source_file", "")
        ),
        "record_count": get_summary_value(
            summary_data,
            metadata,
            "record_count",
            "N/A"
        ),
        "created_at": get_summary_value(
            summary_data,
            metadata,
            "created_at",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    }


def build_weightlifting_key_metrics(summary_data):
    rows = [
        ("Total Samples", safe_text(summary_data.get("record_count"))),
        ("Total Duration", safe_number(summary_data.get("total_duration_s"), 3, "s")),
        ("Detected Phase Count", safe_text(summary_data.get("detected_phase_count"))),
        ("Detected Phases", safe_text(summary_data.get("detected_phases"))),
        ("Barbell Detected Samples", safe_text(summary_data.get("barbell_detected_samples"))),
        ("Max Barbell Height", best_metric_pair(
            summary_data.get("max_barbell_height_m"),
            "m",
            summary_data.get("max_barbell_height_px"),
            "px"
        )),
        ("Max Vertical Velocity", best_metric_pair(
            summary_data.get("max_vertical_velocity_m_s"),
            "m/s",
            summary_data.get("max_vertical_velocity_px_s"),
            "px/s"
        )),
        ("Max Horizontal Velocity", best_metric_pair(
            summary_data.get("max_horizontal_velocity_m_s"),
            "m/s",
            summary_data.get("max_horizontal_velocity_px_s"),
            "px/s"
        )),
        ("Vertical Displacement Range", best_metric_pair(
            summary_data.get("vertical_displacement_range_m"),
            "m",
            summary_data.get("vertical_displacement_range_px"),
            "px"
        )),
        ("Horizontal Displacement Range", best_metric_pair(
            summary_data.get("horizontal_displacement_range_m"),
            "m",
            summary_data.get("horizontal_displacement_range_px"),
            "px"
        )),
        ("Mean Athlete Depth", safe_number(summary_data.get("mean_athlete_depth_m"), 3, "m")),
        ("Mean Center Depth", safe_number(summary_data.get("mean_center_depth_m"), 3, "m"))
    ]

    return rows


def build_sprinting_key_metrics(summary_data):
    rows = [
        ("Total Samples", safe_text(summary_data.get("record_count"))),
        ("Total Duration", safe_number(summary_data.get("total_duration_s"), 3, "s")),
        ("Detected Phase Count", safe_text(summary_data.get("detected_phase_count"))),
        ("Detected Phases", safe_text(summary_data.get("detected_phases"))),
        ("Mean Athlete Depth", safe_number(summary_data.get("mean_athlete_depth_m"), 3, "m")),
        ("Mean Center Depth", safe_number(summary_data.get("mean_center_depth_m"), 3, "m"))
    ]

    return rows


def best_metric_pair(primary_value, primary_unit, fallback_value, fallback_unit):
    if not is_empty_value(primary_value):
        return safe_number(primary_value, 4, primary_unit)

    if not is_empty_value(fallback_value):
        return safe_number(fallback_value, 2, fallback_unit)

    return "N/A"


def dataframe_to_text_table(df, max_rows=12):
    if df.empty:
        return "No phase-wise data available."

    display_df = df.copy()

    useful_columns = [
        "phase",
        "start_time_s",
        "end_time_s",
        "duration_s",
        "sample_count",
        "left_hip_angle_mean_deg",
        "right_hip_angle_mean_deg",
        "left_knee_angle_mean_deg",
        "right_knee_angle_mean_deg",
        "left_ankle_angle_mean_deg",
        "right_ankle_angle_mean_deg",
        "trunk_lean_angle_mean_deg",
        "athlete_depth_mean_m",
        "center_depth_mean_m"
    ]

    existing_columns = [
        column for column in useful_columns
        if column in display_df.columns
    ]

    if existing_columns:
        display_df = display_df[existing_columns]

    display_df = display_df.head(max_rows)

    return display_df.to_string(index=False)


def dataframe_to_html_table(df, max_rows=12):
    if df.empty:
        return "<p>No phase-wise data available.</p>"

    display_df = df.copy()

    useful_columns = [
        "phase",
        "start_time_s",
        "end_time_s",
        "duration_s",
        "sample_count",
        "left_hip_angle_mean_deg",
        "right_hip_angle_mean_deg",
        "left_knee_angle_mean_deg",
        "right_knee_angle_mean_deg",
        "left_ankle_angle_mean_deg",
        "right_ankle_angle_mean_deg",
        "trunk_lean_angle_mean_deg",
        "athlete_depth_mean_m",
        "center_depth_mean_m"
    ]

    existing_columns = [
        column for column in useful_columns
        if column in display_df.columns
    ]

    if existing_columns:
        display_df = display_df[existing_columns]

    display_df = display_df.head(max_rows)

    return display_df.to_html(
        index=False,
        border=0,
        classes="data-table"
    )


def build_txt_report(
    session_path,
    session_info,
    key_metrics,
    phase_summary_df,
    csv_files,
    plot_files
):
    lines = []

    lines.append("BIOMOTION STUDIO ANALYSIS REPORT")
    lines.append("=" * 40)
    lines.append("")

    lines.append("1. SESSION INFORMATION")
    lines.append("-" * 40)
    lines.append(f"Sport        : {safe_text(session_info.get('sport'))}")
    lines.append(f"Exercise     : {safe_text(session_info.get('exercise'))}")
    lines.append(f"Camera View  : {safe_text(session_info.get('camera_view'))}")
    lines.append(f"Input Mode   : {safe_text(session_info.get('input_mode'))}")
    lines.append(f"Source File  : {safe_text(session_info.get('source_file'), 'Live Source / Not recorded')}")
    lines.append(f"Results Path : {session_path}")
    lines.append(f"Created At   : {safe_text(session_info.get('created_at'))}")
    lines.append("")

    lines.append("2. KEY RESULTS")
    lines.append("-" * 40)

    for label, value in key_metrics:
        lines.append(f"{label:<30}: {value}")

    lines.append("")

    lines.append("3. PHASE-WISE BIOMECHANICS SUMMARY")
    lines.append("-" * 40)
    lines.append(dataframe_to_text_table(phase_summary_df))
    lines.append("")

    lines.append("4. GENERATED CSV FILES")
    lines.append("-" * 40)

    if csv_files:
        for file_path in csv_files:
            lines.append(f"- {file_path.name}")
    else:
        lines.append("No CSV files found.")

    lines.append("")

    lines.append("5. GENERATED PLOT FILES")
    lines.append("-" * 40)

    if plot_files:
        for file_path in plot_files:
            lines.append(f"- {file_path.name}")
    else:
        lines.append("No plot files found.")

    lines.append("")

    lines.append("6. INTERPRETATION NOTES")
    lines.append("-" * 40)
    lines.append(
        "This report summarizes recorded biomechanical metrics extracted from "
        "pose landmarks, depth data, phase detection, and tracked movement signals. "
        "Numerical values should be interpreted together with the saved plots and CSV files."
    )
    lines.append("")
    lines.append(
        "For research use, verify phase labels visually and confirm that pose tracking "
        "was stable during the recording."
    )
    lines.append("")

    return "\n".join(lines)


def build_html_report(
    session_path,
    session_info,
    key_metrics,
    phase_summary_df,
    csv_files,
    plot_files
):
    metric_rows = ""

    for label, value in key_metrics:
        metric_rows += f"""
            <tr>
                <td class="key">{html.escape(str(label))}</td>
                <td>{html.escape(str(value))}</td>
            </tr>
        """

    csv_rows = ""

    if csv_files:
        for file_path in csv_files:
            csv_rows += f"<li>{html.escape(file_path.name)}</li>"
    else:
        csv_rows = "<li>No CSV files found.</li>"

    plot_rows = ""

    if plot_files:
        for file_path in plot_files:
            plot_rows += f"<li>{html.escape(file_path.name)}</li>"
    else:
        plot_rows = "<li>No plot files found.</li>"

    phase_table_html = dataframe_to_html_table(phase_summary_df)

    html_text = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>BioMotion Studio Analysis Report</title>

        <style>
            body {{
                font-family: Segoe UI, Arial, sans-serif;
                background-color: #F4F7FA;
                color: #1B1F23;
                margin: 30px;
            }}

            .container {{
                max-width: 1200px;
                margin: auto;
                background-color: white;
                border-radius: 12px;
                padding: 28px;
                box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
            }}

            h1 {{
                color: #005B96;
                border-bottom: 3px solid #0078D7;
                padding-bottom: 10px;
            }}

            h2 {{
                color: #0078D7;
                margin-top: 28px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}

            td, th {{
                border: 1px solid #D8E1E8;
                padding: 8px;
                text-align: left;
                font-size: 14px;
            }}

            th {{
                background-color: #EAF4FF;
                color: #003B5C;
            }}

            .key {{
                font-weight: bold;
                width: 30%;
                background-color: #F1F7FC;
            }}

            .path {{
                font-family: Consolas, monospace;
                color: #444444;
                word-break: break-all;
            }}

            ul {{
                line-height: 1.8;
            }}

            .note {{
                background-color: #FFF8E5;
                border-left: 5px solid #FFCC66;
                padding: 12px;
                margin-top: 10px;
            }}

            .data-table {{
                font-size: 12px;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>BioMotion Studio Analysis Report</h1>

            <h2>1. Session Information</h2>
            <table>
                <tr>
                    <td class="key">Sport</td>
                    <td>{html.escape(safe_text(session_info.get("sport")))}</td>
                </tr>
                <tr>
                    <td class="key">Exercise</td>
                    <td>{html.escape(safe_text(session_info.get("exercise")))}</td>
                </tr>
                <tr>
                    <td class="key">Camera View</td>
                    <td>{html.escape(safe_text(session_info.get("camera_view")))}</td>
                </tr>
                <tr>
                    <td class="key">Input Mode</td>
                    <td>{html.escape(safe_text(session_info.get("input_mode")))}</td>
                </tr>
                <tr>
                    <td class="key">Source File</td>
                    <td class="path">{html.escape(safe_text(session_info.get("source_file"), "Live Source / Not recorded"))}</td>
                </tr>
                <tr>
                    <td class="key">Results Path</td>
                    <td class="path">{html.escape(str(session_path))}</td>
                </tr>
                <tr>
                    <td class="key">Created At</td>
                    <td>{html.escape(safe_text(session_info.get("created_at")))}</td>
                </tr>
            </table>

            <h2>2. Key Results</h2>
            <table>
                {metric_rows}
            </table>

            <h2>3. Phase-wise Biomechanics Summary</h2>
            {phase_table_html}

            <h2>4. Generated CSV Files</h2>
            <ul>
                {csv_rows}
            </ul>

            <h2>5. Generated Plot Files</h2>
            <ul>
                {plot_rows}
            </ul>

            <h2>6. Interpretation Notes</h2>
            <div class="note">
                <p>
                    This report summarizes biomechanical metrics extracted from pose landmarks,
                    depth data, phase detection, and movement tracking signals.
                    Numerical values should be interpreted together with the saved plots and CSV files.
                </p>
                <p>
                    For research use, verify phase labels visually and confirm that pose tracking
                    was stable during the recording.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_text


def generate_analysis_reports(
    session_path,
    sport="",
    exercise="",
    input_mode="",
    source_file="",
    camera_view="N/A"
):
    """
    Generate final TXT and HTML reports for a completed analysis session.

    Output:
        Reports/analysis_report.txt
        Reports/analysis_report.html
    """

    session_path = Path(session_path)

    csv_folder = session_path / "CSV"
    plots_folder = session_path / "Plots"
    reports_folder = session_path / "Reports"

    reports_folder.mkdir(parents=True, exist_ok=True)

    metadata = read_json_file(session_path / "recording_metadata.json")

    summary_data = read_first_csv_row(csv_folder / "lift_summary.csv")

    # Prefer sprint_summary.csv when sport is sprinting and file exists.
    sprint_summary = read_first_csv_row(csv_folder / "sprint_summary.csv")

    if sprint_summary:
        sport_text = str(
            sprint_summary.get("sport")
            or summary_data.get("sport")
            or sport
        ).lower()

        if "sprint" in sport_text:
            summary_data.update(sprint_summary)

    fallback_info = {
        "sport": sport,
        "exercise": exercise,
        "input_mode": input_mode,
        "source_file": source_file,
        "camera_view": camera_view
    }

    session_info = build_session_info(
        summary_data=summary_data,
        metadata=metadata,
        fallback_info=fallback_info
    )

    sport_lower = str(session_info.get("sport", "")).lower()

    if "sprint" in sport_lower:
        key_metrics = build_sprinting_key_metrics(summary_data)
    else:
        key_metrics = build_weightlifting_key_metrics(summary_data)

    phase_summary_df = read_csv_dataframe(
        csv_folder / "phase_biomechanics_summary.csv"
    )

    csv_files = list_files(csv_folder, "*.csv")
    plot_files = list_files(plots_folder, "*.png")

    txt_report = build_txt_report(
        session_path=session_path,
        session_info=session_info,
        key_metrics=key_metrics,
        phase_summary_df=phase_summary_df,
        csv_files=csv_files,
        plot_files=plot_files
    )

    html_report = build_html_report(
        session_path=session_path,
        session_info=session_info,
        key_metrics=key_metrics,
        phase_summary_df=phase_summary_df,
        csv_files=csv_files,
        plot_files=plot_files
    )

    txt_path = reports_folder / "analysis_report.txt"
    html_path = reports_folder / "analysis_report.html"

    with open(txt_path, "w", encoding="utf-8") as file:
        file.write(txt_report)

    with open(html_path, "w", encoding="utf-8") as file:
        file.write(html_report)

    return {
        "txt_report": str(txt_path),
        "html_report": str(html_path)
    }