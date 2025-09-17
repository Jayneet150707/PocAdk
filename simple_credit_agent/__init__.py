"""
Simple Credit Assessment Agent

A streamlined Google ADK implementation for credit assessment
that demonstrates core agent patterns and capabilities.
"""

from .agent import SimpleCreditAssessmentAgent
from .models import (
    CreditApplication, ApplicantInfo, LoanRequest, AssessmentResult,
    AssessmentRequest, AssessmentResponse, HealthStatus,
    EmploymentStatus, LoanPurpose, RiskLevel
)
from .rules import SimpleCreditRules
from .sub_agents import RiskAssessmentAgent, DecisionEngineAgent

__version__ = "1.0.0"
__all__ = [
    'SimpleCreditAssessmentAgent',
    'CreditApplication',
    'ApplicantInfo', 
    'LoanRequest',
    'AssessmentResult',
    'AssessmentRequest',
    'AssessmentResponse',
    'HealthStatus',
    'EmploymentStatus',
    'LoanPurpose',
    'RiskLevel',
    'SimpleCreditRules',
    'RiskAssessmentAgent',
    'DecisionEngineAgent'
]

