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

        fig, ax = plt.subplots(figsize=(9, 5))

        for col in valid_columns:
            ax.plot(df["time_s"], pd.to_numeric(df[col], errors="coerce"), label=col)

        if shade_phases:
            self.add_phase_shading(ax, df)

        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(plots_folder / filename, dpi=300)
        plt.close(fig)

    def add_phase_shading(self, ax, df):
        if "phase" not in df.columns or df.empty:
            return

        phase_segments = []
        current_phase = None
        start_time = None
        last_time = None

        for _, row in df.iterrows():
            phase = row["phase"]
            time_s = row["time_s"]

            if phase != current_phase:
                if current_phase is not None:
                    phase_segments.append((current_phase, start_time, last_time))

                current_phase = phase
                start_time = time_s

            last_time = time_s

        if current_phase is not None:
            phase_segments.append((current_phase, start_time, last_time))

        y_min, y_max = ax.get_ylim()

        for phase, start, end in phase_segments:
            if phase in ["Not Detected", "N/A"]:
                continue

            ax.axvspan(start, end, alpha=0.08)

            midpoint = (start + end) / 2

            ax.text(
                midpoint,
                y_max,
                phase,
                rotation=90,
                verticalalignment="top",
                horizontalalignment="center",
                fontsize=7
            )

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

        if plot_df.empty:
            return

        unit = "m" if use_meters else "px"

        fig, ax = plt.subplots(figsize=(3.6, 7.2))

        ax.plot(
            plot_df[x_col],
            plot_df[y_col],
            linewidth=2,
            label="Barbell path"
        )

        start = plot_df.iloc[0]
        end = plot_df.iloc[-1]

        max_idx = plot_df[y_col].idxmax()
        max_point = plot_df.loc[max_idx]

        ax.scatter(start[x_col], start[y_col], s=35, label="Start")
        ax.scatter(max_point[x_col], max_point[y_col], s=35, label="Max height")
        ax.scatter(end[x_col], end[y_col], s=35, label="End")

        ax.axvline(
            0,
            linestyle="--",
            linewidth=1.5,
            color="red",
            label="Start reference"
        )

        ax.annotate(
            "Start",
            (start[x_col], start[y_col]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8
        )

        ax.annotate(
            "Max Height",
            (max_point[x_col], max_point[y_col]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8
        )

        ax.annotate(
            "End",
            (end[x_col], end[y_col]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8
        )

        self.annotate_phase_points(ax, plot_df, x_col, y_col)

        ax.set_xlabel(f"Horizontal Displacement ({unit})")
        ax.set_ylabel(f"Vertical Displacement ({unit})")

        if use_meters:
            ax.set_title("Barbell Trajectory Plot (in meters)")
        else:
            ax.set_title("Barbell Trajectory Plot (in pixels)")

        ax.grid(True)
        ax.legend(fontsize=7)
        fig.tight_layout()

        fig.savefig(plots_folder / "barbell_trajectory_annotated.png", dpi=300)
        fig.savefig(plots_folder / "barbell_trajectory_powerpoint_style.png", dpi=300)

        plt.close(fig)

    def annotate_phase_points(self, ax, plot_df, x_col, y_col):
        if "phase" not in plot_df.columns:
            return

        previous_phase = None

        for _, row in plot_df.iterrows():
            phase = row["phase"]

            if phase in ["Not Detected", "N/A"]:
                continue

            if phase != previous_phase:
                ax.annotate(
                    phase,
                    (row[x_col], row[y_col]),
                    textcoords="offset points",
                    xytext=(6, 6),
                    fontsize=7
                )

                previous_phase = phase

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
            "note": "V9.1 DLib/OpenCV ROI-based barbell tracking. Trajectory is saved in meters when RealSense depth is available, otherwise in pixels."
        }

        with open(self.session_path / "recording_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)