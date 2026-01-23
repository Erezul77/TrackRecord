# TR Prediction Index - Scoring System
# =====================================
# A proprietary scoring methodology for evaluating prediction quality
#
# Components:
#   - Specificity (35 pts, min 15): How concrete and measurable is the claim?
#   - Verifiability (25 pts, min 10): Can we objectively verify the outcome?
#   - Boldness (20 pts): How contrarian/against-consensus is this?
#   - Relevance (15 pts, min 5): Time horizon (shorter = more relevant)
#   - Stakes (5 pts): How significant if true?
#
# Gate Logic: Must pass ALL minimums AND total >= 40 to be tracked

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class RejectionReason(Enum):
    TOO_VAGUE = "Prediction is too vague - needs specific, measurable outcomes"
    NOT_VERIFIABLE = "Cannot objectively verify outcome"
    TOO_FAR_OUT = "Timeframe exceeds 12 months - not relevant for tracking"
    BELOW_MINIMUM = "Total score below minimum threshold (40)"


@dataclass
class TRIndexScore:
    """Complete TR Index scoring breakdown"""
    specificity: float  # 0-35
    verifiability: float  # 0-25
    boldness: float  # 0-20
    relevance: float  # 0-15
    stakes: float  # 0-5
    total: float  # 0-100
    passed: bool
    rejection_reason: Optional[str] = None
    
    @property
    def tier(self) -> str:
        """Returns the tier based on total score"""
        if not self.passed:
            return "rejected"
        if self.total >= 80:
            return "gold"
        if self.total >= 60:
            return "silver"
        return "bronze"


def calculate_relevance_score(prediction_date: datetime, timeframe: datetime) -> float:
    """
    Calculate relevance score based on time horizon.
    Shorter timeframes = higher scores (more relevant, more testable)
    
    Scoring:
        0-3 months: 15 (max)
        3-6 months: 12
        6-12 months: 9
        1-2 years: 6
        2-5 years: 5 (minimum passing)
        5+ years: 0 (rejected)
    """
    days_until = (timeframe - prediction_date).days
    
    if days_until < 0:
        # Already past - might be historical data, give benefit of doubt
        return 10.0
    
    months = days_until / 30.0
    
    if months <= 3:
        return 15.0
    elif months <= 6:
        return 12.0
    elif months <= 12:
        return 9.0
    elif months <= 24:
        return 6.0
    elif months <= 60:
        return 5.0  # Minimum passing
    else:
        return 0.0  # Rejected - too far out (5+ years)


def calculate_specificity_score(
    has_specific_number: bool = False,
    has_specific_date: bool = False,
    has_clear_condition: bool = False,
    has_measurable_outcome: bool = False,
    is_binary: bool = False
) -> float:
    """
    Calculate specificity score (0-35).
    
    Factors:
        - Has specific number/target (e.g., "$100k", "50%"): +10
        - Has specific date/timeframe: +8
        - Has clear condition/trigger: +7
        - Has measurable outcome: +7
        - Is binary (yes/no verifiable): +3
    """
    score = 0.0
    
    if has_specific_number:
        score += 10.0
    if has_specific_date:
        score += 8.0
    if has_clear_condition:
        score += 7.0
    if has_measurable_outcome:
        score += 7.0
    if is_binary:
        score += 3.0
    
    return min(score, 35.0)


def calculate_verifiability_score(
    has_public_data_source: bool = False,
    outcome_is_objective: bool = False,
    no_subjective_interpretation: bool = False,
    has_clear_resolution_criteria: bool = False
) -> float:
    """
    Calculate verifiability score (0-25).
    
    Factors:
        - Has public data source to verify: +8
        - Outcome is objective (not opinion-based): +7
        - No subjective interpretation needed: +5
        - Has clear resolution criteria: +5
    """
    score = 0.0
    
    if has_public_data_source:
        score += 8.0
    if outcome_is_objective:
        score += 7.0
    if no_subjective_interpretation:
        score += 5.0
    if has_clear_resolution_criteria:
        score += 5.0
    
    return min(score, 25.0)


def calculate_boldness_score(
    against_consensus: bool = False,
    minority_opinion: bool = False,
    predicts_unexpected: bool = False,
    high_confidence_stated: bool = False
) -> float:
    """
    Calculate boldness/contrarian score (0-20).
    
    Factors:
        - Goes against current consensus: +8
        - Minority opinion in expert community: +5
        - Predicts unexpected outcome: +4
        - High confidence stated publicly: +3
    """
    score = 0.0
    
    if against_consensus:
        score += 8.0
    if minority_opinion:
        score += 5.0
    if predicts_unexpected:
        score += 4.0
    if high_confidence_stated:
        score += 3.0
    
    return min(score, 20.0)


def calculate_stakes_score(
    major_market_impact: bool = False,
    affects_many_people: bool = False,
    significant_if_true: bool = False
) -> float:
    """
    Calculate stakes/impact score (0-5).
    
    Factors:
        - Would have major market impact: +2
        - Affects many people/institutions: +2
        - Would be significant news if true: +1
    """
    score = 0.0
    
    if major_market_impact:
        score += 2.0
    if affects_many_people:
        score += 2.0
    if significant_if_true:
        score += 1.0
    
    return min(score, 5.0)


