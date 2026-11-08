"""Modelos básicos do simulador de epidemias em redes."""

from .individuo import EstadoEpidemiologico, Individuo
from .aresta import Aresta
from .grafo import Grafo

__all__ = ["Aresta", "EstadoEpidemiologico", "Grafo", "Individuo"]
