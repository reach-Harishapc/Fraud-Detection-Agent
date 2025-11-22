from flask import Flask, render_template, jsonify, request
from transaction_monitor import transaction_monitor
from anomaly_detector import anomaly_detector
from risk_scorer import risk_scorer
from pattern_detector import pattern_detector
from database import fraud_db

app = Flask(__name__)

@app.route('/')
def index():
    """Fraud monitoring dashboard."""
    return render_template('monitor.html')

@app.route('/api/monitor_transaction', methods=['POST'])
def monitor_transaction_api():
    """Monitor a new transaction."""
    try:
        data = request.json
        
        # Create transaction
        transaction = {
            'account_id': data.get('account_id', 'ACC001'),
            'amount': float(data['amount']),
            'merchant': data['merchant'],
            'location': data['location'],
            'card_present': data.get('card_present', False),
            'device_id': data.get('device_id', 'DEVICE_1'),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        # Get baseline and recent transactions
        baseline = fraud_db.get_account_baseline(transaction['account_id'])
        recent = fraud_db.get_transactions(transaction['account_id'], limit=10)
        velocity = transaction_monitor.calculate_velocity(recent, hours=1)
        
        # Analyze
        anomaly_result = anomaly_detector.predict(transaction, baseline)
        risk_result = risk_scorer.calculate_risk_score(
            transaction, baseline, anomaly_result['anomaly_score'], velocity
        )
        patterns = pattern_detector.detect_patterns(transaction, recent)
        
        # Update transaction
        transaction.update({
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['risk_level'],
            'status': 'Approved' if risk_result['risk_score'] < 50 else 'Flagged'
        })
        
        # Save
        transaction_id = fraud_db.save_transaction(transaction)
        
        # Create alert if needed
        if risk_result['risk_score'] >= 50:
            fraud_db.save_alert({
                'transaction_id': transaction_id,
                'account_id': transaction['account_id'],
                'alert_type': 'High Risk Transaction',
                'severity': risk_result['risk_level'],
                'message': f"${transaction['amount']} at {transaction['merchant']}"
            })
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            **risk_result,
            'anomaly': anomaly_result,
            'patterns': patterns
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<account_id>')
def get_transactions_api(account_id):
    """Get transactions for an account."""
    transactions = fraud_db.get_transactions(account_id, limit=50)
    return jsonify({'transactions': transactions})

@app.route('/api/alerts/<account_id>')
def get_alerts_api(account_id):
    """Get alerts for an account."""
    alerts = fraud_db.get_alerts(account_id, acknowledged=False)
    return jsonify({'alerts': alerts, 'count': len(alerts)})

if __name__ == '__main__':
    app.run(debug=True, port=5016)
