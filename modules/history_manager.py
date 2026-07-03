from pathlib import Path
import json
import csv


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
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                return row

    except Exception:
        return {}

    return {}


def is_valid_session_folder(folder_path):
    folder_path = Path(folder_path)

    if not folder_path.is_dir():
        return False

    if (folder_path / "CSV").exists():
        return True

    if (folder_path / "Plots").exists():
        return True

    if (folder_path / "Reports").exists():
        return True

    if (folder_path / "recording_metadata.json").exists():
        return True

    if (folder_path / "session_metadata.json").exists():
        return True

    return False


def build_session_record(session_folder, sport="", exercise="", camera_view="N/A"):
    session_folder = Path(session_folder)

    recording_metadata = read_json_file(session_folder / "recording_metadata.json")
    session_metadata = read_json_file(session_folder / "session_metadata.json")
    summary_row = read_first_csv_row(session_folder / "CSV" / "lift_summary.csv")

    def get_value(*keys, default=""):
        for key in keys:
            if key in summary_row and summary_row.get(key) not in [None, "", "nan", "NaN"]:
                return summary_row.get(key)

            if key in recording_metadata and recording_metadata.get(key) not in [None, "", "nan", "NaN"]:
                return recording_metadata.get(key)

            if key in session_metadata and session_metadata.get(key) not in [None, "", "nan", "NaN"]:
                return session_metadata.get(key)

        return default

    final_sport = get_value("sport", default=sport)
    final_exercise = get_value("exercise", default=exercise)
    final_camera_view = get_value("camera_view", default=camera_view)
    input_mode = get_value("input_mode", default="N/A")
    source_file = get_value("source_file", default="")
    record_count = get_value("record_count", default="")
    created_at = get_value("created_at", default="")

    try:
        modified_timestamp = session_folder.stat().st_mtime
    except Exception:
        modified_timestamp = 0

    return {
        "sport": final_sport,
        "exercise": final_exercise,
        "camera_view": final_camera_view,
        "input_mode": input_mode,
        "source_file": source_file,
        "record_count": record_count,
        "created_at": created_at,

        "session": session_folder.name,
        "path": str(session_folder),
        "results_folder": str(session_folder),
        "session_path": str(session_folder),

        "modified_timestamp": modified_timestamp
    }


def get_analysis_sessions():
    """
    Scan results folder and return all analysis sessions.

    Supports both old and new folder structures.

    Old:
        results/Weightlifting/Snatch/timestamp/

    New:
        results/Weightlifting/Snatch/Side_View/timestamp/
    """

    results_root = Path("results")
    sessions = []

    if not results_root.exists():
        return sessions

    for sport_folder in results_root.iterdir():
        if not sport_folder.is_dir():
            continue

        sport = sport_folder.name

        for exercise_folder in sport_folder.iterdir():
            if not exercise_folder.is_dir():
                continue

            exercise = exercise_folder.name

            for child in exercise_folder.iterdir():
                if not child.is_dir():
                    continue

                # Old structure:
                # results/Sport/Exercise/Session/
                if is_valid_session_folder(child):
                    sessions.append(
                        build_session_record(
                            session_folder=child,
                            sport=sport,
                            exercise=exercise,
                            camera_view="N/A"
                        )
                    )
                    continue

                # New structure:
                # results/Sport/Exercise/Camera_View/Session/
                camera_view = child.name

                for session_folder in child.iterdir():
                    if not session_folder.is_dir():
                        continue

                    if not is_valid_session_folder(session_folder):
                        continue

                    sessions.append(
                        build_session_record(
                            session_folder=session_folder,
                            sport=sport,
                            exercise=exercise,
                            camera_view=camera_view
                        )
                    )

    sessions.sort(
        key=lambda x: x.get("modified_timestamp", 0),
        reverse=True
    )

    return sessions