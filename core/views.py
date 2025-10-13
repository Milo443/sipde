# core/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
import json

import pandas as pd
from .models import EstudiantePeriodo
from .predictions import PredictionService
from .services import validar_predicciones_con_lista_activos

def dashboard_view(request):
    # Obtener todos los periodos únicos que existen en la base de datos para el desplegable
    periodos_disponibles = EstudiantePeriodo.objects.values_list('periodo', flat=True).distinct().order_by('-periodo')

    # === INICIO DE LA LÓGICA DE SELECCIÓN DE PERIODO ===
    # 1. Determinar el periodo a mostrar
    periodo_seleccionado = request.GET.get('periodo')
    if not periodo_seleccionado and periodos_disponibles:
        periodo_seleccionado = periodos_disponibles[0] # Usar el más reciente por defecto
    # === FIN DE LA LÓGICA DE SELECCIÓN DE PERIODO ===

    context = {
        'periodos_disponibles': periodos_disponibles,
        'periodo_seleccionado': periodo_seleccionado,
        'total_estudiantes': 0,
        'riesgo_alto_count': 0,
        'tasa_retencion': "N/A",
        'chart_distribucion_data': json.dumps({'labels': [], 'data': []}),
        'chart_antiguedad_data': json.dumps({'labels': [], 'data': []}),
    }

    if periodo_seleccionado:
        # 2. Cargar los datos del periodo seleccionado
        estudiantes = EstudiantePeriodo.objects.filter(periodo=periodo_seleccionado)
        
        total_estudiantes = estudiantes.count()

        if total_estudiantes > 0:
            riesgo_alto_count = estudiantes.filter(
                ultima_prob_riesgo__gte=settings.UMBRAL_PREDICCION
            ).count()
            riesgo_bajo_count = total_estudiantes - riesgo_alto_count

            chart_distribucion_data = {
                'labels': ['En Riesgo', 'Sin Riesgo'],
                'data': [riesgo_alto_count, riesgo_bajo_count],
            }

            antiguedad_data = {}
            for est in estudiantes.filter(ultima_prob_riesgo__gte=settings.UMBRAL_PREDICCION, antiguedad_estudiante__isnull=False):
                sem = f"Sem {int(est.antiguedad_estudiante)}"
                antiguedad_data[sem] = antiguedad_data.get(sem, 0) + 1
            
            sorted_keys = sorted(antiguedad_data.keys(), key=lambda x: int(x.split(' ')[1]))
            chart_antiguedad_data = {
                'labels': sorted_keys,
                'data': [antiguedad_data[key] for key in sorted_keys]
            }

            context.update({
                'total_estudiantes': total_estudiantes,
                'riesgo_alto_count': riesgo_alto_count,
                'tasa_retencion': f"{(riesgo_bajo_count / total_estudiantes * 100):.1f}%",
                'chart_distribucion_data': json.dumps(chart_distribucion_data),
                'chart_antiguedad_data': json.dumps(chart_antiguedad_data),
            })

    return render(request, 'dashboard.html', context)

    latest_period_obj = EstudiantePeriodo.objects.order_by('-periodo').first()
    context = {
        'periodo_analizado': "N/A",
        'total_estudiantes': 0,
        'riesgo_alto_count': 0,
        'tasa_retencion': "N/A",
        'chart_distribucion_data': json.dumps({'labels': [], 'data': []}),
        'chart_antiguedad_data': json.dumps({'labels': [], 'data': []}),
    }

    if latest_period_obj:
        latest_period = latest_period_obj.periodo
        estudiantes = EstudiantePeriodo.objects.filter(periodo=latest_period)
        
        total_estudiantes = estudiantes.count()

        if total_estudiantes > 0:
            riesgo_alto_count = estudiantes.filter(
                ultima_prob_riesgo__gte=settings.UMBRAL_PREDICCION
            ).count()
            riesgo_bajo_count = total_estudiantes - riesgo_alto_count

            # Datos para gráfico de distribución
            chart_distribucion_data = {
                'labels': ['En Riesgo', 'Sin Riesgo'],
                'data': [riesgo_alto_count, riesgo_bajo_count],
            }

            # Datos para gráfico de riesgo por antigüedad
            antiguedad_data = {}
            for est in estudiantes.filter(ultima_prob_riesgo__gte=settings.UMBRAL_PREDICCION, antiguedad_estudiante__isnull=False):
                sem = f"Sem {int(est.antiguedad_estudiante)}"
                antiguedad_data[sem] = antiguedad_data.get(sem, 0) + 1
            
            sorted_keys = sorted(antiguedad_data.keys(), key=lambda x: int(x.split(' ')[1]))
            chart_antiguedad_data = {
                'labels': sorted_keys,
                'data': [antiguedad_data[key] for key in sorted_keys]
            }

            context.update({
                'periodo_analizado': latest_period,
                'total_estudiantes': total_estudiantes,
                'riesgo_alto_count': riesgo_alto_count,
                'tasa_retencion': f"{(riesgo_bajo_count / total_estudiantes * 100):.1f}%",
                'chart_distribucion_data': json.dumps(chart_distribucion_data),
                'chart_antiguedad_data': json.dumps(chart_antiguedad_data),
            })

    return render(request, 'dashboard.html', context)


