from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def clean_name(name: str) -> str:
    """
    Converts names into safe folder names.
    Example: Clean & Jerk -> Clean_and_Jerk
    """
    return (
        name.replace("&", "and")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def create_session_folder(
    sport: str,
    exercise: str,
    input_mode: str,
    source_file: str = ""
) -> Path:
    """
    Creates a structured result folder for each analysis session.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    sport_folder = clean_name(sport)
    exercise_folder = clean_name(exercise)

    session_path = Path("results") / sport_folder / exercise_folder / timestamp

    csv_path = session_path / "CSV"
    plots_path = session_path / "Plots"
    videos_path = session_path / "Videos"
    reports_path = session_path / "Reports"

    csv_path.mkdir(parents=True, exist_ok=True)
    plots_path.mkdir(parents=True, exist_ok=True)
    videos_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "sport": sport,
        "exercise": exercise,
        "input_mode": input_mode,
        "source_file": source_file,
        "created_at": timestamp,
        "session_path": str(session_path)
    }

    with open(session_path / "session_metadata.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    return session_path


def generate_dummy_outputs(session_path: Path, sport: str, exercise: str):
    """
    Temporary dummy output generator.
    Later, real analysis results will replace this.
    """

    csv_path = session_path / "CSV"
    plots_path = session_path / "Plots"

    if sport == "Weightlifting":
        data = {
            "time_s": [0.00, 0.03, 0.06, 0.09, 0.12, 0.15],
            "hip_angle_deg": [145.2, 148.1, 152.8, 160.3, 168.5, 172.1],
            "knee_angle_deg": [132.4, 136.2, 140.7, 148.9, 155.2, 160.0],
            "elbow_angle_deg": [168.5, 169.2, 170.1, 172.3, 174.0, 175.5],
            "barbell_velocity_mps": [0.00, 0.35, 0.72, 1.15, 1.30, 1.10],
            "phase": ["Setup", "First Pull", "Second Pull", "Catch", "Recovery", "Finish"]
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path / "joint_angles_and_velocity.csv", index=False)

        phase_df = pd.DataFrame({
            "phase": ["Setup", "First Pull", "Second Pull", "Catch", "Recovery"],
            "start_time_s": [0.00, 0.03, 0.06, 0.09, 0.12],
            "end_time_s": [0.03, 0.06, 0.09, 0.12, 0.15]
        })
        phase_df.to_csv(csv_path / "phase_summary.csv", index=False)

        plt.figure(figsize=(8, 5))
        plt.plot(df["time_s"], df["hip_angle_deg"], label="Hip Angle")
        plt.plot(df["time_s"], df["knee_angle_deg"], label="Knee Angle")
        plt.plot(df["time_s"], df["elbow_angle_deg"], label="Elbow Angle")
        plt.xlabel("Time (s)")
        plt.ylabel("Joint Angle (degrees)")
        plt.title(f"{exercise} Joint Angle Analysis")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plots_path / "joint_angles.png", dpi=300)
        plt.close()

        plt.figure(figsize=(8, 5))
        plt.plot(df["time_s"], df["barbell_velocity_mps"], label="Barbell Velocity")
        plt.xlabel("Time (s)")
        plt.ylabel("Velocity (m/s)")
        plt.title(f"{exercise} Barbell Velocity")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plots_path / "barbell_velocity.png", dpi=300)
        plt.close()

    else:
        data = {
            "time_s": [0.00, 0.03, 0.06, 0.09, 0.12, 0.15],
            "hip_angle_deg": [150.2, 155.4, 162.3, 158.8, 152.0, 149.5],
            "knee_angle_deg": [130.1, 120.5, 105.2, 115.7, 135.4, 148.9],
            "ankle_angle_deg": [90.5, 95.1, 100.4, 98.2, 92.8, 88.7],
            "stride_length_m": [0.00, 0.45, 0.95, 1.50, 2.05, 2.55],
            "phase": ["Initial Contact", "Support", "Toe Off", "Flight", "Swing", "Next Contact"]
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path / "sprint_kinematics.csv", index=False)

        plt.figure(figsize=(8, 5))
        plt.plot(df["time_s"], df["hip_angle_deg"], label="Hip Angle")
        plt.plot(df["time_s"], df["knee_angle_deg"], label="Knee Angle")
        plt.plot(df["time_s"], df["ankle_angle_deg"], label="Ankle Angle")
        plt.xlabel("Time (s)")
        plt.ylabel("Joint Angle (degrees)")
        plt.title("Sprinting Joint Angle Analysis")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plots_path / "sprint_joint_angles.png", dpi=300)
        plt.close()

        plt.figure(figsize=(8, 5))
        plt.plot(df["time_s"], df["stride_length_m"], label="Stride Length")
        plt.xlabel("Time (s)")
        plt.ylabel("Stride Length (m)")
        plt.title("Stride Length Estimation")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plots_path / "stride_length.png", dpi=300)
        plt.close()