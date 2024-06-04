from enum import Enum


# define an enum for embedding type
class EmbeddingType(str, Enum):
    OPENAI = "OPENAI"
    HUGGINGFACE = "HUGGINGFACE"
    LAMMAGPT = "LAMMAGPT"
