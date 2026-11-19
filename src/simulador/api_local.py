from __future__ import annotations

import argparse
import base64
import binascii
from dataclasses import dataclass, field
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from secrets import token_urlsafe
from threading import RLock
from time import monotonic
from urllib.parse import parse_qs, urlsplit

from simulador.carga_rede import (
    ArquivoCSV, ErroCargaRede, ProblemaCargaRede, ServicoCargaRede,
)


from simulador.comparacao_api import (
    executar_comparacao_api,
    executar_simulacao_api,
    validar_comparacao,
)
from simulador.configuracao import ErroConfiguracao
from simulador.configuracao_api import validar_formulario


MAX_CORPO = 8 * 1024 * 1024
MAX_SESSOES = 16
VALIDADE_SESSAO = 4 * 60 * 60
COOKIE_SESSAO = "observatorio_sessao"
LIMITE_NOS_PREVIA = 180
LIMITE_CONTATOS_PREVIA = 1200
LOGGER = logging.getLogger(__name__)
ROTAS = {
    "/api/rede": "GET",
    "/api/rede/configuracao": "POST",
    "/api/rede/comparacao/validar": "POST",
    "/api/rede/comparacao/executar": "POST",
    "/api/rede/simulacao/executar": "POST",
    "/api/rede/gerar": "POST",
    "/api/rede/importar": "POST",
    "/api/rede/confirmar": "POST",
    "/api/rede/previa": "GET",
    "/api/rede/individuo": "GET",
    "/api/rede/individuos": "GET",
    "/api/rede/contatos": "GET",
}

ROTAS_COM_RETRATO = {"/api/rede", "/api/rede/gerar", "/api/rede/importar", "/api/rede/confirmar"}


def _erro(campo: str, mensagem: str) -> ErroCargaRede:
    return ErroCargaRede((ProblemaCargaRede(campo, mensagem),))


def _arquivo(valor: object, campo: str) -> ArquivoCSV:
    if not isinstance(valor, dict):
        raise _erro(campo, "Selecione um arquivo CSV.")
    try:
        conteudo = base64.b64decode(valor["conteudo_base64"], validate=True)
        return ArquivoCSV(valor["nome"], conteudo)
    except (KeyError, TypeError, ValueError, binascii.Error):
        raise _erro(campo, "O arquivo enviado é inválido. Selecione-o novamente.") from None


@dataclass
class SessaoCarga:

    servico: ServicoCargaRede = field(default_factory=ServicoCargaRede)
    lock: RLock = field(default_factory=RLock)
    ultimo_acesso: float = field(default_factory=monotonic)


def _previa(servico: ServicoCargaRede, revisao: int) -> dict[str, object]:

    pessoas = servico.listar_individuos(revisao, limite=LIMITE_NOS_PREVIA)
    ids = {pessoa["id"] for pessoa in pessoas["individuos"]}
    contatos: list[dict[str, object]] = []
    inicio = 0
    total = 0
    while True:
        pagina = servico.listar_contatos(revisao, inicio=inicio, limite=500)
        total = pagina["total"]
        for contato in pagina["contatos"]:
            if contato["origem"] in ids and contato["destino"] in ids:
                contatos.append(contato)
                if len(contatos) == LIMITE_CONTATOS_PREVIA:
                    break
        inicio += len(pagina["contatos"])
        if inicio >= total or len(contatos) == LIMITE_CONTATOS_PREVIA:
            break
    return {
        "revisao": revisao,
        "individuos": pessoas["individuos"],
        "contatos": contatos,
        "total_individuos": pessoas["total"],
        "total_contatos": total,
        "parcial": pessoas["total"] > len(ids) or total > len(contatos),
    }


def atender(
    servico: ServicoCargaRede, metodo: str, caminho: str,
    parametros: dict[str, list[str]], corpo: dict[str, object],
) -> dict[str, object]:
    if caminho not in ROTAS:
        raise _erro("rota", "Operação não encontrada.")
    if metodo != ROTAS[caminho]:
        raise _erro("metodo", f"Use o método {ROTAS[caminho]} para esta operação.")
    if caminho == "/api/rede/comparacao/validar":
        return validar_comparacao(servico, corpo)
    if caminho == "/api/rede/comparacao/executar":
        return executar_comparacao_api(servico, corpo)
    if caminho == "/api/rede/simulacao/executar":
        return executar_simulacao_api(servico, corpo)
    if caminho == "/api/rede/configuracao":
        return validar_formulario(servico, corpo)
    if metodo == "GET" and caminho == "/api/rede":
        return servico.inspecionar()
    if metodo == "POST" and caminho == "/api/rede/gerar":
        return servico.gerar(corpo)
    if metodo == "POST" and caminho == "/api/rede/importar":
        pessoas = corpo.get("arquivo_individuos")
        return servico.importar_csv(
            _arquivo(corpo.get("arquivo_contatos"), "arquivo_contatos"),
            arquivo_individuos=None if pessoas is None else _arquivo(pessoas, "arquivo_individuos"),
            delimitador=corpo.get("delimitador", ","),
        )
    if metodo == "POST" and caminho == "/api/rede/confirmar":
        return servico.confirmar(corpo.get("revisao"))
    try:
        revisao = int(parametros.get("revisao", [""])[0])
    except ValueError:
        raise _erro("revisao", "Informe a revisão da rede inspecionada.") from None
    if metodo == "GET" and caminho == "/api/rede/previa":
        return _previa(servico, revisao)
    if metodo == "GET" and caminho == "/api/rede/individuo":
        return servico.inspecionar_individuo(revisao, parametros.get("id", [""])[0])
    if metodo == "GET" and caminho in ("/api/rede/individuos", "/api/rede/contatos"):
        try:
            inicio = int(parametros.get("inicio", ["0"])[0])
            limite = int(parametros.get("limite", ["20"])[0])
        except ValueError:
            raise _erro("paginacao", "Use números inteiros para a paginação.") from None
        listar = servico.listar_individuos if caminho.endswith("/individuos") else servico.listar_contatos
        return listar(revisao, inicio=inicio, limite=limite)
    raise _erro("rota", "Operação não encontrada.")


