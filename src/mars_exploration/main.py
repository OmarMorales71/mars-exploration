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
MISSION_SUMMARY_JSON= os.path.join(INTERMEDIATE_DIR, "mission_crew_output.json")
MARS_MAP_PATH = os.path.join(INPUT_DIR, "mars_terrain.graphml")
ROVERS_FILE = os.path.join(INPUT_DIR, "rovers.json")
DRONES_FILE = os.path.join(INPUT_DIR, "drones.json")
ROVER_PLAN_JSON = os.path.join(INTERMEDIATE_DIR, "rover_crew_output.json")
DRONE_PLAN_JSON = os.path.join(INTERMEDIATE_DIR, "drone_crew_output.json")

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
            MissionCrew(output_dir=INTERMEDIATE_DIR)
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

    # @listen(process_mission)
    def plan_rover_operations(self):
        print(f"Planning rover operations {self.state.mission_summary}")

        result = (
            RoverCrew(mapp=self.state.mars_map_path, rovers=self.state.rovers, output_dir=INTERMEDIATE_DIR)
            .crew()
            .kickoff(inputs={
                "mission_summary": self.state.mission_summary.model_dump_json()          
            })
        )

        self.state.rover_plan = result.pydantic

        with open(ROVER_PLAN_JSON, "w", encoding="utf-8") as f:
            f.write(self.state.rover_plan.model_dump_json(indent=4))

    @listen(process_mission)
    def plan_drone_operations(self):
        print(f"Planning drone operations {self.state.mission_summary}")
        print(self.state.rovers)
        result = (
            DroneCrew(mapp=self.state.mars_map_path, drones=self.state.drones, output_dir=INTERMEDIATE_DIR)
            .crew()
            .kickoff(inputs={
                "mission_summary": self.state.mission_summary.model_dump_json()          
            })
        )
        print(f"Finish rover 1")
        print(result)
        self.state.drone_plan = result.pydantic
        print(f"Finish rover 1.5")

        with open(DRONE_PLAN_JSON, "w", encoding="utf-8") as f:
            f.write(self.state.drone_plan.model_dump_json(indent=4))
        print(self.state.drone_plan)
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

if __name__ == "__main__":
    kickoff()
