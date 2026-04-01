fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Level",
    color_continuous_scale="Blues"
)

# INVERSIÓN DEL EJE Y para que la primera tarea esté arriba
fig.update_yaxes(autorange="reversed")

fig.update_yaxes(title=None)
fig.update_layout(height=1200, margin=dict(l=350), showlegend=False)

st.plotly_chart(fig, use_container_width=True)
