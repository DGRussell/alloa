"""Module for classes/functions related to costs."""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from alloa_matching.utils.enums import Polarity

if TYPE_CHECKING:
    from alloa_matching.graph import AgentNode, AllocationGraph

# Used for type annotation of cost functions.
CostFunc = Callable[['AgentNode', 'AgentNode', 'AllocationGraph'], int]


def default_cost(
    node1: AgentNode, node2: AgentNode, graph: AllocationGraph
) -> int:
    _ = node1, node2, graph
    return 0


def spa_cost(node1: AgentNode, node2: AgentNode, graph: AllocationGraph) -> int:
    if (
        node1.polarity == Polarity.POSITIVE
    ) and (
        node2.polarity == Polarity.NEGATIVE
    ):
        return 0

    agent1, agent2 = node1.agent, node2.agent

    # Get rank of agent2 in agent1's preferences.
    term = agent1.preference_position(agent2)

    # Get all hierarchies above agent1's level, excluding the final level.
    hierarchy = graph.agent_node_to_hierarchy_map[node1]
    level = hierarchy.level
    intermediate_hierarchies = graph.intermediate_hierarchies(level)

    # Sum the maximal rank at each of the intermediate hierarchies.
    _sum = sum(
        hierarchy.max_preferences_length
        for hierarchy in intermediate_hierarchies
    )
    exponent = term - 1 + _sum

    return (graph.min_upper_capacity_sum + 1) ** exponent
