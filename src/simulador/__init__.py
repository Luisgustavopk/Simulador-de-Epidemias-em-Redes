"""Modelos básicos do simulador de epidemias em redes."""

from simulador.contato import Contato
from simulador.individuo import EstadoSIR, Individuo
from simulador.rede_contatos import RedeContatos

__all__ = [
    "Contato",
    "EstadoSIR",
    "Individuo",
    "RedeContatos",
]
