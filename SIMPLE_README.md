# 🚀 Simple Credit Assessment with Google ADK

A streamlined implementation of credit assessment using Google ADK (Agent Development Kit) that demonstrates core agent patterns, orchestration, and decision-making capabilities.

## 🎯 Overview

This simplified system showcases:

- ✅ **Google ADK Agent Architecture** - Clean agent orchestration patterns
- 🤖 **Sub-Agent Specialization** - Risk assessment and decision-making agents
- 📊 **Transparent Decision Making** - Clear reasoning and confidence scoring
- 🔧 **Simple Business Rules** - Straightforward credit assessment criteria
- 🚀 **FastAPI Integration** - Production-ready REST API
- 🧪 **Comprehensive Testing** - Full test coverage for all components

## 🏗️ Architecture

```
simple_credit_agent/
├── agent.py                    # Main orchestrating agent
├── models.py                   # Clean data models
├── rules.py                    # Simple business rules
├── prompts.py                  # AI prompts (for future enhancement)
└── sub_agents/
    ├── risk_assessor.py        # Risk assessment specialist
    └── decision_engine.py      # Final decision maker
```

## 🔧 Simple Business Rules

### ✅ **Approval Criteria**
- **Age**: 18-75 years
- **Credit Score**: 580+ minimum
- **Income**: $30,000+ annually
- **Debt-to-Income**: ≤40% maximum
- **Employment**: 6+ months history
- **Expenses**: ≤60% of income

### 💰 **Loan Limits by Credit Score**
- **850+**: Up to $500,000 (Excellent)
- **800+**: Up to $300,000 (Very Good)
- **740+**: Up to $200,000 (Good)
- **670+**: Up to $100,000 (Fair)
- **580+**: Up to $50,000 (Poor)

### 📈 **Interest Rates by Risk Level**
- **Low Risk**: 4.5% - 8.5% APR
- **Medium Risk**: 6.5% - 12.5% APR
- **High Risk**: 9.5% - 18.5% APR

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic
```

### 2. Run Tests
```bash
python test_simple_credit.py
```

### 3. Start API Server
```bash
python simple_main.py
```
Server runs on: http://localhost:8001

### 4. Access Documentation
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 📋 API Endpoints

### 🏥 Health Check
```http
GET /health
```
Returns system status and component availability.

### 🔍 Credit Assessment
```http
POST /assess
```
Complete credit assessment using Google ADK agents.

**Sample Request:**
```json
{
  "application": {
    "application_id": "SIMPLE_001",
    "applicant": {
      "name": "John Smith",
      "age": 32,
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "annual_income": 75000,
      "monthly_expenses": 3500,
      "employment_status": "employed",
      "employment_duration_months": 36,
      "credit_score": 720,
      "existing_debt": 15000
    },
    "loan_request": {
      "amount": 25000,
      "purpose": "personal",
      "term_months": 60
    }
  }
}
```

### 📄 Sample Data
```http
GET /sample
```
Get sample application for testing.

### 📖 Business Rules
```http
GET /rules
```
View all business rules and criteria.

### 🔍 Scenario Analysis
```http
POST /scenarios
```
Analyze alternative loan scenarios.

### 📊 Agent Status
```http
GET /agent-status
```
Get detailed agent information and capabilities.

## 🎯 Sample Response

```json
{
  "success": true,
  "result": {
    "application_id": "SIMPLE_001",
    "assessment_id": "ASSESS_20250917120000_001",
    "approved": true,
    "risk_level": "low",
    "recommended_amount": 25000.0,
    "recommended_rate": 0.065,
    "recommended_term": 60,
    "confidence_scores": {
      "overall_confidence": 0.82,
      "income_confidence": 0.85,
      "credit_confidence": 0.80,
      "employment_confidence": 0.80
    },
    "risk_factors": {
      "high_debt_to_income": false,
      "low_credit_score": false,
      "insufficient_income": false,
      "short_employment": false,
      "high_expenses": false,
      "risk_count": 0,
      "risk_level": "low"
    },
    "reasoning": "=== CREDIT DECISION ANALYSIS ===\nDecision: APPROVED\n...",
    "recommendations": [
      "Congratulations! Your loan application has been approved.",
      "Set up automatic payments to ensure timely loan repayment",
      "Consider making extra payments to reduce total interest"
    ]
  }
}
```

## 🧪 Testing Results

Run `python test_simple_credit.py` to see:

```
🧪 SIMPLE CREDIT ASSESSMENT TESTS
==================================================

=== Testing Business Rules ===
✅ All age validation tests passed
✅ All credit score tests passed  
✅ All income validation tests passed

=== Testing Risk Assessment ===
✅ Low risk applicant correctly identified
✅ High risk applicant correctly identified

=== Testing Agent Workflow ===
✅ Agent initialized successfully
✅ Assessment completed: APPROVED
   Risk Level: LOW
   Overall Confidence: 82%
   Processing Time: 0.045s

🎉 All tests completed successfully!
```

## 🤖 Google ADK Features Demonstrated

### 1. **Agent Orchestration**
- Main agent coordinates sub-agents
- Clear workflow management
- Error handling and fallbacks

### 2. **Sub-Agent Specialization**
- **Risk Assessor**: Focused on risk analysis
- **Decision Engine**: Final decision authority
- Clear separation of concerns

### 3. **Transparent Decision Making**
- Detailed reasoning for all decisions
- Confidence scoring for reliability
- Clear factor analysis

### 4. **Scalable Architecture**
- Easy to add new sub-agents
- Modular business rules
- Clean API integration

## 🔍 Key Differences from Complex Version

| Feature | Simple Version | Complex (Paisalo) Version |
|---------|---------------|---------------------------|
| **Business Rules** | 6 simple criteria | 15+ complex validations |
| **Age Range** | 18-75 years | 21-57 years (Paisalo specific) |
| **Credit Score** | 580+ minimum | 18-650 range (unusual) |
| **Document Validation** | Not required | PAN + Voter/DL required |
| **EMI Calculation** | Standard formula | SLM method specific |
| **API Endpoints** | 7 core endpoints | 12+ specialized endpoints |
| **Code Complexity** | ~800 lines | ~2000+ lines |

## 🎯 Use Cases

### ✅ **Perfect For:**
- Learning Google ADK patterns
- Prototyping credit systems
- Demonstrating agent orchestration
- Educational purposes
- Quick POC development

### 🔄 **Can Be Extended For:**
- Industry-specific rules
- Additional sub-agents
- AI/ML integration
- Complex workflows
- Regulatory compliance

## 🚀 Next Steps

1. **Add AI Enhancement**: Integrate with Vertex AI for smarter decisions
2. **Add More Sub-Agents**: Income verification, document processing
3. **Implement Caching**: Redis for performance optimization
4. **Add Monitoring**: Metrics and observability
5. **Database Integration**: Persistent storage for applications

## 🤝 Contributing

This simple implementation is designed to be:
- **Easy to understand** - Clear code structure
- **Easy to modify** - Modular components
- **Easy to extend** - Plugin architecture ready
- **Well documented** - Comprehensive comments

Feel free to use this as a foundation for your own credit assessment systems!

---

**Built with ❤️ using Google ADK patterns and FastAPI**

