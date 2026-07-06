from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from modules.phase_definitions import EXCLUDED_PLOT_PHASES


PHASE_COLORS = {
    "Initial Contact": "#1f77b4",
    "Support Phase": "#ff7f0e",
    "Toe-Off": "#2ca02c",
    "Flight / Swing": "#9467bd",
    "Unknown": "#444444",
}


LOWER_LIMB_PAIRS = [
    {
        "pair_name": "Left Hip vs Right Hip",
        "short_name": "Hip L/R",
        "left_column": "left_hip_angle_deg",
        "right_column": "right_hip_angle_deg",
        "x_label": "Left Hip Angle (deg)",
        "y_label": "Right Hip Angle (deg)",
    },
    {
        "pair_name": "Left Knee vs Right Knee",
        "short_name": "Knee L/R",
        "left_column": "left_knee_angle_deg",
        "right_column": "right_knee_angle_deg",
        "x_label": "Left Knee Angle (deg)",
        "y_label": "Right Knee Angle (deg)",
    },
    {
        "pair_name": "Left Ankle vs Right Ankle",
        "short_name": "Ankle L/R",
        "left_column": "left_ankle_angle_deg",
        "right_column": "right_ankle_angle_deg",
        "x_label": "Left Ankle Angle (deg)",
        "y_label": "Right Ankle Angle (deg)",
    },
]


CONTRALATERAL_PAIRS = [
    {
        "pair_name": "Left Elbow vs Right Knee",
        "short_name": "Left elbow / Right knee",
        "left_column": "left_elbow_angle_deg",
        "right_column": "right_knee_angle_deg",
        "x_label": "Left Elbow Angle (deg)",
        "y_label": "Right Knee Angle (deg)",
    },
    {
        "pair_name": "Right Elbow vs Left Knee",
        "short_name": "Right elbow / Left knee",
        "left_column": "right_elbow_angle_deg",
        "right_column": "left_knee_angle_deg",
        "x_label": "Right Elbow Angle (deg)",
        "y_label": "Left Knee Angle (deg)",
    },
    {
        "pair_name": "Left Shoulder vs Right Hip",
        "short_name": "Left shoulder / Right hip",
        "left_column": "left_shoulder_angle_deg",
        "right_column": "right_hip_angle_deg",
        "x_label": "Left Shoulder Angle (deg)",
        "y_label": "Right Hip Angle (deg)",
    },
    {
        "pair_name": "Right Shoulder vs Left Hip",
        "short_name": "Right shoulder / Left hip",
        "left_column": "right_shoulder_angle_deg",
        "right_column": "left_hip_angle_deg",
        "x_label": "Right Shoulder Angle (deg)",
        "y_label": "Left Hip Angle (deg)",
    },
]


def numeric_series(df, column_name):
    if column_name not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column_name], errors="coerce")


def smooth_signal(series, window=7):
    series = pd.to_numeric(series, errors="coerce")

    if series.notna().sum() < 5:
        return series

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


def clean_phase_value(phase):
    if pd.isna(phase):
        return "Unknown"

    phase = str(phase)

    if phase in EXCLUDED_PLOT_PHASES:
        return "Unknown"

    return phase


def prepare_coordination_dataframe(df):
    if df.empty or "time_s" not in df.columns:
        return pd.DataFrame()

    required_columns = [
        "time_s",
        "phase",
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
    ]

    existing_columns = [column for column in required_columns if column in df.columns]

    if "time_s" not in existing_columns:
        return pd.DataFrame()

    work_df = df[existing_columns].copy()
    work_df["time_s"] = pd.to_numeric(work_df["time_s"], errors="coerce")

    if "phase" in work_df.columns:
        work_df["phase"] = work_df["phase"].apply(clean_phase_value)
    else:
        work_df["phase"] = "Unknown"

    for column in existing_columns:
        if column in ["time_s", "phase"]:
            continue

        work_df[column] = smooth_signal(pd.to_numeric(work_df[column], errors="coerce"))

    work_df = work_df.dropna(subset=["time_s"])
    work_df = work_df.sort_values("time_s")

    return work_df


