#!/usr/bin/env python
from pathlib import Path
from random import randint
from typing import Any, Dict, List

from pydantic import BaseModel
import networkx as nx

from crewai.flow import Flow, listen, start, and_
import os
from mars_exploration.crews.mission_crew.mission_crew import MissionCrew
from mars_exploration.crews.rover_crew.rover_crew import RoverCrew
from mars_exploration.crews.drone_crew.drone_crew import DroneCrew
from mars_exploration.crews.integration_crew.integration_crew import IntegrationCrew
import json

from mars_exploration.models.mission_spec import MissionSpec

#Constants 
INPUT_DIR="src/mars_exploration/data/input"
INTERMEDIATE_DIR="src/mars_exploration/data/intermediate"
OUTPUT_DIR="src/mars_exploration/data/output"
INPUT_REPORT=os.path.join(INPUT_DIR, "mission_report.md")
MISSION_SUMMARY_JSON= os.path.join(INTERMEDIATE_DIR, "mission_summary.json")
MARS_MAP_PATH = os.path.join(INPUT_DIR, "mars_terrain.graphml")
ROVERS_FILE = os.path.join(INPUT_DIR, "rovers.json")
DRONES_FILE = os.path.join(INPUT_DIR, "drones.json")
ROVER_PLAN_JSON = os.path.join(INTERMEDIATE_DIR, "rovers_plan_summary.json")
class MarsMissionState(BaseModel):
    mars_map_path: str = None
    input_report: str = None
    mission_summary: MissionSpec = None
    rovers: List[Dict[str, Any]] = None
    drones : List[Dict[str, Any]] = None
    rover_plan: str = ""
    drone_plan: str = ""
    final_plan: str = ""



class MarsMissionFlow(Flow[MarsMissionState]):
    @start()
    def prepare_mission(self):
        print("Begin flow")
        self.state.input_report = Path(INPUT_REPORT).read_text(encoding="utf-8")
        self.state.mars_map_path = MARS_MAP_PATH
        self.state.rovers = json.loads(Path(ROVERS_FILE).read_text(encoding="utf-8"))
        self.state.drones = json.loads(Path(DRONES_FILE).read_text(encoding="utf-8"))



        
    @listen(prepare_mission)
    def process_mission(self):
        print("Processing mission report")

        result = (
            MissionCrew()
            .crew()
            .kickoff(inputs={
            "mission_report": self.state.input_report
        })
        )

        mission_spec = result.pydantic
        with open(MISSION_SUMMARY_JSON, "w", encoding="utf-8") as f:
            f.write(mission_spec.model_dump_json(indent=4))

        self.state.mission_summary = mission_spec

        print(self.state.drones)
        print(self.state.rovers)

    @listen(process_mission)
    def plan_rover_operations(self):
        print(f"Planning rover operations {self.state.mission_summary}")
        print(self.state.rovers)
        result = (
            RoverCrew(mapp=self.state.mars_map_path, rovers=self.state.rovers)
            .crew()
            .kickoff(inputs={
                "mission_summary": self.state.mission_summary.model_dump_json()          
            })
        )
        print(f"Finish rover 1")
        print(result)
        self.state.rover_plan = result.pydantic
        print(f"Finish rover 1.5")

        with open(ROVER_PLAN_JSON, "w", encoding="utf-8") as f:
            f.write(self.state.rover_plan.model_dump_json(indent=4))
        print(self.state.rover_plan)
        print(f"Finish rover 2")


    # @listen(process_mission)
    # def plan_drone_surveys(self):
    #     print("Planning drone surveys")

    #     result = (
    #         DroneCrew()
    #         .crew()
    #         .kickoff(inputs={
    #             "mission_summary": self.state.mission_summary
    #         })
    #     )

    #     self.state.drone_plan = result.raw

    # @listen(and_(plan_rover_operations, plan_drone_surveys))
    # def integrate_mission(self):
    #     print("Integrating mission plans")

    #     result = (
    #         IntegrationCrew()
    #         .crew()
    #         .kickoff(inputs={
    #             "rover_plan": self.state.rover_plan,
    #             "drone_plan": self.state.drone_plan
    #         })
    #     )

    #     self.state.final_plan = result.raw


def kickoff():
    flow = MarsMissionFlow()
    flow.kickoff()


def plot():
    flow = MarsMissionFlow()
    flow.plot()

def read_map(map):
    return nx.read_graphml(map)
import json
from typing import Any, Dict, List, Optional, Tuple


def run_rover_candidates_with_retries(
    rover_crew,
    rovers: List[Dict[str, Any]],
    primitive_goals: List[Dict[str, Any]],
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Re-run RoverCrew until output covers all primitive goals:
      len(assignments)+len(failures) == len(primitive_goals)

    Uses repair_instructions to tell the model exactly what's missing.
    """
    expected_ids = [g["id"] for g in primitive_goals]
    expected_set = set(expected_ids)

    repair: str = ""
    last_raw: Optional[str] = None

    for attempt in range(max_retries + 1):
        inputs = {"rovers": rovers}
        if repair:
            inputs["repair_instructions"] = repair
        result = rover_crew.crew().kickoff(inputs=inputs)

        last_raw = result.raw

        # parse JSON even if the model wrapped it
        data = None
        try:
            if isinstance(last_raw, str):
                s = last_raw.strip()
                # strip ```json fences if present
                if s.startswith("```"):
                    s = s.split("```", 2)[1] if "```" in s else s
                    s = s.replace("json", "", 1).strip()
                data = json.loads(s)
            elif getattr(result, "json_dict", None):
                data = result.json_dict
            else:
                data = json.loads(str(last_raw))
        except Exception:
            repair = (
                "Your previous output was not valid JSON. Return ONLY valid JSON with top-level keys "
                "assignments and failures, and include one entry per primitive goal."
            )
            continue

        assignments = data.get("assignments", [])
        failures = data.get("failures", [])

        # collect which primitive_goal_ids are covered
        covered = set()
        for a in assignments:
            pid = a.get("primitive_goal_id")
            if pid:
                covered.add(pid)
        for f in failures:
            pid = f.get("primitive_goal_id")
            if pid:
                covered.add(pid)

        missing = [pid for pid in expected_ids if pid not in covered]

        if not missing:
            # success
            return data

        repair = (
            "You omitted some primitive goals. You MUST return entries for EVERY primitive goal id in the context.\n"
            f"Missing primitive_goal_id(s): {missing}\n"
            "For each missing id, add an assignments item with that primitive_goal_id and candidates (max 2). "
            "If no candidate exists, add it to failures with a reason. Return ONLY valid JSON."
        )

    raise RuntimeError(
        f"Failed to cover all primitive goals after {max_retries+1} attempts. Last output was:\n{last_raw}"
    )

if __name__ == "__main__":
    kickoff()
