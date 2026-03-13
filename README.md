# NoraCenter

Plataforma que agrega oportunidades para artistas en España: becas, residencias, convocatorias, subvenciones, premios y empleo cultural.

## El problema

La información sobre oportunidades para artistas en España está dispersa en decenas de webs de instituciones públicas y privadas (Ministerio de Cultura, BOE, comunidades autónomas, fundaciones...). NoraCenter las recopila automáticamente en un solo lugar.

## Fuentes

- **BOE** (Boletín Oficial del Estado) - Ayudas y subvenciones culturales
- **Ministerio de Cultura** - Becas, convocatorias, artes plásticas
- **INAEM** - Artes escénicas y música
- **Acción Cultural Española (AC/E)**
- **Fundaciones** - BBVA, La Caixa, Botín, Casa de Velázquez, Matadero Madrid
- **Comunidades Autónomas** - Madrid, Catalunya, Andalucía, Valencia, País Vasco, Galicia

## Arquitectura

```
backend/
  scrapers/       # Scrapers para cada fuente (RSS, HTML)
  models/         # Modelos de datos (SQLAlchemy)
  api/            # Endpoints REST (FastAPI)
  services/       # Lógica de negocio
  app.py          # Aplicación principal
frontend/
  templates/      # HTML (Jinja2)
  static/         # CSS + JS
scripts/
  run_scraper.py  # Ejecución manual de scrapers
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# Ejecutar scrapers manualmente
python scripts/run_scraper.py

# Iniciar servidor web (incluye scrapers programados)
uvicorn backend.app:app --reload

# La web estará en http://localhost:8000
```

## Cómo añadir nuevas fuentes

1. Crea un nuevo scraper en `backend/scrapers/` que herede de `BaseScraper`
2. Implementa el método `scrape()` que devuelve `list[RawOpportunity]`
3. Añade tu scraper a `ALL_SCRAPERS` en `backend/services/scraper_service.py`

## Categorías

| Categoría | Descripción |
|-----------|-------------|
| beca | Becas de formación o investigación |
| residencia | Residencias artísticas |
| subvencion | Subvenciones y ayudas públicas |
| convocatoria | Convocatorias abiertas |
| empleo | Ofertas de empleo cultural |
| premio | Premios y concursos |
| formacion | Cursos y talleres |
| exposicion | Convocatorias de exposición |
| festival | Participación en festivales |

## Disciplinas

Artes visuales, música, teatro, danza, cine, literatura, fotografía, diseño, artes digitales, multidisciplinar.
