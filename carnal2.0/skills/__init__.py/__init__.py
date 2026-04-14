import importlib, pkgutil

def load_skills():
    skills = {}
    for m in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{m.name}")
        if hasattr(mod, "REGISTRY"):
            skills.update(mod.REGISTRY)
    return skills