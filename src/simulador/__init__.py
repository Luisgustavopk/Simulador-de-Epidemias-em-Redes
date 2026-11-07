"""Modelos básicos do simulador de epidemias em redes."""

from .individuo import EstadoEpidemiologico, Individuo
from .aresta import Aresta

__all__ = ["Aresta", "EstadoEpidemiologico", "Individuo"]
