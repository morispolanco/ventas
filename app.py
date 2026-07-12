import streamlit as st
import time
import random

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Sales Intelligence Guatemala",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para simular el look-and-feel de shadcn/ui
st.markdown("""
<style>
    .reportview-container { background: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .card { background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .score-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; display: inline-block; }
    .score-excelente { background-color: #dcfce7; color: #166534; }
    .score-alta { background-color: #fef9c3; color: #854d0e; }
</style>
""", unsafe_allowed_html=True)

# ==========================================
# SIMULACIÓN DE DATOS (MOCK DATA)
# ==========================================
if 'creditos' not in st.session_state:
    st.session_state.creditos = 150

# Empresas precargadas (Base de conocimiento RAG simulada)
EMPRESAS_MOCK = [
    {
        "nombre": "Corporación Alimentos del Istmo S.A.",
        "giro": "Manufactura y Distribución de Alimentos",
        "ubicacion": "Zona 12, Ciudad de Guatemala",
        "empleados": "350+",
        "digitalizacion": "Media (Sitio web básico, sin píxeles de conversión avanzados)",
        "noticia": "Abriendo nuevo centro de distribución logística en Quetzaltenango (Xela).",
        "tecnologias": ["SAP ERP", "Microsoft 365", "Google Analytics"],
        "score": 96,
        "justificacion": "Match crítico: Buscan expandir operaciones a Xela y carecen de software de optimización de rutas o CRM avanzado para coordinar equipos remotos.",
        "dolor": "Falta de visibilidad en tiempo real del inventario en tránsito hacia los departamentos.",
        "foda": {"F": "Liderazgo en el mercado local", "D": "Procesos de ventas manuales", "O": "Apertura en el occidente del país", "A": "Competencia internacional con mejor tecnología"}
    },
    {
        "nombre": "Logística y Transportes de Guatemala (LogiGuate)",
        "giro": "Transporte de Carga y Cadena de Suministro",
        "ubicacion": "Siquinalá, Escuintla",
        "empleados": "120",
        "digitalizacion": "Alta (GPS corporativo, pasarela de pagos básica)",
        "noticia": "Recibió inversión de fondo regional para modernización de flota.",
        "tecnologias": ["WordPress", "Meta Pixel", "HubSpot Free"],
        "score": 89,
        "justificacion": "Alta compatibilidad: Cuentan con capital reciente para inversión tecnológica y ya usan herramientas de marketing, facilitando la venta de integraciones avanzadas.",
        "dolor": "Alta tasa de rotación en ejecutivos de cuentas clave y demora en cotizaciones complejas.",
        "foda": {"F": "Flota moderna", "D": "Cuellos de botella en atención al cliente", "O": "Automatización de cotizaciones", "A": "Fluctuación del precio del combustible"}
    }
]

# ==========================================
# BARRA LATERAL (SIDEBAR) - ONBOARDING / ICP
# ==========================================
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop", width=60) # Decorativo institucional
    st.title("Sales Intelligence GT")
    st.caption("Tu Asistente de Ventas IA 24/7")
    st.markdown("---")
    
    st.subheader("🎯 Perfil de Tu Empresa (ICP)")
    with st.form("icp_form"):
        que_vende = st.text_input("¿Qué deseas vender?", value="Software ERP de Logística e Inventarios")
        sector_target = st.multiselect("Sectores Objetivo", ["Consumo Masivo", "Logística", "Servicios", "Tecnología"], default=["Consumo Masivo", "Logística"])
        tamaño_target = st.slider("Tamaño de empresa ideal (Empleados)", 10, 500, (50, 400))
        decisor = st.text_input("Cargo del decisor político", value="Gerente de Operaciones / Director Comercial")
        
        submitted = st.form_submit_type("submit")("Actualizar Motor IA")
        if submitted:
            st.success("¡Motor IA recalibrado con tu nuevo ICP!")

    st.markdown("---")
    st.metric(label="🪙 Créditos Disponibles", value=st.session_state.creditos)
    st.caption("Las búsquedas son libres. Las acciones de IA consumen 1 crédito.")

