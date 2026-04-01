# --- GRÁFICO ALTAIR (UNA SOLA COLUMNA CON SANGRÍA OPTIMIZADA) ---

# Ajustamos la sangría: 4 espacios por nivel suelen ser suficientes para que se vea claro pero compacto
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 4 * int(x['Level']) + x['Task'], axis=1)

h = len(df_chart) * 22
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

# Una sola columna de texto para evitar los huecos rojos que marcaste antes
base_text = alt.Chart(df_chart).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='Display_Task:N'
).properties(width=300, height=h) # Ancho fijo para que el texto tenga espacio

# Aplicamos los estilos por nivel
c0 = base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold')
c1 = base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left')
c2 = base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='#555')

text_column = alt.layer(c0, c1, c2)

# Barras del Gantt
bars = alt.Chart(df_chart).mark_bar(cornerRadius=1).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

# Concatenación final sin espacio entre texto y barras
gantt = alt.hconcat(text_column, bars, spacing=10).configure_view(stroke=None)

st.altair_chart(gantt, use_container_width=False)
