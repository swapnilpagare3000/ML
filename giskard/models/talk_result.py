from dataclasses import dataclass

from giskard.llm.client import LLMMessage


@dataclass
class TalkResult:
    """The dataclass containing the result of the 'talk' call.

    Attributes
    ----------
    response : LLMMessage
        The response to the user's query.
    summary : LLMMessage
        The summary of the conversation between the user and the LLM agent.
    """

    response: LLMMessage
    summary: LLMMessage

    def __str__(self):
        return (
            f"LLM Response:\n"
            f"-------------\n"
            f"{self.response.content}\n\n"
            f"Full Conversation Summary:\n"
            f"--------------------------\n"
            f"{self.summary.content}"
        )
