# --- 3. GRÁFICO ALTAIR (VERSION COMPACTA) ---
h = len(df_chart) * 22
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

# Reducimos drásticamente los anchos (width) y eliminamos dx
# Nivel 0: Ajustado a 130px
c0 = alt.Chart(df_chart).mark_text(
    align='left', 
    fontWeight='bold'
).encode(text='L0:N', **col_config).properties(width=130, height=h)

# Nivel 1: Ajustado a 110px y sin dx
c1 = alt.Chart(df_chart).mark_text(
    align='left'
).encode(text='L1:N', **col_config).properties(width=110, height=h)

# Nivel 2: Ajustado a 180px y sin dx
c2 = alt.Chart(df_chart).mark_text(
    align='left', 
    fontStyle='italic', 
    color='#555'
).encode(text='L2:N', **col_config).properties(width=180, height=h)

# Barras del Gantt
bars = alt.Chart(df_chart).mark_bar(cornerRadius=1).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

# Concatenación final
st.altair_chart(alt.hconcat(c0, c1, c2, bars, spacing=0).configure_view(stroke=None))
