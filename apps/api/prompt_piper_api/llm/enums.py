from enum import StrEnum


class ModelProvider(StrEnum):
    LOCAL_OPENAI_COMPATIBLE = "local_openai_compatible"
    EXTERNAL_OPENAI_COMPATIBLE = "external_openai_compatible"


class ModelProfile(StrEnum):
    COMPATIBILITY = "compatibility"
    QUALITY = "quality"
