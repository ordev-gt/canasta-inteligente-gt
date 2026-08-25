from ._catalog import *  # noqa: F401,F403

__all__ = [name for name in globals() if name.isupper() and any(token in name for token in ("CALCIO", "FOSFORO", "MAGNESIO", "HIERRO", "ZINC", "COBRE", "SELENIO", "SODIO", "POTASIO"))]
