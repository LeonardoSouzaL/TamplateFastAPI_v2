# Dashboards — guia de estilização

Guia visual para **criar novos dashboards** neste sistema. Complementa [`docs/layout-sistema.md`](./layout-sistema.md) (chrome, tokens, tema). Não cobre APIs nem regras de negócio.

**Padrão canônico:** Lastmile (`lastmile_dashboard.css`). Reuse essas classes. Não inventar um prefixo novo (`ci-*`, `crm-*`) salvo o módulo já ter identidade própria (Indoor, Kanban).

---

## 1. Dashboards existentes

| Tela | Template | CSS | JS / Chart.js |
|------|----------|-----|----------------|
| Lastmile — Dashboard de viagens | `transportes/templates/transportes/lastmile/dashboard.html` | `transportes/css/lastmile_dashboard.css` | inline + Chart.js 4.4.1 |
| Lastmile — SLA por técnico | `…/lastmile/driver_status_summary.html` | `dashboard_clr.css` + `lastmile_dashboard.css` + `lastmile_driver_status.css` | `lastmile_driver_status.js` |
| Controle de campo — CLR | `…/controle_campo/dashboard_clr.html` | `transportes/css/dashboard_clr.css` | `dashboard_clr.js` |
| Lista de viagens (modo dashboard) | `…/transportes/lista_viagens.html` + `_lista_viagens_results.html` | `lastmile_dashboard.css` + `lista_viagens.css` | `transportes_dashboard_charts.js` |
| Consulta OS (modo dashboard) | `…/transportes/consulta_os_transp.html` / `consulta_os_v2.html` | `lastmile_dashboard.css` + CSS da consulta | `transportes_dashboard_charts.js` |
| CRM — Dashboard | `crm/templates/crm/templates_dashboard/dashboard.html` | **CSS inline** no template | inline Chart.js |
| Kanban — visão dashboard | `crm/…/partials/_kanban_dashboard_view.html` | `global/css/crm_kanban.css` | `crm_kanban_dashboard.js` |
| Claro Indoor — hub KPIs | `logistica/…/templates_claro_indor/hub.html` | `logistica/claro_indor/claro_indor.css` | sem gráfico |

Telas lastmile de **lista** (pendentes, atribuir, OS externas) também usam o wrapper `.lastmile-dashboard` (heading + filtros + tabela), mas não são painéis de KPI/gráfico.

---

## 2. Receita para um dashboard novo

1. `{% extends 'global/base.html' %}`.
2. CSS no `block content` (não existe `extra_css`):

```html
<link rel="stylesheet" href="{% static 'transportes/css/lastmile_dashboard.css' %}?v=YYYYMMDDx">
```

3. Wrapper fluido (não `.app-page--form` de 1300px). O arquivo lastmile já aplica margem da topbar + gutter.
4. Widgets Django com `class="filter-input"` (texto/data) e `class="filter-select"` (select).
5. Chart.js **4.4.1** via CDN. Cores de eixos via `window.AranciaTheme.chart()`. Redesenhar no evento `arancia:themechange`.
6. Overlay escuro: `html[data-theme="dark"]` — **nunca** `prefers-color-scheme`.

### Esqueleto HTML

