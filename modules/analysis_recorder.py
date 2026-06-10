from pathlib import Path
from datetime import datetime
import time
import json

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class AnalysisRecorder:
    def __init__(
        self,
        session_path: Path,
        sport: str,
        exercise: str,
        input_mode: str,
        source_file: str = ""
    ):
        self.session_path = Path(session_path)
        self.sport = sport
        self.exercise = exercise
        self.input_mode = input_mode
        self.source_file = source_file

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
            "center_depth_m": metrics.get("Center Depth (m)")
        }

        self.records.append(record)

    def record_count(self):
        return len(self.records)

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
        self.save_summary_csv(df, csv_folder)
        self.save_plots(df, plots_folder)
        self.save_recording_metadata()

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
            "center_depth_m"
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

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "left_hip_angle_deg",
                "right_hip_angle_deg",
                "left_knee_angle_deg",
                "right_knee_angle_deg"
            ],
            title=f"{self.exercise} Hip and Knee Angles",
            ylabel="Angle (degrees)",
            filename="hip_knee_angles.png"
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
            title=f"{self.exercise} Shoulder and Elbow Angles",
            ylabel="Angle (degrees)",
            filename="upper_limb_angles.png"
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "trunk_lean_angle_deg"
            ],
            title=f"{self.exercise} Trunk Lean Angle",
            ylabel="Angle (degrees)",
            filename="trunk_lean_angle.png"
        )

        self.plot_group(
            df=df,
            plots_folder=plots_folder,
            columns=[
                "athlete_depth_m",
                "center_depth_m"
            ],
            title=f"{self.exercise} Depth Measurements",
            ylabel="Depth (m)",
            filename="depth_measurements.png"
        )

    def plot_group(self, df, plots_folder, columns, title, ylabel, filename):
        valid_columns = []

        for col in columns:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")

                if series.notna().sum() > 0:
                    valid_columns.append(col)

        if not valid_columns:
            return

        plt.figure(figsize=(9, 5))

        for col in valid_columns:
            plt.plot(df["time_s"], pd.to_numeric(df[col], errors="coerce"), label=col)

        plt.xlabel("Time (s)")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_folder / filename, dpi=300)
        plt.close()

    def save_recording_metadata(self):
        metadata = {
            "app_name": "BioMotion Studio",
            "sport": self.sport,
            "exercise": self.exercise,
            "input_mode": self.input_mode,
            "source_file": self.source_file,
            "record_count": self.record_count(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "V7 2D pose-based analysis recording. Depth values are saved when available."
        }

        with open(self.session_path / "recording_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)