def safe_corr(x_series, y_series):
    paired = pd.DataFrame({
        "x": pd.to_numeric(x_series, errors="coerce"),
        "y": pd.to_numeric(y_series, errors="coerce")
    }).dropna()

    if len(paired) < 5:
        return None

    if paired["x"].std() == 0 or paired["y"].std() == 0:
        return None

    return round(float(paired["x"].corr(paired["y"])), 4)


def estimate_time_lag_seconds(time_series, x_series, y_series):
    """
    Estimate the simple timing lag between two joint-angle signals.

    Positive value:
        y signal appears later than x signal.

    Negative value:
        y signal appears earlier than x signal.

    This is a simple cross-correlation estimate for review purposes.
    It should be interpreted together with the phase plots.
    """

    paired = pd.DataFrame({
        "time_s": pd.to_numeric(time_series, errors="coerce"),
        "x": pd.to_numeric(x_series, errors="coerce"),
        "y": pd.to_numeric(y_series, errors="coerce")
    }).dropna()

    if len(paired) < 8:
        return None

    paired = paired.sort_values("time_s")

    time_values = paired["time_s"].to_numpy(dtype=float)
    dt_values = np.diff(time_values)
    dt_values = dt_values[dt_values > 0]

    if len(dt_values) == 0:
        return None

    sample_dt = float(np.median(dt_values))

    x = paired["x"].to_numpy(dtype=float)
    y = paired["y"].to_numpy(dtype=float)

    x = x - np.nanmean(x)
    y = y - np.nanmean(y)

    x_std = np.nanstd(x)
    y_std = np.nanstd(y)

    if x_std == 0 or y_std == 0:
        return None

    x = x / x_std
    y = y / y_std

    correlation = np.correlate(y, x, mode="full")
    lags = np.arange(-len(x) + 1, len(x))

    best_lag_samples = int(lags[int(np.argmax(correlation))])
    lag_seconds = best_lag_samples * sample_dt

    return round(float(lag_seconds), 4)


def calculate_pair_summary(df, pair_info, phase_name="Overall"):
    x_column = pair_info["left_column"]
    y_column = pair_info["right_column"]

    if x_column not in df.columns or y_column not in df.columns:
        return None

    paired = df[["time_s", x_column, y_column]].copy()
    paired[x_column] = pd.to_numeric(paired[x_column], errors="coerce")
    paired[y_column] = pd.to_numeric(paired[y_column], errors="coerce")
    paired = paired.dropna(subset=["time_s", x_column, y_column])

    if len(paired) < 3:
        return None

    difference = paired[x_column] - paired[y_column]

    mean_abs_difference = float(difference.abs().mean())
    rms_difference = float(np.sqrt(np.mean(np.square(difference.to_numpy(dtype=float)))))

    return {
        "phase": phase_name,
        "pair_name": pair_info["pair_name"],
        "short_name": pair_info["short_name"],
        "x_signal": x_column,
        "y_signal": y_column,
        "sample_count": int(len(paired)),
        "mean_abs_difference_deg": round(mean_abs_difference, 4),
        "rms_difference_deg": round(rms_difference, 4),
        "correlation": safe_corr(paired[x_column], paired[y_column]),
        "estimated_time_lag_s": estimate_time_lag_seconds(
            paired["time_s"],
            paired[x_column],
            paired[y_column]
        )
    }


