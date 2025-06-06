import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuración de parámetros de simulación
start_date = datetime(2025, 5, 20)
end_date = start_date + timedelta(days=14)
interval = timedelta(minutes=15)  # Mediciones cada 15 minutos
phases = ['R', 'S', 'T']

# Generar rango de fechas
date_range = pd.date_range(start=start_date, end=end_date, freq=interval)
num_records = len(date_range)

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
df['Active_Power'] = daily_pattern(50, 2.5)  # kW
df['Reactive_Power'] = daily_pattern(20, 2.0)  # kVAR
df['Apparent_Power'] = np.sqrt(df['Active_Power']**2 + df['Reactive_Power']**2)  # kVA

# Generar datos por fase
for phase in phases:
    phase_factor = np.random.uniform(0.95, 1.05)  # Variación entre fases
    df[f'Voltage_{phase}'] = 220 * daily_pattern(1, 1.05, 0.02) * phase_factor
    df[f'Current_{phase}'] = (df['Apparent_Power'] * 1000 / 3) / df[f'Voltage_{phase}'] * phase_factor
    df[f'Power_Factor_{phase}'] = np.clip(df['Active_Power'] / (df['Apparent_Power']/3) * phase_factor, 0.8, 1.0)

df['Active_Power_Demand'] = df['Active_Power'].rolling(4).mean()  # Demanda como promedio de 1 hora

# Reorganizar datos para InfluxDB (formato largo)
records = []
for dt, row in df.iterrows():
    for phase in phases:
        records.append({
            '_time': dt.isoformat() + 'Z',
            '_measurement': 'power_metrics',
            'phase': phase,
            'Active_Power': row['Active_Power'] / 3,  # Distribuido por fase
            'Reactive_Power': row['Reactive_Power'] / 3,
            'Apparent_Power': row['Apparent_Power'] / 3,
            'Voltage': row[f'Voltage_{phase}'],
            'Current': row[f'Current_{phase}'],
            'Power_Factor': row[f'Power_Factor_{phase}'],
            'Active_Power_Demand': row['Active_Power_Demand']
        })

# Crear DataFrame final
final_df = pd.DataFrame(records)

# Guardar en CSV
csv_filename = 'powerlogic_simulated_data.csv'
final_df.to_csv(csv_filename, index=False)

print(f"Datos simulados guardados en {csv_filename}")
print(f"Total de registros: {len(final_df)}")
print(f"Período: {start_date.date()} al {end_date.date()}")