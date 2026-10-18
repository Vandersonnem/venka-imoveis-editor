# Identidade visual do Venka Imóveis Editor

Os ícones de distribuição usam o símbolo real da Venka Imóveis, com as cores
originais. O nome público do produto é **Venka Imóveis Editor**. Os nomes técnicos
legados `concat_logo_*` e `concat.ico` continuam disponíveis para as referências
de empacotamento do Concat; seu conteúdo foi substituído pela marca Venka.

## Fontes e proveniência

| Arquivo preservado | Origem | SHA-256 |
| --- | --- | --- |
| `assets/venka/source/logoTopo.webp` | [Logo público do cabeçalho Venka](https://static.sitemidas.com.br/imobiliarias/2684/logoTopo.webp), referenciado no site `www.venkaimoveis.com.br` | `6f77fcf8ad7e992fdf5c09363fded70625963c02237020a738c1772c354c9d56` |
| `assets/venka/source/venka-logo-local-original.png` | Arquivo Venka local `C:\VENKA_DEV\mapa-condominios-venka-dev\app\static\venka-logo.png`, já usado pelo Portal Venka | `935dae8e0726ac9d4f2cdec844deb5be5881cb70d611a4092dcfba34ddd1999a` |

O logo público foi consultado novamente por HTTPS em **18/10/2026, 02:51 -03:00**,
com HTTP 200 e o mesmo SHA-256. A cópia de verificação está preservada em
`source/logoTopo-live-verification.webp`. O arquivo horizontal também corresponde
ao `outputs/Venka_Cinema_Studio/web/venka-logo.png` existente no projeto de origem.
Não foi extraída uma identidade diferente do Instagram: a fonte visual usada
aqui é a marca efetiva dos arquivos e do site da própria Venka.

## Paleta

| Uso | Cor | Evidência |
| --- | --- | --- |
| Fundo / superfícies do editor | `#101C2D` | Azul marinho complementar escolhido para o produto, conforme pedido; **não é uma cor extraída dos pixels do logo** |
| Cor primária / destaque | `#DCBC64` | Aproximação do dourado visível na versão vertical do logo |
| Dourado do site | `#DABB65` | Cor registrada no CSS público consultado em 17/10/2026 |
| Laranja da marca | `#E48C34` | Aproximação do laranja dominante na versão vertical do logo |
| Texto secundário | `#D6DAE0` | Cor editorial de apoio para contraste no fundo marinho |

Os arquivos originais possuem gradientes e diferenças entre versões. Esses
valores não substituem um manual oficial de marca. Os PNGs de logo e símbolo não
foram recoloridos para forçar correspondência com as cores planas da interface.

## Derivações técnicas

- `venka-logo-stacked.png`: conversão do logo público vertical, 260 × 264 px,
  preservando transparência, proporções e cores.
- `venka-logo-horizontal.png`: recorte técnico da região principal do PNG local,
  de `(81, 375)` a `(1962, 886)`, resultando em 1881 × 511 px. Remove as grandes
  margens transparentes; não redesenha letras nem símbolo.
- `venka-symbol.png`: símbolo V/casa e as quatro janelas isolados do original
  horizontal. A seleção conserva os pixels RGB do símbolo e descarta o texto
  adjacente e pontos isolados da tela transparente. Os parâmetros e componentes
  estão em `symbol-crop.json`.
- `venka-icon-{16,32,64,128,256,512,1024}.png`: símbolo sobre quadrado azul marinho,
  com margem para as máscaras dos sistemas. Não tenta colocar letras minúsculas
  ilegíveis no ícone de 16 px.
- `venka-splash-portrait.png` / `venka-splash-landscape.png`: prévias estáticas em
  1080 × 1920 e 1920 × 1080. A legenda usa Segoe UI no Windows; o logo permanece
  a imagem original.

Os quatro SVGs legados de logo e `assets/venka/venka-icon.svg` incorporam um PNG da
marca real em vez de redesenhar a marca por vetores. Os arquivos `.af` antigos e
as capturas `assets/editor*.png` continuam como material histórico do upstream;
não são ícones nem telas reais da edição Venka. Uma captura atual do aplicativo
deve ser feita somente após compilar e executar o editor.

## Ícones e inicialização por plataforma

| Plataforma | Recursos |
| --- | --- |
| Windows | `assets/icons/concat.ico` com 16, 32, 64, 128 e 256 px; PNGs legados substituídos |
| macOS / Linux | PNGs em `assets/icons/` de 16 até 512 px; fonte de 1024 px em `assets/venka/` |
| Android | `src/crates/concat-android/res/mipmap-*/ic_launcher.png`: 48, 72, 96, 144 e 192 px |
| Android 8–11 | `res/drawable/venka_splash.xml`, logo horizontal em `drawable-nodpi`, tema `VenkaTheme` |
| Android 12+ | `res/values-v31/styles.xml`, símbolo real centralizado e fundo marinho no splash nativo |
| iOS / iPadOS | `assets/venka/ios/Assets.xcassets/AppIcon.appiconset`: iPhone, iPad e marketing 1024 px; todos RGB sem transparência |
| iOS / iPadOS | `LaunchScreen.storyboard` com logo `VenkaLaunchLogo.png`, centrado no fundo marinho |

O manifesto Android deve usar `@style/VenkaTheme`. O bundler Apple deve compilar
`Assets.xcassets` com `xcrun actool`, compilar o storyboard com `xcrun ibtool` e
incluir o resultado no aplicativo. O storyboard usa imagem com 240 × 65 pt,
centralizada, que cabe no iPhone pequeno e em orientação paisagem.

## Reprodução e verificação

Na raiz do repositório, com Python e Pillow instalados:

```sh
python assets/venka/generate_assets.py
```

O script verifica a decodificação das imagens, dimensões e sintaxe XML dos
recursos, e grava SHA-256 em `asset-manifest.json`. O contato visual está em
`branding-preview.png`. Foram inspecionados os quatro logos de origem, os recortes,
o símbolo e a folha final de ícones/splash. A revisão confirmou símbolo íntegro,
sem uso da marca Concat como se fosse Venka, proporções corretas e margens.

A inspeção das imagens e o parse dos XMLs **não comprovam** compilação Android,
compilação do storyboard/asset catalog Apple nem comportamento em telefone real;
esses resultados pertencem à validação dos builds por plataforma.

O `LICENSE` original e a atribuição do Concat permanecem no projeto. A identidade
Venka identifica esta distribuição; sua presença não transfere a titularidade
da marca Venka para o projeto upstream.
