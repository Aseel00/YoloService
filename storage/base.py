from abc import ABC, abstractmethod

class PredictionStorage(ABC):
    @abstractmethod
    def save_prediction_session(self, uid, original_image, predicted_image): pass

    @abstractmethod
    def save_detection_object(self, prediction_uid, label, score, box,index): pass

    @abstractmethod
    def get_prediction_by_uid(self, uid): pass

    @abstractmethod
    def get_predictions_by_label(self, label): pass

    @abstractmethod
    def get_predictions_by_score(self, min_score): pass