```html
{% extends "global/base.html" %}
{% load static %}

{% block content %}
<link rel="stylesheet" href="{% static 'transportes/css/lastmile_dashboard.css' %}?v=…">

<main class="lastmile-dashboard">
  <header class="dashboard-heading">
    <div>
      <p class="eyebrow">Módulo</p>
      <h1><i class="fa-solid fa-chart-line"></i> Título</h1>
      <p class="subtitle">Indicadores · escopo atual</p>
    </div>
    <a href="…" class="btn-export"><i class="fa-solid fa-file-excel"></i> Exportar</a>
  </header>

  <form method="get" class="dashboard-filters">
    <div class="filter-field">
      <label for="id_data">Data</label>
      {{ form.data }}
    </div>
    <div class="filter-actions">
      <button type="submit" class="btn-filter">
        <i class="fa-solid fa-filter"></i> Aplicar filtros
      </button>
      <a href="{% url 'app:esta_tela' %}" class="btn-clear">Limpar</a>
    </div>
  </form>

  <section class="kpi-grid" aria-label="Indicadores">
    <article class="kpi-card kpi-card--warning">
      <span class="kpi-icon"><i class="fa-solid fa-clock"></i></span>
      <div>
        <span class="kpi-label">Pendentes</span>
        <strong>{{ kpis.pending }}</strong>
      </div>
    </article>
    <!-- 3–4 cards; use kpi-grid--six se forem 6 -->
  </section>

  <section class="charts-grid" aria-label="Gráficos">
    <article class="chart-panel">
      <div class="panel-title">
        <h2>Por status</h2>
        <i class="fa-solid fa-chart-pie"></i>
      </div>
      <div class="chart-body">
        <canvas id="statusChart"></canvas>
      </div>
    </article>
    <article class="chart-panel chart-panel--wide">
      <div class="panel-title">
        <h2>Série larga</h2>
        <i class="fa-solid fa-chart-column"></i>
      </div>
      <div class="chart-body chart-body--tall">
        <canvas id="wideChart"></canvas>
      </div>
    </article>
  </section>
</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
{% endblock %}
```

**Alternativa de shell global:** `.app-page.app-page--fluid` (`content-shell.css`) se a tela não for lastmile e não quiser o wrapper `.lastmile-dashboard`. Ainda assim, reusar `kpi-grid` / `chart-panel` do CSS lastmile.

---

## 3. Tokens e paleta

### 3.1 Layout (já no `layout-tokens.css`)

| Token | Valor | Uso no dashboard |
|-------|-------|------------------|
| `--topbar-height` | `50px` | `margin-top: calc(var(--topbar-height) + 24px)` |
| `--content-gutter` | `16px` | padding lateral do wrapper |
| `--content-inset-left` | sidebar + gap | **não** repetir `margin-left: 65px` — o `.forma > .container` já aplica inset |

Wrapper lastmile / CLR:

```css
width: 100%;
max-width: 100%;
margin: calc(var(--topbar-height, 50px) + 24px) 0 32px;
padding: 0 var(--content-gutter, 16px);
```

Fonte autenticada: **Roboto**. Ícones: **Font Awesome 6** (`fa-solid`).

### 3.2 Superfícies (claro → escuro)

| Papel | Claro | Escuro (`html[data-theme="dark"]`) |
|-------|-------|-------------------------------------|
| Texto da página | `#243247` | `#e8eaed` |
| Título h1 / valor KPI | `#172033` | `#e8eaed` |
| Muted / label / subtitle | `#64748b` | `#9aa0a6` |
| Label de campo | `#475569` | `#9aa0a6` |
| Card / filtro / painel | `#fff` | `#2c3240` |
| Borda card | `#e2e8f0` | `#3a3f4b` |
| Borda input | `#cbd5e1` | `#3a3f4b` |
| Poço / thead / ícone KPI | `#f8fafc` / `#f1f5f9` | `#1e2430` |
| Hover linha / item | `#fff7ed` / `#fffaf5` | `#1e3a5f` |
| Página (lista em modo dash) | `#f1f5f9` | overlay do módulo |

Sombra padrão de card: `0 7px 20px rgba(15, 23, 42, .05–.06)`.  
Raio: **14px** cards/painéis/filtros; **8–10px** inputs/botões; **999px** chips.

### 3.3 Marca e ações

