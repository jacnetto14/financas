# Painel — site estático (GitHub Pages)

Versão do painel que roda fora do Cowork, direto no navegador, lendo os dados
do Supabase pela API REST pública (chave anon, somente leitura — protegida
por Row Level Security).

## Ativar o GitHub Pages (uma vez só)

1. No repositório, vá em **Settings → Pages**.
2. Em "Build and deployment" → "Source", selecione **Deploy from a branch**.
3. Em "Branch", selecione **main** e a pasta **/docs**. Clique em **Save**.
4. Espere 1–2 minutos. O GitHub mostra o link do site no topo da página
   (algo como `https://jacnetto14.github.io/financas/`).

Esse link funciona de qualquer navegador, celular ou computador — não
precisa do Cowork aberto.

## Como atualiza

O conteúdo é o mesmo painel de sempre, só que buscando os dados direto do
Supabase via `fetch()` no navegador, em vez de passar pelo Cowork. Sempre
que os dados no banco mudarem (novo mês fechado, cotação do dia, etc.), a
próxima vez que a página for aberta ela já mostra os dados atualizados —
não precisa reconstruir nada.

Se eu (Claude) precisar mudar o layout ou adicionar uma aba nova, edito este
arquivo (`docs/index.html`) e você só precisa dar `git pull` (ou repetir o
processo de commit/push) para a mudança ir ao ar.
