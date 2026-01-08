import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm
from mars_exploration.models.drone_models import DroneMissionContext, DroneSelectionPlan, PossibleDroneAssignments
from mars_exploration.tools.common_tools import SplitGoalsTool
from mars_exploration.tools.drone_path_tool import DronesPathTool


@CrewBase
class DroneCrew:
    """Drone Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, mapp, drones, output_dir):
        self.route_tool = DronesPathTool(mars_map=mapp, drones=drones)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @agent
    def drone_context_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config["drone_context_cleaner"],
            max_iter=5,
            llm=get_llm(),
        )

    @task
    def clean_mission_for_drones(self) -> Task:
        return Task(
            config=self.tasks_config["clean_mission_for_drones"],
            output_pydantic=DroneMissionContext,
            output_file=os.path.join(self.output_dir, "clean_mission_for_drones.json"),
        )
    
    @agent
    def drone_candidates_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["drone_candidates_analyst"],
            llm=get_llm(),
            max_iter=5,
            tools=[self.route_tool],
        )

    @task
    def compute_possible_drone_assignments(self) -> Task:
        return Task(
            config=self.tasks_config["compute_possible_drone_assignments"],
            context=[self.clean_mission_for_drones()],
            output_pydantic=PossibleDroneAssignments,
            output_file=os.path.join(self.output_dir, "compute_possible_drone_assignments.json"),
        )
    
    @agent
    def drone_assignment_selector(self) -> Agent:
        return Agent(
            config=self.agents_config["drone_assignment_selector"],
            llm=get_llm(),
            max_iter=20,
            tools=[SplitGoalsTool()]
        )

    @task
    def select_drone_candidate(self) -> Task:
        return Task(
            config=self.tasks_config["select_drone_candidate"],
            context=[self.compute_possible_drone_assignments()],
            output_pydantic=DroneSelectionPlan,
            output_file=os.path.join(self.output_dir, "select_drone_candidate.json"),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Drone Crew"""

        return Crew(
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
