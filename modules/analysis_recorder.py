from pathlib import Path
from datetime import datetime
import time
import json

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from modules.phase_definitions import EXCLUDED_PLOT_PHASES
from modules.report_generator import generate_analysis_reports


class AnalysisRecorder:
    def __init__(
        self,
        session_path: Path,
        sport: str,
        exercise: str,
        input_mode: str,
        source_file: str = "",
        camera_view: str = "N/A"
    ):
        self.session_path = Path(session_path)
        self.sport = sport
        self.exercise = exercise
        self.input_mode = input_mode
        self.source_file = source_file
        self.camera_view = camera_view

        self.records = []
        self.start_time = None

    def start(self):
        self.records = []
        self.start_time = time.time()

    def add_metrics(self, metrics: dict):
        if self.start_time is None:
            return

        elapsed_time = round(time.time() - self.start_time, 3)

        record = {
            "time_s": elapsed_time,
            "sport": self.sport,
            "exercise": self.exercise,
            "camera_view": self.camera_view,
            "phase": metrics.get("Phase", "Not Detected"),
            "pose_status": metrics.get("Pose", "Not Detected"),

            "left_hip_angle_deg": metrics.get("Left Hip Angle"),
            "right_hip_angle_deg": metrics.get("Right Hip Angle"),

            "left_knee_angle_deg": metrics.get("Left Knee Angle"),
            "right_knee_angle_deg": metrics.get("Right Knee Angle"),

            "left_ankle_angle_deg": metrics.get("Left Ankle Angle"),
            "right_ankle_angle_deg": metrics.get("Right Ankle Angle"),

            "left_shoulder_angle_deg": metrics.get("Left Shoulder Angle"),
            "right_shoulder_angle_deg": metrics.get("Right Shoulder Angle"),

            "left_elbow_angle_deg": metrics.get("Left Elbow Angle"),
            "right_elbow_angle_deg": metrics.get("Right Elbow Angle"),

            "trunk_lean_angle_deg": metrics.get("Trunk Lean Angle"),

            "athlete_depth_m": metrics.get("Athlete Depth (m)"),
            "center_depth_m": metrics.get("Center Depth (m)"),

            "barbell_detected": metrics.get("Barbell Detected"),

            "barbell_x_px": metrics.get("Barbell X (px)"),
            "barbell_y_px": metrics.get("Barbell Y (px)"),

            "barbell_horizontal_displacement_px": metrics.get("Barbell Horizontal Displacement (px)"),
            "barbell_vertical_displacement_px": metrics.get("Barbell Vertical Displacement (px)"),
            "barbell_vertical_velocity_px_s": metrics.get("Barbell Vertical Velocity (px/s)"),
            "barbell_horizontal_velocity_px_s": metrics.get("Barbell Horizontal Velocity (px/s)"),
            "barbell_max_height_px": metrics.get("Barbell Max Height (px)"),

            "barbell_x_m": metrics.get("Barbell X (m)"),
            "barbell_y_m": metrics.get("Barbell Y (m)"),
            "barbell_z_depth_m": metrics.get("Barbell Z Depth (m)"),

            "barbell_horizontal_displacement_m": metrics.get("Barbell Horizontal Displacement (m)"),
            "barbell_vertical_displacement_m": metrics.get("Barbell Vertical Displacement (m)"),
            "barbell_vertical_velocity_m_s": metrics.get("Barbell Vertical Velocity (m/s)"),
            "barbell_horizontal_velocity_m_s": metrics.get("Barbell Horizontal Velocity (m/s)"),
            "barbell_max_height_m": metrics.get("Barbell Max Height (m)")
        }

        self.records.append(record)

    def record_count(self):
        return len(self.records)

    def is_sprinting(self):
        text = f"{self.sport} {self.exercise}".lower()
        return "sprint" in text

    def is_weightlifting(self):
        text = f"{self.sport} {self.exercise}".lower()
        return "weight" in text or "snatch" in text or "clean" in text or "jerk" in text

    def save_outputs(self):
        csv_folder = self.session_path / "CSV"
        plots_folder = self.session_path / "Plots"
        reports_folder = self.session_path / "Reports"

        csv_folder.mkdir(parents=True, exist_ok=True)
        plots_folder.mkdir(parents=True, exist_ok=True)
        reports_folder.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(self.records)

        csv_file = csv_folder / "joint_angles_2d.csv"
        df.to_csv(csv_file, index=False)

        self.save_depth_csv(df, csv_folder)
        self.save_barbell_csv(df, csv_folder)
        self.save_phase_summary_csv(df, csv_folder)
        self.save_lift_summary_csv(df, csv_folder)
        self.save_sprint_summary_csv(df, csv_folder)
        self.save_phase_biomechanics_summary_csv(df, csv_folder)
        self.save_summary_csv(df, csv_folder)
        self.save_plots(df, plots_folder)
        self.save_text_report(df, reports_folder)
        self.save_recording_metadata()
        self.save_final_reports()
        
        return {
            "csv_file": str(csv_file),
            "record_count": len(df),
            "session_path": str(self.session_path)
        }

    def save_depth_csv(self, df, csv_folder):
        depth_columns = ["time_s", "athlete_depth_m", "center_depth_m"]

        if "athlete_depth_m" not in df.columns or "center_depth_m" not in df.columns:
            return

        depth_df = df[depth_columns].copy()

        if depth_df[["athlete_depth_m", "center_depth_m"]].notna().sum().sum() > 0:
            depth_df.to_csv(csv_folder / "depth_data.csv", index=False)

    def save_barbell_csv(self, df, csv_folder):
        barbell_columns = [
            "time_s",
            "phase",
            "barbell_detected",

            "barbell_x_px",
            "barbell_y_px",
            "barbell_horizontal_displacement_px",
            "barbell_vertical_displacement_px",
            "barbell_vertical_velocity_px_s",
            "barbell_horizontal_velocity_px_s",
            "barbell_max_height_px",

            "barbell_x_m",
            "barbell_y_m",
            "barbell_z_depth_m",
            "barbell_horizontal_displacement_m",
            "barbell_vertical_displacement_m",
            "barbell_vertical_velocity_m_s",
            "barbell_horizontal_velocity_m_s",
            "barbell_max_height_m"
        ]

        existing = [col for col in barbell_columns if col in df.columns]

        if not existing:
            return

        barbell_df = df[existing].copy()

        if "barbell_x_px" in barbell_df.columns and barbell_df["barbell_x_px"].notna().sum() > 0:
            barbell_df.to_csv(csv_folder / "barbell_trajectory.csv", index=False)

    def save_phase_summary_csv(self, df, csv_folder):
        if df.empty or "phase" not in df.columns:
            return

        phase_rows = []

        for phase_name, group in df.groupby("phase"):
            phase_rows.append({
                "phase": phase_name,
                "start_time_s": round(group["time_s"].min(), 3),
                "end_time_s": round(group["time_s"].max(), 3),
                "sample_count": len(group)
            })

        phase_df = pd.DataFrame(phase_rows)
        phase_df.to_csv(csv_folder / "phase_summary.csv", index=False)

    def save_lift_summary_csv(self, df, csv_folder):
        if df.empty:
            return

        def numeric_series(column_name):
            if column_name not in df.columns:
                return pd.Series(dtype="float64")

            return pd.to_numeric(df[column_name], errors="coerce")

        def safe_max(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.max(), 4)

        def safe_min(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.min(), 4)

        def safe_abs_max(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.abs().max(), 4)

        def safe_range(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.max() - series.min(), 4)

        total_duration_s = None

        if "time_s" in df.columns:
            time_series = numeric_series("time_s")

            if time_series.notna().sum() > 0:
                total_duration_s = round(time_series.max() - time_series.min(), 3)

        detected_phases = []

        if "phase" in df.columns:
            for phase in df["phase"].dropna().tolist():
                if phase in EXCLUDED_PLOT_PHASES:
                    continue

                if phase not in detected_phases:
                    detected_phases.append(phase)

        barbell_detected_samples = 0

        if "barbell_detected" in df.columns:
            barbell_detected_samples = int(
                df["barbell_detected"]
                .fillna(False)
                .astype(bool)
                .sum()
            )

        lift_summary = {
            "sport": self.sport,
            "exercise": self.exercise,
            "camera_view": self.camera_view,
            "input_mode": self.input_mode,
            "source_file": self.source_file,

            "record_count": len(df),
            "total_duration_s": total_duration_s,

            "detected_phase_count": len(detected_phases),
            "detected_phases": " | ".join(detected_phases),

            "barbell_detected_samples": barbell_detected_samples,

            "max_barbell_height_px": safe_max("barbell_max_height_px"),
            "max_barbell_height_m": safe_max("barbell_max_height_m"),

            "max_vertical_displacement_px": safe_max("barbell_vertical_displacement_px"),
            "max_vertical_displacement_m": safe_max("barbell_vertical_displacement_m"),

            "min_vertical_displacement_px": safe_min("barbell_vertical_displacement_px"),
            "min_vertical_displacement_m": safe_min("barbell_vertical_displacement_m"),

            "vertical_displacement_range_px": safe_range("barbell_vertical_displacement_px"),
            "vertical_displacement_range_m": safe_range("barbell_vertical_displacement_m"),

            "max_horizontal_displacement_px": safe_max("barbell_horizontal_displacement_px"),
            "max_horizontal_displacement_m": safe_max("barbell_horizontal_displacement_m"),

            "min_horizontal_displacement_px": safe_min("barbell_horizontal_displacement_px"),
            "min_horizontal_displacement_m": safe_min("barbell_horizontal_displacement_m"),

            "horizontal_displacement_range_px": safe_range("barbell_horizontal_displacement_px"),
            "horizontal_displacement_range_m": safe_range("barbell_horizontal_displacement_m"),

            "max_vertical_velocity_px_s": safe_abs_max("barbell_vertical_velocity_px_s"),
            "max_vertical_velocity_m_s": safe_abs_max("barbell_vertical_velocity_m_s"),

            "max_horizontal_velocity_px_s": safe_abs_max("barbell_horizontal_velocity_px_s"),
            "max_horizontal_velocity_m_s": safe_abs_max("barbell_horizontal_velocity_m_s"),

            "mean_athlete_depth_m": None,
            "mean_center_depth_m": None,

            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        athlete_depth = numeric_series("athlete_depth_m")
        if athlete_depth.notna().sum() > 0:
            lift_summary["mean_athlete_depth_m"] = round(athlete_depth.mean(), 4)

        center_depth = numeric_series("center_depth_m")
        if center_depth.notna().sum() > 0:
            lift_summary["mean_center_depth_m"] = round(center_depth.mean(), 4)

        summary_df = pd.DataFrame([lift_summary])
        summary_df.to_csv(csv_folder / "lift_summary.csv", index=False)

    def save_sprint_summary_csv(self, df, csv_folder):
        """
        Save sprinting-specific one-row summary.

        Creates:
            CSV/sprint_summary.csv

        This does not replace lift_summary.csv because the ResultsPage and
        older code paths still use lift_summary.csv as the generic session
        summary file.
        """

        if df.empty or not self.is_sprinting():
            return

        def numeric_series(column_name):
            if column_name not in df.columns:
                return pd.Series(dtype="float64")

            return pd.to_numeric(df[column_name], errors="coerce")

        def safe_mean(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.mean(), 4)

        def safe_min(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.min(), 4)

        def safe_max(column_name):
            series = numeric_series(column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.max(), 4)

        total_duration_s = None

        if "time_s" in df.columns:
            time_series = numeric_series("time_s")

            if time_series.notna().sum() > 0:
                total_duration_s = round(time_series.max() - time_series.min(), 3)

        phase_segments = self.build_phase_segments(df)

        def phase_total_duration(phase_name):
            total = 0.0

            for segment in phase_segments:
                if segment["phase"] == phase_name and segment["duration_s"] is not None:
                    total += segment["duration_s"]

            return round(total, 3)

        def phase_segment_count(phase_name):
            count = 0

            for segment in phase_segments:
                if segment["phase"] == phase_name:
                    count += 1

            return count

        detected_phases = []

        if "phase" in df.columns:
            for phase in df["phase"].dropna().tolist():
                if phase in EXCLUDED_PLOT_PHASES:
                    continue

                if phase not in detected_phases:
                    detected_phases.append(phase)

        sprint_summary = {
            "sport": self.sport,
            "exercise": self.exercise,
            "camera_view": self.camera_view,
            "input_mode": self.input_mode,
            "source_file": self.source_file,

            "record_count": len(df),
            "total_duration_s": total_duration_s,

            "detected_phase_count": len(detected_phases),
            "detected_phases": " | ".join(detected_phases),

            "initial_contact_events": phase_segment_count("Initial Contact"),
            "toe_off_events": phase_segment_count("Toe-Off"),

            "support_total_duration_s": phase_total_duration("Support Phase"),
            "flight_swing_total_duration_s": phase_total_duration("Flight / Swing"),
            "initial_contact_total_duration_s": phase_total_duration("Initial Contact"),
            "toe_off_total_duration_s": phase_total_duration("Toe-Off"),

            "mean_left_hip_angle_deg": safe_mean("left_hip_angle_deg"),
            "mean_right_hip_angle_deg": safe_mean("right_hip_angle_deg"),
            "mean_left_knee_angle_deg": safe_mean("left_knee_angle_deg"),
            "mean_right_knee_angle_deg": safe_mean("right_knee_angle_deg"),
            "mean_left_ankle_angle_deg": safe_mean("left_ankle_angle_deg"),
            "mean_right_ankle_angle_deg": safe_mean("right_ankle_angle_deg"),

            "min_left_knee_angle_deg": safe_min("left_knee_angle_deg"),
            "min_right_knee_angle_deg": safe_min("right_knee_angle_deg"),
            "max_left_knee_angle_deg": safe_max("left_knee_angle_deg"),
            "max_right_knee_angle_deg": safe_max("right_knee_angle_deg"),

            "mean_trunk_lean_angle_deg": safe_mean("trunk_lean_angle_deg"),
            "min_trunk_lean_angle_deg": safe_min("trunk_lean_angle_deg"),
            "max_trunk_lean_angle_deg": safe_max("trunk_lean_angle_deg"),

            "mean_athlete_depth_m": safe_mean("athlete_depth_m"),
            "mean_center_depth_m": safe_mean("center_depth_m"),

            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        summary_df = pd.DataFrame([sprint_summary])
        summary_df.to_csv(csv_folder / "sprint_summary.csv", index=False)

    def build_phase_segments(self, df):
        """
        Build contiguous phase segments from the recorded frame-by-frame data.

        Returns list of dictionaries:
            phase, start_time_s, end_time_s, duration_s, sample_count
        """

        if df.empty or "phase" not in df.columns or "time_s" not in df.columns:
            return []

        work_df = df[["time_s", "phase"]].copy()
        work_df["time_s"] = pd.to_numeric(work_df["time_s"], errors="coerce")
        work_df = work_df.dropna(subset=["time_s", "phase"])

        if work_df.empty:
            return []

        segments = []

        current_phase = None
        start_time = None
        end_time = None
        sample_count = 0

        for _, row in work_df.iterrows():
            phase = row["phase"]
            time_s = row["time_s"]

            if pd.isna(phase):
                continue

            phase = str(phase)

            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if current_phase is None:
                current_phase = phase
                start_time = time_s
                end_time = time_s
                sample_count = 1
                continue

            if phase == current_phase:
                end_time = time_s
                sample_count += 1
            else:
                segments.append({
                    "phase": current_phase,
                    "start_time_s": round(float(start_time), 3),
                    "end_time_s": round(float(end_time), 3),
                    "duration_s": round(float(end_time - start_time), 3),
                    "sample_count": sample_count
                })

                current_phase = phase
                start_time = time_s
                end_time = time_s
                sample_count = 1

        if current_phase is not None:
            segments.append({
                "phase": current_phase,
                "start_time_s": round(float(start_time), 3),
                "end_time_s": round(float(end_time), 3),
                "duration_s": round(float(end_time - start_time), 3),
                "sample_count": sample_count
            })

        return segments

    def save_text_report(self, df, reports_folder):
        """
        Save a readable text report for final demo/thesis checking.

        Creates:
            Reports/analysis_report.txt
            Reports/sprinting_summary_report.txt or Reports/weightlifting_summary_report.txt
        """

        if df.empty:
            return

        report_lines = []

        report_lines.append("BioMotion Studio - Analysis Report")
        report_lines.append("=" * 42)
        report_lines.append("")
        report_lines.append(f"Sport          : {self.sport}")
        report_lines.append(f"Exercise       : {self.exercise}")
        report_lines.append(f"Camera View    : {self.camera_view}")
        report_lines.append(f"Input Mode     : {self.input_mode}")
        report_lines.append(f"Source File    : {self.source_file if self.source_file else 'Live Source'}")
        report_lines.append(f"Record Count   : {len(df)}")
        report_lines.append(f"Created At     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        if "time_s" in df.columns:
            time_series = pd.to_numeric(df["time_s"], errors="coerce")

            if time_series.notna().sum() > 0:
                duration = round(time_series.max() - time_series.min(), 3)
                report_lines.append(f"Total Duration : {duration} s")
                report_lines.append("")

        phase_segments = self.build_phase_segments(df)

        if phase_segments:
            report_lines.append("Detected Phase Segments")
            report_lines.append("-" * 42)

            for segment in phase_segments:
                report_lines.append(
                    f"{segment['phase']}: "
                    f"{segment['start_time_s']} s to {segment['end_time_s']} s, "
                    f"duration {segment['duration_s']} s, "
                    f"samples {segment['sample_count']}"
                )

            report_lines.append("")

        def add_numeric_stat(label, column_name, unit=""):
            if column_name not in df.columns:
                return

            series = pd.to_numeric(df[column_name], errors="coerce")

            if series.notna().sum() == 0:
                return

            suffix = f" {unit}" if unit else ""

            report_lines.append(
                f"{label}: mean={series.mean():.3f}{suffix}, "
                f"min={series.min():.3f}{suffix}, "
                f"max={series.max():.3f}{suffix}"
            )

        if self.is_sprinting():
            report_lines.append("Sprinting Biomechanics Summary")
            report_lines.append("-" * 42)

            add_numeric_stat("Left Hip Angle", "left_hip_angle_deg", "deg")
            add_numeric_stat("Right Hip Angle", "right_hip_angle_deg", "deg")
            add_numeric_stat("Left Knee Angle", "left_knee_angle_deg", "deg")
            add_numeric_stat("Right Knee Angle", "right_knee_angle_deg", "deg")
            add_numeric_stat("Left Ankle Angle", "left_ankle_angle_deg", "deg")
            add_numeric_stat("Right Ankle Angle", "right_ankle_angle_deg", "deg")
            add_numeric_stat("Trunk Lean Angle", "trunk_lean_angle_deg", "deg")
            add_numeric_stat("Athlete Depth", "athlete_depth_m", "m")
            add_numeric_stat("Center Depth", "center_depth_m", "m")

        else:
            report_lines.append("Weightlifting Biomechanics Summary")
            report_lines.append("-" * 42)

            add_numeric_stat("Left Hip Angle", "left_hip_angle_deg", "deg")
            add_numeric_stat("Right Hip Angle", "right_hip_angle_deg", "deg")
            add_numeric_stat("Left Knee Angle", "left_knee_angle_deg", "deg")
            add_numeric_stat("Right Knee Angle", "right_knee_angle_deg", "deg")
            add_numeric_stat("Trunk Lean Angle", "trunk_lean_angle_deg", "deg")
            add_numeric_stat("Barbell Vertical Displacement", "barbell_vertical_displacement_m", "m")
            add_numeric_stat("Barbell Horizontal Displacement", "barbell_horizontal_displacement_m", "m")
            add_numeric_stat("Barbell Vertical Velocity", "barbell_vertical_velocity_m_s", "m/s")
            add_numeric_stat("Barbell Horizontal Velocity", "barbell_horizontal_velocity_m_s", "m/s")
            add_numeric_stat("Barbell Vertical Displacement", "barbell_vertical_displacement_px", "px")
            add_numeric_stat("Barbell Horizontal Displacement", "barbell_horizontal_displacement_px", "px")
            add_numeric_stat("Barbell Vertical Velocity", "barbell_vertical_velocity_px_s", "px/s")
            add_numeric_stat("Barbell Horizontal Velocity", "barbell_horizontal_velocity_px_s", "px/s")

        report_lines.append("")
        report_lines.append("Generated by BioMotion Studio.")

        report_text = "\n".join(report_lines)

        generic_report_path = reports_folder / "analysis_report.txt"

        with open(generic_report_path, "w", encoding="utf-8") as file:
            file.write(report_text)

        if self.is_sprinting():
            named_report_path = reports_folder / "sprinting_summary_report.txt"
        else:
            named_report_path = reports_folder / "weightlifting_summary_report.txt"

        with open(named_report_path, "w", encoding="utf-8") as file:
            file.write(report_text)

    def save_phase_biomechanics_summary_csv(self, df, csv_folder):
        """
        Save phase-wise biomechanics summary.

        Creates:
            CSV/phase_biomechanics_summary.csv
        """

        if df.empty:
            return

        if "phase" not in df.columns or "time_s" not in df.columns:
            return

        def numeric_series(dataframe, column_name):
            if column_name not in dataframe.columns:
                return pd.Series(dtype="float64")

            return pd.to_numeric(dataframe[column_name], errors="coerce")

        def safe_mean(dataframe, column_name):
            series = numeric_series(dataframe, column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.mean(), 4)

        def safe_min(dataframe, column_name):
            series = numeric_series(dataframe, column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.min(), 4)

        def safe_max(dataframe, column_name):
            series = numeric_series(dataframe, column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.max(), 4)

        def safe_abs_max(dataframe, column_name):
            series = numeric_series(dataframe, column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.abs().max(), 4)

        def safe_range(dataframe, column_name):
            series = numeric_series(dataframe, column_name)

            if series.notna().sum() == 0:
                return None

            return round(series.max() - series.min(), 4)

        phase_order = []

        for phase in df["phase"].dropna().tolist():
            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if phase not in phase_order:
                phase_order.append(phase)

        if not phase_order:
            return

        summary_rows = []

        for phase_name in phase_order:
            phase_df = df[df["phase"] == phase_name].copy()

            if phase_df.empty:
                continue

            time_series = numeric_series(phase_df, "time_s")

            if time_series.notna().sum() > 0:
                start_time = round(time_series.min(), 3)
                end_time = round(time_series.max(), 3)
                duration = round(end_time - start_time, 3)
            else:
                start_time = None
                end_time = None
                duration = None

            row = {
                "sport": self.sport,
                "exercise": self.exercise,
                "camera_view": self.camera_view,
                "input_mode": self.input_mode,
                "phase": phase_name,

                "start_time_s": start_time,
                "end_time_s": end_time,
                "duration_s": duration,
                "sample_count": len(phase_df),

                "left_hip_angle_mean_deg": safe_mean(phase_df, "left_hip_angle_deg"),
                "left_hip_angle_min_deg": safe_min(phase_df, "left_hip_angle_deg"),
                "left_hip_angle_max_deg": safe_max(phase_df, "left_hip_angle_deg"),
                "left_hip_angle_range_deg": safe_range(phase_df, "left_hip_angle_deg"),

                "right_hip_angle_mean_deg": safe_mean(phase_df, "right_hip_angle_deg"),
                "right_hip_angle_min_deg": safe_min(phase_df, "right_hip_angle_deg"),
                "right_hip_angle_max_deg": safe_max(phase_df, "right_hip_angle_deg"),
                "right_hip_angle_range_deg": safe_range(phase_df, "right_hip_angle_deg"),

                "left_knee_angle_mean_deg": safe_mean(phase_df, "left_knee_angle_deg"),
                "left_knee_angle_min_deg": safe_min(phase_df, "left_knee_angle_deg"),
                "left_knee_angle_max_deg": safe_max(phase_df, "left_knee_angle_deg"),
                "left_knee_angle_range_deg": safe_range(phase_df, "left_knee_angle_deg"),

                "right_knee_angle_mean_deg": safe_mean(phase_df, "right_knee_angle_deg"),
                "right_knee_angle_min_deg": safe_min(phase_df, "right_knee_angle_deg"),
                "right_knee_angle_max_deg": safe_max(phase_df, "right_knee_angle_deg"),
                "right_knee_angle_range_deg": safe_range(phase_df, "right_knee_angle_deg"),

                "left_ankle_angle_mean_deg": safe_mean(phase_df, "left_ankle_angle_deg"),
                "left_ankle_angle_min_deg": safe_min(phase_df, "left_ankle_angle_deg"),
                "left_ankle_angle_max_deg": safe_max(phase_df, "left_ankle_angle_deg"),
                "left_ankle_angle_range_deg": safe_range(phase_df, "left_ankle_angle_deg"),

                "right_ankle_angle_mean_deg": safe_mean(phase_df, "right_ankle_angle_deg"),
                "right_ankle_angle_min_deg": safe_min(phase_df, "right_ankle_angle_deg"),
                "right_ankle_angle_max_deg": safe_max(phase_df, "right_ankle_angle_deg"),
                "right_ankle_angle_range_deg": safe_range(phase_df, "right_ankle_angle_deg"),

                "left_shoulder_angle_mean_deg": safe_mean(phase_df, "left_shoulder_angle_deg"),
                "left_shoulder_angle_min_deg": safe_min(phase_df, "left_shoulder_angle_deg"),
                "left_shoulder_angle_max_deg": safe_max(phase_df, "left_shoulder_angle_deg"),

                "right_shoulder_angle_mean_deg": safe_mean(phase_df, "right_shoulder_angle_deg"),
                "right_shoulder_angle_min_deg": safe_min(phase_df, "right_shoulder_angle_deg"),
                "right_shoulder_angle_max_deg": safe_max(phase_df, "right_shoulder_angle_deg"),

                "left_elbow_angle_mean_deg": safe_mean(phase_df, "left_elbow_angle_deg"),
                "left_elbow_angle_min_deg": safe_min(phase_df, "left_elbow_angle_deg"),
                "left_elbow_angle_max_deg": safe_max(phase_df, "left_elbow_angle_deg"),

                "right_elbow_angle_mean_deg": safe_mean(phase_df, "right_elbow_angle_deg"),
                "right_elbow_angle_min_deg": safe_min(phase_df, "right_elbow_angle_deg"),
                "right_elbow_angle_max_deg": safe_max(phase_df, "right_elbow_angle_deg"),

                "trunk_lean_angle_mean_deg": safe_mean(phase_df, "trunk_lean_angle_deg"),
                "trunk_lean_angle_min_deg": safe_min(phase_df, "trunk_lean_angle_deg"),
                "trunk_lean_angle_max_deg": safe_max(phase_df, "trunk_lean_angle_deg"),
                "trunk_lean_angle_range_deg": safe_range(phase_df, "trunk_lean_angle_deg"),

                "barbell_vertical_displacement_mean_px": safe_mean(phase_df, "barbell_vertical_displacement_px"),
                "barbell_vertical_displacement_min_px": safe_min(phase_df, "barbell_vertical_displacement_px"),
                "barbell_vertical_displacement_max_px": safe_max(phase_df, "barbell_vertical_displacement_px"),
                "barbell_vertical_displacement_range_px": safe_range(phase_df, "barbell_vertical_displacement_px"),

                "barbell_horizontal_displacement_mean_px": safe_mean(phase_df, "barbell_horizontal_displacement_px"),
                "barbell_horizontal_displacement_min_px": safe_min(phase_df, "barbell_horizontal_displacement_px"),
                "barbell_horizontal_displacement_max_px": safe_max(phase_df, "barbell_horizontal_displacement_px"),
                "barbell_horizontal_displacement_range_px": safe_range(phase_df, "barbell_horizontal_displacement_px"),

                "barbell_vertical_velocity_mean_px_s": safe_mean(phase_df, "barbell_vertical_velocity_px_s"),
                "barbell_vertical_velocity_max_abs_px_s": safe_abs_max(phase_df, "barbell_vertical_velocity_px_s"),

                "barbell_horizontal_velocity_mean_px_s": safe_mean(phase_df, "barbell_horizontal_velocity_px_s"),
                "barbell_horizontal_velocity_max_abs_px_s": safe_abs_max(phase_df, "barbell_horizontal_velocity_px_s"),

                "barbell_vertical_displacement_mean_m": safe_mean(phase_df, "barbell_vertical_displacement_m"),
                "barbell_vertical_displacement_min_m": safe_min(phase_df, "barbell_vertical_displacement_m"),
                "barbell_vertical_displacement_max_m": safe_max(phase_df, "barbell_vertical_displacement_m"),
                "barbell_vertical_displacement_range_m": safe_range(phase_df, "barbell_vertical_displacement_m"),

                "barbell_horizontal_displacement_mean_m": safe_mean(phase_df, "barbell_horizontal_displacement_m"),
                "barbell_horizontal_displacement_min_m": safe_min(phase_df, "barbell_horizontal_displacement_m"),
                "barbell_horizontal_displacement_max_m": safe_max(phase_df, "barbell_horizontal_displacement_m"),
                "barbell_horizontal_displacement_range_m": safe_range(phase_df, "barbell_horizontal_displacement_m"),

                "barbell_vertical_velocity_mean_m_s": safe_mean(phase_df, "barbell_vertical_velocity_m_s"),
                "barbell_vertical_velocity_max_abs_m_s": safe_abs_max(phase_df, "barbell_vertical_velocity_m_s"),

                "barbell_horizontal_velocity_mean_m_s": safe_mean(phase_df, "barbell_horizontal_velocity_m_s"),
                "barbell_horizontal_velocity_max_abs_m_s": safe_abs_max(phase_df, "barbell_horizontal_velocity_m_s"),

                "athlete_depth_mean_m": safe_mean(phase_df, "athlete_depth_m"),
                "athlete_depth_min_m": safe_min(phase_df, "athlete_depth_m"),
                "athlete_depth_max_m": safe_max(phase_df, "athlete_depth_m"),

                "center_depth_mean_m": safe_mean(phase_df, "center_depth_m"),
                "center_depth_min_m": safe_min(phase_df, "center_depth_m"),
                "center_depth_max_m": safe_max(phase_df, "center_depth_m")
            }

            summary_rows.append(row)

        if not summary_rows:
            return

        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(csv_folder / "phase_biomechanics_summary.csv", index=False)

    def save_summary_csv(self, df, csv_folder):
        numeric_columns = [
            "left_hip_angle_deg",
            "right_hip_angle_deg",
            "left_knee_angle_deg",
            "right_knee_angle_deg",
            "left_ankle_angle_deg",
            "right_ankle_angle_deg",
            "left_shoulder_angle_deg",
            "right_shoulder_angle_deg",
            "left_elbow_angle_deg",
            "right_elbow_angle_deg",
            "trunk_lean_angle_deg",

            "athlete_depth_m",
            "center_depth_m",

            "barbell_horizontal_displacement_px",
            "barbell_vertical_displacement_px",
            "barbell_vertical_velocity_px_s",
            "barbell_horizontal_velocity_px_s",

            "barbell_horizontal_displacement_m",
            "barbell_vertical_displacement_m",
            "barbell_vertical_velocity_m_s",
            "barbell_horizontal_velocity_m_s"
        ]

        summary_rows = []

        for col in numeric_columns:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")

                if series.notna().sum() > 0:
                    summary_rows.append({
                        "metric": col,
                        "mean": round(series.mean(), 3),
                        "min": round(series.min(), 3),
                        "max": round(series.max(), 3),
                        "valid_samples": int(series.notna().sum())
                    })

        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(csv_folder / "analysis_summary.csv", index=False)

    def save_plots(self, df, plots_folder):
        if df.empty or "time_s" not in df.columns:
            return

        if self.is_sprinting():
            self.save_sprinting_plots(df, plots_folder)
            return

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_hip_angle_deg",
                "right_hip_angle_deg",
                "left_knee_angle_deg",
                "right_knee_angle_deg"
            ],
            title=f"{self.exercise} Hip and Knee Angles ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="hip_knee_angles_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_elbow_angle_deg",
                "right_elbow_angle_deg",
                "left_shoulder_angle_deg",
                "right_shoulder_angle_deg"
            ],
            title=f"{self.exercise} Shoulder and Elbow Angles ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="upper_limb_angles_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=["trunk_lean_angle_deg"],
            title=f"{self.exercise} Trunk Lean Angle ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="trunk_lean_phase_highlighted.png",
            shade_phases=True
        )

        velocity_col = self.choose_column(
            df,
            preferred="barbell_vertical_velocity_m_s",
            fallback="barbell_vertical_velocity_px_s"
        )

        if velocity_col:
            ylabel = "Velocity (m/s)" if velocity_col.endswith("_m_s") else "Velocity (px/s)"

            self.plot_group(
                df=df,
                plots_folder=plots_folder,
                columns=[velocity_col],
                title=f"{self.exercise} Barbell Vertical Velocity ({self.camera_view})",
                ylabel=ylabel,
                filename="barbell_velocity_phase_highlighted.png",
                shade_phases=True
            )

        self.save_barbell_trajectory_plot(df, plots_folder)

    def save_sprinting_plots(self, df, plots_folder):
        """
        Save sprinting-specific plots.

        Creates:
            sprinting_phase_timeline.png
            hip_knee_angles_phase_highlighted.png
            sprinting_knee_ankle_angles_phase_highlighted.png
            upper_limb_angles_phase_highlighted.png
            trunk_lean_phase_highlighted.png
            sprinting_depth_profile_phase_highlighted.png
        """

        self.save_phase_timeline_plot(
            df=df,
            plots_folder=plots_folder,
            filename="sprinting_phase_timeline.png"
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_hip_angle_deg",
                "right_hip_angle_deg",
                "left_knee_angle_deg",
                "right_knee_angle_deg"
            ],
            title=f"{self.exercise} Hip and Knee Angles ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="hip_knee_angles_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_knee_angle_deg",
                "right_knee_angle_deg",
                "left_ankle_angle_deg",
                "right_ankle_angle_deg"
            ],
            title=f"{self.exercise} Knee and Ankle Angles ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="sprinting_knee_ankle_angles_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_elbow_angle_deg",
                "right_elbow_angle_deg",
                "left_shoulder_angle_deg",
                "right_shoulder_angle_deg"
            ],
            title=f"{self.exercise} Shoulder and Elbow Angles ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="upper_limb_angles_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=["trunk_lean_angle_deg"],
            title=f"{self.exercise} Trunk Lean Angle ({self.camera_view})",
            ylabel="Angle (degrees)",
            filename="trunk_lean_phase_highlighted.png",
            shade_phases=True
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "athlete_depth_m",
                "center_depth_m"
            ],
            title=f"{self.exercise} Depth Profile ({self.camera_view})",
            ylabel="Depth (m)",
            filename="sprinting_depth_profile_phase_highlighted.png",
            shade_phases=True
        )

    def save_phase_timeline_plot(self, df, plots_folder, filename):
        if df.empty or "time_s" not in df.columns or "phase" not in df.columns:
            return

        plot_df = df[["time_s", "phase"]].copy()
        plot_df["time_s"] = pd.to_numeric(plot_df["time_s"], errors="coerce")
        plot_df = plot_df.dropna(subset=["time_s", "phase"])

        if plot_df.empty:
            return

        phase_order = []

        for phase in plot_df["phase"].tolist():
            phase = str(phase)

            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if phase not in phase_order:
                phase_order.append(phase)

        if not phase_order:
            return

        phase_to_y = {}

        for index, phase in enumerate(phase_order):
            phase_to_y[phase] = index

        plot_df = plot_df[plot_df["phase"].isin(phase_order)].copy()

        if plot_df.empty:
            return

        plot_df["phase_y"] = plot_df["phase"].map(phase_to_y)

        fig, ax = plt.subplots(figsize=(10.5, 4.8))

        phase_colors = {
            "Initial Contact": "#1f77b4",
            "Support Phase": "#ff7f0e",
            "Toe-Off": "#2ca02c",
            "Flight / Swing": "#9467bd",
        }

        segments = self.build_phase_segments(plot_df)

        for segment in segments:
            phase = segment["phase"]

            if phase not in phase_to_y:
                continue

            y_value = phase_to_y[phase]
            color = phase_colors.get(phase, "#444444")

            ax.hlines(
                y=y_value,
                xmin=segment["start_time_s"],
                xmax=segment["end_time_s"],
                linewidth=7,
                color=color,
                alpha=0.85
            )

            midpoint = (segment["start_time_s"] + segment["end_time_s"]) / 2.0

            if segment["duration_s"] >= 0.20:
                ax.text(
                    midpoint,
                    y_value + 0.12,
                    phase,
                    ha="center",
                    va="bottom",
                    fontsize=7
                )

        ax.set_yticks(list(phase_to_y.values()))
        ax.set_yticklabels(list(phase_to_y.keys()))
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Sprint Phase")
        ax.set_title(f"{self.exercise} Phase Timeline ({self.camera_view})")
        ax.grid(True, axis="x", alpha=0.35)

        fig.tight_layout()
        fig.savefig(plots_folder / filename, dpi=300)
        plt.close(fig)

    def choose_column(self, df, preferred, fallback):
        if preferred in df.columns and pd.to_numeric(df[preferred], errors="coerce").notna().sum() > 0:
            return preferred

        if fallback in df.columns and pd.to_numeric(df[fallback], errors="coerce").notna().sum() > 0:
            return fallback

        return None

    def plot_group(self, df, plots_folder, columns, title, ylabel, filename, shade_phases=False):
        valid_columns = []

        for col in columns:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")

                if series.notna().sum() > 0:
                    valid_columns.append(col)

        if not valid_columns:
            return

        fig, ax = plt.subplots(figsize=(10.5, 5.6))

        def smooth_for_display(series, column_name):
            series = pd.to_numeric(series, errors="coerce")

            valid_count = series.notna().sum()

            if valid_count < 5:
                return series

            column_name_lower = column_name.lower()

            if "velocity" in column_name_lower:
                window = 11
            else:
                window = 7

            median_series = series.rolling(
                window=window,
                center=True,
                min_periods=1
            ).median()

            smooth_series = median_series.rolling(
                window=window,
                center=True,
                min_periods=1
            ).mean()

            return smooth_series

        for col in valid_columns:
            raw_series = pd.to_numeric(df[col], errors="coerce")
            plot_series = smooth_for_display(raw_series, col)

            ax.plot(
                df["time_s"],
                plot_series,
                linewidth=1.8,
                label=col
            )

        if shade_phases:
            self.add_phase_shading(ax, df)

        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.35)

        ax.legend(
            loc="best",
            fontsize=8,
            framealpha=0.85
        )

        fig.tight_layout()
        fig.savefig(plots_folder / filename, dpi=300)
        plt.close(fig)

    def add_phase_shading(self, ax, df):
        if "phase" not in df.columns or df.empty:
            return

        phase_label_map = {
            "Setup": "Setup",
            "Deadlift Phase": "Deadlift",
            "Jump Phase": "Jump",
            "Catch Phase": "Catch",
            "Overhead Squat Phase": "OHS",
            "Squat Phase": "Squat",
            "Jerk Phase": "Jerk",

            "Initial Contact": "Contact",
            "Support Phase": "Support",
            "Toe-Off": "Toe-Off",
            "Flight / Swing": "Swing",

            "Not Detected": "N/D",
            "Unknown": "Unknown"
        }

        phase_colors = {
            "Deadlift Phase": "#1f77b4",
            "Jump Phase": "#ff7f0e",
            "Catch Phase": "#2ca02c",
            "Overhead Squat Phase": "#9467bd",
            "Squat Phase": "#d62728",
            "Jerk Phase": "#17becf",

            "Initial Contact": "#1f77b4",
            "Support Phase": "#ff7f0e",
            "Toe-Off": "#2ca02c",
            "Flight / Swing": "#9467bd",

            "Setup": "#808080",
            "Unknown": "#aaaaaa"
        }

        phase_segments = []
        current_phase = None
        start_time = None
        last_time = None

        for _, row in df.iterrows():
            phase = row["phase"]
            time_s = row["time_s"]

            if pd.isna(phase) or pd.isna(time_s):
                continue

            if phase != current_phase:
                if current_phase is not None:
                    phase_segments.append((current_phase, start_time, last_time))

                current_phase = phase
                start_time = time_s

            last_time = time_s

        if current_phase is not None:
            phase_segments.append((current_phase, start_time, last_time))

        if not phase_segments:
            return

        xaxis_transform = ax.get_xaxis_transform()

        label_levels = [0.98, 0.90, 0.82]
        label_index = 0

        for phase, start, end in phase_segments:
            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if start is None or end is None:
                continue

            duration = end - start

            if duration <= 0:
                continue

            color = phase_colors.get(phase, "#808080")

            ax.axvspan(
                start,
                end,
                alpha=0.08,
                color=color
            )

            if duration < 0.35:
                continue

            short_label = phase_label_map.get(phase, phase)
            midpoint = (start + end) / 2.0
            y_level = label_levels[label_index % len(label_levels)]

            ax.text(
                midpoint,
                y_level,
                short_label,
                transform=xaxis_transform,
                rotation=0,
                verticalalignment="top",
                horizontalalignment="center",
                fontsize=7,
                color="black",
                bbox=dict(
                    boxstyle="round,pad=0.18",
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.65
                )
            )

            label_index += 1

    def save_barbell_trajectory_plot(self, df, plots_folder):
        use_meters = False

        x_col = None
        y_col = None

        if (
            "barbell_horizontal_displacement_m" in df.columns
            and "barbell_vertical_displacement_m" in df.columns
            and pd.to_numeric(df["barbell_horizontal_displacement_m"], errors="coerce").notna().sum() > 0
            and pd.to_numeric(df["barbell_vertical_displacement_m"], errors="coerce").notna().sum() > 0
        ):
            x_col = "barbell_horizontal_displacement_m"
            y_col = "barbell_vertical_displacement_m"
            use_meters = True

        elif (
            "barbell_horizontal_displacement_px" in df.columns
            and "barbell_vertical_displacement_px" in df.columns
            and pd.to_numeric(df["barbell_horizontal_displacement_px"], errors="coerce").notna().sum() > 0
            and pd.to_numeric(df["barbell_vertical_displacement_px"], errors="coerce").notna().sum() > 0
        ):
            x_col = "barbell_horizontal_displacement_px"
            y_col = "barbell_vertical_displacement_px"
            use_meters = False

        if x_col is None or y_col is None:
            return

        plot_df = df.copy()

        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")

        plot_df = plot_df.dropna(subset=[x_col, y_col])

        if len(plot_df) < 2:
            return

        if "phase" in plot_df.columns:
            filtered_df = plot_df[~plot_df["phase"].isin(EXCLUDED_PLOT_PHASES)].copy()

            if len(filtered_df) >= 2:
                plot_df = filtered_df

        smooth_window = 7

        if len(plot_df) >= smooth_window:
            plot_df["trajectory_x_smooth"] = (
                plot_df[x_col]
                .rolling(window=smooth_window, center=True, min_periods=1)
                .mean()
            )

            plot_df["trajectory_y_smooth"] = (
                plot_df[y_col]
                .rolling(window=smooth_window, center=True, min_periods=1)
                .mean()
            )
        else:
            plot_df["trajectory_x_smooth"] = plot_df[x_col]
            plot_df["trajectory_y_smooth"] = plot_df[y_col]

        unit = "m" if use_meters else "px"

        def apply_trajectory_axis_scaling(ax, data):
            x_values = pd.to_numeric(
                data["trajectory_x_smooth"],
                errors="coerce"
            ).dropna()

            y_values = pd.to_numeric(
                data["trajectory_y_smooth"],
                errors="coerce"
            ).dropna()

            if x_values.empty or y_values.empty:
                return

            x_min = float(x_values.min())
            x_max = float(x_values.max())
            y_min = float(y_values.min())
            y_max = float(y_values.max())

            y_range = max(y_max - y_min, 1e-6)

            visible_x_min = min(x_min, 0.0)
            visible_x_max = max(x_max, 0.0)

            visible_x_range = max(visible_x_max - visible_x_min, 1e-6)

            desired_x_range = max(
                visible_x_range * 1.35,
                y_range * 0.35
            )

            x_center = (visible_x_min + visible_x_max) / 2.0

            x_margin_min = x_center - desired_x_range / 2.0
            x_margin_max = x_center + desired_x_range / 2.0

            if use_meters:
                y_margin = max(y_range * 0.05, 0.02)
            else:
                y_margin = max(y_range * 0.05, 5.0)

            ax.set_xlim(x_margin_min, x_margin_max)
            ax.set_ylim(y_min - y_margin, y_max + y_margin)

        start = plot_df.iloc[0]
        end = plot_df.iloc[-1]

        max_idx = plot_df["trajectory_y_smooth"].idxmax()
        max_point = plot_df.loc[max_idx]

        phase_colors = {
            "Deadlift Phase": "#1f77b4",
            "Jump Phase": "#ff7f0e",
            "Catch Phase": "#2ca02c",
            "Overhead Squat Phase": "#9467bd",

            "Squat Phase": "#d62728",
            "Jerk Phase": "#17becf",

            "Initial Contact": "#1f77b4",
            "Support Phase": "#ff7f0e",
            "Toe-Off": "#2ca02c",
            "Flight / Swing": "#9467bd",

            "Unknown": "#444444",
        }

        # ======================================================
        # Plot 1: Annotated trajectory
        # ======================================================
        fig, ax = plt.subplots(figsize=(6.2, 6.8))

        ax.plot(
            plot_df["trajectory_x_smooth"],
            plot_df["trajectory_y_smooth"],
            linewidth=2.5,
            label="Smoothed barbell path"
        )

        ax.scatter(
            start["trajectory_x_smooth"],
            start["trajectory_y_smooth"],
            s=45,
            label="Start"
        )

        ax.scatter(
            max_point["trajectory_x_smooth"],
            max_point["trajectory_y_smooth"],
            s=55,
            marker="^",
            label="Max height"
        )

        ax.scatter(
            end["trajectory_x_smooth"],
            end["trajectory_y_smooth"],
            s=45,
            marker="X",
            label="End"
        )

        ax.axvline(
            0,
            linestyle="--",
            linewidth=1.5,
            color="red",
            label="Start reference"
        )

        ax.annotate(
            "Start",
            (start["trajectory_x_smooth"], start["trajectory_y_smooth"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8
        )

        ax.annotate(
            "Max Height",
            (max_point["trajectory_x_smooth"], max_point["trajectory_y_smooth"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8
        )

        ax.annotate(
            "End",
            (end["trajectory_x_smooth"], end["trajectory_y_smooth"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8
        )

        self.annotate_phase_points(
            ax=ax,
            plot_df=plot_df,
            x_col="trajectory_x_smooth",
            y_col="trajectory_y_smooth"
        )

        ax.set_xlabel(f"Horizontal Displacement ({unit})")
        ax.set_ylabel(f"Vertical Displacement ({unit})")

        if use_meters:
            ax.set_title("Barbell Trajectory Plot (in meters)")
        else:
            ax.set_title("Barbell Trajectory Plot (in pixels)")

        apply_trajectory_axis_scaling(ax, plot_df)

        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

        fig.tight_layout()

        fig.savefig(plots_folder / "barbell_trajectory_annotated.png", dpi=300)
        fig.savefig(plots_folder / "barbell_trajectory_powerpoint_style.png", dpi=300)

        plt.close(fig)

        # ======================================================
        # Plot 2: Phase-highlighted trajectory
        # ======================================================
        if "phase" not in plot_df.columns:
            return

        phase_df = plot_df.copy()
        phase_df["phase"] = phase_df["phase"].fillna("Unknown")

        fig, ax = plt.subplots(figsize=(6.4, 6.8))

        start_index = 0
        phases = phase_df["phase"].tolist()
        used_labels = set()

        for i in range(1, len(phase_df)):
            current_phase = phases[i]
            previous_phase = phases[i - 1]

            if current_phase != previous_phase:
                segment = phase_df.iloc[start_index:i]
                phase_name = previous_phase

                if len(segment) >= 2:
                    color = phase_colors.get(phase_name, "#444444")
                    label = phase_name if phase_name not in used_labels else None

                    ax.plot(
                        segment["trajectory_x_smooth"],
                        segment["trajectory_y_smooth"],
                        linewidth=2.7,
                        color=color,
                        label=label
                    )

                    used_labels.add(phase_name)

                start_index = i

        segment = phase_df.iloc[start_index:]
        phase_name = phases[-1]

        if len(segment) >= 2:
            color = phase_colors.get(phase_name, "#444444")
            label = phase_name if phase_name not in used_labels else None

            ax.plot(
                segment["trajectory_x_smooth"],
                segment["trajectory_y_smooth"],
                linewidth=2.7,
                color=color,
                label=label
            )

            used_labels.add(phase_name)

        ax.scatter(
            start["trajectory_x_smooth"],
            start["trajectory_y_smooth"],
            s=45,
            color="black",
            label="Start"
        )

        ax.scatter(
            max_point["trajectory_x_smooth"],
            max_point["trajectory_y_smooth"],
            s=60,
            color="black",
            marker="^",
            label="Max height"
        )

        ax.scatter(
            end["trajectory_x_smooth"],
            end["trajectory_y_smooth"],
            s=45,
            color="black",
            marker="X",
            label="End"
        )

        ax.axvline(
            0,
            linestyle="--",
            linewidth=1.5,
            color="red",
            label="Start reference"
        )

        ax.annotate(
            "Max Height",
            (max_point["trajectory_x_smooth"], max_point["trajectory_y_smooth"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8
        )

        ax.set_xlabel(f"Horizontal Displacement ({unit})")
        ax.set_ylabel(f"Vertical Displacement ({unit})")
        ax.set_title("Phase-Highlighted Barbell Trajectory")

        apply_trajectory_axis_scaling(ax, phase_df)

        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

        fig.tight_layout()
        fig.savefig(plots_folder / "barbell_trajectory_phase_highlighted.png", dpi=300)

        plt.close(fig)

    def annotate_phase_points(self, ax, plot_df, x_col, y_col):
        if "phase" not in plot_df.columns:
            return

        phase_label_map = {
            "Deadlift Phase": "Deadlift",
            "Jump Phase": "Jump",
            "Catch Phase": "Catch",
            "Overhead Squat Phase": "OHS",
            "Squat Phase": "Squat",
            "Jerk Phase": "Jerk",
            "Initial Contact": "Contact",
            "Support Phase": "Support",
            "Toe-Off": "Toe-Off",
            "Flight / Swing": "Swing"
        }

        previous_phase = None

        for _, row in plot_df.iterrows():
            phase = row["phase"]

            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if phase != previous_phase:
                short_label = phase_label_map.get(phase, phase)

                ax.annotate(
                    short_label,
                    (row[x_col], row[y_col]),
                    textcoords="offset points",
                    xytext=(6, 6),
                    fontsize=7
                )

                previous_phase = phase

    def save_final_reports(self):
        """
        Generate final text and HTML reports.

        This is intentionally wrapped in try/except so that report generation
        cannot break CSV or plot saving.
        """

        reports_folder = self.session_path / "Reports"
        reports_folder.mkdir(parents=True, exist_ok=True)

        try:
            generate_analysis_reports(
                session_path=self.session_path,
                sport=self.sport,
                exercise=self.exercise,
                input_mode=self.input_mode,
                source_file=self.source_file,
                camera_view=self.camera_view
            )

        except Exception as e:
            error_file = reports_folder / "report_generation_error.txt"

            with open(error_file, "w", encoding="utf-8") as file:
                file.write("Report generation failed.\n\n")
                file.write(f"Error: {e}\n")

    def save_recording_metadata(self):
        metadata = {
            "app_name": "BioMotion Studio",
            "sport": self.sport,
            "exercise": self.exercise,
            "camera_view": self.camera_view,
            "input_mode": self.input_mode,
            "source_file": self.source_file,
            "record_count": self.record_count(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Phase definitions added for weightlifting and sprinting."
        }

        with open(self.session_path / "recording_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)