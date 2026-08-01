from dataclasses import dataclass, field
import re
from typing import List, Optional, Tuple

from app.config import settings
from app.templates.loader import TemplateLoader, default_template_loader
from app.templates.schemas import TemplateDefinition


@dataclass
class MatchResult:
    template: Optional[TemplateDefinition]
    score: float
    matched_signals: List[str] = field(default_factory=list)
    missing_required_signals: List[str] = field(default_factory=list)
    alternatives: List[Tuple[TemplateDefinition, float]] = field(default_factory=list)


class TemplateMatcher:
    def __init__(self, template_loader: Optional[TemplateLoader] = None):
        self.loader = template_loader or default_template_loader

    def match(self, ocr_text: str, ocr_confidence: float = 1.0) -> MatchResult:
        if not ocr_text or not ocr_text.strip():
            return MatchResult(template=None, score=0.0)

        normalized_text = ocr_text.upper()
        templates = self.loader.list_templates()

        scores: List[Tuple[TemplateDefinition, float, List[str], List[str]]] = []

        for tpl in templates:
            score, matched, missing = self.score_template(tpl, normalized_text, ocr_confidence)
            scores.append((tpl, score, matched, missing))

        # Sort by score descending then template priority
        scores.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        if not scores:
            return MatchResult(template=None, score=0.0)

        best_tpl, best_score, best_matched, best_missing = scores[0]

        alternatives = [
            (item[0], item[1]) for item in scores[1:] if item[1] >= settings.MIN_TEMPLATE_CONFIDENCE
        ]

        if best_score < settings.MIN_TEMPLATE_CONFIDENCE:
            return MatchResult(
                template=None,
                score=best_score,
                matched_signals=best_matched,
                missing_required_signals=best_missing,
                alternatives=[(item[0], item[1]) for item in scores[:5]]
            )

        return MatchResult(
            template=best_tpl,
            score=best_score,
            matched_signals=best_matched,
            missing_required_signals=best_missing,
            alternatives=alternatives[:3]
        )

    def score_template(
        self, tpl: TemplateDefinition, text_upper: str, ocr_confidence: float
    ) -> Tuple[float, List[str], List[str]]:
        matched_signals: List[str] = []
        missing_required: List[str] = []

        # 1. Required keywords
        req_matched = 0
        for kw in tpl.required_keywords:
            if kw.upper() in text_upper:
                req_matched += 1
                matched_signals.append(f"required:{kw}")
            else:
                missing_required.append(f"required:{kw}")

        # If missing required keywords, heavy penalty
        if tpl.required_keywords:
            req_coverage = req_matched / float(len(tpl.required_keywords))
        else:
            req_coverage = 1.0

        if req_coverage < 1.0:
            req_penalty = (1.0 - req_coverage) * 0.5
        else:
            req_penalty = 0.0

        # 2. Excluded keywords penalty
        excluded_found = False
        for kw in tpl.excluded_keywords:
            if kw.upper() in text_upper:
                excluded_found = True
                matched_signals.append(f"excluded_penalty:{kw}")

        if excluded_found:
            return 0.0, matched_signals, missing_required

        # 3. Optional keywords
        opt_matched = 0
        for kw in tpl.optional_keywords:
            if kw.upper() in text_upper:
                opt_matched += 1
                matched_signals.append(f"optional:{kw}")

        opt_score = (opt_matched / float(len(tpl.optional_keywords))) if tpl.optional_keywords else 0.0

        # 4. Regex indicators
        regex_matched = 0
        for pattern in tpl.regex_indicators:
            try:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    regex_matched += 1
                    matched_signals.append(f"regex:{pattern}")
            except Exception:
                pass

        regex_score = (regex_matched / float(len(tpl.regex_indicators))) if tpl.regex_indicators else 0.0

        # Combine component scores weighted
        # Required keyword score: 0.5, Regex indicators: 0.3, Optional keywords: 0.2
        composite = (req_coverage * 0.50) + (regex_score * 0.30) + (opt_score * 0.20)
        composite = composite - req_penalty

        # Multiply by OCR quality confidence scaling (min factor 0.85 to avoid over-penalty)
        ocr_factor = max(0.85, min(1.0, ocr_confidence))
        final_score = round(max(0.0, min(1.0, composite * ocr_factor)), 2)

        return final_score, matched_signals, missing_required
