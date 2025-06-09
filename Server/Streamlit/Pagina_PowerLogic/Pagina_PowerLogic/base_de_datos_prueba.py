import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=== Generador de Datos PowerLogic 4000 ===")
print("Generando datos simulados del equipo PowerLogic...")

# Configuración de parámetros de simulación
start_date = datetime(2025, 5, 14)
end_date = datetime(2025, 6, 8)  # Fecha fija hasta el 9 de junio
interval = timedelta(minutes=15)  # Mediciones cada 15 minutos
phases = ['R', 'S', 'T']

print(f"Período de simulación: {start_date.date()} al {end_date.date()}")

# Generar rango de fechas
date_range = pd.date_range(start=start_date, end=end_date, freq=interval)
num_records = len(date_range)

print(f"Generando {num_records} registros por fase...")

# Crear DataFrame vacío
df = pd.DataFrame(index=date_range)

# Función para generar patrones diarios con variabilidad
def daily_pattern(base_value, peak_multiplier, noise_factor=0.1, hour_peak=14):
    """Genera un patrón diario con pico en hora específica"""
    hour = df.index.hour + df.index.minute/60
    pattern = base_value * (1 + (peak_multiplier - 1) * np.exp(-(hour - hour_peak)**2/8))
    noise = np.random.normal(1, noise_factor, num_records)
    return pattern * noise

# Generar datos simulados
print("Generando patrones de potencia...")
df['Active_Power'] = daily_pattern(50, 2.5)  # kW
df['Reactive_Power'] = daily_pattern(20, 2.0)  # kVAR
df['Apparent_Power'] = np.sqrt(df['Active_Power']**2 + df['Reactive_Power']**2)  # kVA

# Generar datos por fase
print("Generando datos por fase (R, S, T)...")
for phase in phases:
    phase_factor = np.random.uniform(0.95, 1.05)  # Variación entre fases
    df[f'Voltage_{phase}'] = 220 * daily_pattern(1, 1.05, 0.02) * phase_factor
    df[f'Current_{phase}'] = (df['Apparent_Power'] * 1000 / 3) / df[f'Voltage_{phase}'] * phase_factor
    df[f'Power_Factor_{phase}'] = np.clip(df['Active_Power'] / (df['Apparent_Power']/3) * phase_factor, 0.8, 1.0)

df['Active_Power_Demand'] = df['Active_Power'].rolling(4, min_periods=1).mean()  # Demanda como promedio de 1 hora

# Reorganizar datos para formato compatible con Streamlit (formato largo)
print("Reestructurando datos...")
records = []
for i, (dt, row) in enumerate(df.iterrows()):
    if i % 1000 == 0:  # Mostrar progreso cada 1000 registros
        print(f"Procesando registro {i+1}/{len(df)}...")
    
    for phase in phases:
        records.append({
            'timestamp': dt,  # Mantener como timestamp de pandas
            'phase': phase,
            'Active_Power': row['Active_Power'] / 3,  # Distribuido por fase
            'Reactive_Power': row['Reactive_Power'] / 3,
            'Apparent_Power': row['Apparent_Power'] / 3,
            'Voltage': row[f'Voltage_{phase}'],
            'Current': row[f'Current_{phase}'],
            'Power_Factor': row[f'Power_Factor_{phase}'],
            'Active_Power_Demand': row['Active_Power_Demand'] / 3 if pd.notna(row['Active_Power_Demand']) else row['Active_Power'] / 3
        })

# Crear DataFrame final
print("Creando DataFrame final...")
final_df = pd.DataFrame(records)

# Guardar en CSV
csv_filename = 'powerlogic_simulated_data.csv'
print(f"Guardando datos en {csv_filename}...")
final_df.to_csv(csv_filename, index=False)

print("\n=== RESUMEN DE DATOS GENERADOS ===")
print(f"✅ Archivo guardado: {csv_filename}")
print(f"📊 Total de registros: {len(final_df):,}")
print(f"📅 Período completo: {start_date.date()} al {end_date.date()}")
print(f"🕐 Intervalo de medición: {interval.total_seconds()/60:.0f} minutos")
print(f"⚡ Fases incluidas: {', '.join(phases)}")

print(f"\n📈 Rango de fechas en el archivo:")
print(f"  - Fecha inicial: {final_df['timestamp'].min()}")
print(f"  - Fecha final: {final_df['timestamp'].max()}")

print(f"\n📋 Primeros 5 registros:")
print(final_df.head()[['timestamp', 'phase', 'Active_Power', 'Voltage']].to_string())

print(f"\n📋 Últimos 5 registros:")
print(final_df.tail()[['timestamp', 'phase', 'Active_Power', 'Voltage']].to_string())

print(f"\n🔄 Para actualizar la aplicación Streamlit:")
print(f"   1. Ve a la aplicación web")
print(f"   2. Presiona el botón '🔄 Actualizar Datos'")
print(f"   3. Los nuevos datos se cargarán automáticamente")

print(f"\n✨ ¡Datos generados exitosamente!")