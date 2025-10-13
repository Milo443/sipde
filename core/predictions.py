# en una app de Django, por ejemplo 'core/predictions.py'

import pandas as pd
import joblib
import xgboost as xgb
from django.conf import settings
import os
from .models import EstudiantePeriodo

class PredictionService:
    MODEL = None
    MODEL_COLUMNS = None

    @classmethod
    def load_model(cls):
        """Carga el modelo y las columnas en memoria."""
        if cls.MODEL is None or cls.MODEL_COLUMNS is None:
            try:
                model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'xgboost_final_model.json')
                columns_path = os.path.join(settings.BASE_DIR, 'ml_models', 'model_columns.pkl')
                
                cls.MODEL = xgb.XGBClassifier()
                cls.MODEL.load_model(model_path)
                cls.MODEL_COLUMNS = joblib.load(columns_path)
                print("Modelo de predicción cargado en memoria.")
            except Exception as e:
                print(f"Error crítico al cargar el modelo: {e}")
                # Manejar el error apropiadamente
                cls.MODEL = None
                cls.MODEL_COLUMNS = None

    @classmethod
    def predict(cls, id_estudiante, periodo):
        """
        Realiza una predicción para un estudiante y periodo específicos.
        """
        if cls.MODEL is None:
            cls.load_model()
            if cls.MODEL is None:
                return {"error": "El modelo de predicción no está disponible."}

        # 1. Obtener datos limpios desde la BD de Django
        try:
            estudiante_obj = EstudiantePeriodo.objects.get(id_estudiante=id_estudiante, periodo=periodo)
            # Excluir campos que no son features
            datos_dict = estudiante_obj.__dict__
            datos_dict.pop('_state', None)
            datos_dict.pop('id', None)
            #... otras claves a excluir
            
        except EstudiantePeriodo.DoesNotExist:
            return {"error": "Datos no encontrados para la predicción."}

        # 2. Preparar el DataFrame para la predicción (lógica clave del script 2)
        df_pred = pd.DataFrame([datos_dict])
        
        # Aplicar One-Hot Encoding
        df_pred = pd.get_dummies(df_pred, drop_first=True)
        
        # Alinear columnas con las del modelo entrenado
        df_pred = df_pred.reindex(columns=cls.MODEL_COLUMNS, fill_value=0)

        # 3. Realizar la predicción
        probabilidad = cls.MODEL.predict_proba(df_pred)[:, 1][0]
        
        # 4. Aplicar umbral de decisión
        # El umbral puede estar en settings.py
        UMBRAL = getattr(settings, 'UMBRAL_PREDICCION', 0.515) 
        en_riesgo = probabilidad >= UMBRAL

        return {
            "id_estudiante": id_estudiante,
            "probabilidad": probabilidad,
            "en_riesgo": en_riesgo,
            "umbral_usado": UMBRAL
        }