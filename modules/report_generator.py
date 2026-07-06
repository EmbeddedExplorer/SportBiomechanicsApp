from pathlib import Path
from datetime import datetime
import html
import json
from urllib.parse import quote

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



def make_report_relative_path(folder_name, file_path):
    '''
    Build a browser-safe relative path from Reports/analysis_report.html
    to a file in ../Plots or ../CSV.
    '''

    file_name = Path(file_path).name
    return f"../{folder_name}/{quote(file_name)}"


def title_from_filename(filename):
    stem = Path(filename).stem
    words = stem.replace("_", " ").replace("-", " ").split()
    return " ".join(word.capitalize() for word in words)


def get_plot_display_info(file_path):
    '''
    Return display title, description, and priority for known BioMotion plots.
    Unknown plots are still shown at the end of the report.
    '''

    filename = Path(file_path).name

    plot_info = {
        "barbell_trajectory_phase_highlighted.png": (
            1,
            "Phase-Highlighted Barbell Trajectory",
            "Shows the barbell path with each detected lifting phase highlighted separately."
        ),
        "barbell_trajectory_annotated.png": (
            2,
            "Annotated Barbell Trajectory",
            "Shows the smoothed barbell path with start, maximum height, end point, and phase transition annotations."
        ),
        "barbell_trajectory_powerpoint_style.png": (
            3,
            "Presentation-Style Barbell Trajectory",
            "A clean trajectory figure suitable for presentation slides and report discussion."
        ),
        "barbell_velocity_phase_highlighted.png": (
            4,
            "Barbell Vertical Velocity",
            "Shows barbell vertical velocity over time with phase highlighting."
        ),
        "hip_knee_angles_phase_highlighted.png": (
            5,
            "Hip and Knee Angles",
            "Shows left and right hip/knee joint angle changes over time."
        ),
        "upper_limb_angles_phase_highlighted.png": (
            6,
            "Shoulder and Elbow Angles",
            "Shows upper-limb joint angle changes over time."
        ),
        "trunk_lean_phase_highlighted.png": (
            7,
            "Trunk Lean Angle",
            "Shows trunk lean angle changes over time."
        ),
        "sprinting_phase_timeline.png": (
            1,
            "Sprinting Phase Timeline",
            "Shows detected sprinting phase segments across the recording."
        ),
        "sprinting_knee_ankle_angles_phase_highlighted.png": (
            5,
            "Sprinting Knee and Ankle Angles",
            "Shows knee and ankle angle changes during sprinting."
        ),
        "sprinting_depth_profile_phase_highlighted.png": (
            8,
            "Sprinting Depth Profile",
            "Shows athlete and center depth measurements over time."
        ),
        "interlimb_lower_limb_coordination_time_series.png": (
            9,
            "Lower-Limb Interlimb Coordination",
            "Shows left and right hip, knee, and ankle angle timing relationships across sprinting phases."
        ),
        "interlimb_knee_phase_relationship.png": (
            10,
            "Left-Right Knee Phase Relationship",
            "Shows the phase-colored relationship between left knee and right knee angles."
        ),
        "interlimb_hip_phase_relationship.png": (
            11,
            "Left-Right Hip Phase Relationship",
            "Shows the phase-colored relationship between left hip and right hip angles."
        ),
        "interlimb_contralateral_arm_leg_coordination.png": (
            12,
            "Contralateral Arm-Leg Coordination",
            "Shows coordination relationships between opposite arm and leg movements."
        ),
        "interlimb_coordination_phase_summary.png": (
            13,
            "Phase-wise Interlimb Coordination Summary",
            "Compares mean left-right coordination differences across sprinting phases."
        )
    }

    if filename in plot_info:
        return plot_info[filename]

    return (
        99,
        title_from_filename(filename),
        "Additional generated plot from the analysis session."
    )


def sort_plot_files_for_report(plot_files):
    return sorted(
        plot_files,
        key=lambda file_path: (
            get_plot_display_info(file_path)[0],
            Path(file_path).name.lower()
        )
    )


