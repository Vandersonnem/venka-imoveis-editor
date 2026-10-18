# Página de download — Venka Imóveis Editor

Página estática, sem dependências, CDN, analytics, formulário ou envio de vídeos. Ainda não foi publicada no site da Venka. O fork real é `https://github.com/Vandersonnem/venka-imoveis-editor`; a configuração mantém `sourceVerified: false` até conferir que esse fork recebeu o código Venka modificado correspondente. Os instaladores começam desabilitados porque esta pasta não comprova a existência de builds.

## Arquivos para o site

Copie **todo o conteúdo de `site-download/`** para uma pasta como `/editor/` na hospedagem. Preserve os nomes e os caminhos relativos de `assets/`, `style.css`, `app.js`, `release-config.js`, `LICENSE.txt` e `THIRD_PARTY_NOTICES.md`. Não basta colar somente o HTML em um editor que remova scripts, CSS ou SVG: nesse caso, publique a pasta como página estática ou adapte esses arquivos no tema do seu site.

Para conferir localmente, na raiz do repositório execute `python -m http.server 8842 --bind 127.0.0.1 --directory site-download` e abra `http://127.0.0.1:8842`. A página também abre diretamente como arquivo; o servidor facilita a revisão dos caminhos.

## Habilitar uma versão real

1. Crie o seu fork público e envie **o código modificado completo** que gerou os binários. Preserve a licença AGPL original e todos os avisos de copyright e licenças de terceiros.
2. Fixe uma tag/commit para a versão. Publique os instaladores reais no GitHub Releases do seu fork e teste cada instalação e exportação na plataforma correspondente. Não use os binários do Concat original como se fossem a versão Venka.
3. Calcule SHA-256 dos arquivos finais. No PowerShell, use `Get-FileHash -Algorithm SHA256 -LiteralPath '<arquivo-real>'`.
4. Edite `release-config.js`. Preencha `sourceUrl` com a URL pública real do código correspondente à versão, por exemplo a página da **tag real** ou um arquivo de código fonte completo publicado. Abra a URL para conferir o conteúdo e então marque `sourceVerified: true`.
5. Em cada plataforma disponível, preencha sua URL HTTPS real, `architecture`, `size`, `requirements` e o SHA-256 de 64 caracteres. Só então marque `verified: true`. Plataformas ainda não geradas permanecem com `verified: false` e `url: ""`.
6. Publique a pasta atualizada e confira, no celular e no computador, que cada botão baixa o arquivo certo e que o link de código fonte entrega a versão correspondente. Faça essa conferência novamente a cada release.

O script da página só habilita um botão quando fonte e plataforma estiverem marcadas como verificadas, a URL tiver a extensão esperada e houver um SHA-256 válido. Essa é uma proteção de apresentação; **não substitui a verificação humana dos binários e da licença**. A página não faz chamadas automáticas ao GitHub nem testa remotamente a existência das URLs.

Nomes esperados dos instaladores: `venka-editor-windows.exe`, `venka-editor-macos.dmg`, `venka-editor-android.apk`, `venka-editor-ios.ipa`. Os arquivos podem ficar no GitHub Releases: não precisam ser copiados para a hospedagem do site.

## Identidade visual e origem dos arquivos

- `assets/venka-logo.png`: cópia de `assets/venka/venka-logo-horizontal.png` do repositório. Logo horizontal já existente no projeto Venka, com recorte técnico da área útil. O original foi localizado em `C:\VENKA_DEV\mapa-condominios-venka-dev\app\static\venka-logo.png`.
- `assets/venka-symbol.png`: logo vertical oficial servida pelo site Venka em `https://static.sitemidas.com.br/imobiliarias/2684/logoTopo.webp`, convertida sem redesenho para PNG. Inclui o símbolo e o nome originais.
- Dourado aproximado `#DCBC64` da marca usado como acento, `#DABB65` também observado no site oficial e laranja aproximado `#E48C34` presente na marca. Azul-marinho `#101C2D` é um **complemento editorial solicitado**, não uma cor extraída da logo. A marca não foi recolorida. Consulte a auditoria `docs/branding-venka.md` do repositório.
- O desenho da sala é uma ilustração SVG declarada como tal. Não é imóvel anunciado, captura da versão Venka, demonstração de performance ou resultado de exportação do aplicativo.
- `LICENSE.txt` é cópia integral do `LICENSE` original do repositório; `THIRD_PARTY_NOTICES.md` mantém os avisos fornecidos pelo projeto base. Ao atualizar o projeto, atualize a cópia dos avisos caso necessário.

## Instalação iOS: fontes verificadas

As instruções resumidas são baseadas em documentação oficial consultada em 18/10/2026. As exigências podem mudar; os links da página levam aos guias atuais.

- AltStore Classic para Windows: https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows
- AltStore Classic para macOS: https://faq.altstore.io/altstore-classic/how-to-install-altstore-macos
- Sideloadly, instalação e validade da assinatura: https://sideloadly.io/

Não é uma publicação na App Store. AltStore Classic ou Sideloadly assinam o IPA com a conta Apple do próprio usuário. Não insira credenciais Apple no site Venka e não inclua chaves de assinatura, senhas, certificados ou tokens em `release-config.js`. A página não pede nem recebe credenciais.

Não foram testados aqui a instalação, a reprodução ou a exportação em iPhone/iPad. A página mantém essa limitação explícita até que a validação do app em aparelhos reais seja concluída.
