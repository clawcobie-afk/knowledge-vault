# Plán: CLAUDE.md pro všechny projekty + AI Running Coach

## Context

Krystof má ekosystém projektů pro knowledge base (kb-ingest → kb-indexer → kb-search), Strava data (strava-connector → strava-query) a unified CLI (knowledge-vault). Chybí:
1. CLAUDE.md pro knowledge-vault
2. Aktualizace existujících CLAUDE.md o kontext celého ekosystému (running + coaching)
3. Nový projekt `running-coach/` pro předpočítaná data + OpenClaw coaching konfigurace

AI trenér je **obecný** — personalizaci (cíl, čas, preference) řeší Cobie/LLM na základě konverzace, datová vrstva jen počítá metriky.
Přístup přes OpenClaw/Discord.

---

## 1. Aktualizace existujících CLAUDE.md

Ke každému existujícímu CLAUDE.md přidám sekci **Ekosystém** vysvětlující roli projektu v celku. Zbytek zachovám.

### 1.1 kb-ingest/CLAUDE.md
- Přidat sekci Ekosystém: "Ingestuje YouTube kanály o běhání (Steve Magness aj.) → data jdou do kb-indexer → kb-search → running-coach používá pro evidence-based rady"
- Soubor: `/home/klach/projects/kb-ingest/CLAUDE.md`

### 1.2 kb-indexer/CLAUDE.md
- Přidat sekci Ekosystém: "Vektorizuje chunky z kb-ingest do Qdrant → kb-search přes ně hledá → running-coach dotazuje pro znalosti o tréninku"
- Soubor: `/home/klach/projects/kb-indexer/CLAUDE.md`

### 1.3 kb-search/CLAUDE.md
- Přidat sekci Ekosystém: "Sémantické vyhledávání přes znalostní bázi → running-coach/OpenClaw volá pro evidence-based informace o běhání"
- Přidat info o programatickém API: `search(query, qdrant_client, openai_client, collection, top_k, channel_slug)`
- Soubor: `/home/klach/projects/kb-search/CLAUDE.md`

### 1.4 strava-connector/CLAUDE.md
- Přidat sekci Ekosystém: "Sync Strava aktivit do SQLite → strava-query nad nimi dotazuje → running-coach počítá sumarizace"
- Dokumentovat nový `--detail` flag (viz sekce 3.0)
- Soubor: `/home/klach/projects/strava-connector/CLAUDE.md`

### 1.5 strava-query/CLAUDE.md — rozšířit
Aktuálně jen 12 řádků. Rozšířit na plný formát:
- CLI příkazy: `list`, `stats`, `show`, `check`
- Architektura: `query.py` + `strava/db.py`
- Klíčové funkce: `open_db()`, `list_activities()`, `get_activity()`, `get_stats()`
- DB schéma: activities (id, name, type, distance, moving_time, elapsed_time, total_elevation_gain, start_date_local, sport_type, raw_json, synced_at)
- Ekosystém: "Dotazuje lokální Strava DB → running-coach z něj čte pro výpočty a sumarizace"
- Soubor: `/home/klach/projects/strava-query/CLAUDE.md`

---

## 2. Nový CLAUDE.md pro knowledge-vault

Vytvořit `/home/klach/projects/knowledge-vault/CLAUDE.md`:
- CLI: `kv ingest|index|search|strava sync|webhook|auth|check|query|setup|check`
- Architektura: `kv.py` — Click group delegující na jednotlivé projekty
- Konfigurace: `~/.config/knowledge-vault/.env` (centrální)
- Env: `PATH` rozšířen o `~/.local/bin`, auto-load z `.env`
- Ekosystém: "Centrální CLI hub. Všechny nástroje (KB pipeline, Strava, budoucí coach) přístupné přes `kv` prefix."
- Context7 sekce

---

## 3. Rozšíření strava-connector: detail fetch

### 3.0 Problém
`sync.py` stahuje jen summary endpoint (`GET /athlete/activities`) → chybí splits, laps, best_efforts, calories, perceived_exertion.

### 3.0.1 Řešení
Přidat do `sync.py` flag `--detail`:
1. Po summary syncu projde aktivity kde `raw_json` neobsahuje `splits_metric`
2. Pro každou zavolá `get_activity(access_token, activity_id)` (detailed endpoint)
3. Updatne `raw_json` kompletními daty
4. Rate limit aware: max 100 req/15 min, 1000/den → sleep mezi requesty, `--max-detail N` limit

### 3.0.2 Nová data v raw_json po detail fetch
- `splits_metric` — list per-km splitů (distance, elapsed_time, elevation_difference, average_speed, average_heartrate, pace_zone)
- `splits_standard` — per-mile splity
- `laps` — okruhy s detaily
- `best_efforts` — PRs na 400m, 1/2mi, 1km, 1mi, 2mi, 5km, 10km, HM, M
- `calories` — odhad kalorií
- `perceived_exertion` — subjektivní hodnocení
- `segment_efforts` — segmenty