@login_required
def lista_estudiantes_view(request):
    latest_period_obj = EstudiantePeriodo.objects.order_by('-periodo').first()
    
    if latest_period_obj:
        # 1. Empezamos con el queryset base (todos los estudiantes del último periodo)
        queryset = EstudiantePeriodo.objects.filter(
            periodo=latest_period_obj.periodo
        ).order_by('-ultima_prob_riesgo')
        
        # 2. Obtenemos los valores de los filtros desde la URL (request.GET)
        query_id = request.GET.get('q')
        filtro_riesgo = request.GET.get('riesgo')
        
        # 3. Aplicamos los filtros al queryset si existen
        if query_id:
            queryset = queryset.filter(id_estudiante__icontains=query_id)
            
        if filtro_riesgo == 'con_riesgo':
            queryset = queryset.filter(ultima_prob_riesgo__gte=settings.UMBRAL_PREDICCION)
        elif filtro_riesgo == 'sin_riesgo':
            queryset = queryset.filter(ultima_prob_riesgo__lt=settings.UMBRAL_PREDICCION)

    else:
        queryset = EstudiantePeriodo.objects.none() # Queryset vacío si no hay datos

    # 4. La paginación se aplica al queryset ya filtrado
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'umbral': settings.UMBRAL_PREDICCION,
        # Pasamos los filtros de vuelta a la plantilla para mantener el estado del formulario
        'filtros_aplicados': request.GET 
    }
    return render(request, 'lista_estudiantes.html', context)

@login_required
def detalle_estudiante_view(request, id_estudiante):
    historial_estudiante = EstudiantePeriodo.objects.filter(id_estudiante=id_estudiante).order_by('-periodo')
    
    if not historial_estudiante.exists():
        return render(request, 'detalle_estudiante.html', {'error': 'Estudiante no encontrado.'})

    estudiante_actual = historial_estudiante.first()
    
    prediccion = PredictionService.predict(id_estudiante, estudiante_actual.periodo)

    prob_porcentaje = 0
    umbral_porcentaje = 0
    if not prediccion.get('error'):
        prob_porcentaje = prediccion.get('probabilidad', 0) * 100
        umbral_porcentaje = prediccion.get('umbral_usado', 0) * 100

    context = {
        'estudiante': estudiante_actual,
        'historial': historial_estudiante,
        'prediccion': prediccion,
        'prob_porcentaje': prob_porcentaje,
        'umbral_porcentaje': umbral_porcentaje,
    }
    return render(request, 'detalle_estudiante.html', context)