def build_interlimb_summary(df):
    work_df = prepare_coordination_dataframe(df)

    if work_df.empty:
        return pd.DataFrame()

    rows = []
    all_pairs = LOWER_LIMB_PAIRS + CONTRALATERAL_PAIRS

    for pair_info in all_pairs:
        overall_row = calculate_pair_summary(
            df=work_df,
            pair_info=pair_info,
            phase_name="Overall"
        )

        if overall_row is not None:
            rows.append(overall_row)

    if "phase" in work_df.columns:
        phase_order = []

        for phase in work_df["phase"].dropna().tolist():
            phase = str(phase)

            if phase in EXCLUDED_PLOT_PHASES:
                continue

            if phase not in phase_order:
                phase_order.append(phase)

        for phase_name in phase_order:
            phase_df = work_df[work_df["phase"] == phase_name].copy()

            if len(phase_df) < 3:
                continue

            for pair_info in all_pairs:
                phase_row = calculate_pair_summary(
                    df=phase_df,
                    pair_info=pair_info,
                    phase_name=phase_name
                )

                if phase_row is not None:
                    rows.append(phase_row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def add_phase_shading(ax, df):
    if "phase" not in df.columns or "time_s" not in df.columns:
        return

    phase_segments = []
    current_phase = None
    start_time = None
    last_time = None

    for _, row in df.iterrows():
        phase = row.get("phase", "Unknown")
        time_s = row.get("time_s", None)

        if pd.isna(time_s):
            continue

        phase = str(phase)

        if phase in EXCLUDED_PLOT_PHASES:
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

    phase_label_map = {
        "Initial Contact": "Contact",
        "Support Phase": "Support",
        "Toe-Off": "Toe-Off",
        "Flight / Swing": "Swing",
        "Unknown": "Unknown"
    }

    for phase, start, end in phase_segments:
        if start is None or end is None:
            continue

        duration = end - start

        if duration <= 0:
            continue

        color = PHASE_COLORS.get(phase, "#808080")

        ax.axvspan(
            start,
            end,
            alpha=0.08,
            color=color
        )

        if duration < 0.35:
            continue

        midpoint = (start + end) / 2.0
        short_label = phase_label_map.get(phase, phase)
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


def save_lower_limb_time_series_plot(work_df, plots_folder, exercise, camera_view):
    required = [
        "time_s",
        "left_hip_angle_deg",
        "right_hip_angle_deg",
        "left_knee_angle_deg",
        "right_knee_angle_deg",
        "left_ankle_angle_deg",
        "right_ankle_angle_deg",
    ]

    if any(column not in work_df.columns for column in required):
        return

    plot_df = work_df[required + ["phase"]].copy()
    plot_df = plot_df.dropna(subset=required)

    if len(plot_df) < 5:
        return

    fig, ax = plt.subplots(figsize=(11.0, 5.8))

    ax.plot(plot_df["time_s"], plot_df["left_hip_angle_deg"], linewidth=1.6, label="Left Hip")
    ax.plot(plot_df["time_s"], plot_df["right_hip_angle_deg"], linewidth=1.6, linestyle="--", label="Right Hip")

    ax.plot(plot_df["time_s"], plot_df["left_knee_angle_deg"], linewidth=1.6, label="Left Knee")
    ax.plot(plot_df["time_s"], plot_df["right_knee_angle_deg"], linewidth=1.6, linestyle="--", label="Right Knee")

    ax.plot(plot_df["time_s"], plot_df["left_ankle_angle_deg"], linewidth=1.4, label="Left Ankle")
    ax.plot(plot_df["time_s"], plot_df["right_ankle_angle_deg"], linewidth=1.4, linestyle="--", label="Right Ankle")

    add_phase_shading(ax, plot_df)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Joint Angle (degrees)")
    ax.set_title(f"{exercise} Lower-Limb Interlimb Coordination ({camera_view})")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)

    fig.tight_layout(rect=[0.0, 0.0, 0.82, 1.0])
    fig.savefig(
        Path(plots_folder) / "interlimb_lower_limb_coordination_time_series.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)


def save_phase_relationship_plot(
    work_df,
    pair_info,
    plots_folder,
    filename,
    title,
    show_identity_line=True
):
    x_col = pair_info["left_column"]
    y_col = pair_info["right_column"]

    if x_col not in work_df.columns or y_col not in work_df.columns:
        return

    required = ["time_s", "phase", x_col, y_col]
    plot_df = work_df[required].copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])

    if len(plot_df) < 5:
        return

    fig, ax = plt.subplots(figsize=(7.8, 6.8))

    used_labels = set()

    for phase_name, phase_df in plot_df.groupby("phase"):
        if phase_name in EXCLUDED_PLOT_PHASES:
            continue

        label = phase_name if phase_name not in used_labels else None
        color = PHASE_COLORS.get(phase_name, "#444444")

        ax.scatter(
            phase_df[x_col],
            phase_df[y_col],
            s=28,
            alpha=0.72,
            color=color,
            label=label
        )

        used_labels.add(phase_name)

    if show_identity_line:
        x_values = pd.to_numeric(plot_df[x_col], errors="coerce").dropna()
        y_values = pd.to_numeric(plot_df[y_col], errors="coerce").dropna()

        if not x_values.empty and not y_values.empty:
            lower = float(min(x_values.min(), y_values.min()))
            upper = float(max(x_values.max(), y_values.max()))

            ax.plot(
                [lower, upper],
                [lower, upper],
                linestyle="--",
                linewidth=1.2,
                color="#666666",
                label="Symmetry reference"
            )

    ax.set_xlabel(pair_info["x_label"])
    ax.set_ylabel(pair_info["y_label"])
    ax.set_title(title)
    ax.grid(True, alpha=0.30)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)

    fig.tight_layout(rect=[0.0, 0.0, 0.78, 1.0])
    fig.savefig(
        Path(plots_folder) / filename,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)


