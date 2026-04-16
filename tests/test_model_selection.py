"""Tests for model candidate priority in litescribe.get_model_path."""

import pytest
from unittest.mock import patch
import litescribe


def exists_for(*model_names):
    """Return an os.path.exists side_effect that is True when the path contains any of model_names."""
    return lambda p: any(name in p for name in model_names)


class TestGetModelPath:
    def test_returns_none_when_no_models_exist(self):
        with patch('os.path.exists', return_value=False):
            path, name = litescribe.get_model_path({})
        assert path is None
        assert name is None

    def test_default_model_from_config_used_first(self):
        config = {"model": {"default_model": "ggml-base.bin", "use_small_en": False}}
        with patch('os.path.exists', side_effect=exists_for("ggml-base.bin")):
            path, name = litescribe.get_model_path(config)
        assert name == "ggml-base.bin"

    def test_use_small_en_true_prefers_small_en(self):
        config = {"model": {"use_small_en": True}}
        with patch('os.path.exists', side_effect=exists_for("ggml-small.en.bin", "ggml-base.bin")):
            path, name = litescribe.get_model_path(config)
        assert name == "ggml-small.en.bin"

    def test_use_small_en_falls_back_when_small_missing(self):
        config = {"model": {"use_small_en": True}}
        with patch('os.path.exists', side_effect=exists_for("ggml-base.en.bin")):
            path, name = litescribe.get_model_path(config)
        assert name == "ggml-base.en.bin"

    def test_falls_back_through_full_candidate_list(self):
        """If the configured default is absent, keeps trying further candidates."""
        config = {"model": {"default_model": "ggml-base.bin", "use_small_en": False}}
        # Only the last-resort model is present
        with patch('os.path.exists', side_effect=exists_for("ggml-small.en.bin")):
            path, name = litescribe.get_model_path(config)
        assert name == "ggml-small.en.bin"

    def test_empty_config_defaults_to_base_model(self):
        with patch('os.path.exists', side_effect=exists_for("ggml-base.bin")):
            path, name = litescribe.get_model_path({})
        assert name == "ggml-base.bin"

    def test_returned_path_ends_with_model_name(self):
        config = {"model": {"default_model": "ggml-base.bin", "use_small_en": False}}
        with patch('os.path.exists', side_effect=exists_for("ggml-base.bin")):
            path, name = litescribe.get_model_path(config)
        assert path is not None
        assert path.endswith(name)

    def test_no_duplicates_when_default_matches_fallback(self):
        """default_model=ggml-base.bin appears once even though it's also a fallback."""
        config = {"model": {"default_model": "ggml-base.bin", "use_small_en": False}}
        checked = []
        def tracking_exists(p):
            checked.append(p)
            return "ggml-base.bin" in p
        with patch('os.path.exists', side_effect=tracking_exists):
            litescribe.get_model_path(config)
        names_checked = [p.split('/')[-1] for p in checked]
        assert names_checked.count("ggml-base.bin") == 1