| Papel | Hex | Onde |
|-------|-----|------|
| Accent / ícone de título | `#e57b25` | `.eyebrow`, `h1 i`, `panel-title i`, focus ring |
| CTA filtrar | `#e57b25` borda `#df6e16` | `.btn-filter` |
| Hover CTA | `#cf6c1c` | CLR `.btn-filter:hover` |
| Focus ring | `0 0 0 3px rgba(229, 123, 37, 0.12–0.16)` | input/select/search |
| Accent-color checkbox | `#e57b25` | `.filter-checkbox` |
| Export Excel | `#16a34a` hover `#15803d` | `.btn-export` |
| Limpar / secundário | fundo `#fff`, texto `#475569`, borda `#cbd5e1` | `.btn-clear` |
| Perigo | `#b42318` / `#b91c1c` | `.btn-filter-danger`, empty error |
| Link operacional | `#d96610` | `.travel-link` |
| KPI filtrado (azul) | `#1d4ed8` | valor quando há filtro ativo |

O CTA de **formulário** operacional continua `#fc9b63` (`--button-form-color`). Dashboards usam o laranja **mais saturado** `#e57b25`.

### 3.4 Semântica de KPI (ícone)

Lastmile (`lastmile_dashboard.css`):

| Modificador | Fundo ícone | Cor ícone | Uso |
|-------------|-------------|-----------|-----|
| (default) | `#f1f5f9` | `#475569` | neutro |
| `.kpi-card--warning` | `#fff7e6` | `#d97706` | pendente |
| `.kpi-card--danger` | `#fff0f0` | `#dc2626` | sem técnico / crítico |
| `.kpi-card--success` | `#ecfdf3` | `#15803d` | atendidas |
| `.kpi-card--sla` | `#f3e8ff` | `#7e22ce` | atraso / pior SLA |

CLR (`dashboard_clr.css`) adiciona:

| Modificador | Fundo | Cor |
|-------------|-------|-----|
| `.kpi-card--total` | `#eef2ff` | `#4338ca` |
| `.kpi-card--info` | `#eff6ff` | `#2563eb` |
| `.kpi-card--unassigned` | `#f1f5f9` | `#475569` |
| `.kpi-card--warning` | `#fff7ed` | `#e57b25` |

Escuro: fundos viram `#3a2e14` (warning), `#3a1c1c` (danger), `#163024` (success), `#1e3a5f` (info), `#1e2740` (total).

### 3.5 Status / chips de operação

| Classe | Fundo | Texto |
|--------|-------|-------|
| `.status-chip` | `#f1f5f9` | `#475569` |
| `.travel-status` | `#e8f2ff` | `#1d4ed8` |
| `.travel-type` | `#ecfdf5` | `#047857` |
| `.without-technician` | `#fee2e2` | `#b91c1c` |
| `.late-deadline` | — | `#b91c1c` weight 800 |
| `.dashboard-clr-filter-chip` / `.kanban-dashboard-filter-chip` | `#eff6ff` borda `#bfdbfe` | `#1d4ed8` |
| `.multi-chip` (filtro multi) | `#fff7ed` borda `#fed7aa` | `#c2410c` |

---

## 4. Catálogo de classes (padrão Lastmile / CLR)

### 4.1 Página

| Classe | Função |
|--------|--------|
| `.lastmile-dashboard` | Wrapper canônico (margem topbar, gutter, cor de texto) |
| `.lastmile-dashboard--pa` | Variante PA (menos gráficos de gestão) |
| `.dashboard-clr` | Wrapper CLR; mesmas margens; KPI em 3 colunas |
| `.lastmile-driver-status` | Combinar com `.dashboard-clr` na tela SLA técnico |
| `.lastmile-lista` | Listas lastmile com o mesmo heading/filtros |

### 4.2 Heading

