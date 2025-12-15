TURQUOISE = "#00b4aa"
TEXT_COLOR = "#000000"
BG_COLOR = "#ffffff"

TYTO_ORANGE = (243, 146, 0)
AXIS_COLOR = (60, 60, 60)
GRID_ALPHA = 0.18

# Tipik drone motor testi için mantıklı sabit Y aralıkları
FIXED_RANGES = {
    "thrust_kgf": (0.0, 10.0),       # 0–10 kgf
    "voltage": (0.0, 30.0),          # 0–30 V (3–12S LiPo)
    "current": (0.0, 80.0),          # 0–80 A
    "rpm": (0.0, 40000.0),           # 0–40k RPM
    "temperature": (20.0, 100.0),    # 20–100 °C
    "power": (0.0, 3000.0),          # 0–3 kW
    "pt_eff": (0.0, 0.03),           # 0–0.03 kgf/W
    "tpa": (0.0, 0.2),               # 0–0.2 kgf/A
}

PLOT_TITLES = {
    "thrust_kgf": "Thrust (kgf)",
    "voltage": "Voltage (V)",
    "current": "Current (A)",
    "rpm": "Motor Speed (RPM)",
    "temperature": "Temperature (°C)",
    "power": "Electrical Power (W)",
    "pt_eff": "PT Efficiency (kgf/W)",
    "tpa": "Thrust per Amp (kgf/A)",
}
