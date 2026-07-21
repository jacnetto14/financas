# Automação de cotações diárias

Busca o fechamento diário de todos os tickers em `tickers.txt` via brapi.dev
e acrescenta no arquivo `data/precos_historico.csv`. Roda sozinho todo dia
útil às 18h30 (Brasília) via GitHub Actions — não precisa de nada rodando
no seu computador.

## Configuração (uma vez só)

1. Suba esta pasta para o repositório `jacnetto14/financas` no GitHub.
2. No repositório, vá em **Settings > Secrets and variables > Actions**.
3. Clique em **New repository secret** e crie dois secrets:
   - `BRAPI_TOKEN`: seu token do brapi.dev.
   - `SUPABASE_SERVICE_KEY`: a chave **service_role** do projeto Supabase
     (Supabase > Project Settings > API > "service_role" — clique em "Reveal"
     e copie). NUNCA coloque nenhuma dessas chaves direto num arquivo do
     repositório, mesmo que privado — só como secret.
4. No painel do Supabase, vá em **Project Settings > Data API** e confirme
   que o schema `eqi_financas` está na lista de "Exposed schemas" (schemas
   expostos pela API). Se não estiver, adicione e salve — sem isso a
   sincronização com o Supabase falha mesmo com a chave certa.
5. Vá em **Settings > Actions > General** e confirme que "Allow all actions"
   está habilitado.
6. Vá na aba **Actions** do repositório e rode o workflow "Cotações diárias"
   manualmente uma vez (botão "Run workflow") para testar.

Depois disso ele roda sozinho todo dia de mercado, sem precisar tocar em nada.
Além do CSV, cada execução agora também grava as cotações na tabela
`eqi_financas.precos_diarios` do Supabase, que alimenta a view
`eqi_financas.posicao_mercado` (posição marcada a mercado, atualizada
automaticamente todo dia).

## Adicionando um ativo novo

Edite `tickers.txt` e adicione o código do ticker numa linha nova (uma seção
por tipo, mas isso é só organização — o script lê tudo igual). Na próxima
execução ele já entra na coleta.

## Arquivo de saída

`data/precos_historico.csv` cresce uma linha por ativo por dia:

| data       | ticker  | preco_fechamento | capturado_em_utc         |
|------------|---------|-------------------|---------------------------|
| 2026-07-18 | KNIP11  | 98.45              | 2026-07-18T21:31:02+00:00 |

Esse CSV é lido diretamente (via link "raw" do GitHub) para calcular o
patrimônio marcado a mercado no painel.
