from pathlib import Path


def get_analysis_sessions():
    """
    Scan results folder and return all analysis sessions.

    Supports both old and new folder structures.

    Old:
        results/Weightlifting/Snatch/timestamp/

    New V8:
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

                # Old structure: child is a session folder
                if (child / "CSV").exists() or (child / "session_metadata.json").exists():
                    sessions.append({
                        "sport": sport,
                        "exercise": exercise,
                        "camera_view": "N/A",
                        "session": child.name,
                        "path": str(child)
                    })

                # New structure: child is a camera view folder
                else:
                    camera_view = child.name

                    for session_folder in child.iterdir():
                        if not session_folder.is_dir():
                            continue

                        sessions.append({
                            "sport": sport,
                            "exercise": exercise,
                            "camera_view": camera_view,
                            "session": session_folder.name,
                            "path": str(session_folder)
                        })

    sessions.sort(
        key=lambda x: x["session"],
        reverse=True
    )

    return sessions