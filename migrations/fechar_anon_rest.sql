-- ─────────────────────────────────────────────────────────────────────────────
-- fechar_anon_rest.sql — Rota B: fim do acesso anônimo ao REST/Data API.
--
-- Contexto: o app e o webhook falam com o REST usando SUPABASE_SERVICE_ROLE_KEY
-- (bypassa RLS). As policies "anon *" (USING true, WITH CHECK true) hoje deixam
-- QUALQUER detentor da anon key ler/alterar tudo — inclusive auto-conceder
-- Premium em planos_usuario. Este arquivo revoga o anon nas 6 tabelas.
--
-- PRÉ-REQUISITO: configurar SUPABASE_SERVICE_ROLE_KEY em Local (.env),
-- Streamlit Secrets e Render env ANTES de aplicar (deploy já no ar).
-- Login/registro (/auth/v1, anon key) NÃO é afetado.
--
-- Como aplicar: Supabase → SQL Editor → cole e rode. Idempotente.
-- ─────────────────────────────────────────────────────────────────────────────

-- triagens
drop policy if exists "triagens anon insert" on public.triagens;
drop policy if exists "triagens anon select" on public.triagens;
drop policy if exists "triagens anon update" on public.triagens;
drop policy if exists "anon insert" on public.triagens;
drop policy if exists "anon select" on public.triagens;
drop policy if exists "anon update" on public.triagens;

-- planos_usuario (chave do dinheiro: anon NUNCA acessa)
drop policy if exists "anon insert" on public.planos_usuario;
drop policy if exists "anon select" on public.planos_usuario;
drop policy if exists "anon update" on public.planos_usuario;

-- solicitacoes_pagamento (cobranças: anon NUNCA acessa)
drop policy if exists "anon insert" on public.solicitacoes_pagamento;
drop policy if exists "anon select" on public.solicitacoes_pagamento;
drop policy if exists "anon update" on public.solicitacoes_pagamento;

-- perfis_usuario
drop policy if exists "anon insert" on public.perfis_usuario;
drop policy if exists "anon select" on public.perfis_usuario;
drop policy if exists "anon update" on public.perfis_usuario;

-- usuarios
drop policy if exists "anon insert" on public.usuarios;
drop policy if exists "anon select" on public.usuarios;
drop policy if exists "anon update" on public.usuarios;

-- feedbacks
drop policy if exists "anon insert" on public.feedbacks;
drop policy if exists "anon select" on public.feedbacks;
drop policy if exists "anon update" on public.feedbacks;

-- RLS permanece LIGADO (defesa em profundidade). Com o anon sem policies,
-- qualquer acesso pelo REST exige a service_role; um eventual bug de código
-- que use a anon key passa a falhar alto (deny) em vez de vazar dados.
--
-- Verificação rápida (deve retornar 0 linhas):
--   select * from pg_policies where schemaname = 'public';

-- ─────────────────────────────────────────────────────────────────────────────
-- Diagnóstico local (MCP/diagnóstico read-only): a role `mcp_readonly` usada
-- pelo nosso postgres MCP/script NÃO bypassa RLS e sem policies passa a ser
-- bloqueada. Garantimos SELECT para ela em todas as tabelas (só leitura; ela
-- não tem INSERT/UPDATE/DELETE grants).
-- ─────────────────────────────────────────────────────────────────────────────
create policy "mcp_readonly select" on public.triagens                 for select to mcp_readonly using (true);
create policy "mcp_readonly select" on public.planos_usuario           for select to mcp_readonly using (true);
create policy "mcp_readonly select" on public.solicitacoes_pagamento   for select to mcp_readonly using (true);
create policy "mcp_readonly select" on public.perfis_usuario           for select to mcp_readonly using (true);
create policy "mcp_readonly select" on public.usuarios                 for select to mcp_readonly using (true);
create policy "mcp_readonly select" on public.feedbacks                for select to mcp_readonly using (true);