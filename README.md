# Todas Store — Assistente de Marketing 💖

Sistema web (PWA) simples e intuitivo para a lojista organizar o conteúdo do
Instagram da loja, gerar ideias com IA, acompanhar execução e analisar
concorrentes — tudo em poucos cliques, sem precisar entender de tecnologia.

## 1. O que o sistema faz

- **Dashboard único**: mês atual, progresso, stories/posts feitos, checklist do dia, próximo conteúdo.
- **Planejamento mensal automático**: cada mês é dividido em semanas (Segunda a Domingo) e dias.
- **Geração de conteúdo com IA (Groq)**: um clique gera Story todos os dias + 3 Posts por semana, com tema, legenda, CTA, objetivo, formato e tempo estimado.
- **Checklist editável** por dia.
- **Banco de Ideias**: salvar, buscar, favoritar e reaproveitar ideias.
- **Datas comemorativas** reconhecidas automaticamente (Dia das Mães, Namorados, Natal, Black Friday, estações do ano, liquidações).
- **Análise de concorrentes**: cadastro de perfis do Instagram, coleta de dados públicos (best-effort, já que o Instagram não oferece API gratuita para isso), observações manuais sobre Stories, e análise da IA com pontos fortes, repetições, oportunidades e sugestões de conteúdo inédito.
- **Insights semanais automáticos** sobre frequência, diversidade e equilíbrio entre venda e relacionamento.
- **Configurações**: nome, logo, Instagram, WhatsApp, cidade, segmento, horário.

## 2. Rodando localmente

```bash
# 1. Clonar/baixar o projeto e entrar na pasta
cd todasstore

# 2. Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env e coloque sua chave gratuita da Groq (https://console.groq.com/keys)

# 5. Rodar o sistema
python wsgi.py
```

Acesse em `http://localhost:5000`. Na primeira vez, o sistema vai pedir para
preencher o perfil da loja (onboarding).

## 3. Como conseguir a chave gratuita da Groq

1. Acesse https://console.groq.com/keys
2. Crie uma conta gratuita
3. Clique em "Create API Key"
4. Copie a chave e cole em `GROQ_API_KEY` no arquivo `.env` (local) ou nas
   variáveis de ambiente do Render (produção)

O plano gratuito da Groq tem limites de uso por minuto/dia — suficientes para
o uso diário de uma loja pequena/média.

## 4. Deploy no Render (gratuito)

