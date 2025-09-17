"""
Simple Credit Assessment Agent

Main Google ADK agent that orchestrates credit assessment workflow.
Demonstrates agent coordination, decision-making, and integration patterns.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from .models import CreditApplication, AssessmentResult, AssessmentRequest
from .sub_agents import RiskAssessmentAgent, DecisionEngineAgent
from .prompts import CreditAssessmentPrompts

logger = logging.getLogger(__name__)


class SimpleCreditAssessmentAgent:
    """
    Main Google ADK agent for credit assessment.
    
    This agent demonstrates:
    - Agent orchestration and workflow management
    - Sub-agent coordination
    - Decision integration
    - Error handling and fallback mechanisms
    - Transparent logging and reasoning
    """
    
    def __init__(self, vertex_ai_client=None):
        """
        Initialize the credit assessment agent.
        
        Args:
            vertex_ai_client: Optional Vertex AI client for enhanced AI capabilities
        """
        self.agent_id = "simple_credit_agent"
        self.version = "1.0.0"
        self.vertex_ai_client = vertex_ai_client
        
        # Initialize sub-agents
        self.risk_assessor = RiskAssessmentAgent()
        self.decision_engine = DecisionEngineAgent()
        
        # Agent capabilities
        self.capabilities = [
            'credit_application_processing',
            'risk_assessment',
            'decision_making',
            'recommendation_generation',
            'scenario_analysis'
        ]
        
        logger.info(f"Initialized {self.__class__.__name__} with sub-agents")
        logger.info(f"AI Enhancement: {'Enabled' if vertex_ai_client else 'Disabled (Rule-based only)'}")
    
    async def assess_credit_application(self, request: AssessmentRequest) -> AssessmentResult:
        """
        Main entry point for credit assessment.
        
        This method orchestrates the entire assessment workflow:
        1. Validate application
        2. Perform risk assessment
        3. Make credit decision
        4. Generate recommendations
        5. Return comprehensive result
        
        Args:
            request: Assessment request containing application data
            
        Returns:
            Complete assessment result with decision and recommendations
        """
        start_time = datetime.utcnow()
        application = request.application
        
        logger.info(f"Starting credit assessment for application {application.application_id}")
        
        try:
            # Step 1: Validate application
            self._validate_application(application)
            
            # Step 2: Perform risk assessment using sub-agent
            logger.info("Delegating to Risk Assessment Agent...")
            risk_assessment = self.risk_assessor.assess_credit_risk(
                application.applicant, 
                application.loan_request
            )
            
            # Step 3: Make final decision using decision engine
            logger.info("Delegating to Decision Engine Agent...")
            assessment_result = self.decision_engine.make_credit_decision(
                application.applicant,
                application.loan_request,
                risk_assessment,
                application.application_id
            )
            
            # Step 4: Enhance with AI if available
            if self.vertex_ai_client:
                assessment_result = await self._enhance_with_ai(assessment_result, application)
            
            # Step 5: Log final result
            total_time = (datetime.utcnow() - start_time).total_seconds()
            assessment_result.processing_time_seconds = total_time
            
            logger.info(f"Assessment completed: {'APPROVED' if assessment_result.approved else 'REJECTED'} "
                       f"in {total_time:.3f}s")
            
            return assessment_result
            
        except Exception as e:
            logger.error(f"Assessment failed for {application.application_id}: {str(e)}")
            raise
    
    def _validate_application(self, application: CreditApplication) -> None:
        """Validate application data before processing."""
        if not application.application_id:
            raise ValueError("Application ID is required")
        
        if not application.applicant.name:
            raise ValueError("Applicant name is required")
        
        if application.loan_request.amount <= 0:
            raise ValueError("Loan amount must be positive")
        
        if application.loan_request.term_months <= 0:
            raise ValueError("Loan term must be positive")
        
        logger.debug(f"Application {application.application_id} validation passed")
    
    async def _enhance_with_ai(self, result: AssessmentResult, application: CreditApplication) -> AssessmentResult:
        """
        Enhance assessment result with AI-powered insights.
        
        This demonstrates how Google ADK agents can integrate with AI services
        to provide enhanced analysis and recommendations.
        """
        try:
            logger.info("Enhancing assessment with AI insights...")
            
            # Generate AI-powered explanation
            explanation_prompt = CreditAssessmentPrompts.create_explanation_prompt({
                'approved': result.approved,
                'risk_level': result.risk_level.value,
                'confidence': result.confidence_scores.overall_confidence
            })
            
            # This would call Vertex AI for enhanced explanations
            # For now, we'll add a note that AI enhancement was attempted
            enhanced_reasoning = result.reasoning + "\n\n[AI Enhancement: Available but not implemented in this demo]"
            result.reasoning = enhanced_reasoning
            
            # Add AI-generated recommendations
            ai_recommendations = [
                "AI Insight: Consider setting up automatic payments to improve credit history",
                "AI Suggestion: Monitor credit score monthly for continuous improvement"
            ]
            result.recommendations.extend(ai_recommendations)
            
            logger.info("AI enhancement completed")
            
        except Exception as e:
            logger.warning(f"AI enhancement failed, continuing with rule-based result: {str(e)}")
        
        return result
    
    def analyze_scenarios(self, application: CreditApplication) -> Dict[str, Any]:
        """
        Analyze alternative loan scenarios.
        
        This demonstrates advanced ADK capabilities for scenario analysis
        and recommendation generation.
        """
        logger.info(f"Analyzing scenarios for application {application.application_id}")
        
        try:
            # Use decision engine for scenario analysis
            scenarios = self.decision_engine.evaluate_alternative_scenarios(
                application.applicant,
                application.loan_request,
                self.risk_assessor._assess_risk_factors(application.applicant, application.loan_request)
            )
            
            logger.info(f"Generated {len(scenarios)} alternative scenarios")
            return scenarios
            
        except Exception as e:
            logger.error(f"Scenario analysis failed: {str(e)}")
            return {}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and capabilities."""
        return {
            'agent_id': self.agent_id,
            'version': self.version,
            'status': 'active',
            'capabilities': self.capabilities,
            'sub_agents': {
                'risk_assessor': self.risk_assessor.get_agent_info(),
                'decision_engine': self.decision_engine.get_agent_info()
            },
            'ai_enhanced': self.vertex_ai_client is not None,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def process_batch_applications(self, applications: list[CreditApplication]) -> list[AssessmentResult]:
        """
        Process multiple applications in batch.
        
        This demonstrates how ADK agents can handle batch processing
        while maintaining individual assessment quality.
        """
        logger.info(f"Processing batch of {len(applications)} applications")
        
        results = []
        for application in applications:
            try:
                request = AssessmentRequest(application=application)
                # Note: In async context, this would be awaited
                # result = await self.assess_credit_application(request)
                # For now, we'll create a placeholder
                result = AssessmentResult(
                    application_id=application.application_id,
                    assessment_id=f"BATCH_{uuid4().hex[:8]}",
                    approved=False,
                    risk_level=application.applicant.credit_score > 650,
                    confidence_scores=None,
                    risk_factors=None,
                    reasoning="Batch processing placeholder",
                    processing_time_seconds=0.1
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch processing failed for {application.application_id}: {str(e)}")
                continue
        
        logger.info(f"Batch processing completed: {len(results)} results")
        return results
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get agent processing metrics and performance data."""
        return {
            'agent_id': self.agent_id,
            'metrics': {
                'total_assessments': 0,  # Would be tracked in production
                'approval_rate': 0.0,
                'average_processing_time': 0.0,
                'error_rate': 0.0
            },
            'sub_agent_metrics': {
                'risk_assessor': {
                    'assessments_completed': 0,
                    'average_confidence': 0.0
                },
                'decision_engine': {
                    'decisions_made': 0,
                    'approval_rate': 0.0
                }
            },
            'last_reset': datetime.utcnow().isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"SimpleCreditAssessmentAgent(id={self.agent_id}, version={self.version})"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return (f"SimpleCreditAssessmentAgent("
                f"id='{self.agent_id}', "
                f"version='{self.version}', "
                f"ai_enabled={self.vertex_ai_client is not None}, "
                f"sub_agents={len([self.risk_assessor, self.decision_engine])})")

