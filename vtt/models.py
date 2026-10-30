"""Shared model path resolution for LiteType."""

import os


def models_dir() -> str:
    """Directory holding the downloaded ggml model files."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def list_models() -> list[str]:
    """Names of the model files available in models_dir(), sorted."""
    try:
        return sorted(f for f in os.listdir(models_dir()) if f.endswith(".bin"))
    except OSError:
        return []


def get_model_path(config: dict) -> tuple:
    """Return (path, name) for the best available Whisper model given config."""
    directory = models_dir()
    model_cfg = config.get("model", {})
    use_small_en = model_cfg.get("use_small_en", False)
    default_model = model_cfg.get("default_model", "ggml-base.bin")

    if use_small_en:
        candidates = ["ggml-small.en.bin", "ggml-base.en.bin", "ggml-base.bin"]
    else:
        candidates = [default_model, "ggml-base.en.bin", "ggml-small.en.bin", "ggml-base.bin"]

    seen = set()
    candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    for name in candidates:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return path, name

    return None, None
