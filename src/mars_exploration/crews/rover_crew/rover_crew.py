import os
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm
from mars_exploration.tools.shortest_path_tool import ShortestPathTool
from mars_exploration.tools.rover_simulation import RoverSimTool
from mars_exploration.models.rover_models import PrimitiveGoalsOutput, RoverMissionContext
@CrewBase
class RoverCrew:
    """Rover Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

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
    def primitive_goal_decomposer(self) -> Agent:
        return Agent(
            config=self.agents_config["primitive_goal_decomposer"],
            llm=get_llm(),
        )

    @task
    def decompose_rover_goals(self) -> Task:
        return Task(
            config=self.tasks_config["decompose_rover_goals"],
            context=[self.clean_mission_for_rovers()],
            output_pydantic=PrimitiveGoalsOutput
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
