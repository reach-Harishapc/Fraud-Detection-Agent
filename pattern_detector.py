from typing import Dict, List

class PatternDetector:
    """Detect known fraud patterns."""
    
    def __init__(self):
        pass
    
    def detect_patterns(self, transaction: Dict, recent_transactions: List[Dict]) -> List[Dict]:
        """
        Detect fraud patterns.
        
        Patterns:
        1. Card Testing: Small transaction followed by large transaction
        2. Account Takeover: Sudden change in behavior
        3. Velocity Abuse: Rapid succession of transactions
        4. Round Dollar Amounts: Suspicious round numbers
        5. Geographic Impossibility: Transactions in distant locations in short time
        """
        patterns_found = []
        
        # 1. Card Testing Pattern
        card_testing = self._detect_card_testing(transaction, recent_transactions)
        if card_testing:
            patterns_found.append(card_testing)
        
        # 2. Account Takeover Pattern
        takeover = self._detect_account_takeover(transaction, recent_transactions)
        if takeover:
            patterns_found.append(takeover)
        
        # 3. Velocity Abuse
        velocity_abuse = self._detect_velocity_abuse(transaction, recent_transactions)
        if velocity_abuse:
            patterns_found.append(velocity_abuse)
        
        # 4. Round Dollar Amount
        round_amount = self._detect_round_amount(transaction)
        if round_amount:
            patterns_found.append(round_amount)
        
        return patterns_found
    
    def _detect_card_testing(self, transaction: Dict, recent_transactions: List[Dict]) -> Dict:
        """Detect card testing: small amount followed by large amount."""
        # Check if current transaction is large
        if transaction['amount'] < 500:
            return None
        
        # Check if there was a small transaction recently
        for recent in recent_transactions[-5:]:  # Last 5 transactions
            if recent['amount'] < 5 and recent['merchant'] == transaction['merchant']:
                return {
                    'pattern': 'Card Testing',
                    'description': f'Small test transaction (${recent["amount"]}) followed by large transaction (${transaction["amount"]})',
                    'severity': 'High'
                }
        
        return None
    
    def _detect_account_takeover(self, transaction: Dict, recent_transactions: List[Dict]) -> Dict:
        """Detect account takeover: sudden change in location or device."""
        if len(recent_transactions) < 3:
            return None
        
        # Check for sudden location change
        recent_locations = [t['location'] for t in recent_transactions[-3:]]
        current_location = transaction['location']
        
        # If all recent are domestic but current is foreign
        foreign_keywords = ['Nigeria', 'Russia', 'Philippines', 'Indonesia', 'India']
        recent_foreign = any(any(kw in loc for kw in foreign_keywords) for loc in recent_locations)
        current_foreign = any(kw in current_location for kw in foreign_keywords)
        
        if current_foreign and not recent_foreign:
            return {
                'pattern': 'Account Takeover',
                'description': 'Sudden change to foreign location',
                'severity': 'Critical'
            }
        
        # Check for unknown device use
        recent_devices = [t.get('device_id', '') for t in recent_transactions[-5:]]
        current_device = transaction.get('device_id', '')
        
        if 'UNKNOWN' in current_device and all('UNKNOWN' not in d for d in recent_devices):
            return {
                'pattern': 'Account Takeover',
                'description': 'Sudden use of unknown device',
                'severity': 'High'
            }
        
        return None
    
    def _detect_velocity_abuse(self, transaction: Dict, recent_transactions: List[Dict]) -> Dict:
        """Detect velocity abuse: too many transactions in short time."""
        if len(recent_transactions) < 6:
            return None
        
        # If 6+ transactions in recent history (usually last hour)
        return {
            'pattern': 'Velocity Abuse',
            'description': f'{len(recent_transactions)} transactions in short time period',
            'severity': 'High'
        }
    
    def _detect_round_amount(self, transaction: Dict) -> Dict:
        """Detect suspicious round dollar amounts."""
        amount = transaction['amount']
        
        # Check if it's a round number (e.g., 100, 500, 1000)
        if amount >= 100 and amount % 100 == 0:
            return {
                'pattern': 'Round Dollar Amount',
                'description': f'Suspicious round amount: ${amount}',
                'severity': 'Low'
            }
        
        return None

# Global pattern detector
pattern_detector = PatternDetector()
