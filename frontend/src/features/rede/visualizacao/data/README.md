# Contornos do mapa

`world-land.json` contém os polígonos de terra do mapa do protótipo fornecido para a interface. Cada polígono contém anéis de pares `[longitude, latitude]`; o primeiro é o contorno externo e os seguintes representam vazios. As coordenadas estão arredondadas a duas casas decimais e a Antártida foi omitida no protótipo.

Fonte: [Natural Earth, Land 1:110m](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson). Os dados são de domínio público, conforme os [termos de uso](https://www.naturalearthdata.com/about/terms-of-use/).

O arquivo contém somente geometria para apresentação. Não inclui código de biblioteca de mapas ou de grafos. As posições dos indivíduos são fictícias, calculadas separadamente pelo frontend, e não indicam sua localização real. O desenho funciona sem acesso a servidores de mapas.
