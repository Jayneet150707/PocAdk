"""
FastAPI dependencies for Credit Assessment Agent API.

This module provides dependency injection for the API endpoints.
"""

from fastapi import Depends, HTTPException
from fastapi.requests import Request

from credit_assessment_agent import CreditAssessmentAgent
from credit_assessment_agent.shared_libraries.vertex_ai_client import VertexAIClient


def get_vertex_ai_client(request: Request) -> VertexAIClient:
    """
    Get Vertex AI client from application state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        VertexAIClient instance
        
    Raises:
        HTTPException: If Vertex AI client is not available
    """
    vertex_client = getattr(request.app.state, 'vertex_client', None)
    if vertex_client is None:
        raise HTTPException(
            status_code=503,
            detail="Vertex AI service is not available"
        )
    return vertex_client


def get_credit_agent(request: Request) -> CreditAssessmentAgent:
    """
    Get Credit Assessment Agent from application state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        CreditAssessmentAgent instance
        
    Raises:
        HTTPException: If credit agent is not available
    """
    credit_agent = getattr(request.app.state, 'credit_agent', None)
    if credit_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Credit Assessment Agent is not available"
        )
    return credit_agent
