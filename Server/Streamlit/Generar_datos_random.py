import pandas as pd
import numpy as np

# Crear un rango de tiempo de 7 días (1 min de intervalo)
time_index = pd.date_range(start="2024-01-01", periods=7*24*60, freq="1min")

# Función para generar datos simulados
def gen(base, amp, size, noise=0.5):
    return base + amp * np.sin(np.linspace(0, 20*np.pi, size)) + np.random.normal(0, noise, size)

n = len(time_index)
df = pd.DataFrame({
    "_time": time_index,
    "current_r": gen(10, 2, n),
    "current_s": gen(11, 2, n),
    "current_t": gen(12, 2, n),
    "voltage_r": gen(220, 5, n),
    "voltage_s": gen(221, 5, n),
    "voltage_t": gen(222, 5, n),
    "power_active": gen(500, 30, n),
    "power_reactive": gen(200, 20, n),
    "power_apparent": gen(550, 35, n),
    "pf_r": np.clip(gen(0.95, 0.02, n), 0.8, 1.0),
    "pf_s": np.clip(gen(0.94, 0.02, n), 0.8, 1.0),
    "pf_t": np.clip(gen(0.93, 0.02, n), 0.8, 1.0),
})

# Guardar CSV
df.to_csv("datos_fake_powerlogic.csv", index=False)
print("✅ CSV generado: datos_fake_powerlogic.csv")