| Classe | Função | Medidas |
|--------|--------|---------|
| `.dashboard-heading` | Flex título + ação (export) | `align-items: flex-end`, gap visual 20px abaixo |
| `.eyebrow` | Label uppercase acima do h1 | 0.74rem, weight 800, letter-spacing 0.08em, `#e57b25` |
| `h1` | Título | `clamp(1.55rem, 2.6vw, 2.2rem)` — CLR um pouco menor |
| `h1 i` | Ícone FA | margin-right 8px, `#e57b25` |
| `.subtitle` | Linha de contexto | `#64748b`, 7px abaixo do h1 |
| `.escopo-switch` | Toggle PA/Cluster (CLR) | pill `border-radius: 999px` |
| `.escopo-switch-btn` | Item do toggle | ativo: fundo `#e57b25` branco |
| `.btn-export` | CTA verde Excel | padding 10×14, radius 10px, sombra verde |

### 4.3 Filtros

| Classe | Função |
|--------|--------|
| `.dashboard-filters` | Barra flex wrap, padding 16px, card branco radius 14 |
| `.dashboard-clr-filters` | Mesmo visual em **grid** (PA / UF / cidade / ações) |
| `.dashboard-clr-filters--simple` | Só 1 campo + ações |
| `.filter-field` | Coluna label + controle; `flex: 1 1 190px` |
| `.filter-field--chips` | Multi-select / chips; min 220px max 340px |
| `.filter-field--pa` | Busca de PA; overflow visível |
| `.filter-field--cluster` | Multi cluster CLR |
| `.filter-field--driver` | Autocomplete técnico |
| `.filter-field--checkbox` | Checkbox alinhado à altura do input |
| `.filter-input` | Input 40px, radius 8–10px, borda `#cbd5e1` |
| `.filter-select` | Select 40px + seta SVG custom (sem appearance nativa) |
| `.filter-checkbox` | 17px, `accent-color: #e57b25` |
| `.filter-actions` | Botões no fim da barra |
| `.filter-hint` | Texto auxiliar com ícone laranja |
| `.field-error` / `.form-error` | `#b42318`, 0.76rem |
| `.btn-filter` | Primário laranja, min-height 40px, weight 700 |
| `.btn-clear` | Secundário outlined |
| `.btn-filter-danger` | Outlined vermelho |

Busca / chips (dentro dos filtros):

| Classe | Função |
|--------|--------|
| `.multi-search` / `.multi-search-box` | Caixa de chips + input |
| `.multi-chip` / `.multi-chip-remove` | Chip selecionado |
| `.multi-search-dropdown` / `.multi-search-item` | Lista absoluta z-index 9999 |
| `.pa-search` / `.pa-search-box` / `.pa-search-input` | Combobox PA |
| `.pa-search-dropdown` / `.pa-search-item` / `.is-active` | Dropdown |
| `.pa-search-native` | `<select>` invisível (acessibilidade) |
| `.crm-search-select` | Autocomplete compartilhado (`crm_search_select.js`) |
| `.driver-results` / `.driver-item` | Autocomplete motorista |

### 4.4 KPIs

| Classe | Função | Medidas |
|--------|--------|---------|
| `.kpi-grid` | Grid 4 colunas, gap 16px | ≤1050px → 2; ≤767 → 1 |
| `.kpi-grid--six` | 6 colunas | ≤1280 → 3; ≤720 → 2 |
| `.kpi-link` | Envolve o card (navega para lista) | `text-decoration: none` |
| `.kpi-card` | Card flex, min-height **105px**, padding 18px, radius 14 | hover (via `.kpi-link`): translateY(-2px) |
| `.kpi-card-body` | Coluna label + valor + botão (CLR) | |
| `.kpi-icon` | Quadrado 45×45, radius 12 | |
| `.kpi-label` | 0.76–0.78rem, weight 700, `#64748b` (CLR: uppercase) | |
| `.kpi-card strong` | Valor 1.8rem (CLR: clamp 1.35–1.75) | |
| `.kpi-card small` | Linha extra (PA, detalhe) | ellipsis |
| `.kpi-arrow` | Ícone “abrir lista” | |
| `.kpi-card--clickable` | Cursor pointer + hover (CLR) | |
| `.kpi-card.is-kpi-active` | Borda azul `#93c5fd` quando filtro ativo | |
| `.kpi-ver-lista` | Botão pill “Ver lista” | 0.78rem, radius 999px |
| `.has-active-filters .kpi-card strong` | Valores ficam `#1d4ed8` | |

