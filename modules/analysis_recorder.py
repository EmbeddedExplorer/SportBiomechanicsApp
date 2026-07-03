from importlib.metadata import metadata
from pathlib import Path
from datetime import datetime
import time
import json

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from modules.phase_definitions import EXCLUDED_PLOT_PHASES


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
        """
        Plot angle/velocity groups with display-only smoothing.

        Important:
        - CSV data is NOT changed.
        - Only the plotted curves are smoothed.
        - This improves noisy MediaPipe/velocity plots without affecting raw exported data.
        """

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
            """
            Smooth only for plotting.

            Velocity signals are usually noisier because they are calculated from
            frame-to-frame displacement, so we use a slightly stronger smoothing
            window for velocity columns.
            """

            series = pd.to_numeric(series, errors="coerce")

            valid_count = series.notna().sum()

            if valid_count < 5:
                return series

            column_name_lower = column_name.lower()

            if "velocity" in column_name_lower:
                window = 11
            else:
                window = 7

            # First pass: rolling median reduces sudden MediaPipe/tracking spikes.
            median_series = series.rolling(
                window=window,
                center=True,
                min_periods=1
            ).median()

            # Second pass: rolling mean gives smoother curve shape.
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

        # Keep the legend readable and away from the crowded phase labels.
        ax.legend(
            loc="best",
            fontsize=8,
            framealpha=0.85
        )

        fig.tight_layout()
        fig.savefig(plots_folder / filename, dpi=300)
        plt.close(fig)
    def add_phase_shading(self, ax, df):
        """
        Add phase shading with cleaner, shorter, staggered labels.

        Fixes:
        - Overlapping phase labels at the top of plots
        - Long labels such as "Overhead Squat Phase"
        - Crowded labels in angle and velocity plots
        """

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

        # Use x-axis/data coordinates and y-axis fractional coordinates.
        # This keeps labels at the top without changing y-axis limits.
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

            # Skip labels for very short segments to avoid clutter.
            # The shading is still shown.
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

        # ------------------------------------------------------
        # Prefer meter-based displacement if available
        # ------------------------------------------------------
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

        # ------------------------------------------------------
        # Remove phases that should not appear in trajectory plot
        # only if this still leaves enough valid points.
        # ------------------------------------------------------
        if "phase" in plot_df.columns:
            filtered_df = plot_df[~plot_df["phase"].isin(EXCLUDED_PLOT_PHASES)].copy()

            if len(filtered_df) >= 2:
                plot_df = filtered_df

        # ------------------------------------------------------
        # Smooth trajectory for cleaner research-style output
        # ------------------------------------------------------
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

        # ------------------------------------------------------
        # Axis scaling helper
        # ------------------------------------------------------
        def apply_trajectory_axis_scaling(ax, data):
            """
            Make trajectory plots less vertically stretched by expanding
            the x-axis range while keeping vertical displacement readable.
            """

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

            x_range = max(x_max - x_min, 1e-6)
            y_range = max(y_max - y_min, 1e-6)

            # Include the start reference line at x = 0.
            visible_x_min = min(x_min, 0.0)
            visible_x_max = max(x_max, 0.0)

            visible_x_range = max(visible_x_max - visible_x_min, 1e-6)

            # Main correction:
            # Expand x-axis relative to y-axis so the trajectory does not
            # look like an overly tall/narrow curve.
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

        # ------------------------------------------------------
        # Important trajectory points
        # ------------------------------------------------------
        start = plot_df.iloc[0]
        end = plot_df.iloc[-1]

        max_idx = plot_df["trajectory_y_smooth"].idxmax()
        max_point = plot_df.loc[max_idx]

        # ------------------------------------------------------
        # Phase colors
        # ------------------------------------------------------
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

        # Last phase segment
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

        # ------------------------------------------------------
        # Remove phases that should not appear in trajectory plot
        # only if this still leaves enough valid points.
        # ------------------------------------------------------
        if "phase" in plot_df.columns:
            filtered_df = plot_df[~plot_df["phase"].isin(EXCLUDED_PLOT_PHASES)].copy()

            if len(filtered_df) >= 2:
                plot_df = filtered_df

        # ------------------------------------------------------
        # Smooth trajectory for cleaner research-style output
        # ------------------------------------------------------
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

        # ------------------------------------------------------
        # Important points
        # ------------------------------------------------------
        start = plot_df.iloc[0]
        end = plot_df.iloc[-1]

        max_idx = plot_df["trajectory_y_smooth"].idxmax()
        max_point = plot_df.loc[max_idx]

        # ------------------------------------------------------
        # Phase color map
        # ------------------------------------------------------
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
        # Plot 1: Annotated research-style trajectory
        # ======================================================
        fig, ax = plt.subplots(figsize=(4.2, 7.2))

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

        fig, ax = plt.subplots(figsize=(4.6, 7.2))

        previous_phase = None
        start_index = 0
        phases = phase_df["phase"].tolist()

        used_labels = set()

        for i in range(1, len(phase_df)):
            current_phase = phases[i]
            previous = phases[i - 1]

            if current_phase != previous:
                segment = phase_df.iloc[start_index:i]
                phase_name = previous

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

        # Last phase segment
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
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

        fig.tight_layout()
        fig.savefig(plots_folder / "barbell_trajectory_phase_highlighted.png", dpi=300)

        plt.close(fig)

    def annotate_phase_points(self, ax, plot_df, x_col, y_col):
        if "phase" not in plot_df.columns:
            return

        previous_phase = None

        for _, row in plot_df.iterrows():
            phase = row["phase"]

            if phase in EXCLUDED_PLOT_PHASES:
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
            "note": "Phase definitions added for weightlifting and sprinting."
        }

        with open(self.session_path / "recording_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)