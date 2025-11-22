from typing import Dict

class RiskScorer:
    """Calculate risk scores for transactions."""
    
    def __init__(self):
        pass
    
    def calculate_risk_score(self, transaction: Dict, baseline: Dict = None,
                            anomaly_score: float = 0.0, velocity: int = 0) -> Dict:
        """
        Calculate comprehensive risk score (0-100).
        
        Risk Factors:
        - Amount (unusual amount compared to baseline)
        - Location (foreign location)
        - Velocity (high transaction frequency)
        - Card presence (card not present  riskier)
        - Device (unknown device)
        - Anomaly score from ML model
        - Merchant (suspicious merchant)
        """
        risk_factors = []
        risk_score = 0
        
        # 1. Amount Risk (0-25 points)
        amount = transaction['amount']
        if baseline and 'avg_amount' in baseline:
            avg_amount = baseline['avg_amount']
            
            if amount > avg_amount * 5:
                risk_score += 25
                risk_factors.append('Amount 5x higher than average')
            elif amount > avg_amount * 3:
                risk_score += 20
                risk_factors.append('Amount 3x higher than average')
            elif amount > avg_amount * 2:
                risk_score += 10
                risk_factors.append('Amount 2x higher than average')
        else:
            # Without baseline, flag very high amounts
            if amount > 5000:
                risk_score += 20
                risk_factors.append('Very high transaction amount')
            elif amount > 2000:
                risk_score += 10
                risk_factors.append('High transaction amount')
        
        # Card testing (very small amounts)
        if amount < 5:
            risk_score += 15
            risk_factors.append('Suspiciously small amount (possible card testing)')
        
        # 2. Location Risk (0-20 points)
        location = transaction['location']
        foreign_indicators = ['Nigeria', 'Russia', 'Philippines', 'Indonesia', 'India', 'China']
        
        if any(indicator in location for indicator in foreign_indicators):
            risk_score += 20
            risk_factors.append('Foreign location detected')
        
        # 3. Velocity Risk (0-20 points)
        if velocity > 10:
            risk_score += 20
            risk_factors.append(f'Very high velocity: {velocity} transactions/hour')
        elif velocity > 5:
            risk_score += 15
            risk_factors.append(f'High velocity: {velocity} transactions/hour')
        elif velocity > 3:
            risk_score += 10
            risk_factors.append(f'Elevated velocity: {velocity} transactions/hour')
        
        # 4. Card Presence Risk (0-15 points)
        if not transaction.get('card_present', False):
            risk_score += 10
            risk_factors.append('Card not present')
        
        # 5. Device Risk (0-10 points)
        device_id = transaction.get('device_id', '')
        if 'UNKNOWN' in device_id or not device_id.startswith('DEVICE_'):
            risk_score += 10
            risk_factors.append('Unknown or suspicious device')
        elif int(device_id.split('_')[1]) > 5:  # Device ID > 5 is unusual
            risk_score += 5
            risk_factors.append('Unfamiliar device')
        
        # 6. Merchant Risk (0-15 points)
        merchant = transaction.get('merchant', '')
        suspicious_merchant_keywords = ['Unknown', 'Overseas', 'Cash Advance', 'Wire Transfer', 'Crypto']
        
        if any(keyword in merchant for keyword in suspicious_merchant_keywords):
            risk_score += 15
            risk_factors.append('Suspicious merchant category')
        
        # 7. ML Anomaly Score (0-20 points)
        ml_risk = int(anomaly_score * 20)
        if ml_risk > 0:
            risk_score += ml_risk
            risk_factors.append(f'ML anomaly detection: {int(anomaly_score * 100)}% confidence')
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Classify risk level
        if risk_score >= 75:
            risk_level = 'Critical'
        elif risk_score >= 50:
            risk_level = 'High'
        elif risk_score >= 25:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            'Critical': 'DECLINE transaction and contact customer immediately',
            'High': 'HOLD for manual review and customer verification',
            'Medium': 'APPROVE with additional authentication (e.g., OTP)',
            'Low': 'APPROVE transaction'
        }
        return recommendations.get(risk_level, 'REVIEW transaction')

# Global risk scorer
risk_scorer = RiskScorer()
