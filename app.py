# --- 3. CRONOGRAMA (GANTT) ---
ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        
        # 1. Selector de nivel ENCIMA del título
        # Usamos un radio horizontal para que sea fácil de clickear
        prof = st.radio(
            "🔍 Nivel de detalle del Cronograma:",
            options=[0, 1, 2],
            format_func=lambda x: ["Básico (Hitos)", "Intermedio", "Detallado (Todo)"][x],
            horizontal=True
        )

        st.header("📅 Cronograma de Obra")

        # Procesamiento de fechas
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        
        # Filtrado por nivel
        df_p = df_t[df_t['Level'] <= prof].copy()
        
        # Si no hay datos tras el filtro, evitamos que Altair explote
        if not df_p.empty:
            df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)
            
            h = max(len(df_p) * 25, 200)
            base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
            
            text_layer = alt.layer(
                base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
                base.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
                base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
            ).encode(text='Display:N').properties(width=350, height=h)
            
            bars = base.mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')), x2='End:T',
                color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
                tooltip=['Task', 'Empresa a Cargo']
            ).properties(width=750, height=h)
            
            st.altair_chart(alt.hconcat(text_layer, bars))
        else:
            st.warning("No hay tareas para mostrar en este nivel.")
            
        # ... (aquí sigue el resto de tu código de Gestión de Tareas)
