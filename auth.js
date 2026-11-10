/*
 * Sessão das telas internas (scanner, gestor, admin, colab).
 *
 * O login devolve um "token" que fica salvo junto com os dados do usuário
 * (bb_garcom, bb_gestor, bb_admin ou bb_colab). Este arquivo coloca esse
 * token em todo pedido feito ao servidor. Se o servidor responder que a
 * sessão não vale mais, limpa o login e volta para a tela de entrar.
 *
 * Uso: <script src="auth.js" data-chaves="bb_gestor,bb_admin"></script>
 * antes do script principal da página. As chaves são lidas na ordem.
 */
(function () {
  var tag = document.currentScript;
  var chaves = ((tag && tag.dataset.chaves) || "bb_garcom,bb_gestor,bb_admin,bb_colab").split(",");

  function token() {
    for (var i = 0; i < chaves.length; i++) {
      try {
        var d = JSON.parse(localStorage.getItem(chaves[i]) || "null");
        if (d && d.token) return d.token;
      } catch (e) {}
    }
    return null;
  }

  function ehServidor(url) {
    return /^https?:\/\//.test(url) && url.indexOf(location.host) === -1;
  }

  var original = window.fetch.bind(window);
  window.fetch = function (url, opcoes) {
    var endereco = typeof url === "string" ? url : (url && url.url) || "";
    if (!ehServidor(endereco)) return original(url, opcoes);

    opcoes = opcoes || {};
    var t = token();
    if (t) {
      var cab = new Headers(opcoes.headers || {});
      cab.set("Authorization", "Bearer " + t);
      opcoes.headers = cab;
    }
    return original(url, opcoes).then(function (r) {
      var ehLogin = /\/login(-[a-z]+)?$/.test(endereco);
      if (r.status === 401 && !ehLogin) {
        chaves.forEach(function (k) { try { localStorage.removeItem(k); } catch (e) {} });
        location.href = "login.html";
      }
      return r;
    });
  };
})();
