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

    def __init__(self, output_dir, **kwargs):
        super().__init__(**kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @agent
    def integration_planner(self) -> Agent:
        return Agent(
            config=self.agents_config["integration_planner"], 
            llm=get_llm(),
            reasoning=False
        )

    @task
    def integrate_mission_plans(self) -> Task:
        return Task(
            config=self.tasks_config["integrate_mission_plans"],
            markdown=True,
            output_file=os.path.join(self.output_dir, "integrate_mission_plans.md")
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
