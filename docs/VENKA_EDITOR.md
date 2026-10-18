# Venka Imóveis Editor

Edição da Venka Imóveis para vídeos de imóveis e Reels na Zona Sul do Rio de Janeiro, baseada no Concat de Jareer (@jub0t).

Código correspondente: <https://github.com/Vandersonnem/venka-imoveis-editor>.

## Identidade e uso

- Nome exibido: **Venka Imóveis Editor**.
- Identificador: `com.venkaimoveis.editor`. Configurações e cache são separados do aplicativo original.
- A abertura de um projeto novo usa **1080 × 1920, 9:16, 30 fps**. As demais proporções e taxas continuam selecionáveis.
- A interface começa em português brasileiro e permite trocar de idioma nas configurações.
- Dourado `#DCBC64` extraído da logo, com marinho editorial `#101C2D`. A proveniência dos arquivos está em [branding-venka.md](branding-venka.md).
- Nenhuma marca d'água é acrescentada automaticamente ao vídeo exportado.
- A voz, as legendas e os demais recursos de IA do editor usam os motores do código original e modelos opcionais. Esta versão não apresenta o atendimento VoiceStudio como integrado ou concluído.

## Instalar e distribuir

[BUILD_VENKA.md](BUILD_VENKA.md) explica as ferramentas nativas, os testes e a criação dos instaladores no GitHub Actions. O workflow manual `build.yml` reúne os quatro artefatos solicitados e o código-fonte; só aceita arquivos reais produzidos pelos compiladores de cada plataforma.

`site-download/index.html` é uma página independente, pronta para hospedagem estática. Leia `site-download/PUBLICAR.md` antes de ativar os downloads. Ela conserva os botões indisponíveis enquanto não houver artefatos publicados e verificados. O aplicativo e a página não devem anunciar um build como disponível apenas porque seu código compila em outra plataforma.

## Créditos e licença

Venka Imóveis Editor - Powered by Concat (AGPL-3.0).

Copyright 2026 Jareer (@jub0t) and Concat contributors. O arquivo [LICENSE](../LICENSE), os cabeçalhos de copyright e [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) originais foram preservados. O código do projeto usa **AGPL-3.0-or-later**. Os termos de bibliotecas e recursos de terceiros continuam aplicáveis.

A distribuição deve oferecer o código-fonte correspondente aos binários, incluindo as alterações Venka e os scripts de compilação. O workflow prepara um arquivo de fontes junto aos instaladores. Guarde a referência exata do commit/tag de cada entrega.

Este fork tem marca e identificador próprios; não é uma distribuição oficial do Concat nem afirma endosso do autor original.
