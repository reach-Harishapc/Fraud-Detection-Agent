import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

class FraudDetectionDatabase:
    def __init__(self, db_path: str = "fraud_detection.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                amount REAL,
                merchant TEXT,
                location TEXT,
                timestamp TEXT,
                card_present BOOLEAN,
                device_id TEXT,
                risk_score INTEGER,
                risk_level TEXT,
                is_fraud BOOLEAN,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                account_id TEXT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        ''')
        
        # Create customer_baselines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_baselines (
                account_id TEXT PRIMARY KEY,
                avg_amount REAL,
                std_amount REAL,
                typical_locations TEXT,
                typical_merchants TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_transaction(self, transaction: Dict) -> int:
        """Save a transaction."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (account_id, amount, merchant, location, timestamp,
                                    card_present, device_id, risk_score, risk_level, is_fraud, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction['account_id'],
            transaction['amount'],
            transaction['merchant'],
            transaction['location'],
            transaction['timestamp'],
            transaction.get('card_present', False),
            transaction.get('device_id', ''),
            transaction.get('risk_score', 0),
            transaction.get('risk_level', 'Low'),
            transaction.get('is_fraud', False),
            transaction.get('status', 'Pending')
        ))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return transaction_id
    
    def save_alert(self, alert: Dict):
        """Save a fraud alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (transaction_id, account_id, alert_type, severity, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            alert.get('transaction_id'),
            alert['account_id'],
            alert['alert_type'],
            alert['severity'],
            alert['message']
        ))
        
        conn.commit()
        conn.close()
    
    def get_transactions(self, account_id: str = None, limit: int = 100) -> List[Dict]:
        """Get transactions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if account_id:
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE account_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (account_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM transactions 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_alerts(self, account_id: str = None, acknowledged: bool = False) -> List[Dict]:
        """Get alerts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM alerts WHERE acknowledged = ?'
        params = [acknowledged]
        
        if account_id:
            query += ' AND account_id = ?'
            params.append(account_id)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_account_baseline(self, account_id: str) -> Optional[Dict]:
        """Get customer spending baseline."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customer_baselines WHERE account_id = ?', (account_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            baseline = dict(row)
            # Parse JSON lists
            baseline['typical_locations'] = json.loads(baseline.get('typical_locations', '[]'))
            baseline['typical_merchants'] = json.loads(baseline.get('typical_merchants', '[]'))
            return baseline
        return None
    
    def update_account_baseline(self, account_id: str, baseline: Dict):
        """Update or create customer baseline."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO customer_baselines 
            (account_id, avg_amount, std_amount, typical_locations, typical_merchants, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            baseline.get('avg_amount', 0),
            baseline.get('std_amount', 0),
            json.dumps(baseline.get('typical_locations', [])),
            json.dumps(baseline.get('typical_merchants', [])),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

# Global database instance
fraud_db = FraudDetectionDatabase()
