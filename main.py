import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import json

from transaction_monitor import transaction_monitor
from anomaly_detector import anomaly_detector
from risk_scorer import risk_scorer
from pattern_detector import pattern_detector
from database import fraud_db

# Load environment variables
load_dotenv("../.env")

# Set Google API key
if not os.environ.get('GOOGLE_API_KEY'):
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Initialize Gemini
gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

@tool
def monitor_transaction(account_id: str, amount: float, merchant: str, location: str,
                       card_present: bool = False, device_id: str = "DEVICE_1") -> str:
    """
    Monitor and analyze a transaction for fraud.
    Args:
        account_id: Customer account ID
        amount: Transaction amount
        merchant: Merchant name
        location: Transaction location
        card_present: Whether card was physically present
        device_id: Device identifier
    Returns:
        JSON string with fraud analysis
    """
    try:
        # Create transaction
        transaction = {
            'account_id': account_id,
            'amount': amount,
            'merchant': merchant,
            'location': location,
            'card_present': card_present,
            'device_id': device_id,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        # Get customer baseline
        baseline = fraud_db.get_account_baseline(account_id)
        
        # Get recent transactions for velocity and pattern detection
        recent_transactions = fraud_db.get_transactions(account_id, limit=10)
        velocity = transaction_monitor.calculate_velocity(recent_transactions, hours=1)
        
        # ML anomaly detection
        anomaly_result = anomaly_detector.predict(transaction, baseline)
        
        # Risk scoring
        risk_result = risk_scorer.calculate_risk_score(
            transaction, baseline, anomaly_result['anomaly_score'], velocity
        )
        
        # Pattern detection
        patterns = pattern_detector.detect_patterns(transaction, recent_transactions)
        
        # Combine results
        transaction.update({
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['risk_level'],
            'status': 'Approved' if risk_result['risk_score'] < 50 else 'Flagged'
        })
        
        # Save transaction
        transaction_id = fraud_db.save_transaction(transaction)
        
        # Create alert if high risk
        if risk_result['risk_score'] >= 50:
            alert = {
                'transaction_id': transaction_id,
                'account_id': account_id,
                'alert_type': 'High Risk Transaction',
                'severity': risk_result['risk_level'],
                'message': f"Transaction flagged: ${amount} at {merchant}"
            }
            fraud_db.save_alert(alert)
        
        return json.dumps({
            'transaction_id': transaction_id,
            **risk_result,
            'anomaly': anomaly_result,
            'patterns': patterns,
            'velocity': velocity
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_fraud_alerts(account_id: str) -> str:
    """
    Get active fraud alerts for an account.
    Args:
        account_id: Customer account ID
    Returns:
        JSON string with active alerts
    """
    try:
        alerts = fraud_db.get_alerts(account_id=account_id, acknowledged=False)
        return json.dumps({
            'account_id': account_id,
            'alert_count': len(alerts),
            'alerts': alerts
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def analyze_fraud_pattern(transaction_id: int) -> str:
    """
    Get detailed fraud pattern analysis using Gemini.
    Args:
        transaction_id: Transaction ID
    Returns:
        Detailed analysis
    """
    try:
        # Get transaction details
        transactions = fraud_db.get_transactions(limit=1000)
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        
        if not transaction:
            return "Transaction not found"
        
        # Use Gemini for analysis
        prompt = f"""Analyze this potentially fraudulent transaction:

Amount: ${transaction['amount']}
Merchant: {transaction['merchant']}
Location: {transaction['location']}
Risk Score: {transaction['risk_score']}/100
Risk Level: {transaction['risk_level']}

Provide:
1. Why this transaction might be fraudulent
2. Recommended actions for the customer
3. Prevention tips for future

Keep it under 100 words and customer-friendly."""
        
        analysis = gemini_llm.invoke(prompt).content
        
        return analysis
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize LLM for agent
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

# Define Tools
tools = [monitor_transaction, get_fraud_alerts, analyze_fraud_pattern]

# Define Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Fraud Detection AI Assistant for a financial institution.

Your role is to monitor transactions and protect customers from fraud.

When analyzing transactions:
- Use monitor_transaction to analyze new transactions
- Use get_fraud_alerts to check for active alerts
- Use analyze_fraud_pattern for detailed fraud analysis
- Always prioritize customer security
- Flag suspicious patterns immediately
- Provide clear recommendations

Risk Levels:
- Low (0-24): Normal transaction
- Medium (25-49): Slightly unusual, monitor
- High (50-74): Suspicious, hold for review
- Critical (75-100): Likely fraud, decline

Remember: False positives frustrate customers, but false negatives enable fraud. Balance carefully."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Create Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def main():
    """Test the fraud detection agent."""
    print("\nFraud Detection Agent")
    print("=" * 50)
    
    test_input = "Monitor a transaction: $5000 at Overseas Shop from Lagos, Nigeria"
    
    print(f"\nUser: {test_input}")
    result = agent_executor.invoke({"input": test_input})
    print(f"\nAgent: {result['output']}")

if __name__ == '__main__':
    main()