### 3.0.3 Soubory k úpravě
- `/home/klach/projects/strava-connector/sync.py` — přidat `--detail` flag + druhý průchod
- `/home/klach/projects/strava-connector/CLAUDE.md` — dokumentovat

---

## 4. Nový projekt: running-coach/

### 4.1 Účel
Obecný Python projekt pro předpočítaná běžecká data. Personalizaci (cíl, čas) řeší LLM, tenhle projekt jen počítá metriky.

### 4.2 Metriky

**Týdenní sumarizace:**
- Celkový objem (km, čas, počet běhů)
- Průměrné tempo, nejdelší běh, převýšení
- Změna oproti předchozímu týdnu (%)

**Per-run analýza (z detailed raw_json):**
- Klasifikace běhu (easy/tempo/interval/long/recovery/race) — z workout_type + pace analýzy
- Splits per km (z `splits_metric`)
- HR zóny per aktivita (z `splits_metric.average_heartrate` + nastavitelné HR zóny)
- Pace zóny per aktivita

**Tréninková zátěž:**
- ATL — acute training load (vážený průměr ~7 dní)
- CTL — chronic training load (vážený průměr ~42 dní)
- TSB = CTL - ATL (freshness/forma)

**Nejlepší výkony:**
- PRs z `best_efforts` (400m, 1km, 5km, 10km, HM, M)
- Sledování progression v čase

**Trendy:**
- Posun tempa (rolling average)
- Progrese dlouhých běhů
- Objem vs předchozí období

### 4.3 Architektura
```
running-coach/
├── CLAUDE.md
├── coach.py              # Click CLI entry point
├── coach/
│   ├── zones.py          # Pace/HR zóny, klasifikace běhů
│   ├── weekly.py         # Týdenní sumarizace
│   ├── load.py           # ATL/CTL/TSB výpočty
│   ├── prs.py            # Best efforts / PRs tracking
│   ├── trends.py         # Trendy a rolling averages
│   ├── summary.py        # Celkový souhrn pro LLM (JSON)
│   └── db.py             # SQLite pro sumarizace
├── tests/
│   └── ...
├── requirements.txt
└── pyproject.toml
```

### 4.4 Datový model (SQLite)
```sql
-- Týdenní sumarizace
CREATE TABLE weekly_summary (
    week TEXT PRIMARY KEY,          -- '2026-W07'
    total_km REAL,
    total_time_s INTEGER,
    run_count INTEGER,
    avg_pace_s_per_km REAL,
    longest_run_km REAL,
    elevation_gain_m REAL,
    week_over_week_pct REAL         -- změna objemu vs předchozí týden
);

-- Per-run analýza
CREATE TABLE run_analysis (
    activity_id INTEGER PRIMARY KEY,
    date TEXT,
    distance_km REAL,
    moving_time_s INTEGER,
    avg_pace_s_per_km REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    run_type TEXT,                   -- 'easy','tempo','interval','long','recovery','race'
    calories INTEGER,
    perceived_exertion INTEGER,
    elevation_gain_m REAL
);

-- Zónové sumarizace (per aktivita, z splits_metric)
CREATE TABLE zone_time (
    activity_id INTEGER,
    zone_type TEXT,                  -- 'pace' nebo 'hr'
    zone_name TEXT,                  -- 'z1_easy','z2_aerobic','z3_tempo','z4_threshold','z5_vo2max'
    time_s INTEGER,
    distance_m REAL,
    PRIMARY KEY (activity_id, zone_type, zone_name)
);

-- Tréninková zátěž (denní snapshot)
CREATE TABLE training_load (
    date TEXT PRIMARY KEY,
    atl REAL,                       -- acute (7-day)
    ctl REAL,                       -- chronic (42-day)
    tsb REAL                        -- freshness = ctl - atl
);

-- Best efforts / PRs
CREATE TABLE best_efforts (
    activity_id INTEGER,
    effort_name TEXT,               -- '400m','1k','1 mile','5k','10k','Half-Marathon','Marathon'
    elapsed_time_s INTEGER,
    date TEXT,
    is_pr INTEGER DEFAULT 0,        -- 1 pokud je to aktuální PR
    PRIMARY KEY (activity_id, effort_name)
);

-- Konfigurace (HR zóny, pace zóny)
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT                      -- JSON
);
-- Výchozí: max_hr, rest_hr, pace_zones, hr_zones
```

### 4.5 CLI příkazy
```bash
# Spočítej/aktualizuj sumarizace z Strava dat
python coach.py sync --strava-db /path/to/strava.db --db coach.db

# Nastav HR zóny (pro výpočet času v zónách)
python coach.py config --max-hr 195 --rest-hr 50 --db coach.db

# Týdenní přehled
python coach.py weekly [--weeks 4] --db coach.db

# Zónový report
python coach.py zones --db coach.db [--after 2026-01-01]

# Tréninková zátěž (ATL/CTL/TSB)
python coach.py load --db coach.db [--days 90]

# Nejlepší výkony / PRs
python coach.py prs --db coach.db

# Celkový souhrn pro LLM (JSON)
python coach.py summary --db coach.db --format json

# Health check
python coach.py check --db coach.db
```

