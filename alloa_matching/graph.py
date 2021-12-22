"""Module for constructing a directed graph (network) to model the allocation.
Hierarchies are converted into subgraphs (HierarchyGraph) of the main allocation
graph (AllocationGraph). Edges between the subgraphs represent the preferences 
of the agents between each hierarchy level.
"""
from __future__ import annotations

from collections import namedtuple
from functools import cached_property, total_ordering
from typing import Any, Dict, Generator

import networkx as nx

from alloa_matching.agents import Agent, Hierarchy, List, Optional
from alloa_matching.costs import CostFunc, default_cost
from alloa_matching.utils.enums import GraphElement, Polarity

AllocationDatum = namedtuple('AllocationDatum', ['agent', 'rank'])


@total_ordering
class AgentNode:
    """Agent nodes split into positive and negative component nodes. An edge is
    drawn between them when the graph is built.
    """
    def __init__(self, agent: Agent, polarity: Polarity) -> None:
        """
        Parameters
        ----------
        agent:
            Single Agent that this node represents (together with its opposite
            polarity pair).
        polarity:
            Either POSITIVE(+) or NEGATIVE(-).
        """
        self.agent = agent
        self.polarity = polarity

    def __str__(self) -> str:
        return f'{self.agent}({self.polarity.value})'

    def __hash__(self) -> int:
        """These objects are used as nodes in the graph, in particular they are
        used as dictionary keys. There should only exist one agent with each id
        so that plus polarity suffice as identifiers.
        """
        return hash((self.agent.agent_id, self.polarity))

    def __eq__(self, other: AgentNode) -> bool:
        """These represent nodes on the allocation graph and are compared to
        other objects in the networkx module, so makes sense to define rich
        comparison operators. Also useful for testing.
        """
        return all(self._agent_node_eq_comparison(other))

    def _agent_node_eq_comparison(
        self, other: AgentNode
    ) -> Generator[bool, None, None]:
        """Generator of all attributes which define agent node equality."""
        yield isinstance(other, self.__class__)
        yield self.agent == other.agent
        yield self.polarity == other.polarity

    def __lt__(self, other: AgentNode) -> bool:
        """Lexicographic ordering by agent and polarity. We treat positive as
        less than negative since the graph flows from positive to negative
        between two agent nodes at the same level."""
        if self.agent == other.agent:
            return (
                self.polarity == Polarity.POSITIVE
            ) and (
                other.polarity == Polarity.NEGATIVE
            )
        return self.agent < other.agent


