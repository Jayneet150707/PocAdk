# Credit Assessment Agent POC

A Proof of Concept for intelligent credit application assessment using Google ADK (Agent Development Kit) with Vertex AI integration.

## Overview

This system evaluates credit applications by analyzing multiple data sources:
- Credit application data
- Bank transaction PDFs
- Credit score information

The agent provides credibility assessments with confidence scores through a FastAPI backend service.

## Architecture

```
├── credit_assessment_agent/
│   ├── shared_libraries/          # Helper functions and utilities
│   ├── sub_agents/               # Specialized sub-agents
│   │   ├── transaction_analyzer/ # Bank transaction analysis
│   │   ├── credit_score_evaluator/ # Credit score evaluation
│   │   └── risk_assessment/      # Overall risk assessment
│   ├── tools/                    # Main agent tools
│   ├── agent.py                  # Core orchestrating agent
│   └── prompt.py                 # Agent prompts
├── api/                          # FastAPI backend
├── sample_data/                  # Test data and examples
├── tests/                        # Unit and integration tests
├── eval/                         # Evaluation methods
└── deployment/                   # Deployment configurations
```

## Features

- 🤖 **Multi-Agent Architecture**: Specialized sub-agents for different assessment aspects
- 🧠 **Vertex AI Integration**: Leverages Google's advanced AI models
- 📄 **PDF Processing**: Extracts and analyzes bank transaction data
- 📊 **Confidence Scoring**: Provides probabilistic assessment confidence
- 🚀 **FastAPI Backend**: RESTful API for easy integration
- 🔒 **Secure Processing**: Handles sensitive financial data securely

## Quick Start

### Prerequisites

- Python 3.13+
- Google Cloud Project with Vertex AI enabled
- Service account with appropriate permissions

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PocAdk
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Google Cloud credentials and configuration
```

4. Run the API server:
```bash
uvicorn main:app --reload
```

### API Usage

#### Assess Credit Application

```bash
POST /api/v1/assess-credit
Content-Type: application/json

{
  "applicant_info": {
    "name": "John Doe",
    "age": 35,
    "income": 75000,
    "employment_status": "employed"
  },
  "credit_score": 720,
  "loan_amount": 25000,
  "loan_purpose": "home_improvement"
}
```

#### Upload Bank Statement

```bash
POST /api/v1/upload-bank-statement
Content-Type: multipart/form-data

file: <bank_statement.pdf>
applicant_id: <applicant_id>
```

## Sample Data

The `sample_data/` directory contains:
- Example credit applications with various risk profiles
- Sample bank transaction PDFs
- Test scenarios for different assessment outcomes

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=credit_assessment_agent
```

## Evaluation

Evaluate agent performance:
```bash
python -m eval.evaluation_methods
```

## Deployment

### Docker

```bash
docker build -t credit-assessment-agent .
docker run -p 8000:8000 credit-assessment-agent
```

### Google Cloud Run

```bash
gcloud run deploy credit-assessment-agent \
  --source . \
  --platform managed \
  --region us-central1
```

## Configuration

Key configuration options in `.env`:

- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `VERTEX_AI_MODEL_NAME`: Vertex AI model to use
- `CONFIDENCE_THRESHOLD`: Minimum confidence for positive assessment
- `RISK_SCORE_WEIGHTS_*`: Weights for different risk factors

## Agent Architecture

### Main Agent
The `CreditAssessmentAgent` orchestrates the entire assessment process, coordinating between sub-agents and aggregating results.

### Sub-Agents

1. **TransactionAnalyzer**: Processes bank transaction PDFs to identify spending patterns, income stability, and financial behavior.

2. **CreditScoreEvaluator**: Analyzes credit scores and credit history to assess creditworthiness.

3. **RiskAssessment**: Evaluates overall application risk by combining insights from other agents.

### Tools

Each agent has access to specialized tools for:
- PDF text extraction and analysis
- Vertex AI model interactions
- Data validation and preprocessing
- Confidence score calculations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions or issues, please contact:
- Email: dotnetdev3@paisalo.in
- GitHub Issues: [Create an issue](../../issues)
