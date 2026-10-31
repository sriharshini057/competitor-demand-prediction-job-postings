"""Skill Extraction and Named Entity Recognition package.

Stage 4: spaCy-based Named Entity Recognition (NER) and deterministic
Skill Extraction and Normalization.
"""

from src.skills.extractor import (
    DEFAULT_INPUT_FILE,
    DEFAULT_OUTPUT_FILE,
    build_skills_features,
    format_job_text,
    run_skills_pipeline,
    save_skills_dataset,
    validate_skills_output,
)
from src.skills.ner_extractor import (
    DEFAULT_SPACY_MODEL,
    ModelNotFoundError,
    NamedEntityExtractor,
    RELEVANT_ENTITY_LABELS,
    load_spacy_model,
)
from src.skills.skill_extractor import (
    CANONICAL_SKILL_ALIASES,
    SKILL_TAXONOMY,
    SKILL_TO_CATEGORY,
    SkillExtractor,
)

__all__ = [
    "NamedEntityExtractor",
    "SkillExtractor",
    "load_spacy_model",
    "ModelNotFoundError",
    "build_skills_features",
    "run_skills_pipeline",
    "validate_skills_output",
    "save_skills_dataset",
    "format_job_text",
    "SKILL_TAXONOMY",
    "CANONICAL_SKILL_ALIASES",
    "SKILL_TO_CATEGORY",
    "DEFAULT_SPACY_MODEL",
    "RELEVANT_ENTITY_LABELS",
    "DEFAULT_INPUT_FILE",
    "DEFAULT_OUTPUT_FILE",
]
