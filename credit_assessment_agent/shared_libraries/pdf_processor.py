"""
PDF processing utilities for bank statement analysis.

This module provides functionality to extract and process bank transaction
data from PDF bank statements.
"""

import re
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

import PyPDF2
from PyPDF2 import PdfReader

from .data_models import BankTransaction, TransactionType, TransactionSummary

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes PDF bank statements to extract transaction data."""
    
    def __init__(self, max_file_size_mb: int = 10):
        """
        Initialize PDF processor.
        
        Args:
            max_file_size_mb: Maximum allowed PDF file size in MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.transaction_patterns = self._compile_transaction_patterns()
    
    def _compile_transaction_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for transaction extraction."""
        return {
            # Date patterns (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
            'date': re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})'),
            
            # Amount patterns ($1,234.56, 1234.56, -1234.56)
            'amount': re.compile(r'[-+]?\$?[\d,]+\.?\d{0,2}'),
            
            # Transaction types
            'debit_keywords': re.compile(r'\b(debit|withdrawal|payment|purchase|fee|charge)\b', re.IGNORECASE),
            'credit_keywords': re.compile(r'\b(credit|deposit|transfer in|salary|income|refund)\b', re.IGNORECASE),
            
            # Balance patterns
            'balance': re.compile(r'balance[:\s]*\$?([\d,]+\.?\d{0,2})', re.IGNORECASE),
            
            # Common transaction descriptions
            'description_clean': re.compile(r'[^\w\s\-\.]', re.IGNORECASE),
        }
    
    async def extract_transactions_from_pdf(
        self, 
        pdf_path: Path, 
        account_holder: Optional[str] = None
    ) -> List[BankTransaction]:
        """
        Extract bank transactions from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            account_holder: Optional account holder name for validation
            
        Returns:
            List of extracted bank transactions
            
        Raises:
            ValueError: If PDF is invalid or too large
            Exception: If processing fails
        """
        try:
            # Validate file size
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise ValueError(f"PDF file too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
            
            # Extract text from PDF
            text_content = await self._extract_text_from_pdf(pdf_path)
            
            # Parse transactions from text
            transactions = await self._parse_transactions_from_text(text_content)
            
            # Validate and clean transactions
            validated_transactions = self._validate_transactions(transactions)
            
            logger.info(f"Extracted {len(validated_transactions)} transactions from {pdf_path}")
            return validated_transactions
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
            raise
    
    async def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text_content = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                        continue
                
                return text_content
                
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")
    
    async def _parse_transactions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse transaction data from extracted text."""
        transactions = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:  # Skip short lines
                continue
            
            # Try to extract transaction from line
            transaction_data = self._extract_transaction_from_line(line, line_num)
            if transaction_data:
                transactions.append(transaction_data)
        
        return transactions
    
    def _extract_transaction_from_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Extract transaction data from a single line."""
        try:
            # Find date
            date_match = self.transaction_patterns['date'].search(line)
            if not date_match:
                return None
            
            transaction_date = self._parse_date(date_match.group(1))
            if not transaction_date:
                return None
            
            # Find amounts
            amount_matches = self.transaction_patterns['amount'].findall(line)
            if not amount_matches:
                return None
            
            # Parse amounts and determine transaction type
            amounts = []
            for amount_str in amount_matches:
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    amounts.append(amount)
            
            if not amounts:
                return None
            
            # Use the first significant amount as transaction amount
            transaction_amount = amounts[0]
            balance = amounts[1] if len(amounts) > 1 else None
            
            # Determine transaction type
            transaction_type = self._determine_transaction_type(line, transaction_amount)
            
            # Extract description
            description = self._extract_description(line, date_match.group(1), amount_matches)
            
            return {
                'transaction_id': f"tx_{line_num}_{hash(line) % 10000}",
                'date': transaction_date,
                'description': description,
                'amount': abs(transaction_amount),
                'transaction_type': transaction_type,
                'balance': balance,
                'raw_line': line
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse line {line_num}: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        date_formats = [
            '%m/%d/%Y', '%m/%d/%y',
            '%d/%m/%Y', '%d/%m/%y',
            '%Y-%m-%d', '%m-%d-%Y',
            '%d-%m-%Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                # Validate date is reasonable (within last 10 years)
                if parsed_date.year >= (datetime.now().year - 10):
                    return parsed_date
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Parse amount string into Decimal."""
        try:
            # Clean amount string
            cleaned = re.sub(r'[^\d\.\-+]', '', amount_str)
            if not cleaned:
                return None
            
            amount = Decimal(cleaned)
            
            # Validate amount is reasonable
            if abs(amount) > Decimal('1000000'):  # 1M limit
                return None
            
            return amount
            
        except (InvalidOperation, ValueError):
            return None
    
    def _determine_transaction_type(self, line: str, amount: Decimal) -> TransactionType:
        """Determine transaction type from line content and amount."""
        line_lower = line.lower()
        
        # Check for explicit keywords
        if self.transaction_patterns['credit_keywords'].search(line):
            return TransactionType.CREDIT
        elif self.transaction_patterns['debit_keywords'].search(line):
            return TransactionType.DEBIT
        
        # Check for fee indicators
        if any(keyword in line_lower for keyword in ['fee', 'charge', 'penalty']):
            return TransactionType.FEE
        
        # Check for interest
        if 'interest' in line_lower:
            return TransactionType.INTEREST
        
        # Check for transfer indicators
        if any(keyword in line_lower for keyword in ['transfer', 'wire', 'ach']):
            return TransactionType.TRANSFER
        
        # Default based on amount sign
        return TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT
    
    def _extract_description(self, line: str, date_str: str, amount_matches: List[str]) -> str:
        """Extract transaction description from line."""
        # Remove date and amounts from line
        description = line
        description = description.replace(date_str, '').strip()
        
        for amount in amount_matches:
            description = description.replace(amount, '').strip()
        
        # Clean description
        description = self.transaction_patterns['description_clean'].sub(' ', description)
        description = ' '.join(description.split())  # Normalize whitespace
        
        return description[:200] if description else "Transaction"
    
    def _validate_transactions(self, transactions: List[Dict[str, Any]]) -> List[BankTransaction]:
        """Validate and convert transaction dictionaries to BankTransaction objects."""
        validated = []
        
        for tx_data in transactions:
            try:
                # Create BankTransaction object
                transaction = BankTransaction(
                    transaction_id=tx_data['transaction_id'],
                    date=tx_data['date'],
                    description=tx_data['description'],
                    amount=tx_data['amount'],
                    transaction_type=tx_data['transaction_type'],
                    balance=tx_data.get('balance')
                )
                validated.append(transaction)
                
            except Exception as e:
                logger.warning(f"Invalid transaction data: {str(e)}")
                continue
        
        return validated
    
    def generate_transaction_summary(self, transactions: List[BankTransaction]) -> TransactionSummary:
        """Generate summary statistics from transactions."""
        if not transactions:
            return TransactionSummary(
                total_transactions=0,
                total_credits=Decimal('0'),
                total_debits=Decimal('0'),
                average_monthly_income=Decimal('0'),
                average_monthly_expenses=Decimal('0'),
                income_stability_score=0.0,
                expense_patterns={},
                overdraft_incidents=0,
                large_transactions_count=0,
                analysis_period_months=1
            )
        
        # Calculate basic statistics
        total_credits = sum(tx.amount for tx in transactions if tx.transaction_type == TransactionType.CREDIT)
        total_debits = sum(tx.amount for tx in transactions if tx.transaction_type == TransactionType.DEBIT)
        
        # Calculate date range
        dates = [tx.date for tx in transactions]
        date_range = (max(dates) - min(dates)).days
        analysis_months = max(1, date_range // 30)
        
        # Calculate monthly averages
        avg_monthly_income = total_credits / analysis_months
        avg_monthly_expenses = total_debits / analysis_months
        
        # Calculate income stability (coefficient of variation)
        monthly_incomes = self._calculate_monthly_incomes(transactions)
        income_stability = self._calculate_income_stability(monthly_incomes)
        
        # Analyze expense patterns
        expense_patterns = self._analyze_expense_patterns(transactions)
        
        # Count overdrafts and large transactions
        overdrafts = sum(1 for tx in transactions if tx.balance and tx.balance < 0)
        large_transactions = sum(1 for tx in transactions if tx.amount > avg_monthly_income * Decimal('0.5'))
        
        return TransactionSummary(
            total_transactions=len(transactions),
            total_credits=total_credits,
            total_debits=total_debits,
            average_monthly_income=avg_monthly_income,
            average_monthly_expenses=avg_monthly_expenses,
            income_stability_score=income_stability,
            expense_patterns=expense_patterns,
            overdraft_incidents=overdrafts,
            large_transactions_count=large_transactions,
            analysis_period_months=analysis_months
        )
    
    def _calculate_monthly_incomes(self, transactions: List[BankTransaction]) -> List[Decimal]:
        """Calculate monthly income amounts."""
        monthly_incomes = {}
        
        for tx in transactions:
            if tx.transaction_type == TransactionType.CREDIT:
                month_key = f"{tx.date.year}-{tx.date.month:02d}"
                monthly_incomes[month_key] = monthly_incomes.get(month_key, Decimal('0')) + tx.amount
        
        return list(monthly_incomes.values())
    
    def _calculate_income_stability(self, monthly_incomes: List[Decimal]) -> float:
        """Calculate income stability score (1.0 = very stable, 0.0 = very unstable)."""
        if len(monthly_incomes) < 2:
            return 1.0
        
        # Calculate coefficient of variation
        mean_income = sum(monthly_incomes) / len(monthly_incomes)
        if mean_income == 0:
            return 0.0
        
        variance = sum((income - mean_income) ** 2 for income in monthly_incomes) / len(monthly_incomes)
        std_dev = variance ** Decimal('0.5')
        
        cv = float(std_dev / mean_income)
        
        # Convert to stability score (inverse of CV, capped at 1.0)
        stability = max(0.0, 1.0 - cv)
        return min(1.0, stability)
    
    def _analyze_expense_patterns(self, transactions: List[BankTransaction]) -> Dict[str, Decimal]:
        """Analyze spending patterns by category."""
        patterns = {}
        
        # Simple categorization based on description keywords
        categories = {
            'groceries': ['grocery', 'supermarket', 'food', 'market'],
            'utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'internet'],
            'transportation': ['gas station', 'fuel', 'uber', 'taxi', 'parking'],
            'entertainment': ['restaurant', 'movie', 'entertainment', 'netflix'],
            'healthcare': ['pharmacy', 'medical', 'doctor', 'hospital'],
            'shopping': ['amazon', 'store', 'retail', 'purchase'],
            'other': []
        }
        
        for tx in transactions:
            if tx.transaction_type in [TransactionType.DEBIT, TransactionType.FEE]:
                description_lower = tx.description.lower()
                categorized = False
                
                for category, keywords in categories.items():
                    if category == 'other':
                        continue
                    
                    if any(keyword in description_lower for keyword in keywords):
                        patterns[category] = patterns.get(category, Decimal('0')) + tx.amount
                        categorized = True
                        break
                
                if not categorized:
                    patterns['other'] = patterns.get('other', Decimal('0')) + tx.amount
        
        return patterns
