# SIPDE: Sistema de Información para la Prevención de Deserción Estudiantil

SIPDE es una aplicación web desarrollada en Django que operacionaliza un modelo de Machine Learning para predecir el riesgo de deserción estudiantil. Este proyecto transforma la investigación y el modelo predictivo (basado en XGBoost), concebidos en la tesis de grado, en una herramienta de gestión funcional y proactiva para instituciones académicas.

El sistema permite al personal administrativo cargar reportes académicos, visualizar un dashboard con métricas de riesgo en tiempo real, analizar el perfil individual de cada estudiante y validar la efectividad del modelo a lo largo del tiempo.

## ✨ Características Principales

* **Dashboard Interactivo:** Visualización consolidada del estado de la población estudiantil con KPIs (Indicadores Clave de Rendimiento) y gráficos interactivos (distribución de riesgo, riesgo por antigüedad).
* **Gestión de Estudiantes:** Lista completa de estudiantes con un sistema de búsqueda por ID y filtros por estado de riesgo.
* **Vista de 360° del Estudiante:** Página de detalle individual que muestra la predicción de riesgo, información demográfica, estado académico actual e historial de rendimiento.
* **Módulo de Carga de Datos:** Interfaz en el panel de administrador para cargar reportes académicos (en formato `.csv` o `.xlsx`) de nuevos periodos.
* **Procesamiento Inteligente:** Lógica de backend que limpia, enriquece y unifica los datos de los reportes, calcula el riesgo inicial y los almacena en la base de datos.
* **Acción de "Reprocesar":** Funcionalidad avanzada en el panel de administrador para volver a procesar lotes de datos existentes, aplicando la lógica de negocio más reciente.
* **Módulo de Validación del Modelo:** Herramienta experimental para comparar las predicciones de un periodo contra los datos de matrícula reales de un periodo posterior, calculando métricas de rendimiento como **Recall** y **Precisión**.

## 🛠️ Tecnologías Utilizadas

| Categoría          | Tecnología / Librería                          |
| ------------------ | ---------------------------------------------- |
| **Backend** | Python, Django                                 |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript           |
| **Bases de Datos** | SQLite (desarrollo)                            |
| **Machine Learning** | Pandas, NumPy, Scikit-learn, XGBoost, Joblib |
| **Visualización** | Chart.js                                       |

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para configurar y ejecutar el proyecto en un entorno de desarrollo local.

### 1. Prerrequisitos

* Python 3.8 o superior
* Git

### 2. Clonar el Repositorio

```bash
git clone [https://github.com/Milo443/sipde.git](https://github.com/Milo443/sipde.git)
cd sipde
```

### 3. Configurar el Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto.

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 4. Instalar Dependencias

El archivo `requirements.txt` contiene todas las librerías de Python necesarias.

```bash
pip install -r requirements.txt
```

### 5. Configurar la Base de Datos

El proyecto está configurado para usar SQLite por defecto. Solo necesitas aplicar las migraciones para crear las tablas.

```bash
python manage.py migrate
```

### 6. Crear un Superusuario

Necesitarás una cuenta de administrador para acceder al panel de carga de datos.

```bash
python manage.py createsuperuser
```

### 7. Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

¡Listo! Ahora puedes acceder a la aplicación en tu navegador en `http://127.0.0.1:8000/`.

## 📖 Uso de la Aplicación

1. **Entrenar el Modelo (Paso Offline):**
    * Antes de usar la aplicación, debes tener tu modelo `xgboost_final_model.json` y el archivo de columnas `model_columns.pkl` listos.
    * Asegúrate de colocar estos dos archivos en la carpeta `ml_models/` en la raíz del proyecto.
2. **Iniciar Sesión:**
    * Accede a `http://127.0.0.1:8000/login/` y utiliza las credenciales del superusuario que creaste.
3. **Cargar Datos de un Periodo:**
    * Navega al panel de administrador en `http://127.0.0.1:8000/admin/`.
    * Ve a la sección "Lote carga datos" y haz clic en "Añadir".
    * Completa el formulario subiendo los reportes correspondientes y guarda. El sistema procesará los datos automáticamente.
4. **Analizar los Resultados:**
    * Vuelve a la aplicación principal (`http://127.0.0.1:8000/`) para ver el Dashboard actualizado.
    * Navega a la sección "Estudiantes" para buscar, filtrar y analizar la lista de la población estudiantil.

## 👥 Autores

* **Moisés Buitrago Mosquera**
* **Camilo Calderón Castillo**
