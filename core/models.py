# core/models.py
from django.db import models

class LoteCargaDatos(models.Model):
    periodo = models.CharField(max_length=10, help_text="Ej: 2025A")
    fecha_carga = models.DateTimeField(auto_now_add=True)
    reporte_caracterizacion = models.FileField(upload_to='uploads/')
    reporte_notas = models.FileField(upload_to='uploads/')
    reporte_pagos = models.FileField(upload_to='uploads/')
    reporte_discapacidad = models.FileField(upload_to='uploads/')
    procesado = models.BooleanField(default=False)

    def __str__(self):
        return f"Carga para el periodo {self.periodo} - {self.fecha_carga.strftime('%Y-%m-%d')}"

class EstudiantePeriodo(models.Model):
    # Campos clave de identificación
    id_estudiante = models.CharField(max_length=50, db_index=True)
    periodo = models.CharField(max_length=10, db_index=True)
    
    # Features (características) del modelo
    promedio_semestral = models.FloatField(null=True, blank=True)
    num_materias_cursadas = models.IntegerField(null=True, blank=True)
    num_materias_reprobadas = models.IntegerField(null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    genero = models.CharField(max_length=50, null=True, blank=True)
    es_foraneo = models.IntegerField(null=True, blank=True)
    pago_tardio = models.IntegerField(null=True, blank=True)
    dias_retraso_pago = models.IntegerField(null=True, blank=True)
    antiguedad_estudiante = models.IntegerField(null=True, blank=True)
    discapacidad = models.CharField(max_length=100, null=True, blank=True)
    
    diferencia_promedio_anterior = models.FloatField(null=True, blank=True)
    estado_civil = models.CharField(max_length=100, null=True, blank=True)
    etnia = models.CharField(max_length=100, null=True, blank=True)
    experiencia_laboral = models.IntegerField(null=True, blank=True) # Usamos Integer para 1 (SI), 0 (NO), -1 (N/A)
    num_est_economico = models.IntegerField(null=True, blank=True)
    num_grupo_fam = models.IntegerField(null=True, blank=True)
    periodo_ingreso = models.CharField(max_length=10, null=True, blank=True)
    posicion_hermanos = models.IntegerField(null=True, blank=True)
    programa = models.CharField(max_length=100, null=True, blank=True)
    
    est_alum = models.CharField(max_length=100, null=True, blank=True, verbose_name="Estado del Alumno")

    # Campo para guardar la última predicción
    ultima_prob_riesgo = models.FloatField(null=True, blank=True)

    @property
    def riesgo_porcentaje(self):
        if self.ultima_prob_riesgo is not None:
            # Multiplica la probabilidad por 100 para obtener el porcentaje
            return self.ultima_prob_riesgo * 100
        return None

    class Meta:
        unique_together = ('id_estudiante', 'periodo')

    def __str__(self):
        return f"{self.id_estudiante} - {self.periodo}"