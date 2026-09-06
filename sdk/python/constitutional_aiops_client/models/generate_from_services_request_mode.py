from enum import StrEnum


class GenerateFromServicesRequestMode(StrEnum):
    LLM = "llm"
    TEMPLATE = "template"

    def __str__(self) -> str:
        return str(self.value)
