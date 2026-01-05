import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm


@CrewBase
class IntegrationCrew:
    """Integration Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def mission_integration(self) -> Agent:
        return Agent(
            config=self.agents_config["mission_integration"], 
            llm=get_llm()
        )

    @task
    def integrate_mission_plans(self) -> Task:
        return Task(
            config=self.tasks_config["integrate_mission_plans"], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Integration Crew"""

        return Crew(
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
