"""Tests for transcript cleanup and vocabulary prompt building."""

import pytest
from vtt.transcriber import build_prompt, clean_transcript


class TestBuildPrompt:
    def test_empty_vocabulary_gives_no_prompt(self):
        assert build_prompt([]) == ""
        assert build_prompt(None) == ""

    def test_words_joined_into_glossary(self):
        assert build_prompt(["Claude", "AIWP"]) == "Glossary: Claude, AIWP."

    def test_blank_entries_ignored(self):
        assert build_prompt(["Claude", "  ", ""]) == "Glossary: Claude."


class TestCleanTranscript:
    def test_normal_text_unchanged(self):
        assert clean_transcript("I will mention the skill.") == "I will mention the skill."

    @pytest.mark.parametrize("raw", ["[BLANK_AUDIO]", "(music)", " [inaudible] ", ""])
    def test_tag_only_output_is_dropped(self, raw):
        assert clean_transcript(raw) == ""

    def test_tags_removed_from_real_speech(self):
        assert clean_transcript("Hello [BLANK_AUDIO] world") == "Hello world"

    @pytest.mark.parametrize("raw", ["Thank you.", "you", "Thanks for watching!"])
    def test_phantom_phrases_dropped(self, raw):
        assert clean_transcript(raw) == ""

    def test_phantom_phrase_inside_real_sentence_kept(self):
        text = "Thank you for the slides, they look great."
        assert clean_transcript(text) == text

    def test_echoed_prompt_dropped(self):
        prompt = build_prompt(["Claude", "AIWP"])
        assert clean_transcript("Glossary: Claude, AIWP.", prompt) == ""

    def test_text_mentioning_vocab_kept(self):
        prompt = build_prompt(["Claude", "AIWP"])
        assert clean_transcript("Claude helps with AIWP.", prompt) == "Claude helps with AIWP."
