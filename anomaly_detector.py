from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, List
import pickle
import os

class AnomalyDetector:
    """Detect anomalies using Isolation Forest."""
    
    def __init__(self, model_path: str = 'fraud_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.is_trained = False
        
        # Load existing model if available
        if os.path.exists(model_path):
            self.load_model()
    
    def extract_features(self, transaction: Dict, baseline: Dict = None) -> np.array:
        """
        Extract features from a transaction for ML model.
        
        Features:
        - Amount
        - Amount Z-score (using baseline)
        - Hour of day
        - Is card present (boolean)
        - Is foreign location (boolean)
        """
        # Basic features
        amount = transaction['amount']
        hour = int(transaction['timestamp'][11:13])  # Extract hour
        card_present = 1 if transaction.get('card_present', False) else 0
        is_foreign = 1 if any(loc in transaction['location'] 
                             for loc in ['Nigeria', 'Russia', 'Philippines', 'Indonesia', 'India']) else 0
        
        # Calculate amount z-score if baseline available
        if baseline and 'avg_amount' in baseline:
            avg = baseline['avg_amount']
            std = baseline.get('std_amount', avg * 0.3)  # Default std if not available
            amount_zscore = (amount - avg) / std if std > 0 else 0
        else:
            amount_zscore = 0
        
        features = [
            amount,
            amount_zscore,
            hour,
            card_present,
            is_foreign
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, transactions: List[Dict]):
        """Train the Isolation Forest model."""
        if len(transactions) < 10:
            print("Not enough transactions to train model")
            return
        
        # Extract features for all transactions
        features_list = []
        for trans in transactions:
            features = self.extract_features(trans)
            features_list.append(features[0])
        
        X = np.array(features_list)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        
        self.model.fit(X)
        self.is_trained = True
        
        print(f"Model trained on {len(transactions)} transactions")
    
    def predict(self, transaction: Dict, baseline: Dict = None) -> Dict:
        """
        Predict if a transaction is anomalous.
        
        Returns:
            Dict with anomaly_score and is_anomaly
        """
        if not self.is_trained:
            # Return neutral if model not trained
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0
            }
        
        features = self.extract_features(transaction, baseline)
        
        # Predict: -1 for anomaly, 1 for normal
        prediction = self.model.predict(features)[0]
        
        # Get anomaly score (lower is more anomalous)
        anomaly_score = self.model.score_samples(features)[0]
        
        # Normalize score to 0-1 (higher is more anomalous)
        # Typical scores range from -0.5 to 0.5
        normalized_score = max(0, min(1, (-anomaly_score + 0.5)))
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': round(normalized_score, 3),
            'confidence': round(abs(anomaly_score), 3)
        }
    
    def save_model(self):
        """Save the trained model."""
        if self.model:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load a trained model."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.is_trained = True
            print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")

# Global anomaly detector
anomaly_detector = AnomalyDetector()