# ==========================================
# CUERPO PRINCIPAL - DASHBOARD & PIPELINE
# ==========================================
st.title("💼 Cabina de Inteligencia Comercial")
st.write("Detectando oportunidades en tiempo real para el mercado de Guatemala.")

tab1, tab2, tab3 = st.tabs(["🚀 Oportunidades Encontradas", "📊 Pipeline CRM", "🔔 Alertas de Mercado"])

# ------------------------------------------
# PESTAÑA 1: OPORTUNIDADES ENCONTRADAS (MOTOR DE PROSPECCIÓN)
# ------------------------------------------
with tab1:
    st.subheader("Empresas compatibles detectadas por el Agente Investigador")
    
    for emp in EMPREAS_MOCK:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {emp['nombre']}")
                st.markdown(f"📍 **Ubicación:** {emp['ubicacion']} | 🏢 **Giro:** {emp['giro']} | 👥 **Empleados:** {emp['empleados']}")
                st.markdown(f"📢 **Señal Reciente:** *{emp['noticia']}*")
            
            with col2:
                # Badge dinámico según score
                clase_badge = "score-excelente" if emp['score'] >= 90 else "score-alta"
                st.markdown(f"<div style='text-align: center;'><span class='score-badge {clase_badge}'>Score IA: {emp['score']}/100</span></div>", unsafe_allowed_html=True)
                
                # Acción de valor (Consumo de créditos)
                if st.button(f"Diseñar Estrategia", key=emp['nombre']):
                    if st.session_state.creditos > 0:
                        st.session_state.creditos -= 1
                        st.session_state['empresa_seleccionada'] = emp
                        st.rerun()
                    else:
                        st.error("No tienes créditos suficientes.")
            
            st.markdown("---")

    # Si el usuario seleccionó una empresa para desplegar la Inteligencia Comercial profunda
    if 'empresa_seleccionada' in st.session_state:
        selected = st.session_state['empresa_seleccionada']
        st.markdown(f"## 🧠 Inteligencia Comercial Completa: {selected['nombre']}")
        
        col_foda, col_estrategia = st.columns(2)
        
        with col_foda:
            st.markdown("<div class='card'>", unsafe_allowed_html=True)
            st.markdown("### 📊 Diagnóstico FODA Comercial")
            st.write(f"💪 **Fortaleza:** {selected['foda']['F']}")
            st.write(f"❌ **Debilidad:** {selected['foda']['D']}")
            st.write(f"🚀 **Oportunidad:** {selected['foda']['O']}")
            st.write(f"⚠️ **Amenaza:** {selected['foda']['A']}")
            st.markdown(f"🎯 **Dolor Crítico Detectado:** {selected['dolor']}")
            st.markdown("</div>", unsafe_allowed_html=True)
            
        with col_estrategia:
            st.markdown("<div class='card'>", unsafe_allowed_html=True)
            st.markdown("### 🤖 Razonamiento del Agente Analista")
            st.info(selected['justificacion'])
            st.write(f"⚙️ **Tecnologías Detectadas:** {', '.join(selected['tecnologias'])}")
            st.write(f"💻 **Madurez Digital:** {selected['digitalizacion']}")
            st.markdown("</div>", unsafe_allowed_html=True)

        # GENERADOR IA DE COMUNICACIONES
        st.markdown("### ✉️ Generador de Mensajes Personalizados (Agente Redactor)")
        canal = st.selectbox("Selecciona el canal de contacto:", ["Correo Electrónico Corp.", "Mensaje Directo de LinkedIn", "WhatsApp de Prospección"])
        
        if st.button("Generar Redacción con IA"):
            with st.spinner("El Agente Redactor está contextualizando tu oferta..."):
                time.sleep(1.5) # Simulación de inferencia del LLM
                
                if canal == "Correo Electrónico Corp.":
                    subject = f"Propuesta de Eficiencia en Distribución - Expansión {selected['nombre'].split(' ')[0]}"
                    body = f"Estimado Gerente de Operaciones de {selected['nombre']},\n\nVi que recientemente iniciaron operaciones en su nuevo centro logístico en Quetzaltenango. Sé que coordinar la cadena de suministro desde Ciudad de Guatemala hacia el occidente suele generar fricciones en la visibilidad del inventario en tránsito.\n\nNuestra plataforma de {que_vende} ayuda específicamente a automatizar este control sin necesidad de reemplazar su {selected['tecnologias'][0]} actual. ¿Tendría 10 minutos esta semana para mostrarle cómo lo solucionamos?\n\nAtentamente,\n[Tu Nombre]"
                    st.text_input("Asunto:", value=subject)
                    st.text_area("Contenido del Correo:", value=body, height=200)
                
                elif canal == "Mensaje Directo de LinkedIn":
                    body_li = f"Hola, vi el crecimiento de {selected['nombre']} con su nuevo nodo logístico en Xela. ¡Felicidades! Me especializo en ayudar a empresas de {selected['giro']} a reducir pérdidas de stock en rutas departamentales complejas. Me encantaría conectar."
                    st.text_area("Mensaje de LinkedIn:", value=body_li, height=100)
                
                else:
                    body_wa = f"Buenos días. Me comunico de parte de Sales Intelligence. Vi la expansión de {selected['nombre']} en Quetzaltenango y desarrollamos una estrategia de control de inventario en tránsito para sus rutas comerciales. ¿Le interesaría una breve llamada hoy a las 3:00 PM?"
                    st.text_area("Mensaje de WhatsApp:", value=body_wa, height=100)
                    
            st.success("Mensaje generado omitiendo plantillas genéricas. Basado 100% en eventos reales de la empresa.")