def build_file_links_html(file_paths, folder_name, empty_message):
    if not file_paths:
        return f"<li>{html.escape(empty_message)}</li>"

    rows = []

    for file_path in file_paths:
        relative_path = make_report_relative_path(folder_name, file_path)
        file_name = Path(file_path).name

        rows.append(
            f'''
            <li>
                <a href="{html.escape(relative_path)}" target="_blank">
                    {html.escape(file_name)}
                </a>
            </li>
            '''
        )

    return "\n".join(rows)


def build_plot_gallery_html(plot_files):
    if not plot_files:
        return '''
        <div class="empty-state">
            No plot images were found for this session.
        </div>
        '''

    sorted_plots = sort_plot_files_for_report(plot_files)
    cards = []

    for index, file_path in enumerate(sorted_plots, start=1):
        _, title, description = get_plot_display_info(file_path)
        relative_path = make_report_relative_path("Plots", file_path)
        plot_id = f"plot-review-{index}"

        cards.append(
            f'''
            <article class="plot-card">
                <a href="#{plot_id}" class="plot-thumb-link">
                    <img
                        src="{html.escape(relative_path)}"
                        alt="{html.escape(title)}"
                        class="plot-thumb"
                        loading="lazy"
                    >
                </a>

                <div class="plot-card-body">
                    <h3>{html.escape(title)}</h3>
                    <p>{html.escape(description)}</p>

                    <div class="plot-actions">
                        <a href="#{plot_id}">Review in report</a>
                        <a href="{html.escape(relative_path)}" target="_blank">Open full-size plot</a>
                    </div>
                </div>
            </article>
            '''
        )

    return "\n".join(cards)


def build_individual_plot_review_html(plot_files):
    if not plot_files:
        return '''
        <div class="empty-state">
            No individual plots are available for review.
        </div>
        '''

    sorted_plots = sort_plot_files_for_report(plot_files)
    sections = []

    for index, file_path in enumerate(sorted_plots, start=1):
        _, title, description = get_plot_display_info(file_path)
        relative_path = make_report_relative_path("Plots", file_path)
        plot_id = f"plot-review-{index}"

        sections.append(
            f'''
            <section class="plot-review-card" id="{plot_id}">
                <div class="plot-review-header">
                    <div>
                        <h3>{html.escape(title)}</h3>
                        <p>{html.escape(description)}</p>
                    </div>

                    <a href="{html.escape(relative_path)}" target="_blank" class="button-link">
                        Open image file
                    </a>
                </div>

                <a href="{html.escape(relative_path)}" target="_blank">
                    <img
                        src="{html.escape(relative_path)}"
                        alt="{html.escape(title)}"
                        class="plot-large"
                        loading="lazy"
                    >
                </a>
            </section>
            '''
        )

    return "\n".join(sections)


def build_metric_cards_html(key_metrics):
    cards = []

    for label, value in key_metrics:
        cards.append(
            f'''
            <div class="metric-card">
                <div class="label">{html.escape(str(label))}</div>
                <div class="value">{html.escape(str(value))}</div>
            </div>
            '''
        )

    return "\n".join(cards)


