from abc import ABC, abstractmethod
from typing import Dict, Any

class IMLPredictorService(ABC):
    """
    Port Interface untuk Layanan Prediksi Machine Learning.
    Memisahkan Use Case dari detail protokol HTTP atau SDK ML di MachineLearningPBL.
    """

    @abstractmethod
    def predict_burnout(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mengevaluasi fitur input data primer dan mengembalikan hasil prediksi.
        Return dict minimal berisi: burnout_score, burnout_level, recommendation.
        """
        pass
