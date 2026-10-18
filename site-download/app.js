"use strict";
(() => {
  const config = window.VENKA_EDITOR_RELEASE || {};
  const extensions = {windows: ".exe", macos: ".dmg", android: ".apk", ios: ".ipa"};
  const safeUrl = value => {
    if (typeof value !== "string" || !value.trim()) return null;
    try {
      const url = new URL(value, document.baseURI);
      if (url.username || url.password || url.hash) return null;
      if (url.protocol !== "https:" && url.origin !== window.location.origin) return null;
      if (!["https:", "http:", "file:"].includes(url.protocol)) return null;
      return url;
    } catch { return null; }
  };
  const sourceUrl = safeUrl(config.sourceUrl);
  const sourceReady = config.sourceVerified === true && sourceUrl !== null;
  if (sourceReady) {
    const link = document.getElementById("source-link");
    link.href = sourceUrl.href;
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
    link.rel = "noopener noreferrer";
    document.getElementById("source-state").textContent = "Consulte o código fonte correspondente desta versão, suas modificações e os avisos de licença. Concat © jub0t e colaboradores; adaptação visual para Venka Imóveis.";
  }
  let available = 0;
  for (const [platform, extension] of Object.entries(extensions)) {
    const release = config.platforms?.[platform] || {};
    const url = safeUrl(release.url);
    const checksumReady = typeof release.sha256 === "string" && /^[a-f0-9]{64}$/i.test(release.sha256);
    const isReady = sourceReady && release.verified === true && url && url.pathname.toLowerCase().endsWith(extension) && checksumReady;
    if (!isReady) continue;
    available++;
    const link = document.getElementById(`download-${platform}`);
    link.href = url.href;
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
    link.setAttribute("download", `venka-editor-${platform}${extension}`);
    link.rel = "noopener noreferrer";
    document.getElementById(`state-${platform}`).textContent = config.version ? `Versão ${config.version}` : "Versão publicada";
    const meta = document.getElementById(`meta-${platform}`);
    meta.replaceChildren();
    const info = [release.architecture, release.size, release.requirements].filter(value => typeof value === "string" && value.trim());
    const infoText = document.createElement("span");
    infoText.textContent = info.join(" · ") || "Instalador verificado";
    meta.append(infoText);
    const checksum = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Conferir SHA-256";
    const code = document.createElement("code");
    code.textContent = release.sha256.toLowerCase();
    checksum.append(summary, code);
    meta.append(checksum);
    if (platform === "ios") {
      const help = document.createElement("a");
      help.href = "#iphone";
      help.textContent = "Instruções de sideload";
      meta.append(help);
    }
  }
  if (available) document.getElementById("release-notice").textContent = "Baixe uma das versões publicadas abaixo. Cada instalador disponível inclui seu código fonte correspondente e uma soma SHA-256 para conferência. As demais plataformas seguem aguardando publicação.";
  document.querySelectorAll('[aria-disabled="true"]').forEach(link => {
    link.addEventListener("click", event => event.preventDefault());
  });
})();