class ServidorCarga(ThreadingHTTPServer):

    daemon_threads = True

    def __init__(self, porta: int = 8000) -> None:
        self.sessoes: dict[str, SessaoCarga] = {}
        self.lock_sessoes = RLock()
        super().__init__(("127.0.0.1", porta), ManipuladorCarga)

    def sessao(self, cookie: str) -> tuple[str, SessaoCarga]:
        biscoitos = SimpleCookie()
        try:
            biscoitos.load(cookie)
        except CookieError:
            pass
        identificador = biscoitos[COOKIE_SESSAO].value if COOKIE_SESSAO in biscoitos else ""
        with self.lock_sessoes:
            agora = monotonic()
            expirados = [chave for chave, sessao in self.sessoes.items()
                         if agora - sessao.ultimo_acesso > VALIDADE_SESSAO]
            for chave in expirados:
                del self.sessoes[chave]
            if identificador not in self.sessoes:
                if len(self.sessoes) >= MAX_SESSOES:
                    raise _erro("sessao", "O limite de sessões locais foi atingido. Reinicie a API.")
                identificador = token_urlsafe(32)
                self.sessoes[identificador] = SessaoCarga()
            sessao = self.sessoes[identificador]
            sessao.ultimo_acesso = agora
            return identificador, sessao


class ManipuladorCarga(BaseHTTPRequestHandler):

    server: ServidorCarga

    def _responder(self, status: int, dados: dict[str, object], sessao: str = "") -> None:
        conteudo = json.dumps(dados, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if status == 405:
            self.send_header("Allow", ROTAS[urlsplit(self.path).path])
        if sessao:
            self.send_header("Set-Cookie", f"{COOKIE_SESSAO}={sessao}; Path=/api; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(conteudo)

    def _processar(self) -> None:
        identificador = ""
        try:
            host = urlsplit("http://" + self.headers.get("Host", "")).hostname
            origem = self.headers.get("Origin")
            if host not in ("localhost", "127.0.0.1") or (
                origem and urlsplit(origem).hostname not in ("localhost", "127.0.0.1")
            ):
                self._responder(403, _erro("origem", "A API aceita somente acesso local.").para_dict())
                return
            corpo: dict[str, object] = {}
            if self.command == "POST":
                if self.headers.get_content_type() != "application/json":
                    self._responder(415, _erro("formulario", "Envie os dados como JSON.").para_dict())
                    return
                tamanho = int(self.headers.get("Content-Length", "0"))
                if not 0 < tamanho <= MAX_CORPO:
                    self._responder(413, _erro("arquivos", "O envio deve ter até 8 MiB, incluindo a codificação dos arquivos.").para_dict())
                    return
                corpo = json.loads(self.rfile.read(tamanho))
                if not isinstance(corpo, dict):
                    raise _erro("formulario", "Envie um objeto com os campos do formulário.")
            identificador, sessao = self.server.sessao(self.headers.get("Cookie", ""))
            url = urlsplit(self.path)
            with sessao.lock:
                resultado = atender(sessao.servico, self.command, url.path, parse_qs(url.query), corpo)
                if url.path in ROTAS_COM_RETRATO:
                    resultado["contexto_rede"] = sessao.servico.contexto_rede
            self._responder(200, resultado, identificador)
        except ErroConfiguracao as erro:
            self._responder(422, erro.para_dict(), identificador)
        except ErroCargaRede as erro:
            status_por_campo = {"revisao": 409, "rota": 404, "metodo": 405, "sessao": 503}
            status = next((status_por_campo[p.campo] for p in erro.problemas
                           if p.campo in status_por_campo), 422)
            self._responder(status, erro.para_dict(), identificador)
        except (ValueError, UnicodeDecodeError):
            self._responder(400, _erro("formulario", "Não foi possível ler a solicitação JSON.").para_dict(), identificador)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            LOGGER.exception("Falha no adaptador de carga")
            self._responder(500, _erro("servidor", "Não foi possível concluir a operação. Tente novamente.").para_dict(), identificador)

    def do_GET(self) -> None:
        self._processar()

    def do_POST(self) -> None:
        self._processar()


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa a API local do Simulador de Epidemias em Redes.")
    parser.add_argument("--porta", type=int, default=8000)
    argumentos = parser.parse_args()
    with ServidorCarga(argumentos.porta) as servidor:
        print(f"API de carga: http://127.0.0.1:{servidor.server_port}/api/rede", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
