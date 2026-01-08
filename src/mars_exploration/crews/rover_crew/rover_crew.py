import os
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Any, Tuple

from mars_exploration.commons.llm import get_llm
from mars_exploration.tools.common_tools import SplitGoalsTool
from mars_exploration.tools.rover_path_tool import RoversPathTool
from mars_exploration.models.rover_models import PossibleAssignments, RoverMissionContext, RoverSelectionPlan
@CrewBase
class RoverCrew:
    """Rover Crew"""


    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    def __init__(self, mapp, rovers, output_dir):
        self.route_tool = RoversPathTool(mars_map=mapp, rovers=rovers)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)


    @agent
    def rover_context_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config["rover_context_cleaner"],
            max_iter=5,
            llm=get_llm(),
        )

    
    @task
    def clean_mission_for_rovers(self) -> Task:
        return Task(
            config=self.tasks_config["clean_mission_for_rovers"],
            output_pydantic=RoverMissionContext,
            output_file=os.path.join(self.output_dir, "clean_mission_for_rovers.json")
        )
    
    @agent
    def rover_candidates_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["rover_candidates_analyst"],
            llm=get_llm(),
            max_iter=5,
            tools=[self.route_tool]
        )
    
    @task
    def compute_possible_rover_assignments(self) -> Task:
        return Task(
            config=self.tasks_config["compute_possible_rover_assignments"],
            context=[self.clean_mission_for_rovers()],
            output_pydantic=PossibleAssignments,
            output_file=os.path.join(self.output_dir, "compute_possible_rover_assignments.json")
        )

    @agent
    def rover_assignment_selector(self) -> Agent:
        return Agent(
            config=self.agents_config["rover_assignment_selector"],
            llm=get_llm(),
            max_iter=20,
            tools=[SplitGoalsTool()]
        )
    
    @task
    def select_rover_candidate(self) -> Task:
        return Task(
            config=self.tasks_config["select_rover_candidate"],
            context=[self.compute_possible_rover_assignments()],
            output_pydantic=RoverSelectionPlan,
            output_file=os.path.join(self.output_dir, "select_rover_candidate.json")
        )

    
    @crew
    def crew(self) -> Crew:
        """Creates the Rover Crew"""

        return Crew(
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
