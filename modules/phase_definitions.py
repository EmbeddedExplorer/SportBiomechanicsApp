SETUP_PHASE = "Setup"

SNATCH_PHASES = [
    "Deadlift Phase",
    "Jump Phase",
    "Catch Phase",
    "Overhead Squat Phase"
]

CLEAN_JERK_PHASES = [
    "Deadlift Phase",
    "Jump Phase",
    "Catch Phase",
    "Squat Phase",
    "Jerk Phase"
]

SPRINTING_PHASES = [
    "Initial Contact",
    "Support Phase",
    "Toe-Off",
    "Flight / Swing"
]

WEIGHTLIFTING_PHASES = SNATCH_PHASES + CLEAN_JERK_PHASES

PLOT_PHASES = (
    WEIGHTLIFTING_PHASES
    + SPRINTING_PHASES
)

EXCLUDED_PLOT_PHASES = [
    "Setup",
    "Not Detected",
    "N/A"
]

TRAJECTORY_END_PHASES = [
    "Overhead Squat Phase",
    "Jerk Phase"
]