KPI clicável lastmile:

```html
<a class="kpi-link" href="…">
  <article class="kpi-card kpi-card--warning">
    <span class="kpi-icon"><i class="fa-solid fa-clock"></i></span>
    <div>
      <span class="kpi-label">Viagens pendentes</span>
      <strong>{{ n }}</strong>
    </div>
    <i class="fa-solid fa-arrow-up-right-from-square kpi-arrow"></i>
  </article>
</a>
```

### 4.5 Gráficos

| Classe | Função | Medidas |
|--------|--------|---------|
| `.charts-grid` | 2 colunas, gap 16px | ≤760/960 → 1 |
| `.charts-grid--pa` | Ordem: resumo primeiro (usuário PA) | |
| `.chart-panel` | Card do gráfico | overflow hidden, radius 14 |
| `.chart-panel--wide` | `grid-column: 1 / -1` | |
| `.chart-panel--summary` / `--pa-secondary` | Ordem no grid PA | |
| `.panel-title` | Header 15×18px + borda `#edf1f5` | h2 0.95rem `#334155` |
| `.chart-body` | Área canvas **300px** + padding 16px | |
| `.chart-body--tall` | **420px** | |
| `.chart-body--doughnut` | Coluna centralizada (SLA técnico) | |
| `.chart-canvas-wrap` | Caixa doughnut ~240×210 | |
| `.chart-legend` / `__swatch` / `__value` | Legenda HTML (não a do Chart.js) | |
| `.chart-empty` | Placeholder sem dados | `#94a3b8` |

Canvas: `maintainAspectRatio: false` (o CSS manda a altura). `borderRadius` da barra: **5–6px**.

### 4.6 Breakdown, empty, export, loading

| Classe | Função |
|--------|--------|
| `.breakdown-panel` / `.breakdown-grid` | Grid 2 colunas de mini-listas |
| `.pending-overview` / `.pending-breakdown` | Resumo + chips de status |
| `.dashboard-export` | Faixa verde `#f0fdf4` / borda `#bbf7d0` |
| `.empty-state` | Tracejado, min-height 250px |
| `.empty-state--error` | Fundo `#fff7f7`, texto `#991b1b` |
| `.screen-placeholder` | Tela “em construção” / sem escopo |
| `.dashboard-clr-hint` / `.kanban-dashboard-hint` | “Clique nas barras…” |
| `.dashboard-clr-active-filters` | Chips do recorte atual |
| `.dashboard-clr-filter-loading` | Overlay `rgba(15,23,42,.35)` z-index 10070 |
| `.dashboard-clr-filter-loading-box` | Caixa branca com spinner laranja |

### 4.7 Tabela embutida / modal de casos (CLR)

| Classe | Função |
|--------|--------|
| `.dashboard-clr-modal` | Overlay flex, z-index **10060** |
| `.dashboard-clr-modal-box` | `min(1760px, 98vw)` × `min(960px, 94vh)` |
| `.dashboard-clr-casos-table` | thead sticky `#f8fafc` |
| `td.status-pendente` | `#dc2626` weight 700 |
| `.kanban-dashboard-results` | Lista de tasks abaixo dos KPIs |

---

## 5. Chart.js

### 5.1 Biblioteca e tema

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

`theme.js` expõe:

```js
window.AranciaTheme.chart()
// { text, muted, grid, border, legend }
```

| Chave | Claro | Escuro |
|-------|-------|--------|
| `text` | `#172033` | `#e8eaed` |
| `muted` | `#64748b` | `#c5c9d0` |
| `grid` | `rgba(148, 163, 184, 0.14)` | `rgba(154, 160, 166, 0.18)` |
| `border` | `#ffffff` | `#1c1f26` |
| `legend` | `#334155` | `#e8eaed` |

