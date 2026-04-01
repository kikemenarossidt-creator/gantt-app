# -------------------- GRAFICO GANTT --------------------
st.subheader("📈 Gantt")

df_plot = st.session_state.df.copy()

# Función para formatear el nombre con indentación real y negritas para niveles superiores
def format_task_name(row):
    # Usamos \u00A0 que es el código unicode para espacios que no se colapsan
    indent = "\u00A0" * (int(row["Level"]) * 6) 
    if row["Level"] == 0:
        return f"<b>{row['Task']}</b>"  # Nivel 0 en negrita
    elif row["Level"] == 1:
        return f"{indent}<b>{row['Task']}</b>" # Nivel 1 con sangría y negrita
    else:
        return f"{indent}{row['Task']}" # Nivel 2 solo con sangría

df_plot["Task_display"] = df_plot.apply(format_task_name, axis=1)

# IMPORTANTE: Definimos el orden de las categorías para que no se ordene alfabéticamente
task_order = df_plot["Task_display"].tolist()

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Status",
    # Mantenemos el orden tal cual aparece en el DataFrame
    category_orders={"Task_display": task_order}
)

# Ajustes visuales adicionales
fig.update_yaxes(autorange="reversed") # Tareas de arriba hacia abajo
fig.update_layout(
    xaxis_title="Cronograma",
    yaxis_title=None,
    margin=dict(l=200), # Espacio extra a la izquierda para las etiquetas indentadas
)

st.plotly_chart(fig, use_container_width=True)
