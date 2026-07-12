from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.auth import password_gate, get_secret
from src.db import (
    delete_prospect,
    get_saved_prospects,
    init_db,
    save_prospects,
    stage_summary,
    update_note,
    update_stage,
)
from src.prospecting import generate_prospects
from src.utils import PIPELINE_STAGES, safe_float, score_label


APP_TITLE = "Sales Intelligence Guatemala"
DEFAULT_MODEL = get_secret("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

st.set_page_config(page_title=APP_TITLE, page_icon="📈", layout="wide")
password_gate(APP_TITLE)
init_db()


if "default_stage" not in st.session_state:
    st.session_state.default_stage = PIPELINE_STAGES[0]
if "filters" not in st.session_state:
    st.session_state.filters = {"min_score": 0.0, "stage": "Todos"}


st.title(APP_TITLE)
st.caption("Asistente inteligente de ventas para encontrar, calificar, contactar y convertir prospectos en Guatemala.")

with st.sidebar:
    st.header("Configuración")
    st.write("Modelo IA:", DEFAULT_MODEL)
    st.write("Modo:", "OpenRouter" if get_secret("OPENROUTER_API_KEY", "").strip() else "Demo local")

    st.subheader("Pipeline por defecto")
    st.session_state.default_stage = st.selectbox("Etapa", PIPELINE_STAGES, index=0)

    st.subheader("Filtros")
    min_score = st.slider("Score mínimo", 0, 100, 0)
    stage_filter = st.selectbox("Etapa", ["Todos"] + PIPELINE_STAGES, index=0)
    st.session_state.filters = {"min_score": float(min_score), "stage": stage_filter}

    st.subheader("Exportación")
    export_format = st.selectbox("Formato", ["Excel", "CSV", "JSON"])

pages = st.tabs(["Prospección", "Pipeline CRM", "Alertas", "Automatización", "Ajustes"])


# -----------------------------
# Prospección
# -----------------------------
with pages[0]:
    st.subheader("Define tu oferta")

    c1, c2 = st.columns(2)
    with c1:
        product_service = st.text_input("¿Qué producto o servicio deseas vender?")
        description = st.text_area("Descripción breve")
        sector = st.text_input("Sector económico")
        price = st.text_input("Precio aproximado")
        ideal_client = st.text_input("Tipo de cliente ideal")
    with c2:
        coverage = st.text_input("Cobertura geográfica", value="Guatemala")
        company_size = st.text_input("Tamaño de empresa objetivo")
        decision_role = st.text_input("Cargo del decisor")
        competitors = st.text_input("Competidores")

    benefits = st.text_area("Beneficios principales")
    problems = st.text_area("Problemas que resuelve")
    success_cases = st.text_area("Casos de éxito")

    profile = {
        "product_service": product_service,
        "description": description,
        "sector": sector,
        "price": price,
        "ideal_client": ideal_client,
        "coverage": coverage,
        "company_size": company_size,
        "decision_role": decision_role,
        "competitors": competitors,
        "benefits": benefits,
        "problems": problems,
        "success_cases": success_cases,
    }

    col_a, col_b = st.columns([1, 3])
    with col_a:
        run_btn = st.button("Buscar prospectos con IA", type="primary")
    with col_b:
        st.caption("La IA prioriza empresas con mayor compatibilidad y genera mensajes personalizados por prospecto.")

    if run_btn:
        if not product_service or not sector:
            st.error("Completa al menos el producto/servicio y el sector económico.")
        else:
            with st.spinner("Investigando prospectos y generando inteligencia comercial..."):
                prospects = generate_prospects(profile, DEFAULT_MODEL)
                save_prospects(prospects, st.session_state.default_stage)
                st.success(f"Se guardaron {len(prospects)} prospectos.")
                st.rerun()

    all_prospects = get_saved_prospects()
    filtered = [
        p for p in all_prospects
        if safe_float(p.get("score", 0)) >= st.session_state.filters["min_score"]
        and (st.session_state.filters["stage"] == "Todos" or p.get("stage", "") == st.session_state.filters["stage"])
    ]

    if filtered:
        df = pd.DataFrame([
            {
                "id": p.get("id"),
                "created_at": p.get("created_at"),
                "name": p.get("name"),
                "giro": p.get("giro"),
                "ubicacion": p.get("ubicacion"),
                "tamano": p.get("tamano"),
                "website": p.get("website"),
                "telefono": p.get("telefono"),
                "correo": p.get("correo"),
                "redes": p.get("redes"),
                "descripcion": p.get("descripcion"),
                "motivo": p.get("motivo"),
                "score": p.get("score"),
                "score_label": p.get("score_label"),
                "stage": p.get("stage"),
                "note": p.get("note"),
            }
            for p in filtered
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        if export_format == "Excel":
            output = Path("prospectos.xlsx")
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Prospectos")
            st.download_button(
                "Descargar Excel",
                data=output.read_bytes(),
                file_name="prospectos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        elif export_format == "CSV":
            st.download_button(
                "Descargar CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="prospectos.csv",
                mime="text/csv",
            )
        else:
            st.download_button(
                "Descargar JSON",
                data=json.dumps(filtered, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="prospectos.json",
                mime="application/json",
            )

        st.markdown("---")
        for p in filtered:
            st.markdown(f"### {p.get('name', 'Prospecto')}")
            st.caption(f"{p.get('giro', '')} · {p.get('ubicacion', '')} · {p.get('tamano', '')}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Score", f"{safe_float(p.get('score', 0)):.0f}%", p.get("score_label", score_label(safe_float(p.get("score", 0)))))
            m2.metric("Web", "Sí" if p.get("website") else "No")
            m3.metric("Teléfono", "Sí" if p.get("telefono") else "No")
            m4.metric("Correo", "Sí" if p.get("correo") else "No")
            st.write(p.get("descripcion", ""))
            st.info(f"**Por qué fue seleccionado:** {p.get('motivo', '')}")
            with st.expander("Inteligencia comercial"):
                st.write("**Resumen ejecutivo:**", p.get("summary", ""))
                st.write("**Fortalezas:**", p.get("fortalezas", ""))
                st.write("**Necesidades probables:**", p.get("necesidades", ""))
                st.write("**Problemas que podría resolver:**", p.get("problems", ""))
                st.write("**Argumentos de venta:**", p.get("argumentos", ""))
                st.write("**Posibles objeciones:**", p.get("objeciones", ""))
                st.write("**Respuestas recomendadas:**", p.get("respuestas", ""))

            with st.expander("Mensajes personalizados"):
                st.text_area("Correo", p.get("email", ""), height=100, key=f"email_{p['id']}")
                st.text_area("WhatsApp", p.get("whatsapp", ""), height=100, key=f"wa_{p['id']}")
                st.text_area("LinkedIn", p.get("linkedin", ""), height=100, key=f"li_{p['id']}")
                st.text_area("Llamada", p.get("call_script", ""), height=100, key=f"call_{p['id']}")
                st.text_area("Elevator Pitch", p.get("pitch", ""), height=80, key=f"pitch_{p['id']}")
                st.text_area("Propuesta comercial", p.get("proposal", ""), height=100, key=f"proposal_{p['id']}")
                st.text_area("Presentación comercial", p.get("presentation", ""), height=100, key=f"presentation_{p['id']}")
            st.divider()
    else:
        st.info("Todavía no hay prospectos guardados.")


# -----------------------------
# Pipeline CRM
# -----------------------------
with pages[1]:
    st.subheader("Pipeline CRM")
    prospects = get_saved_prospects()
    if not prospects:
        st.info("Primero genera prospectos desde la pestaña de Prospección.")
    else:
        for p in prospects:
            cols = st.columns([3, 2, 3, 1])
            with cols[0]:
                st.markdown(f"**{p.get('name', '')}**")
                st.caption(f"Score: {safe_float(p.get('score', 0)):.0f}% · {p.get('ubicacion', '')}")
            with cols[1]:
                stage = st.selectbox(
                    "Etapa",
                    PIPELINE_STAGES,
                    index=PIPELINE_STAGES.index(p.get("stage", PIPELINE_STAGES[0])) if p.get("stage", PIPELINE_STAGES[0]) in PIPELINE_STAGES else 0,
                    key=f"stage_{p['id']}",
                )
                if stage != p.get("stage"):
                    update_stage(p["id"], stage)
            with cols[2]:
                note = st.text_input("Nota", value=p.get("note", ""), key=f"note_{p['id']}")
                if note != p.get("note", ""):
                    update_note(p["id"], note)
            with cols[3]:
                if st.button("Eliminar", key=f"del_{p['id']}"):
                    delete_prospect(p["id"])
                    st.rerun()
            st.divider()

        summary = stage_summary(prospects)
        summary_df = pd.DataFrame({"Etapa": list(summary.keys()), "Cantidad": list(summary.values())})
        st.bar_chart(summary_df.set_index("Etapa"))
        st.dataframe(summary_df, use_container_width=True, hide_index=True)


# -----------------------------
# Alertas
# -----------------------------
with pages[2]:
    st.subheader("Alertas inteligentes")
    st.write("Este módulo puede ampliarse para vigilar nuevas empresas, cambios de gerente, aperturas de sucursal, contrataciones, importaciones, exportaciones y crecimiento acelerado.")
    alerts = [
        "Nueva empresa detectada en el sector objetivo.",
        "Señal de expansión regional.",
        "Aumento de actividad digital.",
        "Posible cambio de decisor comercial.",
        "Apertura de una nueva sucursal.",
    ]
    for alert in alerts:
        st.success(alert)


# -----------------------------
# Automatización
# -----------------------------
with pages[3]:
    st.subheader("Automatización")
    st.write("Aquí puedes conectar alertas, exportaciones, correo, WhatsApp y sincronización con CRMs externos.")
    st.checkbox("Exportar prospectos nuevos automáticamente")
    st.checkbox("Enviar alertas cuando aparezcan prospectos de alta puntuación")
    st.checkbox("Sincronizar con CRM externo")
    st.checkbox("Generar correos personalizados en lote")
    st.checkbox("Generar propuestas comerciales automáticamente")
    st.info("En producción, este módulo se conectaría con trabajos asíncronos y colas de tareas.")


# -----------------------------
# Ajustes
# -----------------------------
with pages[4]:
    st.subheader("Ajustes técnicos")
    st.markdown(
        """
        **Variables de entorno / secretos:**
        ```bash
        APP_PASSWORD=tu_contraseña
        OPENROUTER_API_KEY=tu_api_key
        OPENROUTER_MODEL=deepseek/deepseek-v4-flash
        OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
        APP_DB_PATH=sales_intelligence.db
        ```
        """
    )
    st.markdown(
        """
        **requirements.txt**
        ```txt
        streamlit
        pandas
        requests
        openpyxl
        ```
        """
    )
    st.warning("Para producción real conviene migrar SQLite a PostgreSQL y separar frontend, API y motor IA.")


st.caption(f"Última ejecución: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
