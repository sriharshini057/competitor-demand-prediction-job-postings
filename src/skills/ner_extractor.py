"""Named Entity Recognition (NER) Module for Job Postings.

Stage 4: spaCy-based Named Entity Recognition identifying organizations,
locations, persons, products, and other standard named entities in job postings.

Important Pretrained Model Disclaimer:
    Pretrained spaCy English models (such as `en_core_web_sm`) are trained on
    general-domain corpora (Ontonotes 5 / web text). They extract general entities
    like ORG, GPE, PERSON, LOC, PRODUCT, and DATE. Pretrained NER models DO NOT
    reliably identify technical skills automatically; domain-specific technical
    skills are extracted using deterministic phrase matching in
    `src.skills.skill_extractor.SkillExtractor`.
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import spacy
from spacy.language import Language

# Console encoding safety for Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger(__name__)

#: Default spaCy model used for general entity recognition.
DEFAULT_SPACY_MODEL = "en_core_web_sm"

#: Relevant entity labels extracted from job descriptions.
RELEVANT_ENTITY_LABELS: Set[str] = {
    "ORG",      # Companies, agencies, institutions (e.g. Microsoft, Google)
    "GPE",      # Countries, cities, states (e.g. Redmond, Dublin, Ireland)
    "LOC",      # Non-GPE locations, mountain ranges, bodies of water
    "PERSON",   # People, including fictional
    "PRODUCT",  # Objects, vehicles, foods, branded products
    "NORP",     # Nationalities or religious or political groups
    "FAC",      # Buildings, airports, highways, bridges
    "DATE",     # Absolute or relative dates or periods
}


class ModelNotFoundError(RuntimeError):
    """Raised when the requested spaCy language model is not installed."""
    pass


def load_spacy_model(
    model_name: str = DEFAULT_SPACY_MODEL,
    disable: Optional[List[str]] = None,
) -> Language:
    """Loads a spaCy language model with actionable error reporting if absent.

    Args:
        model_name: Name or path of the spaCy model (default: "en_core_web_sm").
        disable: Optional list of pipeline components to disable for performance.

    Returns:
        Loaded spaCy `Language` pipeline.

    Raises:
        ModelNotFoundError: If the model cannot be loaded, providing exact
            installation instructions.
    """
    disable_components = disable or []
    try:
        nlp = spacy.load(model_name, disable=disable_components)
        logger.debug("Successfully loaded spaCy model: %s", model_name)
        return nlp
    except (OSError, IOError) as exc:
        msg = (
            f"spaCy language model '{model_name}' is not installed or could not be loaded.\n"
            f"To install the required model, run:\n"
            f"    python -m spacy download {model_name}\n"
            f"Original error: {exc}"
        )
        logger.error(msg)
        raise ModelNotFoundError(msg) from exc


class NamedEntityExtractor:
    """Extracts named entities from job description texts using spaCy.

    Identifies standard entities (ORG, GPE, LOC, PERSON, PRODUCT, etc.)
    and returns structured, deduplicated entity records.
    """

    def __init__(
        self,
        nlp: Optional[Language] = None,
        model_name: str = DEFAULT_SPACY_MODEL,
        allowed_labels: Optional[Set[str]] = None,
    ) -> None:
        """Initializes the entity extractor.

        Args:
            nlp: Optional preloaded spaCy Language pipeline. If None, loads `model_name`.
            model_name: Model name to load if `nlp` is not provided.
            allowed_labels: Set of entity labels to retain. Defaults to `RELEVANT_ENTITY_LABELS`.
        """
        if nlp is not None:
            self.nlp = nlp
        else:
            self.nlp = load_spacy_model(model_name)

        self.allowed_labels = allowed_labels if allowed_labels is not None else RELEVANT_ENTITY_LABELS

    def extract_entities(self, text: Any) -> List[Dict[str, str]]:
        """Extracts deduplicated named entities from a job description or text string.

        Args:
            text: Input string or value (str, None, NaN).

        Returns:
            List of dictionaries, each with 'text' and 'label' keys:
                [{'text': 'Microsoft', 'label': 'ORG'}, ...]
            Returns an empty list for empty, whitespace, or null inputs.
        """
        if text is None:
            return []

        text_str = str(text).strip()
        if not text_str:
            return []

        doc = self.nlp(text_str)

        entities: List[Dict[str, str]] = []
        seen_entity_keys: Set[Tuple[str, str]] = set()

        for ent in doc.ents:
            cleaned_text = ent.text.strip()
            label = ent.label_

            if not cleaned_text:
                continue

            if self.allowed_labels and label not in self.allowed_labels:
                continue

            # Deduplicate by lowercase text + label, preserving first occurrence casing
            dedup_key = (cleaned_text.lower(), label)
            if dedup_key not in seen_entity_keys:
                seen_entity_keys.add(dedup_key)
                entities.append({
                    "text": cleaned_text,
                    "label": label,
                })

        return entities

    def get_entity_counts(self, entities: List[Dict[str, str]]) -> Dict[str, int]:
        """Calculates frequency counts of entity labels in a list of entities.

        Args:
            entities: Output of :meth:`extract_entities`.

        Returns:
            Dictionary mapping entity label to count, e.g. {'ORG': 2, 'GPE': 1}.
        """
        counts: Dict[str, int] = {}
        for ent in entities:
            label = ent.get("label", "UNKNOWN")
            counts[label] = counts.get(label, 0) + 1
        return counts
