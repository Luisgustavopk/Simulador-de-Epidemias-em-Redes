import pytest

from simulador.aleatoriedade import GeradorAleatorio


def test_estado_avanca_sem_reiniciar_e_sem_afetar_outros_fluxos():
    epidemia = GeradorAleatorio(42)
    mesma = GeradorAleatorio(42)
    iniciais = GeradorAleatorio(7)
    isolamento = GeradorAleatorio(8)
    primeiro = epidemia.uniforme()
    for _ in range(10):
        iniciais.uniforme()
        isolamento.uniforme()
    segundo = epidemia.uniforme()
    assert [primeiro, segundo] == [mesma.uniforme(), mesma.uniforme()]
    assert primeiro != segundo
    assert 0 <= primeiro < 1 and 0 <= segundo < 1
    assert epidemia.semente == 42


@pytest.mark.parametrize('semente', [True, None, 2.5, '42'])
def test_semente_exige_inteiro(semente):
    with pytest.raises(TypeError):
        GeradorAleatorio(semente)
