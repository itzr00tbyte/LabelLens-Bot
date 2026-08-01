from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FieldExtractionRule(BaseModel):
    type: str  # "constant", "regex", "anchored_text", "anchored_block"
    value: Optional[str] = None
    patterns: Optional[List[str]] = None
    anchor: Optional[str] = None
    required: bool = False
    normalize: Optional[str] = None  # "digits_only", "currency", "date", "uppercase"


class TemplateDefinition(BaseModel):
    id: str
    name: str
    category: str
    version: int = 1
    priority: int = 100
    enabled: bool = True
    required_keywords: List[str] = Field(default_factory=list)
    optional_keywords: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    regex_indicators: List[str] = Field(default_factory=list)
    minimum_score: float = 0.72
    fields: Dict[str, FieldExtractionRule] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=lambda: ["approve", "correct", "rescan", "reject", "details"])
