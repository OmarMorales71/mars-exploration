import os
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm
from mars_exploration.models.mission_spec import MissionSpec

@CrewBase
class MissionCrew:
    """Mission Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def mission_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["mission_analyst"], 
            llm=get_llm()
        )

    @task
    def process_mission_report(self) -> Task:
        return Task(
            config=self.tasks_config["process_mission_report"],
            output_pydantic=MissionSpec
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Mission Crew"""

        return Crew(
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
