"""Model path resolution for LiteType.

Models live in the user data dir (see paths.models_dir), downloaded via the
`litetype-download-models` command.
"""

import os

from .paths import models_dir


def get_model_path(config: dict) -> tuple:
    """Return (path, name) for the best available Whisper model given config."""
    mdir = models_dir()
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
        path = os.path.join(mdir, name)
        if os.path.exists(path):
            return path, name

    return None, None
