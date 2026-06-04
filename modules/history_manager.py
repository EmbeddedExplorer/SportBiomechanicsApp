from pathlib import Path


def get_analysis_sessions():
    """
    Scan results folder and return all analysis sessions.
    """

    results_root = Path("results")

    sessions = []

    if not results_root.exists():
        return sessions

    for sport_folder in results_root.iterdir():

        if not sport_folder.is_dir():
            continue

        for exercise_folder in sport_folder.iterdir():

            if not exercise_folder.is_dir():
                continue

            for session_folder in exercise_folder.iterdir():

                if not session_folder.is_dir():
                    continue

                sessions.append({
                    "sport": sport_folder.name,
                    "exercise": exercise_folder.name,
                    "session": session_folder.name,
                    "path": str(session_folder)
                })

    sessions.sort(
        key=lambda x: x["session"],
        reverse=True
    )

    return sessions