# ------------------------------------------
# PESTAÑA 2: PIPELINE CRM LIGERO
# ------------------------------------------
with tab2:
    st.subheader("Embudo de Ventas Activo")
    st.caption("Visualiza y organiza tus prospectos según su nivel de maduración.")
    
    # Kanban básico simulado por columnas de Streamlit
    col_nuevos, col_contactados, col_interesados, col_ganados = st.columns(4)
    
    with col_nuevos:
        st.markdown("#### 📥 Nuevos")
        st.markdown("<div class='card'><b>Corporación Alimentos del Istmo</b>< #96<br><small>Asignado a: Mí</small></div>", unsafe_allowed_html=True)
        
    with col_contactados:
        st.markdown("#### 📞 Contactados")
        st.markdown("<div class='card'><b>LogiGuate</b><br>Score: 89<br><small>Próxima acción: Enviar propuesta</small></div>", unsafe_allowed_html=True)
        
    with col_interesados:
        st.markdown("#### 🤝 Reunión / Interés")
        st.write("*Vacío por el momento*")
        
    with col_ganados:
        st.markdown("#### 🎉 Ganados")
        st.markdown("<div class='card' style='border-left: 4px solid green;'><b>Distribuidora Central, S.A.</b><br><small>Cerrado por Q25,000</small></div>", unsafe_allowed_html=True)

    st.markdown("---")
    st.markdown("💡 **Recomendación del Agente CRM:** El prospecto *LogiGuate* lleva 4 días en 'Contactado' sin actividad registrada. Te sugerimos reactivarlo enviando un mensaje de seguimiento por WhatsApp.")

# ------------------------------------------
# PESTAÑA 3: ALERTAS INTELIGENTES DE MERCADO
# ------------------------------------------
with tab3:
    st.subheader("📡 Monitoreo Continuo (Señales de Compra en Guatemala)")
    st.caption("El Agente Monitor evalúa el Diario de Centro América, portales de empleo y registros de importaciones de manera continua.")
    
    st.warning("⚠️ **Nueva Licitación Adjudicada:** Una gran empresa cervecera en Escuintla acaba de ganar un contrato de distribución estatal. Relevancia para tu negocio: **Muy Alta**. Requieren optimizar distribución.")
    st.info("ℹ️ **Cambio de Liderazgo:** Nuevo Director Comercial asignado en Industrias del Atlántico. Oportunidad ideal para romper el hielo y presentar soluciones antes de que definan presupuesto anual.")
