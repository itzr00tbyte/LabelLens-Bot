from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ImageRegionConfig(BaseModel):
    id: str
    label: str
    x: int
    y: int
    width: int
    height: int
    mode: str = "contain"  # "fit", "fill", "contain"
    description: Optional[str] = None


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
    reference_image_path: Optional[str] = None
    width: int = 1200
    height: int = 1800
    print_size_mm: Optional[List[int]] = None
    phash: Optional[str] = None
    required_keywords: List[str] = Field(default_factory=list)
    optional_keywords: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    regex_indicators: List[str] = Field(default_factory=list)
    minimum_score: float = 0.70
    is_official_carrier: bool = False
    fields: Dict[str, FieldExtractionRule] = Field(default_factory=dict)
    image_regions: Dict[str, ImageRegionConfig] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=lambda: ["approve", "correct", "rescan", "reject", "details"])
