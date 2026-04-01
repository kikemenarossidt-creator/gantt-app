# --- 5. SECCIÓN HITOS DE PAGO (VERSION PROTEGIDA) ---
st.header("💰 Hitos de Pago (Payment Milestones)")
ws_hitos = conectar_hoja(client, "Hitos")

if ws_hitos:
    try:
        v_h = ws_hitos.get_all_values()
        
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            
            # --- PROTECCIÓN: Si 'PAGADO' no existe en el Excel, la creamos vacía ---
            if 'PAGADO' not in df_h.columns:
                df_h['PAGADO'] = "FALSE"
            
            # Convertir a booleano para el checkbox de Streamlit
            df_h['PAGADO'] = df_h['PAGADO'].apply(lambda x: str(x).upper() == 'TRUE')
        else:
            # Si la hoja está totalmente vacía, definimos las columnas
            df_h = pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])

        t1, t2 = st.tabs(["🚢 Offshore Payments", "🏗️ Onshore Payments"])
        
        config_hitos = {
            "PAGADO": st.column_config.CheckboxColumn("Estado Pago"),
            "PORCENTAJE": st.column_config.TextColumn("Cuota %")
        }

        with t1:
            df_off = df_h[df_h["TIPO"] == "Offshore"]
            ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, key="ed_off", 
                                   column_order=("HITO", "PORCENTAJE", "PAGADO"), column_config=config_hitos, num_rows="dynamic")
        with t2:
            df_on = df_h[df_h["TIPO"] == "Onshore"]
            ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, key="ed_on", 
                                  column_order=("HITO", "PORCENTAJE", "PAGADO"), column_config=config_hitos, num_rows="dynamic")

        if st.button("💾 Guardar Hitos de Pago"):
            # Re-etiquetar tipos antes de unir
            ed_off["TIPO"] = "Offshore"
            ed_on["TIPO"] = "Onshore"
            df_final = pd.concat([ed_off, ed_on])
            
            # Convertir booleano a texto para Google Sheets
            df_final['PAGADO'] = df_final['PAGADO'].astype(str).upper()
            
            # Limpiar y actualizar
            ws_hitos.clear()
            ws_hitos.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Hitos actualizados correctamente")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error cargando hitos: {e}")
        st.info("Asegúrate de que la pestaña 'Hitos' tenga los encabezados: TIPO, HITO, PORCENTAJE, PAGADO")
