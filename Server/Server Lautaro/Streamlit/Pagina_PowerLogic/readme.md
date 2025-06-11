<<<<<<< HEAD
# 📊 PowerLogic 4000 Monitor

Sistema de monitoreo y visualización de parámetros eléctricos basado en Streamlit para equipos PowerLogic 4000 de Schneider Electric™.

## 🎯 Descripción

Esta aplicación web permite visualizar y analizar datos de monitoreo eléctrico de forma interactiva, proporcionando gráficos en tiempo real de parámetros críticos como potencia, tensión, corriente y factor de potencia por fase (R, S, T).

## ✨ Características

- **📈 Visualización Interactiva**: Gráficos dinámicos con Plotly para análisis detallado
- **🔄 Datos Multifase**: Monitoreo independiente de las tres fases eléctricas (R, S, T)
- **📅 Filtrado Temporal**: Selección de rangos de fechas personalizables
- **📊 Múltiples Parámetros**: 
  - Potencia Activa (kW)
  - Potencia Reactiva (kVAR) 
  - Potencia Aparente (kVA)
  - Demanda de Potencia Activa
  - Tensión por fase (V)
  - Corriente por fase (A)
  - Factor de Potencia
- **💾 Exportación**: Descarga de datos en formato CSV y Excel
- **🎨 Interfaz Moderna**: Diseño responsive con sidebar de configuración

## 🗂️ Estructura de Datos

### Fuente de Datos Actual

La aplicación actualmente utiliza **datos simulados** almacenados en:
```
powerlogic_simulated_data.csv
```

### Formato de Datos

El archivo CSV contiene las siguientes columnas:

| Campo | Descripción | Unidad |
|-------|-------------|---------|
| `timestamp` | Fecha y hora del registro | YYYY-MM-DD HH:MM:SS |
| `phase` | Fase eléctrica | R, S, T |
| `Active_Power` | Potencia activa | kW |
| `Reactive_Power` | Potencia reactiva | kVAR |
| `Apparent_Power` | Potencia aparente | kVA |
| `Voltage` | Tensión | V |
| `Current` | Corriente | A |
| `Power_Factor` | Factor de potencia | 0.0 - 1.0 |
| `Active_Power_Demand` | Demanda de potencia activa | kW |

### Generación de Datos Simulados

Si el archivo `powerlogic_simulated_data.csv` no existe, la aplicación automáticamente:

1. **Genera 14 días de datos** (desde 2025-05-20)
2. **Registros cada 15 minutos** para las tres fases
3. **Patrones diarios realistas** con picos de consumo a las 14:00
4. **Variaciones aleatorias** para simular condiciones reales
5. **Parámetros eléctricos coherentes** (tensión nominal ~220V)

## 🚀 Instalación y Uso

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar el repositorio**:
```bash
git clone <URL_DEL_REPOSITORIO>
cd powerlogic-monitor
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación**:
```bash
streamlit run pagina.py
```

4. **Abrir en navegador**:
   - La aplicación se abrirá automáticamente en `http://localhost:8501`
   - O seguir la URL mostrada en la terminal

## 🎮 Uso de la Aplicación

### Panel de Control (Sidebar)

- **📅 Selector de Fechas**: Filtra datos por rango temporal
- **⚙️ Selector de Fases**: Muestra/oculta fases específicas (R, S, T)
- **🔄 Actualizar Datos**: Recarga el cache de datos
- **🗑️ Regenerar Datos**: Crea nuevos datos simulados

### Pestañas Principales

#### 1. 📈 Potencia
- Gráficos de potencia activa, reactiva, aparente y demanda
- Visualización por fase con colores distintivos

#### 2. ⚡ Energía  
- Monitoreo de tensión y corriente por fase
- Factor de potencia del sistema

#### 3. 📥 Datos
- Tabla de datos crudos con filtros aplicados
- Exportación a CSV y Excel
- Contador de registros

## 🔧 Configuración Avanzada

### Personalización de Datos

Para usar **datos reales** en lugar de simulados:

1. Reemplaza `powerlogic_simulated_data.csv` con tu archivo de datos
2. Asegúrate de que tenga la estructura de columnas correcta
3. Reinicia la aplicación

### Modificación de Parámetros

En el código `pagina.py` puedes ajustar:

- **Rango de fechas**: Modifica `start_date` y `end_date`
- **Intervalo de muestreo**: Cambia `interval = timedelta(minutes=15)`
- **Parámetros eléctricos**: Ajusta valores base en `daily_pattern()`

## 📋 Dependencias

```text
streamlit>=1.28.0    # Framework web
pandas>=2.0.0        # Manipulación de datos
numpy>=1.24.0        # Cálculos numéricos
plotly>=5.15.0       # Gráficos interactivos
openpyxl>=3.1.0      # Exportación Excel
```

## 🐛 Solución de Problemas

### Error: "Missing column 'timestamp'"
- La aplicación detecta automáticamente archivos CSV corruptos
- Usa el botón "🗑️ Regenerar Datos" para crear nuevos datos

### Error: "No module named 'openpyxl'"
- Ejecuta: `pip install openpyxl`
- O usa solo exportación CSV (disponible sin dependencias adicionales)

### Warnings de ScriptRunContext
- Son normales al ejecutar con `python3 pagina.py`
- Usa `streamlit run pagina.py` para evitarlos

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📧 Contacto

Para reportar bugs o solicitar nuevas funcionalidades, crear un issue en el repositorio.

---

