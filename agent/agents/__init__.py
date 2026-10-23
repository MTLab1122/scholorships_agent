"""Specialized Multi-Agent Modules for Student Opportunity Intelligence Platform.
Exposes all 14 modular agents.
"""

from agent.agents.discovery_agent import OpportunityDiscoveryAgent
from agent.agents.extraction_agent import OpportunityExtractionAgent
from agent.agents.classification_agent import OpportunityClassificationAgent
from agent.agents.eligibility_agent import EligibilityVerificationAgent
from agent.agents.source_verifier_agent import OfficialSourceVerificationAgent
from agent.agents.deduplicator_agent import DeduplicationAndChangeDetectionAgent
from agent.agents.semester_matching_agent import SemesterMatchingAgent
from agent.agents.recommendation_agent import PersonalizedRecommendationAgent
from agent.agents.deadline_agent import DeadlineMonitoringAgent
from agent.agents.report_agent import ReportGenerationAgent
from agent.agents.application_prep_agent import ApplicationPreparationAgent
from agent.agents.application_tracker_agent import ApplicationTrackingAgent
from agent.agents.fraud_qc_agent import FraudAndQCAgent
from agent.agents.source_coverage_agent import SourceCoverageAgent

__all__ = [
    "OpportunityDiscoveryAgent",
    "OpportunityExtractionAgent",
    "OpportunityClassificationAgent",
    "EligibilityVerificationAgent",
    "OfficialSourceVerificationAgent",
    "DeduplicationAndChangeDetectionAgent",
    "SemesterMatchingAgent",
    "PersonalizedRecommendationAgent",
    "DeadlineMonitoringAgent",
    "ReportGenerationAgent",
    "ApplicationPreparationAgent",
    "ApplicationTrackingAgent",
    "FraudAndQCAgent",
    "SourceCoverageAgent",
]
