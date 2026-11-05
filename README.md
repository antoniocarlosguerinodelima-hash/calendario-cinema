# Calendário de estreias — São Paulo

Calendário compartilhável por assinatura para acompanhar estreias brasileiras de 05/11/2026 a 31/12/2028, com foco em **UCI Anália Franco** e **Cinemark Mooca Plaza Shopping**.

## Link de assinatura Apple Calendar

https://antoniocarlosguerinodelima-hash.github.io/calendario-cinema/Cinema_Estreias_UCI_Cinemark_Identificados.ics

**No iPhone:** Calendário → Calendários → Adicionar Calendário → Adicionar Assinatura de Calendário. Cole o link acima. Não use "Adicionar Tudo" no arquivo baixado: isso importa uma cópia estática.

## Atualização

O workflow `.github/workflows/atualizar-cinema.yml` está agendado diariamente para 11:17 UTC (08:17 em São Paulo), sujeito a atrasos do GitHub. Também pode ser executado em **Actions → Atualizar calendário de cinema → Run workflow**.

O programa `atualizar.py`:
- consulta a lista **Em breve** da UCI e os títulos **Coming Soon** da Cinemark;
- atualiza datas publicadas pela UCI, reconhece títulos da Cinemark com data já conhecida e inclui novos filmes datados encontrados na UCI;
- mantém a lista inicial quando uma fonte estiver indisponível, evitando apagar eventos;
- preserva identificadores dos eventos para reduzir duplicações;
- gera avisos `VALARM` de 7 dias antes (a exibição da notificação depende do aplicativo Apple Calendar).

## Limitações importantes

- **Não é garantia de 100% de todos os filmes até 2028.** As redes e distribuidoras ainda não anunciaram toda a programação.
- Um filme anunciado pela UCI ou Cinemark **não significa** sessão confirmada no Anália Franco ou no Mooca Plaza.
- Os títulos presentes no arquivo inicial são **previsões sujeitas à verificação**; alguns podem sofrer alteração de nome ou de data.
- O coletor da Cinemark não cria automaticamente filmes sem data brasileira conhecida. Para cobertura mais abrangente será necessário integrar outras fontes confiáveis de calendários de distribuidoras.
- A atualização programada é feita pelo GitHub Actions; a tarefa de monitoramento do ChatGPT é um aviso independente, não publica este arquivo.