@login_required
def validacion_view(request):
    periodos_disponibles = EstudiantePeriodo.objects.values_list('periodo', flat=True).distinct().order_by('-periodo')
    
    context = {
        'periodos_disponibles': periodos_disponibles,
    }

    if request.method == 'POST':
        periodo_prediccion = request.POST.get('periodo_prediccion')
        archivo_activos = request.FILES.get('archivo_activos')

        if periodo_prediccion and archivo_activos:
            try:
                # === INICIO DE LA SOLUCIÓN DEFINITIVA PARA LECTURA DE ARCHIVOS ===
                archivo_nombre = archivo_activos.name
                df_activos = None # Inicializar el DataFrame como Nulo

                if archivo_nombre.lower().endswith('.csv'):
                    # Lista de codificaciones comunes a probar en orden de probabilidad
                    encodings_to_try = ['cp1252', 'latin1', 'utf-8']
                    
                    for encoding in encodings_to_try:
                        try:
                            print(f"Intentando leer CSV con codificación: '{encoding}'...")
                            # Es crucial resetear el puntero del archivo en cada intento
                            archivo_activos.seek(0)
                            df_activos = pd.read_csv(archivo_activos, sep=';', encoding=encoding, low_memory=False)
                            print(f"¡Éxito! Archivo leído correctamente con '{encoding}'.")
                            break # Si la lectura es exitosa, salimos del bucle
                        except UnicodeDecodeError:
                            print(f"Falló la lectura con '{encoding}'. Probando siguiente...")
                            continue # Si falla, continuamos con la siguiente codificación

                    # Si después de todos los intentos el DataFrame sigue siendo Nulo, lanzamos un error
                    if df_activos is None:
                        raise ValueError("No se pudo decodificar el archivo con las codificaciones comunes (cp1252, latin1, utf-8).")

                elif archivo_nombre.lower().endswith(('.xls', '.xlsx')):
                    df_activos = pd.read_excel(archivo_activos)
                else:
                    raise ValueError("Formato de archivo no soportado. Por favor, sube un archivo .csv o .xlsx.")
                # === FIN DE LA SOLUCIÓN DEFINITIVA ===
                
                # Estandarizar nombres de columna para consistencia
                df_activos.columns = df_activos.columns.str.lower().str.strip()
                if 'est_alum' in df_activos.columns:
                    df_activos.rename(columns={'est_alum': 'est_alum'}, inplace=True)
                if 'cedula' not in df_activos.columns:
                     raise ValueError("La columna 'cedula' no se encontró en el archivo.")

                # Filtrar por estado del alumno
                ids_activos = set()
                if 'est_alum' in df_activos.columns:
                    estados_continuidad = ['ACTIVO', 'EGRESADO', 'GRADUADO']
                    df_activos['est_alum'] = df_activos['est_alum'].astype(str).str.strip().str.upper()
                    df_filtrado = df_activos[df_activos['est_alum'].isin(estados_continuidad)]
                    ids_activos = set(df_filtrado['cedula'].astype(str).str.strip())
                    print(f"Se encontraron {len(ids_activos)} estudiantes con estado de continuidad en el archivo subido.")
                else:
                    raise ValueError("La columna 'est_alum' es necesaria para la validación y no se encontró en el archivo.")

                # Llamar al servicio de validación con la lista de IDs filtrada
                resultados_validacion = validar_predicciones_con_lista_activos(periodo_prediccion, ids_activos)
                context['resultados'] = resultados_validacion

                # Línea de diagnóstico adicional
                print("\n--- RESULTADOS DE LA VALIDACIÓN ---")
                print({k: v for k, v in resultados_validacion.items() if not isinstance(v, list)})
                print("---------------------------------\n")

            except Exception as e:
                context['error'] = f"Error al procesar el archivo: {e}."
        else:
            context['error'] = "Por favor, selecciona un periodo y sube el archivo de activos."

    return render(request, 'validacion.html', context)