Obrigatório ao montar gráficos:

```js
function chartTheme() {
  if (window.AranciaTheme && typeof window.AranciaTheme.chart === "function") {
    return window.AranciaTheme.chart();
  }
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  return { /* fallback da tabela acima */ };
}

render();
window.addEventListener("arancia:themechange", render);
```

Antes de redesenhar: `Chart.getChart(canvas)?.destroy()`.

Defaults globais (já aplicados por `theme.js` se Chart.js carregou):

```js
Chart.defaults.color = palette.text;
Chart.defaults.borderColor = palette.grid;
```

Opções comuns (lastmile):

```js
{
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { beginAtZero: true, grid: { color: theme.grid }, ticks: { color: theme.muted } },
    y: { beginAtZero: true, grid: { color: theme.grid }, ticks: { color: theme.muted } },
  },
}
```

Doughnut: `legend.position = "bottom"`, `boxWidth: 12`, `usePointStyle: true`, `borderWidth: 2`, `borderColor: theme.border`.

Helper compartilhado (consulta OS / lista viagens): `base_static/transportes/js/transportes_dashboard_charts.js`.

Dados: passar JSON via `{{ dashboard|json_script:"meu-id" }}` e ler no JS — não interpolar objeto no script.

### 5.2 Paletas de série

**Cíclica (consulta OS / lista viagens)** — `transportes_dashboard_charts.js`:

`#2563eb` `#f59e0b` `#10b981` `#ef4444` `#8b5cf6` `#06b6d4` `#f97316` `#64748b` `#ec4899` `#14b8a6` `#84cc16` `#6366f1`

**Cíclica CLR** — `dashboard_clr.js`:

`#e57b25` `#2563eb` `#16a34a` `#dc2626` `#7c3aed` `#0891b2` `#ca8a04` `#64748b` `#db2777` `#0f766e`

**Cíclica CRM dashboard** (inline):

`#3498db` `#2ecc71` `#e74c3c` `#f39c12` `#9b59b6` `#1abc9c` `#e67e22` `#34495e` `#16a085` `#c0392b`

**Lastmile — uma cor por métrica** (barra):

| Série | Hex |
|-------|-----|
| Pendentes | `#f59e0b` |
| Sem motorista | `#ef4444` |
| Finalizadas | `#22c55e` |
| Atrasadas (PA) | `#8b5cf6` |
| Tempo médio | `#0ea5e9` |
| Pendentes × cliente | `#ea580c` |
| Pendentes × tipo | `#0284c7` |
| Sem técnico × cliente | `#dc2626` |
| Sem técnico × tipo | `#f43f5e` |
| Atendidas × cliente | `#16a34a` |
| Atendidas × tipo | `#0d9488` |
| Atraso × cliente | `#7c3aed` |
| Atraso × tipo | `#a855f7` |

**SLA técnico:**

| Status | Hex |
|--------|-----|
| Finalizadas | `#16a34a` |
| Em andamento | `#e57b25` |
| Atrasadas | `#7c3aed` |
| Sem prazo | `#64748b` |

**CLR — produtividade / TEC1 (fixas, não cíclicas):**

| Label | Hex |
|-------|-----|
| Visita com sucesso / Atendido no horário | `#16a34a` |
| Visita sem sucesso | `#e57b25` |
| Não visitado / Pendente no horário | `#dc2626` |
| Pendente fora do horário | `#b91c1c` |
| Pendente aguardando Janela/horário | `#2563eb` |
| Atendido fora do horário | `#ca8a04` |

Regra: status **ruim** = vermelho; **ok** = verde; **em curso / marca** = laranja `#e57b25`; **atraso SLA** = roxo; **aguardando** = azul.

