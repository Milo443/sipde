# core/admin.py

from django.contrib import admin, messages
from .models import LoteCargaDatos, EstudiantePeriodo
from .services import procesar_y_guardar_datos_de_periodo

@admin.register(EstudiantePeriodo)
class EstudiantePeriodoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administrador para el modelo EstudiantePeriodo.
    Permite ver, buscar y filtrar los datos de los estudiantes ya procesados.
    """
    list_display = ('id_estudiante', 'periodo', 'promedio_semestral', 'ultima_prob_riesgo', 'est_alum')
    search_fields = ('id_estudiante', 'periodo')
    list_filter = ('periodo', 'discapacidad', 'programa', 'est_alum')
    readonly_fields = ('id_estudiante', 'periodo') # Campos que no deberían ser editados manualmente

@admin.register(LoteCargaDatos)
class LoteCargaDatosAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administrador para el modelo LoteCargaDatos.
    Gestiona la carga de nuevos reportes y permite el reprocesamiento de lotes existentes.
    """
    list_display = ('periodo', 'fecha_carga', 'procesado')
    readonly_fields = ('procesado',)
    actions = ['reprocesar_lotes_seleccionados'] # Registra la nueva acción

    @admin.action(description="Reprocesar lotes de datos seleccionados")
    def reprocesar_lotes_seleccionados(self, request, queryset):
        """
        Acción personalizada que borra los datos procesados antiguos y vuelve a ejecutar
        el servicio de procesamiento sobre los archivos del lote seleccionado.
        """
        lotes_procesados_con_exito = 0
        for lote in queryset:
            print(f"Iniciando reprocesamiento para el periodo {lote.periodo}...")
            
            # Paso 1: Limpiar los datos viejos de este periodo para evitar duplicados
            registros_borrados, _ = EstudiantePeriodo.objects.filter(periodo=lote.periodo).delete()
            print(f"Se eliminaron {registros_borrados} registros antiguos del periodo {lote.periodo}.")

            # Paso 2: Preparar y ejecutar el servicio de procesamiento
            archivos_cargados = {
                'caracterizacion': lote.reporte_caracterizacion.path,
                'notas': lote.reporte_notas.path,
                'pagos': lote.reporte_pagos.path,
                'discapacidad': lote.reporte_discapacidad.path,
            }
            
            exito = procesar_y_guardar_datos_de_periodo(archivos_cargados, lote.periodo)

            # Paso 3: Actualizar el estado del lote y notificar al usuario
            if exito:
                lote.procesado = True
                lote.save()
                lotes_procesados_con_exito += 1
            else:
                self.message_user(
                    request,
                    f"Ocurrió un error al reprocesar el lote para el periodo {lote.periodo}. Revisa los logs del servidor.",
                    messages.ERROR
                )
        
        if lotes_procesados_con_exito > 0:
            self.message_user(
                request,
                f"{lotes_procesados_con_exito} lote(s) de datos fueron reprocesados exitosamente.",
                messages.SUCCESS
            )

    def save_model(self, request, obj, form, change):
        """
        Sobrescribe el método de guardado para ejecutar el procesamiento de datos
        únicamente la primera vez que se crea un lote.
        """
        # El guardado inicial del objeto ocurre primero para que los archivos estén disponibles
        super().save_model(request, obj, form, change)
        
        # 'change' es Falso cuando se está creando un nuevo objeto
        if not change:
            archivos_cargados = {
                'caracterizacion': obj.reporte_caracterizacion.path,
                'notas': obj.reporte_notas.path,
                'pagos': obj.reporte_pagos.path,
                'discapacidad': obj.reporte_discapacidad.path,
            }
            
            print("Procesando lote por primera vez...")
            exito = procesar_y_guardar_datos_de_periodo(archivos_cargados, obj.periodo)
            
            if exito:
                obj.procesado = True
                obj.save()
                messages.success(request, f"Archivos del periodo {obj.periodo} procesados y guardados exitosamente.")
            else:
                messages.error(request, "Hubo un error al procesar los archivos. Revisa los logs del servidor.")