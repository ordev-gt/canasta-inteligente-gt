from dataclasses import dataclass, field

from .persona import Persona


@dataclass
class Family:
    """Hogar compuesto por las personas cuyas necesidades se planificarán."""

    members: list[Persona] = field(default_factory=list)

    def add_member(self, person: Persona) -> None:
        self.members.append(person)

    def remove_member(self, person: Persona) -> None:
        self.members.remove(person)


# Alias en español 
Familia = Family
    