def build_html_report(
    session_path,
    session_info,
    key_metrics,
    phase_summary_df,
    csv_files,
    plot_files
):
    csv_rows = build_file_links_html(
        file_paths=csv_files,
        folder_name="CSV",
        empty_message="No CSV files found."
    )

    plot_rows = build_file_links_html(
        file_paths=sort_plot_files_for_report(plot_files),
        folder_name="Plots",
        empty_message="No plot files found."
    )

    phase_table_html = dataframe_to_html_table(phase_summary_df)
    phase_table_html = f'<div class="table-scroll">{phase_table_html}</div>'

    metric_cards_html = build_metric_cards_html(key_metrics)
    plot_gallery_html = build_plot_gallery_html(plot_files)
    individual_plot_review_html = build_individual_plot_review_html(plot_files)

    report_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_text = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>BioMotion Studio Analysis Report</title>

        <style>
            :root {{
                --bg-main: #eef3f8;
                --bg-card: #ffffff;
                --bg-soft: #f6f9fc;
                --primary: #005b96;
                --primary-light: #0078d7;
                --text-main: #1b1f23;
                --text-muted: #5d6975;
                --border: #d8e1e8;
                --shadow: 0 8px 24px rgba(15, 40, 70, 0.12);
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: Segoe UI, Arial, sans-serif;
                background: linear-gradient(180deg, #eaf3fb 0%, var(--bg-main) 100%);
                color: var(--text-main);
                margin: 0;
                padding: 28px;
            }}

            .container {{
                max-width: 1280px;
                margin: auto;
                overflow: hidden;
            }}

            .hero {{
                background: linear-gradient(135deg, #003b5c 0%, #0078d7 100%);
                color: white;
                border-radius: 18px;
                padding: 30px;
                box-shadow: var(--shadow);
                margin-bottom: 22px;
            }}

            .hero h1 {{
                margin: 0;
                font-size: 32px;
                letter-spacing: 0.2px;
            }}

            .hero p {{
                margin: 10px 0 0 0;
                color: #d9ecff;
                font-size: 15px;
            }}

            .hero-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                gap: 12px;
                margin-top: 22px;
            }}

            .hero-item {{
                background: rgba(255, 255, 255, 0.13);
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 12px;
                padding: 12px;
            }}

            .hero-item span {{
                display: block;
                font-size: 12px;
                color: #bfe0ff;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                margin-bottom: 5px;
            }}

            .hero-item strong {{
                display: block;
                font-size: 15px;
                word-break: break-word;
            }}

            .section {{
                background-color: var(--bg-card);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 22px;
                box-shadow: var(--shadow);
            }}

            h2 {{
                color: var(--primary);
                margin: 0 0 16px 0;
                font-size: 22px;
            }}

            h3 {{
                color: #003b5c;
                margin: 0 0 8px 0;
                font-size: 17px;
            }}

            p {{
                color: var(--text-muted);
                line-height: 1.55;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                overflow: hidden;
                border-radius: 10px;
            }}

            td, th {{
                border: 1px solid var(--border);
                padding: 9px;
                text-align: left;
                font-size: 14px;
                vertical-align: top;
            }}

            th {{
                background-color: #eaf4ff;
                color: #003b5c;
                font-weight: 700;
            }}

            .key {{
                font-weight: bold;
                width: 30%;
                background-color: #f1f7fc;
            }}

            .path {{
                font-family: Consolas, monospace;
                color: #444444;
                word-break: break-all;
            }}

            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 14px;
                margin-top: 14px;
            }}

            .metric-card {{
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 14px;
            }}

            .metric-card .label {{
                color: var(--text-muted);
                font-size: 13px;
                margin-bottom: 6px;
            }}

            .metric-card .value {{
                color: #003b5c;
                font-size: 18px;
                font-weight: 700;
                word-break: break-word;
            }}

            .plot-gallery {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 18px;
            }}

            .plot-card {{
                background-color: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 14px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                min-height: 100%;
            }}

            .plot-thumb-link {{
                display: block;
                background: #ffffff;
                border-bottom: 1px solid var(--border);
            }}

            .plot-thumb {{
                display: block;
                width: 100%;
                height: 220px;
                object-fit: contain;
                padding: 10px;
                background: white;
            }}

            .plot-card-body {{
                padding: 14px;
                flex: 1;
                display: flex;
                flex-direction: column;
            }}

            .plot-card-body p {{
                margin: 0 0 12px 0;
                font-size: 13px;
                flex: 1;
            }}

            .plot-actions {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}

            a {{
                color: var(--primary-light);
                text-decoration: none;
                font-weight: 600;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            .plot-actions a,
            .button-link {{
                display: inline-block;
                background: #eaf4ff;
                border: 1px solid #c8e4ff;
                color: #005b96;
                border-radius: 999px;
                padding: 7px 11px;
                font-size: 12px;
                text-decoration: none;
            }}

            .plot-actions a:hover,
            .button-link:hover {{
                background: #d8ecff;
                text-decoration: none;
            }}

            .plot-review-card {{
                border: 1px solid var(--border);
                background-color: var(--bg-soft);
                border-radius: 16px;
                padding: 18px;
                margin-bottom: 22px;
                scroll-margin-top: 20px;
            }}

            .plot-review-header {{
                display: flex;
                justify-content: space-between;
                gap: 14px;
                align-items: flex-start;
                margin-bottom: 14px;
            }}

            .plot-review-header p {{
                margin: 0;
            }}

            .plot-large {{
                width: 100%;
                max-height: 900px;
                object-fit: contain;
                background: white;
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 10px;
            }}

            ul {{
                line-height: 1.8;
                margin-top: 8px;
            }}

            .file-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 18px;
            }}

            .note {{
                background-color: #fff8e5;
                border-left: 5px solid #ffcc66;
                padding: 14px;
                border-radius: 8px;
                margin-top: 10px;
            }}

            .data-table {{
                font-size: 12px;
            }}

            .table-scroll {{
                width: 100%;
                overflow-x: auto;
                overflow-y: hidden;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: white;
                margin-top: 12px;
            }}

            .table-scroll table {{
                min-width: 1200px;
                margin-top: 0;
                border: 0;
                border-radius: 0;
            }}

            .table-scroll th,
            .table-scroll td {{
                white-space: nowrap;
            }}

            .table-scroll td:first-child,
            .table-scroll th:first-child {{
                position: sticky;
                left: 0;
                z-index: 2;
                background: #f1f7fc;
                box-shadow: 2px 0 4px rgba(0, 0, 0, 0.06);
            }}

            .table-scroll th:first-child {{
                z-index: 3;
                background: #eaf4ff;
            }}

            .empty-state {{
                background: #f6f9fc;
                border: 1px dashed #b9c7d3;
                border-radius: 12px;
                padding: 18px;
                color: var(--text-muted);
            }}

            .footer {{
                text-align: center;
                color: var(--text-muted);
                font-size: 12px;
                padding: 18px;
            }}

            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}

                .hero,
                .section {{
                    box-shadow: none;
                    break-inside: avoid;
                }}

                .plot-card {{
                    break-inside: avoid;
                }}

                .plot-review-card {{
                    break-inside: avoid;
                }}

                .button-link,
                .plot-actions {{
                    display: none;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <header class="hero">
                <h1>BioMotion Studio Analysis Report</h1>
                <p>
                    Review summary metrics, phase-wise biomechanics, generated files,
                    and all plots directly inside this report.
                </p>

                <div class="hero-grid">
                    <div class="hero-item">
                        <span>Sport</span>
                        <strong>{html.escape(safe_text(session_info.get("sport")))}</strong>
                    </div>
                    <div class="hero-item">
                        <span>Exercise</span>
                        <strong>{html.escape(safe_text(session_info.get("exercise")))}</strong>
                    </div>
                    <div class="hero-item">
                        <span>Camera view</span>
                        <strong>{html.escape(safe_text(session_info.get("camera_view")))}</strong>
                    </div>
                    <div class="hero-item">
                        <span>Input mode</span>
                        <strong>{html.escape(safe_text(session_info.get("input_mode")))}</strong>
                    </div>
                    <div class="hero-item">
                        <span>Created at</span>
                        <strong>{html.escape(safe_text(session_info.get("created_at")))}</strong>
                    </div>
                    <div class="hero-item">
                        <span>Report generated</span>
                        <strong>{html.escape(report_generated_at)}</strong>
                    </div>
                </div>
            </header>

            <section class="section">
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
            </section>

            <section class="section">
                <h2>2. Key Results</h2>

                <div class="metrics-grid">
                    {metric_cards_html}
                </div>
            </section>

            <section class="section">
                <h2>3. Phase-wise Biomechanics Summary</h2>
                {phase_table_html}
            </section>

            <section class="section">
                <h2>4. Plot Gallery</h2>
                <p>
                    Each plot is embedded for quick review. Use
                    <strong>Review in report</strong> to jump to the larger version,
                    or <strong>Open full-size plot</strong> to view the original PNG file.
                </p>

                <div class="plot-gallery">
                    {plot_gallery_html}
                </div>
            </section>

            <section class="section">
                <h2>5. Individual Plot Review</h2>
                {individual_plot_review_html}
            </section>

            <section class="section">
                <h2>6. Generated Files</h2>

                <div class="file-grid">
                    <div>
                        <h3>CSV Files</h3>
                        <ul>
                            {csv_rows}
                        </ul>
                    </div>

                    <div>
                        <h3>Plot Files</h3>
                        <ul>
                            {plot_rows}
                        </ul>
                    </div>
                </div>
            </section>

            <section class="section">
                <h2>7. Interpretation Notes</h2>
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
            </section>

            <div class="footer">
                Generated by BioMotion Studio.
            </div>
        </div>
    </body>
    </html>
    '''

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