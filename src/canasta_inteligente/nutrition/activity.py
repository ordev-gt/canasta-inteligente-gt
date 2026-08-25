class PhysicalActivityLevel:
    """Convierte el nivel de actividad declarado al factor nutricional NAF."""

    @staticmethod
    def factor(sexo: str, level: str | None) -> float | None:
        if level is None:
            return None
        if level == "low":
            return 1.55
        if sexo == "mujer":
            return 1.75 if level == "moderate" else 2.1
        return 1.85 if level == "moderate" else 2.2
