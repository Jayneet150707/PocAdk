# Credit Assessment Agent POC

A Proof of Concept (POC) implementation of a Credit Assessment Agent using Google ADK architecture that integrates with Vertex AI for intelligent credit application processing.

## 🎯 Definition of Done

This POC demonstrates:
- ✅ **Google ADK Agent Architecture**: Structured agent system with sub-agents and tools
- ✅ **Vertex AI Integration**: With fallback assessment when cloud services unavailable
- ✅ **Credit Application Processing**: Receives fabricated credit data and analyzes credibility
- ✅ **Confidence Scoring**: Returns assessment with confidence metrics
- ✅ **Bank Statement Analysis**: PDF processing capabilities (with sample data)
- ✅ **FastAPI Backend**: RESTful API endpoints for data input and JSON responses
- ✅ **Robust Error Handling**: Graceful degradation when dependencies unavailable

## 🏗️ Architecture

```
credit_assessment_agent/
├── shared_libraries/           # Helper functions and utilities
│   ├── data_models.py         # Pydantic models for data validation
│   ├── pdf_processor.py       # PDF bank statement processing
│   ├── vertex_ai_client.py    # Vertex AI integration with fallback
│   └── utils.py               # Utility functions
├── sub_agents/                # Sub-agent implementations
│   └── transaction_analyzer/  # Bank transaction analysis agent
│       ├── tools/             # Transaction analysis tools
│       ├── agent.py           # Core transaction analyzer logic
│       └── prompt.py          # AI prompts for transaction analysis
├── tools/                     # Main agent tools
├── agent.py                   # Core credit assessment agent
├── prompt.py                  # Main agent prompts
└── __init__.py               # Agent initialization
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Optional: Google Cloud credentials for Vertex AI (works without)
- Optional: python-multipart for file uploads

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd PocAdk
```

2. **Install dependencies** (optional - works without):
```bash
pip install -r requirements.txt
# OR install specific dependencies:
pip install fastapi uvicorn pydantic
pip install google-cloud-aiplatform  # Optional for Vertex AI
pip install PyPDF2                    # Optional for PDF processing
pip install python-multipart         # Optional for file uploads
```

3. **Environment setup** (optional):
```bash
cp .env.example .env
# Edit .env with your Google Cloud credentials if available
```

### Running the Service

```bash
# Start the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "vertex_ai": "available",
    "credit_agent": "available"
  },
  "timestamp": "2024-09-16T11:30:00Z"
}
```

### Credit Assessment
```bash
POST /api/v1/assess-credit
```

**Request Body**:
```json
{
  "credit_application": {
    "application_id": "TEST_001",
    "applicant_info": {
      "name": "John Doe",
      "age": 35,
      "income": 75000,
      "employment_status": "employed",
      "employment_duration_months": 24,
      "address": "123 Main St, Anytown, USA",
      "phone": "+1234567890",
      "email": "john.doe@example.com"
    },
    "credit_score": 720,
    "loan_amount": 25000,
    "loan_purpose": "home_improvement",
    "requested_term_months": 60
  },
  "priority": "normal"
}
```

**Response**:
```json
{
  "success": true,
  "assessment": {
    "application_id": "TEST_001",
    "assessment_id": "ASSESS_20250916134311_b4e552de",
    "approved": true,
    "risk_level": "low",
    "recommended_loan_amount": "25000.0",
    "recommended_interest_rate": 0.065,
    "confidence_scores": {
      "overall_confidence": 0.65,
      "credit_score_confidence": 0.85,
      "income_confidence": 0.9,
      "transaction_confidence": 0.3,
      "application_confidence": 0.49,
      "data_quality_score": 0.44
    },
    "risk_factors": {
      "high_debt_to_income": false,
      "insufficient_income": false,
      "poor_credit_history": false,
      "irregular_income": false,
      "excessive_expenses": false,
      "frequent_overdrafts": false,
      "short_employment_history": false,
      "high_loan_to_value": false,
      "risk_factors_count": 0,
      "risk_level": "low"
    },
    "reasoning": "Credit Assessment Decision: APPROVED...",
    "recommendations": [
      "Maintain current financial habits to ensure successful repayment",
      "Consider setting up automatic payments to avoid missed payments"
    ],
    "assessed_at": "2025-09-16T13:43:11.089867",
    "processing_time_seconds": 0.000554
  },
  "message": "Credit assessment completed successfully"
}
```

