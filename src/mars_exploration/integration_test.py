#!/usr/bin/env python
import os
import json
from pathlib import Path

from mars_exploration.crews.integration_crew.integration_crew import IntegrationCrew

# Paths (adjust if needed)
INTERMEDIATE_DIR = "src/mars_exploration/data_test_case_2/intermediate"

MISSION_SUMMARY_JSON = os.path.join(INTERMEDIATE_DIR, "mission_crew", "mission_crew_output.json")
ROVER_PLAN_JSON = os.path.join(INTERMEDIATE_DIR, "rover_crew", "rover_crew_output.json")
DRONE_PLAN_JSON = os.path.join(INTERMEDIATE_DIR, "drone_crew", "drone_crew_output.json")

OUT_DIR = os.path.join(INTERMEDIATE_DIR, "integration_crew")
OUT_MD = os.path.join(OUT_DIR, "final_mission_plan.md")

def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def kickoff_integration_only():
    os.makedirs(OUT_DIR, exist_ok=True)

    mission_summary = load_json(MISSION_SUMMARY_JSON)
    rover_plan = load_json(ROVER_PLAN_JSON)
    drone_plan = load_json(DRONE_PLAN_JSON)

    # Pass as strings (safe for templating inside CrewAI tasks)
    result = (
        IntegrationCrew(output_dir=OUT_DIR)
        .crew()
        .kickoff(inputs={
            "mission_summary": json.dumps(mission_summary),
            "rover_plan": json.dumps(rover_plan),
            "drone_plan": json.dumps(drone_plan),
        })
    )

    # result.raw is usually the final text (Markdown)
    Path(OUT_MD).write_text(result.raw or "", encoding="utf-8")
    print(f"✅ Integration-only plan saved to: {OUT_MD}")

    # If you used output_pydantic for integration, you can also inspect:
    # print(result.pydantic)

if __name__ == "__main__":
    kickoff_integration_only()