1. Suba este projeto para um repositório no GitHub.
2. No [Render](https://render.com), clique em **New > Blueprint** e aponte
   para o repositório — o arquivo `render.yaml` já configura automaticamente:
   - o serviço web (plano gratuito)
   - o banco de dados PostgreSQL (plano gratuito)
   - as variáveis de ambiente necessárias
3. Quando pedido, cole sua `GROQ_API_KEY` (a única variável que precisa ser
   preenchida manualmente — as demais são geradas ou conectadas automaticamente).
4. Aguarde o build. Pronto, o sistema estará no ar em uma URL gratuita `*.onrender.com`.

> **Sem serviços pagos obrigatórios**: web service gratuito, banco de dados
> gratuito (Render free tier) e IA gratuita (Groq). O plano gratuito do
> Render "dorme" após 15 minutos sem uso, e o primeiro acesso depois disso
> pode demorar ~30s para acordar — isso é esperado e normal no plano free.

## 5. Estrutura do projeto

```
/app
  /models        -> modelos do banco de dados (SQLAlchemy)
  /routes        -> rotas/blueprints (dashboard, planejamento, ideias, concorrentes, config)
  /services       -> regras de negócio (planejamento, checklist, analytics, instagram)
  /ai             -> serviço de IA (Groq) e templates de prompts
  /templates      -> telas HTML (Bootstrap 5)
  /static         -> CSS, JS, ícones, manifest do PWA
config.py         -> configurações centrais (lidas de variáveis de ambiente)
render.yaml       -> configuração de deploy no Render
app.py            -> ponto de entrada
requirements.txt  -> dependências Python
.env.example      -> modelo de variáveis de ambiente
```

## 6. Sobre a análise de concorrentes

O Instagram não oferece uma API gratuita e oficial para consultar perfis de
terceiros, e ativamente bloqueia leituras automatizadas. Por isso o sistema:

- Tenta ler dados **públicos e básicos** da página do perfil (best effort,
  pode não funcionar sempre);
- Sempre oferece um campo para a lojista **registrar manualmente** observações
  sobre os Stories dos concorrentes (que nunca podem ser coletados
  automaticamente, pois somem em 24h);
- Usa a IA para transformar o que foi coletado + as observações manuais em
  insights práticos e sugestões de conteúdo inédito (nunca cópia).

## 7. Banco de dados e migrations (Alembic)

O esquema do banco é controlado por **migrations Alembic** (via `Flask-Migrate`)
na pasta `migrations/`. As migrations atuais são:

- `0001_baseline_producao`: snapshot do esquema que **já existia** em produção
  antes das melhorias (todas as tabelas originais).
- `0002_add_descricao_visual_e_versao_conteudo`: adiciona a coluna
  `dia.descricao_visual` e a tabela `versao_conteudo` (histórico de versões
  antes de regenerar conteúdo).

### Em ambiente novo (dev local)

Basta rodar:

```bash
flask --app wsgi db upgrade
```

O Alembic aplica todas as migrations, criando o esquema completo do zero.
Como rede de segurança, `db.create_all()` é chamado no `create_app()` (é
no-op seguro quando as tabelas já existem).

### Em producao (Render, PostgreSQL ja com dados)

O `render.yaml` ja tem `preDeployCommand: "python scripts/run_migrations.py"`.
Esse script e idempotente: detecta se o banco ja tem `alembic_version`, faz
`stamp` da baseline se for a primeira vez (banco legado) e sobe as
incrementais pendentes. Disponde o engine no fim para garantir que o gunicorn
que sobe logo depois comece com conexoes novas e limpas - evitando o bug
`psycopg2.errors.InFailedSqlTransaction` (transacao abortada em cascata).

### Ao adicionar uma nova coluna/tabela no models.py

```bash
flask --app wsgi db migrate -m "descreva a mudanca"
flask --app wsgi db upgrade
```

Revise o arquivo gerado em `migrations/versions/` antes de commitar.

### Sobre db.create_all()

O `create_app()` roda `db.create_all()` apenas em SQLite local (dev/test). Em
producao (PostgreSQL, quando `DATABASE_URL` comeca com `postgresql://`) isto
e desativado automaticamente - em PostgreSQL, qualquer `db.create_all()` que
tente criar tabela/coluna nova dentro de uma transacao DDL pode abortar a
transacao e quebrar queries seguintes (origem do bug InFailedSqlTransaction).
Em producao, apenas as migrations Alembic devem tocar o esquema.

Para forcar o caminho "migrations only" em dev (util para testar o caminho de
producao localmente):

```bash
TODASSTORE_SKIP_CREATE_ALL=1 python scripts/run_migrations.py
```

## 8. Próximos passos sugeridos (evolução para SaaS)

A arquitetura já separa bem models/routes/services/ai, o que facilita:
- Adicionar autenticação multi-usuária (várias lojas, cada uma com seus dados).
- Adicionar um plano pago com limites de geração de IA.
- Trocar/adicionar outros provedores de IA no `ai_service.py` sem alterar o resto do sistema.

## 9. Novidades nesta versão (melhorias de experiência e persistência)

- ✅ **Bug do checklist resolvido**: ao desmarcar um item, o selo "Story ✅ / Post ✅"
  agora volta a refletir a realidade (antes ficava preso em verde).
- ✅ **Botão "Salvar no Banco de Ideias"** em cada card do dia — em 1 clique você
  preserva um Story/Reels/Feed que gostou (marcado como origem `ia`).
- ✅ **Histórico de versões por dia**: cada "Gerar nova ideia" preserva a versão
  anterior. Você pode restaurar versões anteriores direto na tela do dia.
- ✅ **Promoção da semana agora é considerada ao regerar** um dia específico
  (antes era esquecida ao clicar em "Gerar nova ideia").
- ✅ **Prompts menos superficiais**: legenda entre 80–220 palavras + novo campo
  "Inspiração visual" (cena concreta a fotografar/gravar) + `max_tokens` 4000.
- ✅ **Onboarding pede diferenciais e dores do público** (opcionais), que é o
  que mais deixa o conteúdo da IA específico para a sua loja.
- ✅ **Migrations reais (Alembic)** substituem o patch manual antigo — sem mais
  "coluna nova some em produção".
