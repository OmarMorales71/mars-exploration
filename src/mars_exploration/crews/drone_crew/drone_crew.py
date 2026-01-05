import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from mars_exploration.commons.llm import get_llm


@CrewBase
class DroneCrew:
    """Drone Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

   
    @agent
    def drone_survey(self) -> Agent:
        return Agent(
            config=self.agents_config["drone_survey"],  
            llm=get_llm()
        )

    @task
    def plan_drone_surveys(self) -> Task:
        return Task(
            config=self.tasks_config["plan_drone_surveys"],  
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
