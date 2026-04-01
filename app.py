tasks1 = [
    {"Task": "1: Instalación eléctrica", "Level": 0, "Parent": None, "Start": None, "Finish": None, "Status": None},
    {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: Instalación eléctrica", "Start": None, "Finish": None, "Status": None},
    {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date, "Finish": base_date + timedelta(days=5), "Status": "En curso"},
    # ... resto nivel 1 y 2 ...
]

tasks2 = [
    {"Task": "2: Comunicaciones", "Level": 0, "Parent": None, "Start": None, "Finish": None, "Status": None},
    {"Task": "Tendido Cableado", "Level": 1, "Parent": "2: Comunicaciones", "Start": None, "Finish": None, "Status": None},
    # ... resto ...
]

tasks3 = [
    {"Task": "3: Sensores", "Level": 0, "Parent": None, "Start": None, "Finish": None, "Status": None},
    # ...
]

# Concatenar todas las secciones
tasks = tasks1 + tasks2 + tasks3  # + tasks5 + tasks6 + tasks7
