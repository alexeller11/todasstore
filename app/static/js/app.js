// Token CSRF disponível globalmente para qualquer chamada fetch (AJAX) do app
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || "";

// Marca item do checklist como feito/não feito sem recarregar a página
async function alternarChecklist(itemId, elemento) {
  try {
    const resp = await fetch(`/planejamento/checklist/${itemId}/alternar`, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF_TOKEN },
    });
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

// Pequeno aviso flutuante de confirmação (usado ao copiar texto, por ex.)
function mostrarToast(mensagem) {
  const toast = document.createElement("div");
  toast.textContent = mensagem;
  toast.style.cssText = `
    position: fixed; left: 50%; bottom: 100px; transform: translateX(-50%);
    background: var(--ameixa); color: white; padding: 10px 20px; border-radius: 20px;
    font-family: 'Quicksand', sans-serif; font-weight: 700; font-size: .85rem;
    box-shadow: var(--sombra-forte); z-index: 2000; opacity: 0; transition: opacity .25s ease;
  `;
  document.body.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = "1"; });
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 1800);
}

// Copia um texto (legenda, ideia, etc.) para a área de transferência com 1 toque
async function copiarTexto(texto, botao) {
  if (!texto || !texto.trim()) {
    mostrarToast("Nada para copiar ainda");
    return;
  }
  try {
    await navigator.clipboard.writeText(texto);
  } catch (e) {
    const area = document.createElement("textarea");
    area.value = texto;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
  mostrarToast("Copiado! 📋");
  if (botao) {
    const original = botao.innerHTML;
    botao.innerHTML = '<i class="bi bi-check-lg"></i>';
    setTimeout(() => { botao.innerHTML = original; }, 1200);
  }
}

// Abre o WhatsApp com uma mensagem pronta (usado para compartilhar planejamento)
function compartilharWhatsapp(texto) {
  const url = `https://wa.me/?text=${encodeURIComponent(texto)}`;
  window.open(url, "_blank", "noopener");
}

// Dá feedback visual (spinner + texto) em qualquer formulário que chama a IA,
// pra lojista saber que o pedido foi enviado e não clicar de novo enquanto
// espera (a Groq pode levar alguns segundos pra responder). Basta marcar o
// <form> com class="form-ia"; o texto do botão durante o carregamento pode
// ser customizado com data-loading-text="Gerando ideia..." no botão.
document.addEventListener("submit", (evento) => {
  const form = evento.target;
  if (!form.classList || !form.classList.contains("form-ia")) return;

  const botao = form.querySelector('button[type="submit"], button:not([type])');
  if (!botao || botao.disabled) return;

  const textoCarregando = botao.dataset.loadingText || "Gerando com a IA...";
  botao.dataset.textoOriginal = botao.innerHTML;
  botao.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${textoCarregando}`;
  botao.disabled = true;
  botao.setAttribute("aria-busy", "true");
  // trava visual: se por algum motivo a navegação não acontecer (ex: erro de
  // rede), destrava depois de 25s pra não deixar o botão preso pra sempre
  setTimeout(() => {
    if (botao.dataset.textoOriginal) {
      botao.innerHTML = botao.dataset.textoOriginal;
      botao.disabled = false;
    }
  }, 25000);
});

// Registro do Service Worker (funcionalidade PWA / offline básico)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // silencioso: PWA é um extra, não deve travar o uso do sistema
    });
  });
}