---

## 6. Outros padrões (não misturar)

### 6.1 Kanban dashboard (`crm_kanban.css`)

Usar **só** na visão dashboard do board. Classes próprias:

| Classe | Notas |
|--------|-------|
| `.kanban-page--dashboard` | Modo da página |
| `.kanban-dashboard-view` | Coluna flex, gap 14px |
| `.kanban-dashboard-kpis` | Grid 4 col; ≤960 → 1 |
| `.kanban-dashboard-kpi` | min-height 84px, padding 14×16, **sem** ícone 45px |
| `.kanban-dashboard-kpi--warn` | valor `#b91c1c` |
| `.kanban-dashboard-kpi__action` | pill “Ver lista” (igual CLR) |
| `.kanban-dashboard-grid` | 2 colunas de painéis |
| `.kanban-dashboard-panel` | padding 16px (título é `h3`, não `.panel-title`) |
| `.kanban-dashboard-panel--assignees` | full width |
| `.kanban-dashboard-panel__chart-wrap` | altura **220px** |
| `.kanban-dashboard-legend` / `.kanban-dashboard-swatch` | 10px círculo |
| `.kanban-dashboard-load-btn` | “Carregar itens” das colunas adiadas |
| `.kanban-filters--dashboard` | Filtros compactos (altura 34px) |

KPI ativo: mesma borda azul `#93c5fd` do CLR.

### 6.2 CRM dashboard comercial

CSS **inline** no template. Prefixo `.crm-dashboard-page`.

- Shell legado: `margin: calc(var(--topbar-height) + 20px) var(--content-gutter) 28px var(--content-offset)` e `max-width: 1300px` — **não copiar** em tela nova (preferir inset do container + wrapper lastmile/fluid).
- `.crm-kpi-row` flex wrap; card radius **12px**, sem ícone.
- `.graficos-grid` 2 colunas; `.chart-card` min-height 260px, canvas max 240px.
- `.crm-alert-banner` amarelo `#fff3cd`.
- Atalhos: `.box` + lista (padrão gestão skills).

Tela nova de CRM: reusar lastmile **ou** extrair essas classes para um CSS; não duplicar o inline.

### 6.3 Claro Indoor hub

Prefixo `ci-*` exclusivo do módulo Indoor. Não usar fora.

| Classe | Notas |
|--------|-------|
| `.ci-kpi-grid` | `auto-fit, minmax(180px, 1fr)` |
| `.ci-kpi-card` | radius **16px**, padding 16×18 |
| `.ci-kpi-label` | 12px uppercase |
| `.ci-kpi-value` | 28px, cor `--ci-primary` (`#153e70`) |
| `.ci-chip` / `.ci-shortcut` | atalhos, não gráficos |

Accent Indoor: `#ef6c00` (não `#e57b25`).

### 6.4 Modo dashboard em listas (Consulta OS / Lista viagens)

Não é página só de dashboard: o usuário troca com `.btn-view-mode`.

```html
<a class="btn-view-mode{% if view_mode == 'dashboard' %} active{% endif %}" title="Dashboard">
```

- Inativo: transparente, `#64748b`.
- `.active`: fundo `#fff`, texto `#2563eb`, sombra leve.
- Resultados: `.lista-viagens-dashboard.consulta-os-dashboard` + as **mesmas** `.kpi-grid` / `.charts-grid`.
- Fundo do poço: `#f1f5f9` quando o modo dashboard está ativo.

---

## 7. Responsivo (desktop-first)

Não projetar mobile-first. Media queries **restringem** larguras menores.

| Breakpoint | Efeito típico |
|------------|----------------|
| ≤1280 | `.kpi-grid--six` → 3 colunas |
| ≤1100 | CLR KPI → 2; filtros CLR → 2 |
| ≤1050 | `.kpi-grid` → 2 |
| ≤980 / 960 | gráficos → 1 coluna; Kanban KPI → 1 |
| ≤767 | heading empilha; filtros coluna; inputs **16px** / min-height **44px**; botões full width; overflow-x só na tabela |
| ≤720 | `.kpi-grid--six` → 2 |
| ≤560 | CLR KPI e filtros → 1 |

