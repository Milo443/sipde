# core/services.py

from django.conf import settings
import pandas as pd
import numpy as np
from datetime import datetime
from .models import EstudiantePeriodo
from .predictions import PredictionService

def procesar_y_guardar_datos_de_periodo(archivos_cargados, periodo_actual):
    """
    Orquesta todo el proceso de carga, limpieza, enriquecimiento y guardado de datos
    para un nuevo periodo, finalizando con el cálculo del riesgo inicial para cada estudiante.
    """
    print(f"Iniciando procesamiento para el periodo: {periodo_actual}")

    # 1. Carga y Estandarización de Archivos
    dataframes_nuevos = {}
    for key, path in archivos_cargados.items():
        try:
            df_temp = pd.read_csv(path, sep=';', encoding='latin1', low_memory=False) if str(path).endswith('.csv') else pd.read_excel(path)
            
            # Estandarización robusta de nombres de columna
            df_temp.columns = df_temp.columns.str.lower().str.strip()
            if 'est_alum' in df_temp.columns:
                df_temp.rename(columns={'est_alum': 'est_alum'}, inplace=True)
            df_temp.columns = df_temp.columns.str.replace(' ', '_').str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

            dataframes_nuevos[key] = df_temp
        except Exception as e:
            print(f"Error crítico cargando el archivo para '{key}': {e}")
            return False

    # Estandarización de la columna de ID de estudiante en todos los dataframes
    mapeo_id = {'ide_estudiante': 'id_estudiante', 'cedula': 'id_estudiante', 'num_identificacion': 'id_estudiante', 'identificacion': 'id_estudiante'}
    for df in dataframes_nuevos.values():
        df.rename(columns=mapeo_id, inplace=True)
        if 'id_estudiante' in df.columns:
            df['id_estudiante'] = df['id_estudiante'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    # 2. Enriquecimiento de Datos (Feature Engineering)
    if "notas" not in dataframes_nuevos or "caracterizacion" not in dataframes_nuevos:
        print("Error: Los reportes de 'Notas' y 'Caracterización' son esenciales y no se encontraron.")
        return False
    
    # Excluir estudiantes graduados/egresados ANTES de cualquier otro procesamiento
    caracterizacion_df = dataframes_nuevos["caracterizacion"]
    if 'est_alum' in caracterizacion_df.columns:
        estados_a_excluir = ['--', '---', 'GRADUADO', 'EGRESADO']
        caracterizacion_df['est_alum'] = caracterizacion_df['est_alum'].astype(str).str.strip().str.upper()
        caracterizacion_df = caracterizacion_df[~caracterizacion_df['est_alum'].isin(estados_a_excluir)]
        dataframes_nuevos["caracterizacion"] = caracterizacion_df
        print(f" -> Se han excluido estudiantes graduados/egresados. Población activa: {len(caracterizacion_df)}")

    # Iniciar la construcción del DataFrame final a partir de las notas
    df_new = dataframes_nuevos["notas"].groupby('id_estudiante').agg(
        promedio_semestral=('def_historia', 'mean'),
        num_materias_cursadas=('nom_materia', 'nunique'),
        num_materias_reprobadas=('def_historia', lambda x: (pd.to_numeric(x, errors='coerce') < 3.0).sum())
    ).reset_index()

    # Unir con datos de Caracterización
    caracterizacion_df['es_foraneo'] = (~caracterizacion_df['lugar_residencia'].astype(str).str.upper().str.contains('CALI', na=False)).astype(int)
    if 'experiencia_laboral' in caracterizacion_df.columns:
        caracterizacion_df['experiencia_laboral'] = caracterizacion_df['experiencia_laboral'].astype(str).str.upper().map(
            {'SI': 1, 'NO': 0}
        ).fillna(-1)
    
    cols_a_unir = [
        'id_estudiante', 'edad', 'genero', 'num_est_economico', 'etnia', 
        'estado_civil', 'programa', 'periodo_ingreso', 'es_foraneo', 
        'experiencia_laboral', 'num_grupo_fam', 'posicion_hermanos', 'est_alum'
    ]
    cols_existentes = [col for col in cols_a_unir if col in caracterizacion_df.columns]
    demografia_unicos = caracterizacion_df[cols_existentes].groupby('id_estudiante').last().reset_index()
    df_new = pd.merge(df_new, demografia_unicos, on='id_estudiante', how='left')

    # Unir con datos de Discapacidad
    if 'discapacidad' in dataframes_nuevos:
        discapacidad_df = dataframes_nuevos['discapacidad']
        if 'id_estudiante' in discapacidad_df.columns and 'discapacidad' in discapacidad_df.columns:
            discapacidad_unicos = discapacidad_df[['id_estudiante', 'discapacidad']].groupby('id_estudiante').last().reset_index()
            df_new = pd.merge(df_new, discapacidad_unicos, on='id_estudiante', how='left')

    # Unir con datos Financieros
    if 'pagos' in dataframes_nuevos:
        pagos_df = dataframes_nuevos['pagos'].copy()
        pagos_df['fecha_pago'] = pd.to_datetime(pagos_df['fecha_pago'], format='%d/%m/%Y', errors='coerce')
        pagos_unicos = pagos_df.groupby('id_estudiante').last().reset_index()
        year, sem = int(periodo_actual[:4]), periodo_actual[4]
        fecha_vencimiento = datetime(year, 2, 28) if sem == 'A' else datetime(year, 8, 31)
        pagos_unicos['pago_tardio'] = (pagos_unicos['fecha_pago'] > fecha_vencimiento).astype(int)
        pagos_unicos['dias_retraso_pago'] = (pagos_unicos['fecha_pago'] - fecha_vencimiento).dt.days.clip(lower=0)
        df_new = pd.merge(df_new, pagos_unicos[['id_estudiante', 'pago_tardio', 'dias_retraso_pago']], on='id_estudiante', how='left')

    # Calcular características de Tendencia
    df_new['diferencia_promedio_anterior'] = 0
    def periodo_a_numero(p):
        try: return int(p[:4]) * 2 + (1 if p[4] == 'A' else 2)
        except: return np.nan
        
    if 'periodo_ingreso' in df_new.columns:
        periodo_actual_num = periodo_a_numero(periodo_actual)
        df_new['periodo_ingreso_num'] = df_new['periodo_ingreso'].astype(str).apply(periodo_a_numero)
        df_new['antiguedad_estudiante'] = (periodo_actual_num - df_new['periodo_ingreso_num']) + 1
        df_new.drop(columns=['periodo_ingreso_num'], inplace=True)

    # 3. Limpieza Final antes de Guardar
    numeric_cols = df_new.select_dtypes(include=np.number).columns
    df_new[numeric_cols] = df_new[numeric_cols].fillna(0)
    print(" -> Valores NaN en columnas numéricas han sido reemplazados por 0.")
    
    # 4. Guardar en Base de Datos y Calcular Riesgo
    model_fields = [field.name for field in EstudiantePeriodo._meta.get_fields()]
    print("Guardando estudiantes y calculando riesgo inicial...")
    for _, row in df_new.iterrows():
        defaults_data = {key: value for key, value in row.to_dict().items() if key in model_fields}
        
        obj, created = EstudiantePeriodo.objects.update_or_create(
            id_estudiante=row['id_estudiante'],
            periodo=periodo_actual,
            defaults=defaults_data
        )

        prediccion = PredictionService.predict(obj.id_estudiante, obj.periodo)
        if not prediccion.get('error'):
            obj.ultima_prob_riesgo = prediccion.get('probabilidad')
            obj.save()
            
    print("¡Proceso de carga y cálculo de riesgo completado!")
    return True




def validar_predicciones_con_lista_activos(periodo_prediccion, ids_estudiantes_activos):
    """
    Compara las predicciones de un periodo contra una lista explícita de IDs de estudiantes
    que se consideran "activos" o que no desertaron.
    """
    umbral = settings.UMBRAL_PREDICCION

    # 1. Obtener a todos los estudiantes que se predijeron en el periodo de interés
    estudiantes_a_evaluar = EstudiantePeriodo.objects.filter(periodo=periodo_prediccion)

    if not estudiantes_a_evaluar.exists():
        return {"error": f"No se encontraron datos para el periodo de predicción {periodo_prediccion}."}

    # 2. Clasificar a cada estudiante basado en la lista de IDs activos
    verdaderos_positivos = [] # Predijimos riesgo, y desertaron (no están en la lista de activos)
    falsos_positivos = []    # Predijimos riesgo, pero no desertaron (sí están en la lista de activos)
    falsos_negativos = []    # No predijimos riesgo, pero desertaron (no están en la lista de activos)
    verdaderos_negativos = [] # No predijimos riesgo, y no desertaron (sí están en la lista de activos)
    
    total_deserciones_reales = 0

    for estudiante in estudiantes_a_evaluar:
        prediccion_fue_riesgo = (estudiante.ultima_prob_riesgo is not None and estudiante.ultima_prob_riesgo >= umbral)
        # El estudiante NO desertó si su ID está en la lista de activos que subimos
        no_deserto_realmente = estudiante.id_estudiante in ids_estudiantes_activos

        if not no_deserto_realmente:
            total_deserciones_reales += 1

        if prediccion_fue_riesgo and not no_deserto_realmente:
            verdaderos_positivos.append(estudiante)
        elif prediccion_fue_riesgo and no_deserto_realmente:
            falsos_positivos.append(estudiante)
        elif not prediccion_fue_riesgo and not no_deserto_realmente:
            falsos_negativos.append(estudiante)
        elif not prediccion_fue_riesgo and no_deserto_realmente:
            verdaderos_negativos.append(estudiante)

    # 3. Calcular Métricas
    tp = len(verdaderos_positivos)
    fp = len(falsos_positivos)
    fn = len(falsos_negativos)
    
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0

    return {
        'periodo_prediccion': periodo_prediccion,
        'total_estudiantes_evaluados': len(estudiantes_a_evaluar),
        'total_deserciones_reales': total_deserciones_reales,
        'recall': recall * 100,
        'precision': precision * 100,
        'verdaderos_positivos': verdaderos_positivos,
        'falsos_positivos': falsos_positivos,
        'falsos_negativos': falsos_negativos,
    }