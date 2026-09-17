# Servicio de IA

API en FastAPI que genera el resumen ejecutivo de un proyecto y sugiere oportunidades afines.

## Ejecución

```bash
cd ai
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # opcional: agrega tu ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva en <http://localhost:8000/docs>.

## Endpoints

| Método | Ruta        | Descripción |
|--------|-------------|-------------|
| GET    | `/salud`    | Estado del servicio y si hay modelo configurado. |
| POST   | `/analizar` | Recibe `{ proyecto, oportunidades }` y devuelve `{ resumen, recomendaciones, simulado }`. |

Sin `ANTHROPIC_API_KEY` el servicio responde con la heurística local y marca `simulado: true`;
el frontend muestra ese aviso. La afinidad se calcula por área (0.6), coincidencia de
etiquetas (0.25) y vigencia de la convocatoria (0.15).