### Bank Statement Upload
```bash
POST /api/v1/upload-bank-statement
```

**Note**: Requires `python-multipart` dependency. Returns 501 if not available.

## 🧪 Testing

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test credit assessment
curl -X POST http://localhost:8000/api/v1/assess-credit \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

### Sample Request File
Create `sample_request.json`:
```json
{
  "credit_application": {
    "application_id": "SAMPLE_001",
    "applicant_info": {
      "name": "Jane Smith",
      "age": 28,
      "income": 65000,
      "employment_status": "employed",
      "employment_duration_months": 36,
      "phone": "+1555123456",
      "email": "jane.smith@example.com"
    },
    "credit_score": 680,
    "loan_amount": 15000,
    "loan_purpose": "debt_consolidation",
    "requested_term_months": 48
  }
}
```

## 🔧 Features

### ✅ Implemented
- **Google ADK Architecture**: Structured agent system
- **Vertex AI Integration**: With intelligent fallback
- **Credit Assessment**: Rule-based and AI-powered analysis
- **Risk Analysis**: Comprehensive risk factor evaluation
- **Confidence Scoring**: Multi-dimensional confidence metrics
- **PDF Processing**: Bank statement analysis capabilities
- **RESTful API**: FastAPI-based service endpoints
- **Error Handling**: Graceful degradation and error responses
- **Logging**: Structured logging throughout the system

### 🔄 Fallback Mechanisms
When optional dependencies are unavailable:
- **Vertex AI**: Falls back to rule-based assessment
- **PDF Processing**: Returns appropriate error messages
- **File Uploads**: Returns 501 with installation instructions

## 🎯 Assessment Logic

The system uses a multi-layered assessment approach:

1. **Primary Assessment** (with Vertex AI):
   - Advanced ML-based credit scoring
   - Natural language reasoning
   - Complex pattern recognition

2. **Fallback Assessment** (rule-based):
   - Income-based scoring (≥$50k: +50 points)
   - Employment status evaluation
   - Debt-to-income ratio analysis
   - Transaction pattern analysis
   - Risk factor identification

3. **Confidence Scoring**:
   - Overall confidence (0.0-1.0)
   - Credit score confidence
   - Income verification confidence
   - Transaction analysis confidence
   - Application completeness score

## 🔒 Security & Privacy

- Input validation using Pydantic models
- Secure file handling for PDF uploads
- No sensitive data logging
- Temporary file cleanup
- Error message sanitization

## 📊 Monitoring & Observability

- Structured logging with timestamps
- Processing time metrics
- Service health checks
- Error tracking and reporting
- Assessment audit trail

## 🚀 Production Considerations

For production deployment:

1. **Environment Variables**:
   - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key
   - `API_HOST`, `API_PORT`: Server configuration
   - `LOG_LEVEL`: Logging verbosity

2. **Dependencies**:
   - Install all optional dependencies for full functionality
   - Configure Google Cloud authentication
   - Set up proper database for assessment storage

3. **Scaling**:
   - Use proper ASGI server (Gunicorn + Uvicorn)
   - Implement database persistence
   - Add caching layer for frequent assessments
   - Configure load balancing

## 📝 Development

### Project Structure
- `main.py`: FastAPI application entry point
- `credit_assessment_agent/`: Core agent implementation
- `tests/`: Unit tests (to be implemented)
- `deployment/`: Deployment configurations
- `eval/`: Evaluation methods and metrics

### Adding New Features
1. Extend data models in `shared_libraries/data_models.py`
2. Add new tools in respective `tools/` directories
3. Update agent logic in `agent.py` files
4. Add API endpoints in `main.py`
5. Update tests and documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**POC Status**: ✅ Complete - All requirements met with robust fallback mechanisms

