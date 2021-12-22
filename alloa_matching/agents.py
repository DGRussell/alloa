"""Module containing Agent and Hierarchy classes. Agents represent nodes on the
graph and are bucketed into a hierarchy of multiple agents, with a given level.
Each agent has an (ordered) list of preferences of agents at the next level.
"""
from __future__ import annotations

import itertools
import uuid
from typing import Any, Collection, Dict, Iterator, List, Optional, Union

from alloa_matching.utils.exceptions import AgentExistsError


class Agent:
    """Representation of an individual agent e.g. student/project/supervisor."""
    def __init__(
        self,
        agent_id: Optional[str] = None,
        capacities: Optional[Collection[int]] = None,
        preferences: Optional[List[Union[Agent, List[Agent]]]] = None,
        name: Any = None
    ) -> None:
        """
        Parameters
        ----------
        agent_id:
            Unique ID identifying the agent.
        name:
            Name of agent e.g. Paul. This is not unique.
        capacities:
            The minimum and maximum amount this agent can take on, e.g.
            a project supervisor with capacities (1, 3) would mean she must
            supervise one project as a minimum, but can supervise up to three
            in total.
        preferences:
            The agents at the next hierarchy level that this agent prefers.
            Elements can be agents or lists of agents to represent ties.
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.capacities = capacities or []
        self.preferences = preferences or []

    def __str__(self) -> str:
        return f'AGENT_{self.agent_id}'

    def __hash__(self) -> int:
        """Agents are used as dictionary keys when flow is calculated, so need a
        hash method.
        """
        return hash(self.agent_id)

    def __eq__(self, other: Agent):
        if not isinstance(self, other.__class__):
            return False
        return self.agent_id == other.agent_id

    @property
    def upper_capacity(self) -> Optional[int]:
        if self.capacities:
            return self.capacities[1]

    @property
    def lower_capacity(self) -> Optional[int]:
        if self.capacities:
            return self.capacities[0]

    @property
    def capacity_difference(self) -> Optional[int]:
        if self.capacities:
            return self.upper_capacity - self.lower_capacity

    def preference_position(self, other: Agent) -> int:
        """Position of another agent in the preference list."""
        for i, preference in enumerate(self.preferences):
            # Is the agent in the preference list?
            if other == preference:
                return i + 1
            # Is the agent tied with other agents?
            try:
                if other in preference:
                    return i + 1
            except TypeError:
                continue
        return 0


class Hierarchy:
    """Representation of a bucket of agents."""
    def __init__(
        self, level: int, agents: Optional[List[Agent]] = None
    ) -> None:
        self.level = level
        self.agent_ids = set()
        self.agents = agents or []

    def __str__(self) -> str:
        return f'HIERARCHY_{self.level}'

    def __iter__(self) -> Iterator[Agent]:
        return iter(self.agents)

    @property
    def agents(self) -> List[Agent]:
        return self._agents

    @agents.setter
    def agents(self, value: List[Agent]) -> None:
        self._agents = value or []
        for agent in self._agents:
            if self._has_agent_with_id(agent.agent_id):
                raise AgentExistsError(self, agent.agent_id)
            self.agent_ids.add(agent.agent_id)

    @property
    def name_agent_map(self) -> Dict[str, Agent]:
        return {v: k for k, v in self._agent_name_map.items()}

    def add_agent(self, agent: Agent) -> None:
        if self._has_agent_with_id(agent.agent_id):
            raise AgentExistsError(self, agent.agent_id)
        self.agents.append(agent)
        self.agent_ids.add(agent.agent_id)

    @property
    def number_of_agents(self) -> int:
        return len(self.agents)

    @staticmethod
    def preferred(agent_subset: Collection[Agent]) -> List[Agent]:
        """Return list of unique agents, sorted by ID, that the agents in the
        given subset prefer at the next hierarchy level.
        """
        all_unflattened = [agent.preferences for agent in agent_subset]
        all_flattened = itertools.chain(*all_unflattened)
        all_flattened_unique = set(all_flattened)
        return sorted(all_flattened_unique, key=lambda agent: agent.agent_id)

    @property
    def max_preferences_length(self) -> int:
        return max(len(agent.preferences) for agent in self.agents)

    @property
    def upper_capacity_sum(self) -> int:
        return sum(agent.upper_capacity for agent in self)

    def _has_agent_with_id(self, agent_id: str) -> bool:
        return agent_id in self.agent_ids

    @property
    def _agent_name_map(self) -> Dict[Agent, str]:
        return {agent: agent.name for agent in self.agents}