def calculate_tr_index(
    prediction_date: datetime,
    timeframe: datetime,
    # Specificity factors
    has_specific_number: bool = False,
    has_specific_date: bool = False,
    has_clear_condition: bool = False,
    has_measurable_outcome: bool = False,
    is_binary: bool = False,
    # Verifiability factors
    has_public_data_source: bool = False,
    outcome_is_objective: bool = False,
    no_subjective_interpretation: bool = False,
    has_clear_resolution_criteria: bool = False,
    # Boldness factors
    against_consensus: bool = False,
    minority_opinion: bool = False,
    predicts_unexpected: bool = False,
    high_confidence_stated: bool = False,
    # Stakes factors
    major_market_impact: bool = False,
    affects_many_people: bool = False,
    significant_if_true: bool = False
) -> TRIndexScore:
    """
    Calculate complete TR Prediction Index score.
    
    Gate Logic:
        1. Specificity must be >= 15
        2. Verifiability must be >= 10
        3. Relevance must be >= 5 (timeframe <= 12 months)
        4. Total must be >= 40
    """
    
    # Calculate individual scores
    specificity = calculate_specificity_score(
        has_specific_number, has_specific_date, has_clear_condition,
        has_measurable_outcome, is_binary
    )
    
    verifiability = calculate_verifiability_score(
        has_public_data_source, outcome_is_objective,
        no_subjective_interpretation, has_clear_resolution_criteria
    )
    
    boldness = calculate_boldness_score(
        against_consensus, minority_opinion,
        predicts_unexpected, high_confidence_stated
    )
    
    relevance = calculate_relevance_score(prediction_date, timeframe)
    
    stakes = calculate_stakes_score(
        major_market_impact, affects_many_people, significant_if_true
    )
    
    total = specificity + verifiability + boldness + relevance + stakes
    
    # Gate checks
    passed = True
    rejection_reason = None
    
    if specificity < 15:
        passed = False
        rejection_reason = RejectionReason.TOO_VAGUE.value
    elif verifiability < 10:
        passed = False
        rejection_reason = RejectionReason.NOT_VERIFIABLE.value
    elif relevance < 5:
        passed = False
        rejection_reason = RejectionReason.TOO_FAR_OUT.value
    elif total < 40:
        passed = False
        rejection_reason = RejectionReason.BELOW_MINIMUM.value
    
    return TRIndexScore(
        specificity=specificity,
        verifiability=verifiability,
        boldness=boldness,
        relevance=relevance,
        stakes=stakes,
        total=total,
        passed=passed,
        rejection_reason=rejection_reason
    )


# Quick scoring for admin panel - simplified interface
def quick_score(
    prediction_date: datetime,
    timeframe: datetime,
    specificity_level: int,  # 1-5 (1=vague, 5=very specific)
    verifiability_level: int,  # 1-5 (1=hard to verify, 5=easily verified)
    boldness_level: int,  # 1-5 (1=consensus, 5=very contrarian)
    stakes_level: int  # 1-5 (1=minor, 5=major impact)
) -> TRIndexScore:
    """
    Simplified scoring interface for manual entry.
    Uses 1-5 scale inputs and converts to detailed scores.
    """
    
    # Convert 1-5 scale to actual scores
    specificity_map = {
        1: (False, False, False, False, False),  # ~7 pts
        2: (False, False, True, False, False),   # ~14 pts
        3: (False, True, True, True, False),     # ~22 pts (passes min)
        4: (True, True, True, True, False),      # ~32 pts
        5: (True, True, True, True, True),       # ~35 pts (max)
    }
    
    verifiability_map = {
        1: (False, False, False, False),  # ~0 pts
        2: (True, False, False, False),   # ~8 pts
        3: (True, True, False, False),    # ~15 pts (passes min)
        4: (True, True, True, False),     # ~20 pts
        5: (True, True, True, True),      # ~25 pts (max)
    }
    
    boldness_map = {
        1: (False, False, False, False),  # ~0 pts (consensus)
        2: (False, False, False, True),   # ~3 pts
        3: (False, False, True, True),    # ~7 pts
        4: (True, False, True, True),     # ~15 pts
        5: (True, True, True, True),      # ~20 pts (max contrarian)
    }
    
    stakes_map = {
        1: (False, False, False),  # ~0 pts
        2: (False, False, True),   # ~1 pt
        3: (True, False, True),    # ~3 pts
        4: (True, True, False),    # ~4 pts
        5: (True, True, True),     # ~5 pts (max)
    }
    
    spec = specificity_map.get(specificity_level, specificity_map[3])
    veri = verifiability_map.get(verifiability_level, verifiability_map[3])
    bold = boldness_map.get(boldness_level, boldness_map[1])
    stak = stakes_map.get(stakes_level, stakes_map[2])
    
    return calculate_tr_index(
        prediction_date=prediction_date,
        timeframe=timeframe,
        has_specific_number=spec[0],
        has_specific_date=spec[1],
        has_clear_condition=spec[2],
        has_measurable_outcome=spec[3],
        is_binary=spec[4],
        has_public_data_source=veri[0],
        outcome_is_objective=veri[1],
        no_subjective_interpretation=veri[2],
        has_clear_resolution_criteria=veri[3],
        against_consensus=bold[0],
        minority_opinion=bold[1],
        predicts_unexpected=bold[2],
        high_confidence_stated=bold[3],
        major_market_impact=stak[0],
        affects_many_people=stak[1],
        significant_if_true=stak[2]
    )
