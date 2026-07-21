// Marca item do checklist como feito/não feito sem recarregar a página
async function alternarChecklist(itemId, elemento) {
  try {
    const resp = await fetch(`/planejamento/checklist/${itemId}/alternar`, { method: "POST" });
    const dados = await resp.json();
    if (dados.ok) {
      elemento.classList.toggle("concluido", dados.concluido);
      const circulo = elemento.querySelector(".check-circulo");
      circulo.innerHTML = dados.concluido ? '<i class="bi bi-check-lg"></i>' : "";
    }
  } catch (e) {
    console.error("Não foi possível atualizar o item agora.", e);
  }
}

// Registro do Service Worker (funcionalidade PWA / offline básico)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // silencioso: PWA é um extra, não deve travar o uso do sistema
    });
  });
}