class AllocationGraph(nx.DiGraph):
    """Representation of the allocation problem as a directed graph (network).
    For each agent, split them into positive and negative agent nodes and draw
    an edge between these. The capacity of the edge represents the capacity of
    the agent. The rules are:
        1) edge capacity = agent upper capacity - agent lower capacity.
        2) positive node demand = agent lower capacity.
        3) negative node demand = agent lower capacity * (-1).
    We also draw an edge from the negative node of an agent to the positive node
    of each agent at the next hierarchy level, based on preference. The cost of
    these edges is determined by the cost function passed in.
    """
    def __init__(self, cost: Optional[CostFunc] = None):
        """
        Parameters
        ----------
        cost:
            Function determining the cost of an edge between two given agents
        """
        super().__init__()
        self.cost = default_cost if cost is None else cost
        self._agent_positive_node_map = {}
        self._agent_negative_node_map = {}
        self.hierarchies = []
        self.hierarchy_subgraphs = []

        self.flow = None
        self.flow_cost = None
        self.max_flow = None
        self.simple_flow = None

        self.allocation = None

        self.agent_node_to_hierarchy_map = {}

    def __eq__(self, other: AllocationGraph) -> bool:
        return all(self._graph_eq_comparison(other))

    def _graph_eq_comparison(
        self, other: AllocationGraph
    ) -> Generator[bool, None, None]:
        """Generator of all attributes which define graph equality."""
        yield isinstance(other, self.__class__)
        yield self.nodes == other.nodes
        yield sorted(self.edges(data=True)) == sorted(other.edges(data=True))
        yield self.hierarchies == other.hierarchies

    @cached_property
    def source(self) -> AgentNode:
        """Create source agent which equally prefers all level 1 agents."""
        source_agent = Agent(
            preferences=[self.first_level_agents],
            name=GraphElement.SOURCE
        )
        zero_hierarchy = Hierarchy(level=0)
        zero_hierarchy.add_agent(source_agent)
        source = AgentNode(source_agent, Polarity.POSITIVE)
        self.agent_node_to_hierarchy_map[source] = zero_hierarchy
        return source

    @cached_property
    def sink(self) -> AgentNode:
        """Create sink agent which is equally preferred by all agents in the
        last hierarchy.
        """
        sink_agent = Agent(name=GraphElement.SINK)
        for agent in self.last_level_agents:
            agent.preferences = [sink_agent]
        final_hierarchy = Hierarchy(level=self.number_of_hierarchies + 1)
        final_hierarchy.agents.append(sink_agent)
        sink = AgentNode(sink_agent, Polarity.NEGATIVE)
        self.agent_node_to_hierarchy_map[sink] = final_hierarchy
        return sink

    @property
    def first_level_agents(self) -> List[Agent]:
        return self.hierarchies[0].agents

    @property
    def last_level_agents(self) -> List[Agent]:
        return self.hierarchies[-1].agents

    @property
    def number_of_hierarchies(self) -> int:
        return len(self.hierarchies)

    @property
    def positive_agent_nodes(self) -> List[AgentNode]:
        """Return generator of all positive agent nodes, in order."""
        return [node for node in self if node.polarity == Polarity.POSITIVE]

    @property
    def negative_agent_nodes(self) -> List[AgentNode]:
        """Return generator of all negative agent nodes, in order."""
        return [node for node in self if node.polarity == Polarity.NEGATIVE]

    @classmethod
    def with_edges(
        cls,
        hierarchies: List[Hierarchy],
        cost: CostFunc
    ) -> AllocationGraph:
        graph = cls(cost)
        for hierarchy in hierarchies:
            graph.add_hierarchy(hierarchy)
        graph.populate_all_edges()
        return graph

    def add_hierarchy(self, hierarchy: Hierarchy) -> None:
        for agent in hierarchy.agents:
            out_node = AgentNode(agent, Polarity.POSITIVE)
            self.agent_node_to_hierarchy_map[out_node] = hierarchy
            in_node = AgentNode(agent, Polarity.NEGATIVE)
            self.agent_node_to_hierarchy_map[in_node] = hierarchy
            demand = agent.lower_capacity
            capacity = agent.capacity_difference
            self.add_node(out_node, demand=demand)
            self.add_node(in_node, demand=-demand)
            self.add_edge_with_cost(out_node, in_node, capacity=capacity)
        self.hierarchies.append(hierarchy)

    def add_node(self, node: AgentNode, **attr: Any) -> None:
        if node.polarity == Polarity.POSITIVE:
            self._agent_positive_node_map[node.agent] = node
        else:
            self._agent_negative_node_map[node.agent] = node
        super().add_node(node, **attr)

    def populate_all_edges(self) -> None:
        self.populate_edges_from_source()
        self.populate_edges_to_sink()
        for hierarchy in self.hierarchies[:-1]:
            self.glue(hierarchy)

    def populate_edges_from_source(self) -> None:
        for agent in self.first_level_agents:
            node = self._agent_positive_node_map[agent]
            self.add_edge_with_cost(self.source, node)

    def populate_edges_to_sink(self) -> None:
        for agent in self.last_level_agents:
            node = self._agent_negative_node_map[agent]
            self.add_edge_with_cost(node, self.sink)

    def allocate(self) -> None:
        allocation = {}

        # Make inexpensive deep copy of simple_flow.
        g = ((agent, dict(d)) for agent, d in self.simple_flow.items())
        flow = dict(g)

        for agent in self.hierarchies[0]:
            allocation[agent] = self.single_allocation(agent, flow)

        self.allocation = allocation

    @staticmethod
    def single_allocation(
        agent: Agent,
        flow: Dict[Agent, Dict[Agent, int]]
    ) -> List[AllocationDatum]:
        """Return a list of AllocationDatum objects describing the allocation
        of higher level agents to a given level 1 agent.
        Parameters
        ----------
        agent:
            Agent at level 1.
        flow:
            Copy of self.simple_flow where keys are deleted or values modified
            as they are encountered.
        """
        value = []
        current_agent = agent
        while current_agent in flow:
            agent_flow = flow[current_agent]
            try:
                next_agent, flow_units = next(iter(agent_flow.items()))
            except StopIteration:
                break
            else:
                rank = current_agent.preference_position(next_agent)
                value.append(AllocationDatum(next_agent, rank))
                if flow_units == 1:
                    agent_flow.pop(next_agent)
                else:
                    agent_flow[next_agent] -= 1
                current_agent = next_agent
        return value

    def intermediate_hierarchies(self, level: int) -> List[Hierarchy]:
        """Return all hierarchies strictly between the given level (inclusive)
        and the last hierarchy (non-inclusive).
        """
        return self.hierarchies[level: -1]

    @property
    def min_upper_capacity_sum(self) -> int:
        return min(
            hierarchy.upper_capacity_sum for hierarchy in self.hierarchies
        )

    def glue(self, hierarchy: Hierarchy) -> None:
        for agent in hierarchy.agents:
            for preference in agent.preferences:

                # Handle preference ties.
                if isinstance(preference, Agent):
                    preference_list = [preference]
                elif isinstance(preference, list):
                    preference_list = preference
                else:
                    preference_list = []

                for other_agent in preference_list:
                    out_node = self.negative_node(agent)
                    in_node = self.positive_node(other_agent)
                    self.add_edge_with_cost(out_node, in_node)

    def positive_node(self, agent: Agent) -> AgentNode:
        """Return positive node corresponding to the agent."""
        return self._agent_positive_node_map[agent]

    def negative_node(self, agent) -> AgentNode:
        """Return negative node corresponding to the agent."""
        return self._agent_negative_node_map[agent]

    def add_edge_with_cost(
        self,
        out_node: AgentNode,
        in_node: AgentNode,
        capacity: Optional[int] = None
    ) -> None:
        weight = self.cost(out_node, in_node, graph=self)
        if capacity is not None:
            self.add_edge(out_node, in_node, weight=weight, capacity=capacity)
        else:
            self.add_edge(out_node, in_node, weight=weight)

    def compute_flow(self) -> None:
        self.flow = nx.max_flow_min_cost(self, self.source, self.sink)
        self.flow_cost = nx.cost_of_flow(self, self.flow)
        self.max_flow = nx.maximum_flow(self, self.source, self.sink)[0]

    def simplify_flow(self) -> None:
        """Create new dictionary mapping
            Agent --> OrderedDict(Agents: int)
        Map Agents to every Agent they have non-zero flow towards, and what the
        flow value is.  Assign to simple_flow attribute.
        """
        mapping = {}

        # For each agent node (except the last level):
        for hierarchy in self.hierarchies[:-1]:
            for agent in hierarchy.agents:
                # Assign to it the non-zero flows from negative agent nodes to
                # positive agent nodes at the next level.
                negative_node = self.negative_node(agent)
                flow = self.flow[negative_node]
                items = ((k.agent, v) for k, v in flow.items() if v)
                mapping[agent] = dict(items)

        self.simple_flow = mapping