def save_contralateral_relationship_plot(work_df, plots_folder, exercise, camera_view):
    needed_columns = [
        "phase",
        "left_elbow_angle_deg",
        "right_knee_angle_deg",
        "right_elbow_angle_deg",
        "left_knee_angle_deg"
    ]

    if any(column not in work_df.columns for column in needed_columns):
        return

    plot_df = work_df[needed_columns].copy()

    for column in needed_columns:
        if column == "phase":
            continue

        plot_df[column] = pd.to_numeric(plot_df[column], errors="coerce")

    plot_df = plot_df.dropna(
        subset=[
            "left_elbow_angle_deg",
            "right_knee_angle_deg",
            "right_elbow_angle_deg",
            "left_knee_angle_deg"
        ]
    )

    if len(plot_df) < 5:
        return

    fig, ax = plt.subplots(figsize=(8.4, 6.8))

    ax.scatter(
        plot_df["left_elbow_angle_deg"],
        plot_df["right_knee_angle_deg"],
        s=28,
        alpha=0.70,
        label="Left Elbow vs Right Knee"
    )

    ax.scatter(
        plot_df["right_elbow_angle_deg"],
        plot_df["left_knee_angle_deg"],
        s=28,
        alpha=0.70,
        marker="x",
        label="Right Elbow vs Left Knee"
    )

    ax.set_xlabel("Elbow Angle (degrees)")
    ax.set_ylabel("Opposite Knee Angle (degrees)")
    ax.set_title(f"{exercise} Contralateral Arm-Leg Coordination ({camera_view})")
    ax.grid(True, alpha=0.30)
    ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(
        Path(plots_folder) / "interlimb_contralateral_arm_leg_coordination.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)


def save_phase_summary_plot(summary_df, plots_folder, exercise, camera_view):
    if summary_df.empty:
        return

    lower_limb_names = [pair["pair_name"] for pair in LOWER_LIMB_PAIRS]

    plot_df = summary_df[
        (summary_df["pair_name"].isin(lower_limb_names))
        & (summary_df["phase"] != "Overall")
    ].copy()

    if plot_df.empty:
        return

    plot_df = plot_df.dropna(subset=["mean_abs_difference_deg"])

    if plot_df.empty:
        return

    pivot_df = plot_df.pivot_table(
        index="phase",
        columns="short_name",
        values="mean_abs_difference_deg",
        aggfunc="mean"
    )

    if pivot_df.empty:
        return

    phase_order = [
        phase for phase in [
            "Initial Contact",
            "Support Phase",
            "Toe-Off",
            "Flight / Swing",
            "Unknown"
        ]
        if phase in pivot_df.index
    ]

    remaining = [phase for phase in pivot_df.index if phase not in phase_order]
    phase_order.extend(remaining)

    pivot_df = pivot_df.loc[phase_order]

    fig, ax = plt.subplots(figsize=(10.8, 5.8))

    pivot_df.plot(
        kind="bar",
        ax=ax,
        width=0.78
    )

    ax.set_xlabel("Sprint Phase")
    ax.set_ylabel("Mean Absolute Left-Right Difference (deg)")
    ax.set_title(f"{exercise} Phase-wise Lower-Limb Coordination Difference ({camera_view})")
    ax.grid(True, axis="y", alpha=0.30)
    ax.legend(title="Joint Pair", fontsize=8, title_fontsize=8)
    ax.tick_params(axis="x", rotation=25)

    fig.tight_layout()
    fig.savefig(
        Path(plots_folder) / "interlimb_coordination_phase_summary.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)


def save_interlimb_coordination_outputs(
    df,
    csv_folder,
    plots_folder,
    exercise="Sprinting",
    camera_view="Side View"
):
    """
    Save sprinting interlimb coordination outputs.

    Creates:
        CSV/interlimb_coordination_summary.csv

        Plots/interlimb_lower_limb_coordination_time_series.png
        Plots/interlimb_knee_phase_relationship.png
        Plots/interlimb_hip_phase_relationship.png
        Plots/interlimb_contralateral_arm_leg_coordination.png
        Plots/interlimb_coordination_phase_summary.png
    """

    csv_folder = Path(csv_folder)
    plots_folder = Path(plots_folder)

    csv_folder.mkdir(parents=True, exist_ok=True)
    plots_folder.mkdir(parents=True, exist_ok=True)

    work_df = prepare_coordination_dataframe(df)

    if work_df.empty or len(work_df) < 5:
        return {
            "created": False,
            "reason": "Not enough sprinting data for interlimb coordination analysis."
        }

    summary_df = build_interlimb_summary(work_df)

    if not summary_df.empty:
        summary_df.to_csv(
            csv_folder / "interlimb_coordination_summary.csv",
            index=False
        )

    save_lower_limb_time_series_plot(
        work_df=work_df,
        plots_folder=plots_folder,
        exercise=exercise,
        camera_view=camera_view
    )

    knee_pair = LOWER_LIMB_PAIRS[1]
    save_phase_relationship_plot(
        work_df=work_df,
        pair_info=knee_pair,
        plots_folder=plots_folder,
        filename="interlimb_knee_phase_relationship.png",
        title=f"{exercise} Left-Right Knee Phase Relationship ({camera_view})",
        show_identity_line=True
    )

    hip_pair = LOWER_LIMB_PAIRS[0]
    save_phase_relationship_plot(
        work_df=work_df,
        pair_info=hip_pair,
        plots_folder=plots_folder,
        filename="interlimb_hip_phase_relationship.png",
        title=f"{exercise} Left-Right Hip Phase Relationship ({camera_view})",
        show_identity_line=True
    )

    save_contralateral_relationship_plot(
        work_df=work_df,
        plots_folder=plots_folder,
        exercise=exercise,
        camera_view=camera_view
    )

    save_phase_summary_plot(
        summary_df=summary_df,
        plots_folder=plots_folder,
        exercise=exercise,
        camera_view=camera_view
    )

    return {
        "created": True,
        "summary_rows": int(len(summary_df))
    }
