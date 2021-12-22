from typing import List

from alloa_matching.agents import Agent, Hierarchy
from alloa_matching.costs import CostFunc
from alloa_matching.files import FileReader
from alloa_matching.graph import AllocationGraph


class GraphBuilder:
    def __init__(
        self, file_data_objects: List[FileReader], cost: CostFunc
    ) -> None:
        self.file_data_objects = file_data_objects
        self.hierarchies = [
            Hierarchy(i + 1) for i, _ in enumerate(self.file_data_objects)
        ]
        self.cost = cost

    def build_graph(self) -> AllocationGraph:
        self.create_agents()
        graph = AllocationGraph.with_edges(self.hierarchies, cost=self.cost)
        return graph

    def create_agents(self) -> None:
        """Create agents and add to hierarchies in reverse order, setting the
        preferences as we go.
        """
        number_of_hierarchies = len(self.file_data_objects)
        upper_hierarchy = Hierarchy(level=number_of_hierarchies + 1)

        for file_data, lower_hierarchy in zip(
            reversed(self.file_data_objects), reversed(self.hierarchies)
        ):
            for line in file_data.file_content:
                preferences = [
                    upper_hierarchy.name_agent_map.get(preference)
                    for preference in line.raw_preferences
                ]
                agent = Agent(
                    capacities=line.capacities,
                    preferences=preferences,
                    name=line.raw_name
                )
                lower_hierarchy.agents.append(agent)
            upper_hierarchy = lower_hierarchy