Telefone: tap-target ≥44px; `overflow-x` só no wrapper da tabela (`.pending-table-scroll`, `.table-responsive`, `.dashboard-clr-casos-table-wrap`).

---

## 8. Dark overlay — checklist

Toda superfície clara do dashboard precisa de regra `html[data-theme="dark"] …`. O lastmile já cobre heading, filtros, KPI, painéis, empty, paginação, modais. Se criar classe nova:

| Superfície clara | Escuro |
|------------------|--------|
| `#fff` card | `#2c3240` |
| `#f8fafc` / `#f1f5f9` poço | `#1e2430` |
| texto `#172033` | `#e8eaed` |
| muted `#64748b` | `#9aa0a6` |
| borda `#e2e8f0` | `#3a3f4b` |
| hover laranja claro | `#1e3a5f` |
| faixa export verde | `#163024` / texto `#86efac` |
| erro | `#3a1c1c` / `#fca5a5` |

Não pintar hex de canvas/card **sem** a regra dark. Login/print/e-mail nunca herdam este overlay.

---

## 9. Formulários Django (widgets)

Nos forms do dashboard, aplicar classe no widget — o CSS não estiliza `input` cru.

```python
forms.DateInput(attrs={"type": "date", "class": "filter-input"})
forms.Select(attrs={"class": "filter-select"})
forms.Select(attrs={"class": "filter-select js-crm-search-select"})  # busca
```

Select pesquisável lastmile: `lastmile_searchable_select.js` (`data-searchable="1"` / `data-searchable-multi="1"`).

---

## 10. Acessibilidade e conteúdo

- `aria-label` nas seções (`.kpi-grid`, `.charts-grid`).
- Ícones FA com `aria-hidden="true"` quando o texto ao lado já descreve a ação.
- Empty state com ícone + frase; erro com `.empty-state--error`.
- KPI que navega: envolver com `.kpi-link` **ou** botão `.kpi-ver-lista` — não os dois no mesmo card sem necessidade.
- Cache-bust CSS/JS: `?v=YYYYMMDDx` quando o arquivo muda.

---

## 11. O que não fazer

- Novo prefixo CSS (`xyz-kpi`) se o lastmile já resolve.
- `margin-left: 65px`, `width: 1300px`, `margin-top: 95px`.
- `.app-page--form` em dashboard (corta em 1300px).
- Chart.js de outra major version.
- Cores de gráfico hardcoded sem `AranciaTheme.chart()` nos eixos.
- `prefers-color-scheme` para tema.
- Copiar o CSS inline do CRM dashboard como base.
- Usar classes `ci-*` fora do Indoor.
- Esconder overflow no wrapper de filtros (quebra dropdown de PA/chips).

---

## 12. Arquivos de referência

| Arquivo | Papel |
|---------|--------|
| `base_static/transportes/css/lastmile_dashboard.css` | **Fonte principal** de classes compartilhadas |
| `base_static/transportes/css/dashboard_clr.css` | CLR: KPI 3 col, filtros grid, modal casos, switch escopo |
| `base_static/transportes/css/lastmile_driver_status.css` | Ajustes SLA técnico |
| `base_static/transportes/js/transportes_dashboard_charts.js` | Doughnut/bar reutilizáveis |
| `base_static/global/javascript/theme.js` | `AranciaTheme.chart` + evento `arancia:themechange` |
| `base_static/global/css/crm_kanban.css` | Só visão dashboard do board |
| `docs/layout-sistema.md` | Chrome, tokens, tipos de tela |
| `docs/dashboard-operacional-frontend.md` | API CLR (não é UI) |
