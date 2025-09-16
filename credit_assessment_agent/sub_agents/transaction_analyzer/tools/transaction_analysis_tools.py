"""
Transaction Analysis Tools

This module provides specialized tools for analyzing bank transaction data
to extract financial insights and patterns.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from collections import defaultdict, Counter

from ....shared_libraries.data_models import BankTransaction, TransactionType, TransactionSummary

logger = logging.getLogger(__name__)


class TransactionAnalysisTools:
    """Tools for analyzing bank transaction data."""
    
    def __init__(self):
        """Initialize transaction analysis tools."""
        self.logger = logger
    
    def analyze_cash_flow(self, transactions: List[BankTransaction]) -> Dict[str, Any]:
        """
        Analyze cash flow patterns from transactions.
        
        Args:
            transactions: List of bank transactions
            
        Returns:
            Cash flow analysis results
        """
        try:
            if not transactions:
                return {"error": "No transactions provided"}
            
            # Group transactions by month
            monthly_flows = defaultdict(lambda: {"inflow": Decimal('0'), "outflow": Decimal('0')})
            
            for tx in transactions:
                month_key = f"{tx.date.year}-{tx.date.month:02d}"
                
                if tx.transaction_type == TransactionType.CREDIT:
                    monthly_flows[month_key]["inflow"] += tx.amount
                elif tx.transaction_type in [TransactionType.DEBIT, TransactionType.FEE]:
                    monthly_flows[month_key]["outflow"] += tx.amount
            
            # Calculate net flows and trends
            monthly_data = []
            for month, flows in sorted(monthly_flows.items()):
                net_flow = flows["inflow"] - flows["outflow"]
                monthly_data.append({
                    "month": month,
                    "inflow": float(flows["inflow"]),
                    "outflow": float(flows["outflow"]),
                    "net_flow": float(net_flow)
                })
            
            # Calculate overall statistics
            total_inflow = sum(data["inflow"] for data in monthly_data)
            total_outflow = sum(data["outflow"] for data in monthly_data)
            avg_monthly_net = sum(data["net_flow"] for data in monthly_data) / len(monthly_data) if monthly_data else 0
            
            return {
                "monthly_cash_flows": monthly_data,
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "average_monthly_net_flow": avg_monthly_net,
                "cash_flow_volatility": self._calculate_volatility([data["net_flow"] for data in monthly_data])
            }
            
        except Exception as e:
            logger.error(f"Cash flow analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_spending_patterns(self, transactions: List[BankTransaction]) -> Dict[str, Any]:
        """
        Analyze spending patterns and categorize expenses.
        
        Args:
            transactions: List of bank transactions
            
        Returns:
            Spending pattern analysis
        """
        try:
            if not transactions:
                return {"error": "No transactions provided"}
            
            # Filter debit transactions (expenses)
            expense_transactions = [
                tx for tx in transactions 
                if tx.transaction_type in [TransactionType.DEBIT, TransactionType.FEE]
            ]
            
            if not expense_transactions:
                return {"categories": {}, "patterns": {}}
            
            # Categorize expenses
            categories = self._categorize_expenses(expense_transactions)
            
            # Analyze spending frequency
            daily_spending = defaultdict(Decimal)
            for tx in expense_transactions:
                daily_spending[tx.date] += tx.amount
            
            # Calculate patterns
            avg_daily_spending = sum(daily_spending.values()) / len(daily_spending) if daily_spending else Decimal('0')
            max_daily_spending = max(daily_spending.values()) if daily_spending else Decimal('0')
            
            # Identify high-spending days
            high_spending_threshold = avg_daily_spending * Decimal('2')
            high_spending_days = [
                {"date": date.isoformat(), "amount": float(amount)}
                for date, amount in daily_spending.items()
                if amount > high_spending_threshold
            ]
            
            return {
                "categories": {cat: float(amount) for cat, amount in categories.items()},
                "patterns": {
                    "average_daily_spending": float(avg_daily_spending),
                    "max_daily_spending": float(max_daily_spending),
                    "high_spending_days": high_spending_days,
                    "spending_frequency": len(expense_transactions),
                    "unique_spending_days": len(daily_spending)
                }
            }
            
        except Exception as e:
            logger.error(f"Spending pattern analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_income_patterns(self, transactions: List[BankTransaction]) -> Dict[str, Any]:
        """
        Analyze income patterns and regularity.
        
        Args:
            transactions: List of bank transactions
            
        Returns:
            Income pattern analysis
        """
        try:
            if not transactions:
                return {"error": "No transactions provided"}
            
            # Filter credit transactions (income)
            income_transactions = [
                tx for tx in transactions 
                if tx.transaction_type == TransactionType.CREDIT
            ]
            
            if not income_transactions:
                return {"patterns": {}, "regularity": {}}
            
            # Group by month
            monthly_income = defaultdict(Decimal)
            for tx in income_transactions:
                month_key = f"{tx.date.year}-{tx.date.month:02d}"
                monthly_income[month_key] += tx.amount
            
            # Analyze income sources
            income_sources = self._analyze_income_sources(income_transactions)
            
            # Calculate regularity metrics
            monthly_amounts = list(monthly_income.values())
            avg_monthly_income = sum(monthly_amounts) / len(monthly_amounts) if monthly_amounts else Decimal('0')
            income_volatility = self._calculate_volatility([float(amount) for amount in monthly_amounts])
            
            # Identify regular vs irregular income
            regular_income = sum(
                amount for desc, amount in income_sources.items()
                if any(keyword in desc.lower() for keyword in ['salary', 'payroll', 'wage', 'direct deposit'])
            )
            
            return {
                "patterns": {
                    "monthly_income": {month: float(amount) for month, amount in monthly_income.items()},
                    "average_monthly_income": float(avg_monthly_income),
                    "income_volatility": income_volatility,
                    "total_income_sources": len(income_sources)
                },
                "regularity": {
                    "regular_income_amount": float(regular_income),
                    "regular_income_percentage": float(regular_income / sum(income_sources.values()) * 100) if income_sources else 0,
                    "income_frequency": len(income_transactions)
                },
                "sources": {desc: float(amount) for desc, amount in income_sources.items()}
            }
            
        except Exception as e:
            logger.error(f"Income pattern analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_financial_behavior(
        self, 
        transactions: List[BankTransaction], 
        summary: TransactionSummary
    ) -> Dict[str, Any]:
        """
        Analyze overall financial behavior patterns.
        
        Args:
            transactions: List of bank transactions
            summary: Transaction summary statistics
            
        Returns:
            Financial behavior analysis
        """
        try:
            if not transactions:
                return {"error": "No transactions provided"}
            
            # Analyze transaction timing
            transaction_times = [tx.date.weekday() for tx in transactions]
            weekday_distribution = Counter(transaction_times)
            
            # Analyze transaction amounts
            amounts = [float(tx.amount) for tx in transactions]
            
            # Identify unusual transactions
            avg_amount = sum(amounts) / len(amounts)
            large_transactions = [
                {"date": tx.date.isoformat(), "amount": float(tx.amount), "description": tx.description}
                for tx in transactions
                if float(tx.amount) > avg_amount * 3
            ]
            
            # Calculate financial health indicators
            savings_rate = self._calculate_savings_rate(summary)
            expense_stability = self._calculate_expense_stability(transactions)
            
            return {
                "transaction_patterns": {
                    "weekday_distribution": dict(weekday_distribution),
                    "average_transaction_amount": avg_amount,
                    "transaction_frequency": len(transactions) / summary.analysis_period_months if summary.analysis_period_months > 0 else 0
                },
                "unusual_activity": {
                    "large_transactions": large_transactions,
                    "large_transaction_count": len(large_transactions)
                },
                "financial_health": {
                    "savings_rate": savings_rate,
                    "expense_stability": expense_stability,
                    "income_stability": summary.income_stability_score,
                    "overdraft_frequency": summary.overdraft_incidents / summary.analysis_period_months if summary.analysis_period_months > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Financial behavior analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_seasonal_trends(self, transactions: List[BankTransaction]) -> Dict[str, Any]:
        """
        Analyze seasonal spending and income trends.
        
        Args:
            transactions: List of bank transactions
            
        Returns:
            Seasonal trend analysis
        """
        try:
            if not transactions:
                return {"error": "No transactions provided"}
            
            # Group by month of year
            monthly_spending = defaultdict(Decimal)
            monthly_income = defaultdict(Decimal)
            
            for tx in transactions:
                month = tx.date.month
                if tx.transaction_type in [TransactionType.DEBIT, TransactionType.FEE]:
                    monthly_spending[month] += tx.amount
                elif tx.transaction_type == TransactionType.CREDIT:
                    monthly_income[month] += tx.amount
            
            # Calculate seasonal patterns
            seasonal_spending = {}
            seasonal_income = {}
            
            seasons = {
                "winter": [12, 1, 2],
                "spring": [3, 4, 5],
                "summer": [6, 7, 8],
                "fall": [9, 10, 11]
            }
            
            for season, months in seasons.items():
                seasonal_spending[season] = float(sum(monthly_spending[month] for month in months))
                seasonal_income[season] = float(sum(monthly_income[month] for month in months))
            
            return {
                "monthly_trends": {
                    "spending": {str(month): float(amount) for month, amount in monthly_spending.items()},
                    "income": {str(month): float(amount) for month, amount in monthly_income.items()}
                },
                "seasonal_patterns": {
                    "spending": seasonal_spending,
                    "income": seasonal_income
                },
                "peak_spending_month": max(monthly_spending.items(), key=lambda x: x[1])[0] if monthly_spending else None,
                "peak_income_month": max(monthly_income.items(), key=lambda x: x[1])[0] if monthly_income else None
            }
            
        except Exception as e:
            logger.error(f"Seasonal trend analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _categorize_expenses(self, transactions: List[BankTransaction]) -> Dict[str, Decimal]:
        """Categorize expense transactions."""
        categories = defaultdict(Decimal)
        
        category_keywords = {
            'groceries': ['grocery', 'supermarket', 'food', 'market', 'walmart', 'target'],
            'utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'internet', 'cable'],
            'transportation': ['gas station', 'fuel', 'uber', 'taxi', 'parking', 'metro', 'bus'],
            'entertainment': ['restaurant', 'movie', 'entertainment', 'netflix', 'spotify', 'gaming'],
            'healthcare': ['pharmacy', 'medical', 'doctor', 'hospital', 'health', 'dental'],
            'shopping': ['amazon', 'store', 'retail', 'purchase', 'mall', 'shop'],
            'banking': ['fee', 'charge', 'overdraft', 'maintenance', 'atm'],
            'other': []
        }
        
        for tx in transactions:
            description_lower = tx.description.lower()
            categorized = False
            
            for category, keywords in category_keywords.items():
                if category == 'other':
                    continue
                
                if any(keyword in description_lower for keyword in keywords):
                    categories[category] += tx.amount
                    categorized = True
                    break
            
            if not categorized:
                categories['other'] += tx.amount
        
        return dict(categories)
    
    def _analyze_income_sources(self, transactions: List[BankTransaction]) -> Dict[str, Decimal]:
        """Analyze and group income sources."""
        sources = defaultdict(Decimal)
        
        for tx in transactions:
            # Simplify description for grouping
            desc = tx.description.lower().strip()
            
            # Group similar descriptions
            if any(keyword in desc for keyword in ['salary', 'payroll', 'wage']):
                sources['salary/wages'] += tx.amount
            elif any(keyword in desc for keyword in ['direct deposit', 'deposit']):
                sources['direct deposits'] += tx.amount
            elif any(keyword in desc for keyword in ['transfer', 'wire']):
                sources['transfers'] += tx.amount
            elif any(keyword in desc for keyword in ['interest', 'dividend']):
                sources['investment income'] += tx.amount
            elif any(keyword in desc for keyword in ['refund', 'return']):
                sources['refunds'] += tx.amount
            else:
                sources['other income'] += tx.amount
        
        return dict(sources)
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as volatility measure."""
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        return std_dev / abs(mean_val)
    
    def _calculate_savings_rate(self, summary: TransactionSummary) -> float:
        """Calculate savings rate from transaction summary."""
        if summary.average_monthly_income <= 0:
            return 0.0
        
        savings = summary.average_monthly_income - summary.average_monthly_expenses
        return float(savings / summary.average_monthly_income)
    
    def _calculate_expense_stability(self, transactions: List[BankTransaction]) -> float:
        """Calculate expense stability score."""
        expense_transactions = [
            tx for tx in transactions 
            if tx.transaction_type in [TransactionType.DEBIT, TransactionType.FEE]
        ]
        
        if not expense_transactions:
            return 1.0
        
        # Group by month
        monthly_expenses = defaultdict(Decimal)
        for tx in expense_transactions:
            month_key = f"{tx.date.year}-{tx.date.month:02d}"
            monthly_expenses[month_key] += tx.amount
        
        if len(monthly_expenses) < 2:
            return 1.0
        
        # Calculate coefficient of variation (inverse of stability)
        amounts = [float(amount) for amount in monthly_expenses.values()]
        volatility = self._calculate_volatility(amounts)
        
        # Convert to stability score (1.0 = very stable, 0.0 = very unstable)
        return max(0.0, 1.0 - volatility)