=======
# 📊 PowerLogic 4000 Monitor

Sistema de monitoreo y visualización de parámetros eléctricos basado en Streamlit para equipos PowerLogic 4000 de Schneider Electric™.

## 🎯 Descripción

Esta aplicación web permite visualizar y analizar datos de monitoreo eléctrico de forma interactiva, proporcionando gráficos en tiempo real de parámetros críticos como potencia, tensión, corriente y factor de potencia por fase (R, S, T).

## ✨ Características

- **📈 Visualización Interactiva**: Gráficos dinámicos con Plotly para análisis detallado
- **🔄 Datos Multifase**: Monitoreo independiente de las tres fases eléctricas (R, S, T)
- **📅 Filtrado Temporal**: Selección de rangos de fechas personalizables
- **📊 Múltiples Parámetros**: 
  - Potencia Activa (kW)
  - Potencia Reactiva (kVAR) 
  - Potencia Aparente (kVA)
  - Demanda de Potencia Activa
  - Tensión por fase (V)
  - Corriente por fase (A)
  - Factor de Potencia
- **💾 Exportación**: Descarga de datos en formato CSV y Excel
- **🎨 Interfaz Moderna**: Diseño responsive con sidebar de configuración

## 🗂️ Estructura de Datos

### Fuente de Datos Actual

La aplicación actualmente utiliza **datos simulados** almacenados en:
```
powerlogic_simulated_data.csv
```

### Formato de Datos

El archivo CSV contiene las siguientes columnas:

| Campo | Descripción | Unidad |
|-------|-------------|---------|
| `timestamp` | Fecha y hora del registro | YYYY-MM-DD HH:MM:SS |
| `phase` | Fase eléctrica | R, S, T |
| `Active_Power` | Potencia activa | kW |
| `Reactive_Power` | Potencia reactiva | kVAR |
| `Apparent_Power` | Potencia aparente | kVA |
| `Voltage` | Tensión | V |
| `Current` | Corriente | A |
| `Power_Factor` | Factor de potencia | 0.0 - 1.0 |
| `Active_Power_Demand` | Demanda de potencia activa | kW |

### Generación de Datos Simulados

Si el archivo `powerlogic_simulated_data.csv` no existe, la aplicación automáticamente:

1. **Genera 14 días de datos** (desde 2025-05-20)
2. **Registros cada 15 minutos** para las tres fases
3. **Patrones diarios realistas** con picos de consumo a las 14:00
4. **Variaciones aleatorias** para simular condiciones reales
5. **Parámetros eléctricos coherentes** (tensión nominal ~220V)

## 🚀 Instalación y Uso

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar el repositorio**:
```bash
git clone <URL_DEL_REPOSITORIO>
cd powerlogic-monitor
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación**:
```bash
streamlit run pagina.py
```

4. **Abrir en navegador**:
   - La aplicación se abrirá automáticamente en `http://localhost:8501`
   - O seguir la URL mostrada en la terminal

## 🎮 Uso de la Aplicación

### Panel de Control (Sidebar)

- **📅 Selector de Fechas**: Filtra datos por rango temporal
- **⚙️ Selector de Fases**: Muestra/oculta fases específicas (R, S, T)
- **🔄 Actualizar Datos**: Recarga el cache de datos
- **🗑️ Regenerar Datos**: Crea nuevos datos simulados

### Pestañas Principales

#### 1. 📈 Potencia
- Gráficos de potencia activa, reactiva, aparente y demanda
- Visualización por fase con colores distintivos

#### 2. ⚡ Energía  
- Monitoreo de tensión y corriente por fase
- Factor de potencia del sistema

#### 3. 📥 Datos
- Tabla de datos crudos con filtros aplicados
- Exportación a CSV y Excel
- Contador de registros

## 🔧 Configuración Avanzada

### Personalización de Datos

Para usar **datos reales** en lugar de simulados:

1. Reemplaza `powerlogic_simulated_data.csv` con tu archivo de datos
2. Asegúrate de que tenga la estructura de columnas correcta
3. Reinicia la aplicación

### Modificación de Parámetros

En el código `pagina.py` puedes ajustar:

- **Rango de fechas**: Modifica `start_date` y `end_date`
- **Intervalo de muestreo**: Cambia `interval = timedelta(minutes=15)`
- **Parámetros eléctricos**: Ajusta valores base en `daily_pattern()`

## 📋 Dependencias

```text
streamlit>=1.28.0    # Framework web
pandas>=2.0.0        # Manipulación de datos
numpy>=1.24.0        # Cálculos numéricos
plotly>=5.15.0       # Gráficos interactivos
openpyxl>=3.1.0      # Exportación Excel
```

## 🐛 Solución de Problemas

### Error: "Missing column 'timestamp'"
- La aplicación detecta automáticamente archivos CSV corruptos
- Usa el botón "🗑️ Regenerar Datos" para crear nuevos datos

### Error: "No module named 'openpyxl'"
- Ejecuta: `pip install openpyxl`
- O usa solo exportación CSV (disponible sin dependencias adicionales)

### Warnings de ScriptRunContext
- Son normales al ejecutar con `python3 pagina.py`
- Usa `streamlit run pagina.py` para evitarlos

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📧 Contacto

Para reportar bugs o solicitar nuevas funcionalidades, crear un issue en el repositorio.

---

>>>>>>> bb7f761b1fe8c713249ab87d0753ed0f4860f6a1
**© 2025 Schneider Electric - Power Monitoring System | v1.0**