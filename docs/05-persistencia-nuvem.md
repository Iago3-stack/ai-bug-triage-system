# 05 — Persistência em Nuvem (Supabase)

O `ai-bug-triage-system` grava cada triagem como um **snapshot fiel**. Desde a **v2.1**,
esse histórico pode viver em um **Postgres na nuvem (Supabase)** em vez do disco efêmero
da Streamlit Cloud — o que faz o histórico **sobreviver a redeploys**. Desde a **v2.6.16**
esse mesmo Supabase também é usado para o **login multi-tenant (Auth/GoTrue)**, e cada
registro persistido carrega um `tenant_id` para **isolar o histórico por usuário**.

## Como funciona (arquitetura)

| Camada | Papel |
|---|---|
| `home.py` / `dashboard.py` / `rag.py` | Consomem `persistencia` (API única) |
| `persistencia.py` | **Facade** — se o Supabase estiver configurado, delega; senão, JSONL local |
| `nuvem_supabase.py` | Backend REST do Supabase (insert / select / update + vínculo Jira) |

**Decisão de design (fallback):** o JSONL local **nunca deixa de existir**. Sem credenciais,
o app segue 100% funcional com o arquivo (`PERSISTENCIA_BACKEND=jsonl` força esse modo).
Com credenciais, o histórico passa a ser gravado na nuvem e o expender do histórico mostra
`☁️ Supabase (nuvem — público)`.

> **Modelo de dado:** o registro inteiro viaja como `payload` (jsonb) + colunas tipadas
> (`id`, `data`, `data_hora`, `jira_key`, `jira_url`) — flexível e indexável.

## Como ativar (5 passos)

### 1. Crie o projeto no Supabase
1. Acesse [supabase.com](https://supabase.com) → **New project**.
2. Escolha uma senha de banco (guarde! você usa só se for conectar via psql) e região
   próxima (ex.: **South America (São Paulo)**).

### 2. Crie a tabela (SQL Editor)
No painel do projeto, abra **SQL Editor** → **New query** e cole:

```sql
create table if not exists triagens (
  id         text primary key,
  data_hora  timestamptz not null,
  data       date        not null,
  jira_key   text,
  jira_url   text,
  payload    jsonb       not null default '{}'::jsonb
);

alter table triagens enable row level security;

grant select, insert, update on table triagens to anon;
grant select, insert, update on table triagens to authenticated;

create policy "triagens anon insert" on triagens
  for insert to anon with check (true);

create policy "triagens anon select" on triagens
  for select to anon using (true);

create policy "triagens anon update" on triagens
  for update to anon using (true);
```

> **Por que RLS aberto ao `anon`?** Na fase atual o app é uma **vitrine pública**
> ("público = vitrine"): qualquer visitante pode triar e ver o histórico, igual ao
> comportamento já existente da Cloud. Quando o **login (multi-tenant)** entrar
> (próxima fase), essas políticas passam a ser por usuário (`to authenticated`).

### 3. Pegue as credenciais
Em **Settings → API**:
- **Project URL** → vira `SUPABASE_URL`
- **anon public key** → vira `SUPABASE_ANON_KEY`

> Use sempre a **anon key** (pública, com as regras do RLS). **NUNCA** use a
> `service_role` — ela contorna o RLS e é uma senha administrativa.

### 4. Configure nos secrets da Cloud
Streamlit Cloud → **Settings → Secrets** do app:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOi..."
```

> **Local (dev):** coloque as mesmas variáveis no arquivo `.env` do repositório
> (gitignored). O `nuvem_supabase._config()` lê nesta ordem:
> `st.secrets` → `.env` → `os.environ`.

### 5. Teste
1. Rode uma triagem → o expander do histórico deve mostrar `☁️ Supabase` e a linha
   aparece em **Supabase → Table Editor → triagens**.
2. **Redeploy** na Cloud → o histórico continua lá (persiste!).
3. Forçar local de novo, se quiser: `PERSISTENCIA_BACKEND=jsonl`.

## Pode resolver/evitar

- **Histórico sumindo a cada redeploy** (disco efêmero da Cloud) — resolvido: agora fica no Postgres.
- **Visão de "produto SaaS"**: dados persistentes e consultáveis por API + **login multi-tenant**
  (`auth_supabase.py`, v2.6.16) com `tenant_id` isolando registros por conta.

## Limitações atuais

- `excluir_antigos()` é **no-op** na nuvem (exclusão em massa via REST exige RPC — fora do
  escopo atual; o JSONL local continua suportando o recorte por idade).
- As políticas RLS do exemplo continuam abertas ao `anon` na **vitrine pública**; para um
  produto com contas, troque por políticas `to authenticated` com filtro por `tenant_id`
  (o app já persiste e filtra pelo tenant atual).
- **Failover já implementado**: se o Supabase estiver fora do ar, a triagem **não quebra** —
  o snapshot é gravado no JSONL local automaticamente.
- **Resolução (aprendizado do RAG)**: o campo `resolucao` vive dentro do `payload` (jsonb) —
  **sem migração de schema**. O `registrar_resolucao()` faz fetch + PATCH por `id` no payload
  e o RAG passa a incluir a resolução no contexto montado.

---

> ⚙️ Setup documentado em **07/09/2026** como parte da **v2.1 — fundação SaaS**.
> A etapa seguinte (**login multi-tenant**) foi implementada na **v2.6.16**, reutilizando as
> mesmas credenciais `SUPABASE_URL`/`SUPABASE_ANON_KEY` — sem config nova.