# Sales Intelligence Guatemala

Una app SaaS en Streamlit para prospección comercial B2B con IA, pipeline CRM ligero, alertas y exportaciones.

## Funciones
- Prospección inteligente de empresas
- Scoring de probabilidad de compra
- Generación de mensajes personalizados
- Pipeline comercial
- Notas y seguimiento por prospecto
- Exportación a Excel, CSV y JSON
- Integración con OpenRouter + `deepseek/deepseek-v4-flash`

## Ejecutar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secrets en Streamlit Cloud
Crea `.streamlit/secrets.toml` con:
```toml
APP_PASSWORD = "tu_contraseña"
OPENROUTER_API_KEY = "tu_api_key"
OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
APP_DB_PATH = "sales_intelligence.db"
```

## Notas
- SQLite funciona para MVP y demo.
- Puedes migrar a PostgreSQL cambiando `APP_DB_PATH` por una URL y adaptando `src/db.py`.
