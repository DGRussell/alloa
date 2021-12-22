"""Module containing useful custom Exceptions."""


class AgentExistsError(Exception):
    """Exception raised when instantiating an agent with the same id as an
    existing agent on the hierarchy."""

    def __init__(self, hierarchy, agent_id):
        super().__init__(
            f'{hierarchy} already has an agent with ID {agent_id}.'
        )
