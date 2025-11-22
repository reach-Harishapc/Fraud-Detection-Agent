import random
from datetime import datetime, timedelta
from typing import Dict, List

class TransactionMonitor:
    """Monitor and generate transaction data."""
    
    def __init__(self):
        self.merchants = [
            'Amazon', 'Walmart', 'Target', 'Starbucks', 'McDonald\'s',
            'Shell Gas', 'Best Buy', 'CVS Pharmacy', 'Home Depot',
            'Costco', 'Whole Foods', 'Netflix', 'Uber', 'Airbnb'
        ]
        
        self.suspicious_merchants = [
            'Unknown Vendor XYZ', 'Overseas Shop', 'Cash Advance',
            'Wire Transfer Service', 'Crypto Exchange'
        ]
        
        self.locations = [
            'New York, NY', 'Los Angeles, CA', 'Chicago, IL',
            'Houston, TX', 'Phoenix, AZ', 'Philadelphia, PA',
            'San Antonio, TX', 'San Diego, CA', 'Dallas, TX'
        ]
        
        self.foreign_locations = [
            'Lagos, Nigeria', 'Moscow, Russia', 'Manila, Philippines',
            'Jakarta, Indonesia', 'Mumbai, India'
        ]
    
    def generate_normal_transaction(self, account_id: str = 'ACC001') -> Dict:
        """Generate a normal transaction."""
        return {
            'account_id': account_id,
            'amount': round(random.uniform(10, 500), 2),
            'merchant': random.choice(self.merchants),
            'location': random.choice(self.locations),
            'timestamp': datetime.now().isoformat(),
            'card_present': random.choice([True, True, True, False]),  # 75% card present
            'device_id': f'DEVICE_{random.randint(1, 3)}',  # User's common devices
            'is_fraud': False
        }
    
    def generate_fraudulent_transaction(self, account_id: str = 'ACC001', 
                                       fraud_type: str = 'amount') -> Dict:
        """
        Generate a fraudulent transaction.
        
        Types:
        - amount: Unusually high amount
        - location: Foreign location
        - velocity: Part of rapid succession
        - merchant: Suspicious merchant
        - card_testing: Small test amount
        """
        base_transaction = {
            'account_id': account_id,
            'timestamp': datetime.now().isoformat(),
            'is_fraud': True
        }
        
        if fraud_type == 'amount':
            # Unusually high amount
            base_transaction.update({
                'amount': round(random.uniform(2000, 10000), 2),
                'merchant': random.choice(self.merchants),
                'location': random.choice(self.locations),
                'card_present': False,
                'device_id': 'DEVICE_UNKNOWN'
            })
        
        elif fraud_type == 'location':
            # Foreign location
            base_transaction.update({
                'amount': round(random.uniform(100, 1000), 2),
                'merchant': random.choice(self.suspicious_merchants),
                'location': random.choice(self.foreign_locations),
                'card_present': False,
                'device_id': 'DEVICE_UNKNOWN'
            })
        
        elif fraud_type == 'velocity':
            # Rapid succession (part of velocity attack)
            base_transaction.update({
                'amount': round(random.uniform(50, 500), 2),
                'merchant': random.choice(self.merchants),
                'location': random.choice(self.locations),
                'card_present': False,
                'device_id': f'DEVICE_{random.randint(10, 99)}'  # Unknown device
            })
        
        elif fraud_type == 'merchant':
            # Suspicious merchant
            base_transaction.update({
                'amount': round(random.uniform(100, 2000), 2),
                'merchant': random.choice(self.suspicious_merchants),
                'location': random.choice(self.locations + self.foreign_locations),
                'card_present': False,
                'device_id': 'DEVICE_UNKNOWN'
            })
        
        elif fraud_type == 'card_testing':
            # Card testing - small amount
            base_transaction.update({
                'amount': round(random.uniform(0.50, 5.00), 2),
                'merchant': random.choice(self.merchants),
                'location': random.choice(self.locations),
                'card_present': False,
                'device_id': 'DEVICE_UNKNOWN'
            })
        
        return base_transaction
    
    def calculate_velocity(self, transactions: List[Dict], hours: int = 1) -> int:
        """Calculate transaction velocity (transactions per hour)."""
        if not transactions:
            return 0
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [t for t in transactions 
                 if datetime.fromisoformat(t['timestamp']) > cutoff]
        
        return len(recent)

# Global transaction monitor
transaction_monitor = TransactionMonitor()
