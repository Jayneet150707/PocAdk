# 🏦 Paisalo Credit Assessment POC

A comprehensive AI-powered credit assessment system built with Google ADK (Agent Development Kit) and Vertex AI, implementing Paisalo's specific business rules and policies.

## 🎯 Overview

This POC demonstrates a complete credit assessment solution that:

- ✅ **Validates applications** against Paisalo's business rules
- 🤖 **Uses Vertex AI** for intelligent risk assessment
- 📊 **Calculates EMI** using SLM (Straight Line Method)
- 🔍 **Analyzes bank statements** and transaction patterns
- 📋 **Provides detailed recommendations** and reasoning
- 🚀 **Exposes REST API** for integration

## 🏗️ Architecture

```
├── credit_assessment_agent/           # Main agent implementation
│   ├── shared_libraries/              # Common utilities and models
│   │   ├── data_models.py            # Pydantic data models
│   │   ├── paisalo_rules.py          # Business rules engine
│   │   ├── vertex_ai_client.py       # Vertex AI integration
│   │   ├── pdf_processor.py          # Bank statement processing
│   │   └── utils.py                  # Helper functions
│   ├── sub_agents/                   # Specialized sub-agents
│   │   └── transaction_analyzer/     # Bank transaction analysis
│   ├── tools/                        # Agent tools and utilities
│   └── agent.py                      # Main orchestrating agent
├── main.py                           # FastAPI application
├── test_paisalo_rules.py            # Comprehensive test suite
├── sample_paisalo_request.json      # Sample test data
└── requirements.txt                 # Python dependencies
```

## 🔧 Paisalo Business Rules

### 1. **Age Validation**
- **Range**: 21-57 years
- **Action**: Automatic rejection if outside range

### 2. **Credit Score Requirements**
- **Range**: 18-650
- **Action**: Automatic rejection if outside range

### 3. **Document Requirements**
- **Valid Combinations**:
  - Voter ID + PAN Card
  - Driving License + PAN Card
- **PAN Format**: `ABCDE1234F` (5 letters + 4 digits + 1 letter)

### 4. **Loan Amount Limits**
- **Range**: ₹50,000 - ₹1,00,000
- **Action**: Automatic rejection if outside range

### 5. **EMI Calculation (SLM Method)**
- **12 months**: 7% ROI
- **24 months**: 9% ROI
- **36 months**: 12% ROI
- **48 months**: 18% ROI

### 6. **Income vs Expense Validation**
- **Rule**: Total expenses ≤ 50% of total income
- **Calculation**: (Personal + Family Expenses) / (Personal + Family Income)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Project with Vertex AI enabled
- Service Account with appropriate permissions

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd paisalo-credit-assessment
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Google Cloud credentials**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

4. **Run the API server**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

### Run Paisalo Rules Tests
```bash
python test_paisalo_rules.py
```

### Sample API Request
```bash
curl -X POST "http://localhost:8000/assess" \
  -H "Content-Type: application/json" \
  -d @sample_paisalo_request.json
```

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
Performs complete credit assessment with Paisalo rules validation.

**Request Body:**
```json
{
  "credit_application": {
    "application_id": "PAISALO_001",
    "applicant_info": {
      "name": "Rajesh Kumar",
      "age": 35,
      "income": 45000,
      "family_income": 25000,
      "personal_expenses": 20000,
      "family_expenses": 15000,
      "employment_status": "employed",
      "pan_number": "ABCDE1234F",
      "has_voter_id": true,
      "documents_provided": ["pan", "voter_id"]
    },
    "credit_score": 450,
    "loan_amount": 75000,
    "requested_term_months": 24
  }
}
```

### ✅ Rules Validation
```http
POST /validate
```
Validates application against Paisalo business rules only.

### 💰 EMI Calculator
```http
POST /calculate-emi
```
Calculates EMI using Paisalo's SLM method.

**Request:**
```json
{
  "loan_amount": 75000,
  "term_months": 24
}
```

### 📖 Business Rules Info
```http
GET /business-rules
```
Returns detailed information about all Paisalo business rules.

### 📄 Sample Request
```http
GET /sample-request
```
Returns a sample request for testing purposes.

## 🎯 Sample Response

```json
{
  "success": true,
  "assessment_result": {
    "application_id": "PAISALO_001",
    "approved": true,
    "risk_level": "low",
    "recommended_loan_amount": 75000.0,
    "recommended_interest_rate": 0.09,
    "confidence_scores": {
      "overall_confidence": 0.85,
      "credit_score_confidence": 0.75,
      "income_confidence": 0.90
    },
    "reasoning": "=== PAISALO CREDIT ASSESSMENT ===\nApplication processed using Paisalo business rules...",
    "recommendations": [
      "Monthly EMI: ₹3,687.50 using SLM method",
      "Set up automatic EMI payments to avoid defaults"
    ]
  },
  "paisalo_validation": {
    "is_valid": true,
    "risk_level": "low",
    "emi_details": {
      "monthly_emi": 3687.50,
      "annual_roi": 0.09,
      "total_interest": 13500.0,
      "total_amount": 88500.0
    }
  }
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Paisalo Configuration
PAISALO_MIN_AGE=21
PAISALO_MAX_AGE=57
PAISALO_MIN_CREDIT_SCORE=18
PAISALO_MAX_CREDIT_SCORE=650
```

## 🧪 Test Scenarios

The system includes comprehensive test coverage for:

### ✅ **Approval Scenarios**
- Valid age (21-57)
- Valid credit score (18-650)
- Valid loan amount (₹50K-₹1L)
- Valid documents (Voter+PAN or DL+PAN)
- Expenses ≤ 50% of income

### ❌ **Rejection Scenarios**
- Age outside range
- Credit score outside range
- Loan amount outside range
- Invalid document combinations
- Expenses > 50% of income
- Invalid PAN format

### 💰 **EMI Calculations**
- 12 months @ 7% ROI
- 24 months @ 9% ROI
- 36 months @ 12% ROI
- 48 months @ 18% ROI

## 🔍 Monitoring and Logging

The system provides comprehensive logging for:

- 📋 Application processing steps
- ✅ Business rules validation results
- 🤖 AI assessment decisions
- ⚠️ Error conditions and warnings
- 📊 Performance metrics

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Google Cloud Run
```bash
gcloud run deploy paisalo-credit-assessment \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- 📧 Email: support@paisalo.com
- 📞 Phone: +91-XXXX-XXXX
- 🌐 Website: https://paisalo.com

---

**Built with ❤️ using Google ADK and Vertex AI**

