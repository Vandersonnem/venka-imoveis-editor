# Compilar e distribuir o Venka Imóveis Editor

Fork: <https://github.com/Vandersonnem/venka-imoveis-editor>.
Base: [Concat de jub0t](https://github.com/jub0t/Concat), AGPL-3.0-or-later.
O arquivo LICENSE e os avisos originais de Jareer/jub0t e contribuidores são preservados.
Os nomes internos dos crates, bibliotecas e helpers `concat` permanecem para compatibilidade; os nomes apresentados ao usuário e identificadores do aplicativo são Venka.

## O que compila em cada máquina

| Saída | Máquina de build | Identidade | Verificação no workflow |
| --- | --- | --- | --- |
| `venka-editor-windows.exe` | Windows x64, MSVC + SDK + Rust + CMake/LLVM | Venka Imóveis Editor / AppId `com.venkaimoveis.editor` | Dependências DLL, `--version`, `--smoke`, baseline x86 |
| `venka-editor-macos.dmg` | macOS Apple silicon, Xcode/SDK + Homebrew | Bundle ID `com.venkaimoveis.editor` | Assinatura, dylibs, `--version`, `--smoke` |
| `venka-editor-macos-intel.dmg` (opcional) | macOS Intel | Mesmo bundle ID | Mesmas verificações, binário Intel |
| `venka-editor-android.apk` | Linux + Android SDK/NDK + Java + cargo-apk | Package `com.venkaimoveis.editor`, arm64-v8a | Build arm64; mesma fonte x86_64 inicia em emuladores API 30 e 35 |
| `venka-editor-ios.ipa` | macOS + Xcode, SDK iPhoneOS | Bundle ID `com.venkaimoveis.editor`, arm64 | Device build empacotado; mesma fonte inicia no iOS Simulator |

O Windows sozinho não contém o SDK nem o codesign da Apple e não substitui um runner macOS. Um smoke no simulador confirma a inicialização da compilação de simulador; não prova desempenho ou exportação no iPhone físico. Teste final de importação, edição 9:16 e exportação deve ocorrer em Android e iPhone reais antes de anunciar desempenho garantido.

## Workflow único

O upstream atual usa `.github/workflows/build-app.yml` e `mobile.yml`; não tinha `build.yml`. O novo `.github/workflows/build.yml` reúne os dois e só prepara os nomes finais depois que ambos, inclusive seus smokes, terminam com sucesso. O modo Venka compila Windows x64 e macOS Apple silicon; os ramos opcionais Linux e Intel permanecem no código, mas não são disparados para esta entrega. O job final:

1. exige builds reais para as quatro saídas obrigatórias e inclui Intel apenas se houver esse build;
2. confere PE, UDIF/DMG, CRC do APK/IPA e identidade do IPA;
3. preserva os builds com arquitetura/versão e cria os nomes estáveis da página;
4. inclui `venka-editor-codigo-fonte.zip`, `VENKA_RELEASE.json` e `SHA256SUMS`.

Esse workflow cria artefatos de Actions e não publica release. No GitHub, abra **Actions → Venka Imóveis Editor - build completo → Run workflow**. Com GitHub CLI autenticado, a partir do fork já enviado:

```powershell
gh workflow run build.yml --repo Vandersonnem/venka-imoveis-editor --ref main
gh run list --repo Vandersonnem/venka-imoveis-editor --workflow build.yml
gh run watch NUMERO_DO_RUN --repo Vandersonnem/venka-imoveis-editor
gh run download NUMERO_DO_RUN --repo Vandersonnem/venka-imoveis-editor --name venka-editor-instaladores-e-fontes --dir dist
```

Use o número retornado pelo comando anterior. Não baixe um run antigo para publicar como se fosse a versão nova.

## QA de edição e exportação 9:16

Além dos smokes de inicialização, os dois jobs desktop compilam `concat-cli` no mesmo target e perfil `app` do editor. `scripts/venka/test_reel_export.py` usa o contrato JSON-RPC nativo do código Rust: abre a fixture sintética em `examples/venka-reel-9x16`, altera um título por `edit.apply`, corta o vídeo-base em duas partes, confere o documento alterado, salva e chama `export.run`. O teste só avança após o evento real `export.done` do job solicitado; `export.failed`, timeout, processo encerrado ou resposta de erro falham o job.

O arquivo exportado deve conter H.264 e AAC, 1080×1920, 30 fps e cerca de quatro segundos. FFmpeg decodifica o arquivo inteiro, e dois frames PNG ficam disponíveis para revisão visual. O artifact `qa-native-reel-<plataforma>-<arquitetura>` guarda o vídeo, os frames, FFprobe, trocas RPC, erros nativos, documento editado e `QA_REEL_RESULT.json`; não inclui as DLLs copiadas para o runtime de teste. No Windows, a CLI usa as bibliotecas do mesmo estágio desktop já verificado. No Mac, usa a compilação nativa e as dependências do runner.

Uma execução bem-sucedida prova essa edição/exportação no engine nativo da plataforma testada. Não prova gestos da interface, velocidade em aparelho físico, iPhone/Android nem compatibilidade com qualquer arquivo de câmera. A interface e os dispositivos precisam de revisão própria.

## Windows local

Instale Visual Studio Build Tools com MSVC x64/x86 e Windows SDK, CMake e Rust. Abra Developer PowerShell. O script abaixo lê os hashes fixos de `scripts/ci/deps.lock`; reutiliza downloads corretos e não aceita hash divergente:

```powershell
. ./scripts/venka/Setup-WindowsDeps.ps1 -Depot ../work/concat/build-deps
cd src
cargo build --locked --profile app -p concat --target x86_64-pc-windows-msvc
```

O resultado inicial `concat.exe` é o binário interno, não o instalador pedido. O workflow desktop copia FFmpeg, ONNX Runtime, sherpa e bibliotecas whisper/ggml para o pacote, roda o smoke, e gera o instalador Inno Setup e MSI. Não distribua apenas esse EXE isolado. A identidade PE, o ícone e o nome no menu são Venka. A assinatura Authenticode é opcional e depende de um certificado legítimo configurado; nenhuma assinatura é simulada.

Depois de empacotar, `concat.exe --version` (ou `concat --version` em macOS/Linux) deve responder `Venka Imóveis Editor 0.2.7`, com a versão real do workspace. Os smokes exigem esse prefixo e os metadados de marca; sair com status zero sozinho não basta.

## Android local

O caminho mais fiel ao CI é Linux/Ubuntu. Tenha Android SDK, platform API 35, build-tools, NDK, Java, Rust e cargo-apk. Aceite as licenças do SDK diretamente com o fornecedor. Exporte os caminhos reais `ANDROID_HOME` e `ANDROID_NDK_HOME`.

```bash
rustup target add aarch64-linux-android
cargo install cargo-apk --locked
src/scripts/ffmpeg-mobile.sh aarch64-linux-android
src/scripts/sherpa-mobile.sh aarch64-linux-android
cd src
eval "$(scripts/mobile-env.sh aarch64-linux-android)"
cargo apk build --release -p concat-android --target aarch64-linux-android
```

O APK interno é `src/target/release/apk/VenkaEditor.apk`. O workflow gera uma chave transitória para builds de teste. Para atualizações instaláveis sobre versões anteriores, mantenha uma chave de release própria e estável; nunca comite a chave ou senha. O fluxo existente aceita os secrets `ANDROID_KEYSTORE`, `ANDROID_KEYSTORE_PASSWORD`, e opcionais `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` somente na etapa de assinatura de release. Sem essa configuração, o build continua sendo de teste e não garante atualização sobre uma versão anterior.

## iOS/iPadOS e macOS

Use um Mac com Xcode, SDKs instalados e Rust no alvo adequado. O workflow `mobile.yml` é a referência completa: compila FFmpeg para iOS, obtém sherpa, compila Rust e chama `src/scripts/ios-app.sh`. O bundler gera os ícones Venka com `actool`, compila a tela inicial com `ibtool`, mantém permissões legíveis, inclui os avisos e aplica assinatura ad-hoc. O IPA não é uma publicação na App Store e ainda precisa ser re-assinado com a identidade do usuário para instalação em aparelho.

Para sideload, siga [AltStore Classic](https://faq.altstore.io/altstore-classic) ou [Sideloadly](https://sideloadly.io/) em suas fontes oficiais. Instale a ferramenta no computador, conecte e confie no iPhone, importe `venka-editor-ios.ipa`, forneça as credenciais diretamente à ferramenta e siga as instruções de assinatura/confiabilidade/modo de desenvolvedor. Validade e renovação variam conforme a conta e o método; não envie senhas para a Venka ou para o agente.

macOS sem secrets recebe assinatura ad-hoc, não notarização. Uma distribuição notarizada usa os secrets Apple documentados em `build-app.yml`. Nenhuma credencial Apple é necessária para preparar o código e compilar um IPA ad-hoc no runner.

## GitHub Releases e página de download

Antes de distribuir os binários, o commit correspondente precisa estar no fork e o código fonte completo da mesma versão deve acompanhar o release. A página deve apontar para esse fork e para arquivos que realmente estejam no release publicado.

Para criar um **rascunho** após baixar e conferir o artifact:

```powershell
gh release create v0.2.7-venka.1 --repo Vandersonnem/venka-imoveis-editor --target COMMIT_COMPILADO --draft --prerelease --title "Venka Imóveis Editor 0.2.7 - Venka 1" --notes-file RELEASE_NOTES_VENKA.md
gh release upload v0.2.7-venka.1 ./dist/venka-editor-windows.exe ./dist/venka-editor-macos.dmg ./dist/venka-editor-android.apk ./dist/venka-editor-ios.ipa ./dist/venka-editor-codigo-fonte.zip ./dist/VENKA_RELEASE.json ./dist/SHA256SUMS --repo Vandersonnem/venka-imoveis-editor
```

Crie o tag no commit efetivamente compilado; não deixe o GitHub escolher um HEAD que já mudou. Como alternativa, o workflow `release.yml` roda testes/builds e cria um rascunho quando recebe um tag `v<versão>` ou seu sufixo de pré-release. Revise o código fonte, checksums, instruções e funcionamento antes de publicar o rascunho. No release público, os botões podem usar `/releases/latest/download/venka-editor-android.apk` e equivalentes. Esse endereço ignora pré-releases; durante o beta use `/releases/download/TAG/ARQUIVO` explícito na configuração da página.

Se os quatro jobs nativos concluíram e apenas a coleta final falhou, não é necessário recompilar para corrigir um aviso de distribuição. Baixe os artifacts dos mesmos jobs e use o coletor corrigido com `--archive-source --archive-ref SHA_REAL_DO_RUN`. O arquivo Cargo e o ZIP de fontes vêm desse commit, e `VENKA_RELEASE.json` registra esse SHA como `commit`; `collector_commit` identifica a revisão da ferramenta coletora separadamente. Um aviso adicional pode ser passado com `--distribution-notice NOTICE_VENKA.md`: ele fica em `DISTRIBUTION_NOTICES/`, fora da árvore compilada `venka-imoveis-editor/`, com hash e escopo explícitos. O coletor não altera nem re-assina os binários recebidos.

O workflow manual `collect-existing.yml` automatiza essa recuperação depois que o run original termina. Ele valida o SHA, os seis jobs nativos obrigatórios, seus passos de smoke/QA, quaisquer smokes adicionais existentes e a disponibilidade dos quatro artifacts; a falha do antigo job de coleta é permitida. Baixa os artifacts pelo run ID original e produz um novo `venka-editor-instaladores-e-fontes`, sem executar compiladores. `ORIGINAL_RUN_VALIDATION.json` e o campo `build_run` do manifesto preservam a ligação com a execução compilada.

```powershell
gh workflow run collect-existing.yml --repo Vandersonnem/venka-imoveis-editor -f run_id=NUMERO_DO_RUN_ORIGINAL_TERMINADO
```

Fontes primárias: [workflow upstream de mobile](https://github.com/jub0t/Concat/blob/main/.github/workflows/mobile.yml), [GitHub: gerenciar releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository), [AltStore no Windows](https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows).
