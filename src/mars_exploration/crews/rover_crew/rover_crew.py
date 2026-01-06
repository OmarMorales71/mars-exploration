import os
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm
from mars_exploration.tools.rover_path_tool import RoversPathTool
from mars_exploration.models.rover_models import PossibleAssignments, RoverMissionContext
@CrewBase
class RoverCrew:
    """Rover Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, mapp, rovers):
        self.route_tool = RoversPathTool(mars_map=mapp, rovers=rovers)

    @agent
    def rover_context_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config["rover_context_cleaner"],
            llm=get_llm(),
        )

    
    @task
    def clean_mission_for_rovers(self) -> Task:
        return Task(
            config=self.tasks_config["clean_mission_for_rovers"],
            output_pydantic=RoverMissionContext
        )
    
    @agent
    def rover_candidates_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["rover_candidates_analyst"],
            llm=get_llm(),
            tools=[self.route_tool]
        )
    
    @task
    def compute_possible_rover_assignments(self) -> Task:
        return Task(
            config=self.tasks_config["compute_possible_rover_assignments"],
            context=[self.clean_mission_for_rovers()],
            output_pydantic=PossibleAssignments,
        )

    # @agent
    # def primitive_goal_decomposer(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["primitive_goal_decomposer"],
    #         llm=get_llm(),
    #     )

    # @task
    # def decompose_rover_goals(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["decompose_rover_goals"],
    #         context=[self.clean_mission_for_rovers()],
    #         output_pydantic=PrimitiveGoalsOutput
    #     )

    # @agent
    # def rover_candidate_matcher(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["rover
    # _candidate_matcher"],
    #         llm=get_llm(),
    #         tools=[self.route_tool]
    #     )

    # @task
    # def match_rovers_to_primitive_goals(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["match_rovers_to_primitive_goals"],
    #         context=[self.decompose_rover_goals()],  
    #         output_pydantic=RoverCandidatesPlan,
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the Rover Crew"""

        return Crew(
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