### 4.6 Integrace s knowledge-vault
Přidat do `kv.py`:
```python
@cli.group(name="coach")
def coach_group():
    """Running coach commands."""
    pass

# kv coach sync, kv coach config, kv coach weekly, kv coach zones,
# kv coach load, kv coach prs, kv coach summary, kv coach check
```

### 4.7 Integrace s OpenClaw (později)
Do OpenClaw workspace přidat coaching instrukce, kde Cobie:
- Volá `kv coach summary --format json` pro aktuální data
- Volá `kv search "dotaz" --channel SteveMagness` pro znalosti
- Má instrukce pro tvorbu plánů, review, doporučení
- Cíl je dynamický — nastavuje uživatel přes konverzaci

### 4.8 CLAUDE.md pro running-coach
```markdown
# CLAUDE.md — running-coach

## Spuštění testů
source venv/bin/activate
pytest tests/ -v

## CLI
python coach.py sync --strava-db strava.db --db coach.db
python coach.py config --max-hr 195 --rest-hr 50 --db coach.db
python coach.py weekly [--weeks 4] --db coach.db
python coach.py zones --db coach.db [--after 2026-01-01]
python coach.py load --db coach.db [--days 90]
python coach.py prs --db coach.db
python coach.py summary --db coach.db --format json

## Architektura
- coach.py — Click CLI
- coach/zones.py — pace/HR zóny, klasifikace běhů
- coach/weekly.py — týdenní sumarizace
- coach/load.py — ATL/CTL/TSB výpočty
- coach/prs.py — best efforts / PRs tracking
- coach/trends.py — trendy a rolling averages
- coach/summary.py — celkový souhrn pro LLM (JSON output)
- coach/db.py — SQLite operace + config

## Datové zdroje
- Strava DB (read-only) → surové aktivity s detailed raw_json
- KB search (Qdrant) → evidence-based znalosti o běhání
- Coach DB (vlastní) → sumarizace, zóny, zátěž, PRs

## Ekosystém
Čte surová data ze strava-connector SQLite (včetně detailed splits),
počítá sumarizace a ukládá do vlastní DB.
OpenClaw/Cobie volá CLI pro coaching data.
KB pipeline (kb-search) poskytuje evidence-based znalosti.

## Context7
Vždy používej Context7 MCP.

## Konvence
- TDD: testy se píší před implementací
- Strava DB je read-only, coach DB je vlastní
- JSON output pro strojové zpracování (OpenClaw)
- HR/pace zóny jsou konfigurovatelné per uživatel
```

---

## 5. Pořadí implementace

1. Aktualizovat existující CLAUDE.md (5 souborů) — ekosystém sekce
2. Rozšířit strava-query/CLAUDE.md na plný formát
3. Vytvořit knowledge-vault/CLAUDE.md
4. Rozšířit strava-connector o `--detail` flag + CLAUDE.md update
5. Vytvořit running-coach/ projekt (scaffold + CLAUDE.md)
6. Integrace running-coach do knowledge-vault (kv coach)
7. ~~OpenClaw coaching konfigurace~~ (později, až running-coach funguje)

---

## 6. Verifikace

- Ověřit že všechny CLAUDE.md mají konzistentní formát (česky, sekce: Testy, CLI, Architektura, Ekosystém, Context7, Konvence)
- Ověřit že knowledge-vault/CLAUDE.md reflektuje všechny aktuální `kv` příkazy
- Ověřit že running-coach/CLAUDE.md odpovídá skutečné struktuře projektu
- Spustit `pytest tests/ -v` ve strava-connector po přidání --detail
- Spustit `pytest tests/ -v` v running-coach po scaffoldu

---

## Soubory k úpravě/vytvoření

| Soubor | Akce |
|--------|------|
| `/home/klach/projects/kb-ingest/CLAUDE.md` | Edit — přidat Ekosystém |
| `/home/klach/projects/kb-indexer/CLAUDE.md` | Edit — přidat Ekosystém |
| `/home/klach/projects/kb-search/CLAUDE.md` | Edit — přidat Ekosystém + API |
| `/home/klach/projects/strava-connector/CLAUDE.md` | Edit — přidat Ekosystém + --detail docs |
| `/home/klach/projects/strava-connector/sync.py` | Edit — přidat --detail flag |
| `/home/klach/projects/strava-query/CLAUDE.md` | Rewrite — rozšířit na plný formát |
| `/home/klach/projects/knowledge-vault/CLAUDE.md` | Create — nový |
| `/home/klach/projects/knowledge-vault/kv.py` | Edit — přidat coach group |
| `/home/klach/projects/running-coach/` | Create — celý nový projekt |
| `/home/klach/projects/running-coach/CLAUDE.md` | Create — nový |
