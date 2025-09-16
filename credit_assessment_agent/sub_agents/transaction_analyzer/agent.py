"""
Transaction Analyzer Agent

This agent specializes in analyzing bank transaction data to assess
financial behavior and stability.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ...shared_libraries.data_models import (
    BankTransaction,
    TransactionSummary,
    AgentResponse
)
from ...shared_libraries.pdf_processor import PDFProcessor
from ...shared_libraries.vertex_ai_client import VertexAIClient
from .tools.transaction_analysis_tools import TransactionAnalysisTools

logger = logging.getLogger(__name__)


class TransactionAnalyzerAgent:
    """Agent for analyzing bank transaction data."""
    
    def __init__(
        self,
        vertex_ai_client: Optional[VertexAIClient] = None,
        pdf_processor: Optional[PDFProcessor] = None
    ):
        """
        Initialize the Transaction Analyzer Agent.
        
        Args:
            vertex_ai_client: Vertex AI client for intelligent analysis
            pdf_processor: PDF processor for bank statement extraction
        """
        self.agent_name = "TransactionAnalyzerAgent"
        self.vertex_ai_client = vertex_ai_client
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.analysis_tools = TransactionAnalysisTools()
        
        logger.info(f"Initialized {self.agent_name}")
    
    async def analyze_bank_statement_pdf(
        self,
        pdf_path: Path,
        account_holder: Optional[str] = None
    ) -> AgentResponse:
        """
        Analyze a bank statement PDF and extract transaction insights.
        
        Args:
            pdf_path: Path to the bank statement PDF
            account_holder: Optional account holder name for validation
            
        Returns:
            Agent response with transaction analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting PDF analysis for {pdf_path}")
            
            # Extract transactions from PDF
            transactions = await self.pdf_processor.extract_transactions_from_pdf(
                pdf_path, account_holder
            )
            
            if not transactions:
                return AgentResponse(
                    agent_name=self.agent_name,
                    success=False,
                    message="No transactions found in PDF",
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            # Generate transaction summary
            transaction_summary = self.pdf_processor.generate_transaction_summary(transactions)
            
            # Perform AI-powered analysis if available
            ai_insights = {}
            if self.vertex_ai_client:
                ai_insights = await self.vertex_ai_client.analyze_transaction_patterns(transactions)
            
            # Combine analysis results
            analysis_data = {
                "transactions_count": len(transactions),
                "transaction_summary": transaction_summary.dict(),
                "ai_insights": ai_insights,
                "transactions": [tx.dict() for tx in transactions[:50]]  # Limit for response size
            }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                message=f"Successfully analyzed {len(transactions)} transactions",
                data=analysis_data,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze PDF {pdf_path}: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                message=f"PDF analysis failed: {str(e)}",
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def analyze_transaction_list(
        self,
        transactions: List[BankTransaction],
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Analyze a list of bank transactions.
        
        Args:
            transactions: List of bank transactions to analyze
            analysis_context: Optional context for analysis
            
        Returns:
            Agent response with transaction analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Analyzing {len(transactions)} transactions")
            
            if not transactions:
                return AgentResponse(
                    agent_name=self.agent_name,
                    success=False,
                    message="No transactions provided for analysis"
                )
            
            # Generate transaction summary
            transaction_summary = self.pdf_processor.generate_transaction_summary(transactions)
            
            # Perform detailed analysis
            detailed_analysis = await self._perform_detailed_analysis(
                transactions, transaction_summary, analysis_context
            )
            
            # AI-powered insights
            ai_insights = {}
            if self.vertex_ai_client:
                ai_insights = await self.vertex_ai_client.analyze_transaction_patterns(transactions)
            
            analysis_data = {
                "transaction_summary": transaction_summary.dict(),
                "detailed_analysis": detailed_analysis,
                "ai_insights": ai_insights,
                "risk_indicators": self._identify_risk_indicators(transactions, transaction_summary)
            }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                message=f"Successfully analyzed {len(transactions)} transactions",
                data=analysis_data,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze transactions: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                message=f"Transaction analysis failed: {str(e)}",
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _perform_detailed_analysis(
        self,
        transactions: List[BankTransaction],
        summary: TransactionSummary,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform detailed transaction analysis."""
        try:
            analysis = {}
            
            # Cash flow analysis
            analysis["cash_flow"] = self.analysis_tools.analyze_cash_flow(transactions)
            
            # Spending pattern analysis
            analysis["spending_patterns"] = self.analysis_tools.analyze_spending_patterns(transactions)
            
            # Income pattern analysis
            analysis["income_patterns"] = self.analysis_tools.analyze_income_patterns(transactions)
            
            # Financial behavior analysis
            analysis["financial_behavior"] = self.analysis_tools.analyze_financial_behavior(
                transactions, summary
            )
            
            # Seasonal analysis
            analysis["seasonal_trends"] = self.analysis_tools.analyze_seasonal_trends(transactions)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed detailed analysis: {str(e)}")
            return {"error": str(e)}
    
    def _identify_risk_indicators(
        self,
        transactions: List[BankTransaction],
        summary: TransactionSummary
    ) -> List[Dict[str, Any]]:
        """Identify potential risk indicators from transactions."""
        risk_indicators = []
        
        try:
            # High overdraft frequency
            if summary.overdraft_incidents > 3:
                risk_indicators.append({
                    "type": "frequent_overdrafts",
                    "severity": "high" if summary.overdraft_incidents > 10 else "medium",
                    "description": f"{summary.overdraft_incidents} overdraft incidents detected",
                    "impact": "Indicates poor cash flow management"
                })
            
            # Irregular income
            if summary.income_stability_score < 0.6:
                risk_indicators.append({
                    "type": "irregular_income",
                    "severity": "high" if summary.income_stability_score < 0.4 else "medium",
                    "description": f"Income stability score: {summary.income_stability_score:.2f}",
                    "impact": "Unpredictable income may affect loan repayment ability"
                })
            
            # High expense-to-income ratio
            if summary.average_monthly_expenses > 0:
                expense_ratio = float(
                    summary.average_monthly_expenses / 
                    max(summary.average_monthly_income, summary.average_monthly_expenses)
                )
                if expense_ratio > 0.8:
                    risk_indicators.append({
                        "type": "high_expense_ratio",
                        "severity": "high" if expense_ratio > 0.9 else "medium",
                        "description": f"Expense-to-income ratio: {expense_ratio:.1%}",
                        "impact": "High expenses relative to income may strain finances"
                    })
            
            # Large transaction frequency
            large_tx_threshold = summary.average_monthly_income * 0.5
            large_transactions = [
                tx for tx in transactions 
                if tx.amount > large_tx_threshold
            ]
            
            if len(large_transactions) > 5:
                risk_indicators.append({
                    "type": "frequent_large_transactions",
                    "severity": "medium",
                    "description": f"{len(large_transactions)} large transactions detected",
                    "impact": "May indicate irregular spending patterns"
                })
            
            return risk_indicators
            
        except Exception as e:
            logger.error(f"Failed to identify risk indicators: {str(e)}")
            return []
    
    async def generate_transaction_report(
        self,
        transactions: List[BankTransaction],
        include_ai_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive transaction analysis report.
        
        Args:
            transactions: List of transactions to analyze
            include_ai_insights: Whether to include AI-powered insights
            
        Returns:
            Comprehensive transaction report
        """
        try:
            # Basic analysis
            summary = self.pdf_processor.generate_transaction_summary(transactions)
            
            # Detailed analysis
            detailed_analysis = await self._perform_detailed_analysis(transactions, summary)
            
            # Risk indicators
            risk_indicators = self._identify_risk_indicators(transactions, summary)
            
            # AI insights
            ai_insights = {}
            if include_ai_insights and self.vertex_ai_client:
                ai_insights = await self.vertex_ai_client.analyze_transaction_patterns(transactions)
            
            report = {
                "report_generated_at": datetime.utcnow().isoformat(),
                "analysis_period": {
                    "months": summary.analysis_period_months,
                    "transaction_count": len(transactions)
                },
                "summary": summary.dict(),
                "detailed_analysis": detailed_analysis,
                "risk_indicators": risk_indicators,
                "ai_insights": ai_insights,
                "recommendations": self._generate_recommendations(summary, risk_indicators)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate transaction report: {str(e)}")
            return {"error": str(e)}
    
    def _generate_recommendations(
        self,
        summary: TransactionSummary,
        risk_indicators: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on transaction analysis."""
        recommendations = []
        
        try:
            # Income stability recommendations
            if summary.income_stability_score < 0.7:
                recommendations.append(
                    "Consider diversifying income sources to improve financial stability"
                )
            
            # Overdraft recommendations
            if summary.overdraft_incidents > 0:
                recommendations.append(
                    "Set up account alerts to avoid overdraft fees and improve cash flow management"
                )
            
            # Expense management recommendations
            if summary.average_monthly_expenses > summary.average_monthly_income * 0.8:
                recommendations.append(
                    "Review and optimize monthly expenses to improve debt-to-income ratio"
                )
            
            # Savings recommendations
            savings_rate = 1.0 - float(
                summary.average_monthly_expenses / 
                max(summary.average_monthly_income, summary.average_monthly_expenses)
            )
            if savings_rate < 0.1:
                recommendations.append(
                    "Establish an emergency fund by saving at least 10% of monthly income"
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return ["Unable to generate recommendations due to analysis error"]
