"""Unit tests for Stage 4 Named Entity Recognition (NER) module.

Tests cover:
- Valid job description entity extraction
- Empty text handling
- None input handling
- Whitespace-only input
- Multiple entities in single text
- Entity dictionary structure (text and label keys)
- Missing model error handling with actionable instructions
- Entity deduplication behavior
"""

from unittest.mock import patch
import pytest

from src.skills.ner_extractor import (
    DEFAULT_SPACY_MODEL,
    ModelNotFoundError,
    NamedEntityExtractor,
    RELEVANT_ENTITY_LABELS,
    load_spacy_model,
)


@pytest.fixture(scope="module")
def shared_ner():
    """Module-level fixture to load spaCy model once for all NER tests."""
    return NamedEntityExtractor()


class TestNamedEntityExtractor:
    """Test suite for NamedEntityExtractor class."""

    def test_valid_job_description(self, shared_ner):
        """Valid job description produces expected named entities."""
        text = "Microsoft is hiring a Senior Software Engineer in Redmond, Washington."
        entities = shared_ner.extract_entities(text)

        assert isinstance(entities, list)
        assert len(entities) >= 2

        texts = [e["text"] for e in entities]
        labels = [e["label"] for e in entities]

        assert "Microsoft" in texts
        assert "ORG" in labels
        assert any(label in ("GPE", "LOC") for label in labels)

    def test_empty_text(self, shared_ner):
        """Empty string returns an empty list."""
        assert shared_ner.extract_entities("") == []

    def test_whitespace_text(self, shared_ner):
        """Whitespace-only string returns an empty list."""
        assert shared_ner.extract_entities("   \n\t  ") == []

    def test_none_input(self, shared_ner):
        """None input returns an empty list without raising exception."""
        assert shared_ner.extract_entities(None) == []

    def test_multiple_entities(self, shared_ner):
        """Extracts multiple entities of different types."""
        text = "Satya Nadella spoke at Microsoft headquarters in Redmond, Washington regarding Azure."
        entities = shared_ner.extract_entities(text)

        labels = {e["label"] for e in entities}
        assert "ORG" in labels
        assert "GPE" in labels or "PERSON" in labels

    def test_entity_label_structure(self, shared_ner):
        """Each entity dictionary contains exactly 'text' and 'label' string fields."""
        text = "Google and Microsoft compete in cloud services in Seattle."
        entities = shared_ner.extract_entities(text)

        assert len(entities) > 0
        for ent in entities:
            assert isinstance(ent, dict)
            assert "text" in ent
            assert "label" in ent
            assert isinstance(ent["text"], str)
            assert isinstance(ent["label"], str)
            assert len(ent["text"]) > 0
            assert ent["label"] in RELEVANT_ENTITY_LABELS

    def test_entity_deduplication(self, shared_ner):
        """Repeated mentions of the same entity return a single deduplicated entry."""
        text = "Microsoft announces that Microsoft has opened a new Microsoft facility in Dublin, Dublin."
        entities = shared_ner.extract_entities(text)

        microsoft_mentions = [e for e in entities if e["text"].lower() == "microsoft"]
        assert len(microsoft_mentions) == 1

        dublin_mentions = [e for e in entities if e["text"].lower() == "dublin"]
        assert len(dublin_mentions) == 1

    def test_get_entity_counts(self, shared_ner):
        """Counts frequency of entity labels correctly."""
        entities = [
            {"text": "Microsoft", "label": "ORG"},
            {"text": "Amazon", "label": "ORG"},
            {"text": "Dublin", "label": "GPE"},
        ]
        counts = shared_ner.get_entity_counts(entities)
        assert counts == {"ORG": 2, "GPE": 1}

    def test_model_unavailable_handling(self):
        """Attempting to load a nonexistent model raises ModelNotFoundError with instructions."""
        with pytest.raises(ModelNotFoundError) as exc_info:
            load_spacy_model("nonexistent_model_xyz_123")

        err_msg = str(exc_info.value)
        assert "nonexistent_model_xyz_123" in err_msg
        assert "python -m spacy download nonexistent_model_xyz_123" in err_msg
