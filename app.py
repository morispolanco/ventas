import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


# =========================================================
# STREAMLIT APP: INTELIGENCIA COMERCIAL REAL
# - Sin datos simulados
# - Sin créditos
# - Sin pagos
# - Sin autenticación
# =========================================================

st.set_page_config(
    page_title="Sales Intelligence Guatemala",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.2rem; }
        .small-muted { color: #6b7280; font-size: 0.92rem; }
        .card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: 0 1px 2px rgba(0,0,0,.04);
            margin-bottom: 0.9rem;
        }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.25rem;
            border: 1px solid #e5e7eb;
            background: #f9fafb;
        }
        .badge-high { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
        .badge-med { background: #fffbeb; border-color: #fde68a; color: #92400e; }
        .badge-low { background: #f3f4f6; border-color: #d1d5db; color: #374151; }
    </style>
    """,
    unsafe_allow_html=True,
)


@dataclass
class Prospect:
    name: str
    sector: str = ""
    location: str = ""
    size: str = ""
    website: str = ""
    source: str = ""
    signal: str = ""
    rationale: str = ""
    pain_point: str = ""
    score: int = 0
    technologies: Optional[List[str]] = None
    evidence: Optional[List[str]] = None
    stage: str = "Nuevo"
    next_step: str = ""

    def __post_init__(self) -> None:
        if self.technologies is None:
            self.technologies = []
        if self.evidence is None:
            self.evidence = []


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_query_tokens(text: str) -> List[str]:
    return [t.strip() for t in text.split(",") if t.strip()]


def score_prospect(prospect: Dict[str, Any], query: Dict[str, Any]) -> int:
    score = 0
    sector = (prospect.get("sector") or "").lower()
    location = (prospect.get("location") or "").lower()
    signal = (prospect.get("signal") or "").lower()
    rationale = (prospect.get("rationale") or "").lower()
    evidence = prospect.get("evidence") or []

    target_sectors = [s.lower() for s in query.get("target_sectors", [])]
    target_locations = [s.lower() for s in query.get("target_locations", [])]
    keywords = [s.lower() for s in query.get("keywords", [])]

    if any(ts and ts in sector for ts in target_sectors):
        score += 30
    if any(tl and tl in location for tl in target_locations):
        score += 20
    if any(k and (k in signal or k in rationale) for k in keywords):
        score += 25
    if prospect.get("website"):
        score += 10
    score += min(len(evidence) * 3, 15)

    return min(score, 100)


def google_custom_search(query: str, num: int = 10) -> List[Dict[str, Any]]:
    api_key = env("GOOGLE_CSE_API_KEY")
    cse_id = env("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cse_id, "q": query, "num": min(num, 10)}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    results: List[Dict[str, Any]] = []
    for item in data.get("items", []):
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Google Custom Search",
            }
        )
    return results


def newsapi_search(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    api_key = env("NEWSAPI_KEY")
    if not api_key:
        return []

    url = "https://newsapi.org/v2/everything"
    headers = {"X-Api-Key": api_key}
    params = {"q": query, "pageSize": min(page_size, 10), "language": "es"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    results: List[Dict[str, Any]] = []
    for item in data.get("articles", []):
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "source": item.get("source", {}).get("name", "NewsAPI"),
                "publishedAt": item.get("publishedAt", ""),
            }
        )
    return results


def build_prospect_from_result(result: Dict[str, Any], query: Dict[str, Any]) -> Prospect:
    title = (result.get("title") or "").strip()
    link = (result.get("link") or "").strip()
    snippet = (result.get("snippet") or "").strip()
    source = (result.get("source") or "Fuente real").strip()

    sector = query.get("primary_sector", "")
    location = ", ".join(query.get("target_locations", [])) if query.get("target_locations") else ""

    return Prospect(
        name=title or "Resultado sin título",
        sector=sector,
        location=location,
        website=link,
        source=source,
        signal=snippet,
        rationale="Coincide con la búsqueda definida por el usuario y aparece en una fuente real recuperada por la integración.",
        pain_point="Por confirmar con más evidencia en fuentes conectadas.",
        evidence=[snippet] if snippet else [],
        technologies=[],
    )


if "pipeline" not in st.session_state:
    st.session_state.pipeline = []

if "selected_prospect" not in st.session_state:
    st.session_state.selected_prospect = None


with st.sidebar:
    st.title("💼 Sales Intelligence GT")
    st.caption("Inteligencia comercial real para Streamlit Cloud")
    st.markdown("---")

    st.subheader("Perfil de búsqueda")
    with st.form("search_form", clear_on_submit=False):
        product = st.text_input("¿Qué deseas vender?", placeholder="Ej. software ERP, impresión digital, consultoría, etc.")
        primary_sector = st.text_input("Sector principal", placeholder="Ej. logística")
        target_sectors_raw = st.text_input("Sectores objetivo", placeholder="Ej. logística, manufactura, retail")
        target_locations_raw = st.text_input("Cobertura geográfica", placeholder="Ej. Ciudad de Guatemala, Escuintla")
        size = st.text_input("Tamaño objetivo", placeholder="Ej. 50-400 empleados")
        keyword_raw = st.text_input("Señales / palabras clave", placeholder="Ej. expansión, contratación, nueva sucursal")
        limit = st.slider("Máximo de resultados por fuente", 5, 20, 10)
        submitted = st.form_submit_button("Buscar prospectos reales")

    st.markdown("---")
    st.subheader("Fuentes conectadas")
    st.write("Google Custom Search:", "✅" if env("GOOGLE_CSE_API_KEY") and env("GOOGLE_CSE_ID") else "⚪ no configurada")
    st.write("NewsAPI:", "✅" if env("NEWSAPI_KEY") else "⚪ no configurada")
    st.caption("Si no configuras APIs, la app no mostrará datos ficticios.")


st.title("Cabina de Inteligencia Comercial")
st.write(
    "La aplicación busca y prioriza prospectos reales a partir de fuentes conectadas. No usa mock data, créditos, pagos ni autenticación."
)

query_cfg: Dict[str, Any] = {}
if submitted:
    target_sectors = get_query_tokens(target_sectors_raw)
    target_locations = get_query_tokens(target_locations_raw)
    keywords = get_query_tokens(keyword_raw)

    query_cfg = {
        "product": product,
        "primary_sector": primary_sector,
        "target_sectors": target_sectors,
        "target_locations": target_locations,
        "size": size,
        "keywords": keywords,
    }

    search_parts = [product, primary_sector, " ".join(target_sectors), " ".join(target_locations), " ".join(keywords)]
    search_query = " ".join([p for p in search_parts if p]).strip()

    if not search_query:
        st.warning("Completa al menos el producto o un criterio de búsqueda.")
    else:
        with st.spinner("Consultando fuentes reales..."):
            google_results = google_custom_search(search_query, num=limit)
            news_results = newsapi_search(search_query, page_size=limit)

            combined: List[Dict[str, Any]] = []
            combined.extend(google_results)
            combined.extend(news_results)

            prospects: List[Prospect] = []
            for result in combined:
                p = build_prospect_from_result(result, query_cfg)
                p.score = score_prospect(asdict(p), query_cfg)
                prospects.append(p)

            prospects = sorted(prospects, key=lambda x: x.score, reverse=True)
            st.session_state.pipeline = [asdict(p) for p in prospects]
            st.session_state.selected_prospect = st.session_state.pipeline[0] if st.session_state.pipeline else None


tab1, tab2, tab3 = st.tabs(["Prospectos reales", "Pipeline", "Mensajes"])


with tab1:
    st.subheader("Prospectos encontrados")
    if not st.session_state.pipeline:
        st.info("No hay prospectos cargados todavía. Conecta una API real y ejecuta una búsqueda.")
        st.markdown(
            """
            <div class="card">
                <strong>Estado vacío honesto</strong><br>
                La aplicación no muestra empresas ficticias ni señales simuladas.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for i, prospect in enumerate(st.session_state.pipeline):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {prospect.get('name', '')}")
                meta = []
                if prospect.get("sector"):
                    meta.append(f"Sector: {prospect['sector']}")
                if prospect.get("location"):
                    meta.append(f"Ubicación: {prospect['location']}")
                if prospect.get("source"):
                    meta.append(f"Fuente: {prospect['source']}")
                if meta:
                    st.write(" | ".join(meta))
                if prospect.get("signal"):
                    st.markdown(f"**Señal observada:** {prospect['signal']}")
                if prospect.get("rationale"):
                    st.markdown(f"**Razón de encaje:** {prospect['rationale']}")
                if prospect.get("pain_point"):
                    st.markdown(f"**Dolor probable:** {prospect['pain_point']}")
                if prospect.get("website"):
                    st.markdown(f"[Abrir fuente / sitio]({prospect['website']})")
                if prospect.get("technologies"):
                    st.caption(f"Tecnologías detectadas: {', '.join(prospect['technologies'])}")
            with col2:
                score = int(prospect.get("score", 0))
                badge_class = "badge-high" if score >= 75 else "badge-med" if score >= 45 else "badge-low"
                st.markdown(f'<span class="badge {badge_class}">Score {score}/100</span>', unsafe_allow_html=True)
                if st.button("Seleccionar", key=f"sel_{i}"):
                    st.session_state.selected_prospect = prospect
                    st.success("Prospecto seleccionado.")
            st.markdown("</div>", unsafe_allow_html=True)


with tab2:
    st.subheader("Pipeline de trabajo")
    st.caption("Seguimiento simple, sin CRM de pago, sin login y sin créditos.")

    pipeline_df = pd.DataFrame(st.session_state.pipeline)
    if pipeline_df.empty:
        st.info("Todavía no hay prospectos en el pipeline.")
    else:
        if "stage" not in pipeline_df.columns:
            pipeline_df["stage"] = "Nuevo"
        if "next_step" not in pipeline_df.columns:
            pipeline_df["next_step"] = ""

        edited = st.data_editor(
            pipeline_df[["name", "score", "source", "stage", "next_step", "website"]],
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "stage": st.column_config.SelectboxColumn(
                    "stage",
                    options=["Nuevo", "Contactado", "Interesado", "Reunión", "Ganado", "Descartado"],
                    required=True,
                )
            },
        )
        st.caption("Los cambios de esta vista se mantienen en la sesión actual.")

        if st.button("Guardar cambios del pipeline"):
            updated_pipeline = edited.to_dict(orient="records")
            st.session_state.pipeline = updated_pipeline
            st.success("Pipeline actualizado.")


with tab3:
    st.subheader("Mensajes personalizados")

    prospect_dict = st.session_state.selected_prospect
    if not prospect_dict and st.session_state.pipeline:
        prospect_dict = st.session_state.pipeline[0]

    if not prospect_dict:
        st.info("Selecciona un prospecto para generar un mensaje.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            channel = st.selectbox("Canal", ["Correo", "LinkedIn", "WhatsApp"])
            tone = st.selectbox("Tono", ["Profesional", "Directo", "Consultivo"])
            generate = st.button("Generar mensaje")

        with col2:
            st.markdown(f"**Prospecto activo:** {prospect_dict.get('name', '')}")
            if generate:
                name = prospect_dict.get("name", "la empresa")
                signal = prospect_dict.get("signal", "una señal reciente observada en fuente real")
                product = env("DEFAULT_PRODUCT", "tu solución")

                if channel == "Correo":
                    body = (
                        f"Hola, equipo de {name}:\n\n"
                        f"Revisé {signal[:220]}. Creemos que {product} podría ayudarles a resolver una necesidad concreta relacionada con ese contexto.\n\n"
                        f"¿Te parece si coordinamos 10 minutos para compartirte una propuesta breve?\n\n"
                        f"Saludos,\n"
                        f"[Tu nombre]"
                    )
                elif channel == "LinkedIn":
                    body = (
                        f"Hola, vi una señal reciente sobre {name} y me pareció una buena razón para conectar.\n"
                        f"Trabajo con {product} y creo que podría ser relevante para su contexto actual."
                    )
                else:
                    body = (
                        f"Hola, soy [Tu nombre]. Vi una señal reciente sobre {name} y quería compartirte una idea corta sobre {product}.\n"
                        f"¿Te puedo enviar 3 líneas por aquí?"
                    )

                st.text_area("Borrador", value=body, height=220)
                st.caption(f"Tono sugerido: {tone}")


st.markdown("---")
st.caption(
    "Para que la app funcione con datos reales en Streamlit Cloud, define al menos una fuente: GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID, NEWSAPI_KEY u otra API real conectada."
)
