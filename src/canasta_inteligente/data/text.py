import re
import unicodedata


class TextNormalizer:
    STOPWORDS = {"de", "del", "la", "el", "los", "las", "y", "con", "sin", "para", "en", "por", "tipo"}

    @classmethod
    def normalize(cls, value: str | None) -> str:
        if value is None:
            return ""
        text = str(value).lower().strip()
        text = "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        tokens = re.sub(r"\s+", " ", text).strip().split()
        return " ".join(token for token in tokens if token not in cls.STOPWORDS)
