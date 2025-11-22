# Finance Fraud Detection Agent

## Problem Statement
**Fraud Detection & Prevention**

Financial institutions lose billions annually to fraudulent transactions. Traditional rule-based systems generate excessive false positives, frustrating legitimate customers while missing sophisticated fraud patterns. Real-time detection is critical but challenging.

## Solution
An AI agent designed to:
- **Real-time transaction monitoring** with instant risk scoring
- **Anomaly detection** using ML models (Isolation Forest)
- **Pattern recognition** for fraud signatures
- **Risk-based alerts** with severity classification
- **Transaction history analysis** for behavioral profiling

## Tech Stack
- **LangChain**: Agent orchestration
- **Google Gemini**: LLM for fraud pattern analysis and recommendations
- **scikit-learn**: Isolation Forest for anomaly detection
- **Flask**: Real-time monitoring dashboard
- **SQLite**: Transaction history and alert tracking

## Key Features
- Real-time transaction scoring (0-100 risk score)
- Multi-factor fraud detection (amount, location, velocity, device)
- Behavioral baseline comparison
- Automated alert generation
- False positive learning
- Transaction approval/decline recommendations
