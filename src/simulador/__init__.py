"""Modelos básicos do simulador de epidemias em redes."""

from .individuo import EstadoSIR, Individuo
from .aresta import Aresta
from .grafo import Grafo

Contato = Aresta
RedeContatos = Grafo
EstadoEpidemiologico = EstadoSIR

__all__ = [
    "Aresta", "Contato", "EstadoEpidemiologico", "EstadoSIR",
    "Grafo", "Individuo", "RedeContatos",
]
