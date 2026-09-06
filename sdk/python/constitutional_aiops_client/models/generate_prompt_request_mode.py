from enum import StrEnum


class GeneratePromptRequestMode(StrEnum):
    LLM = "llm"
    TEMPLATE = "template"

    def __str__(self) -> str:
        return str(self.value)
