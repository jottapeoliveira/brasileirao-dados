-- passa quando devolve ZERO linhas
-- o grao da fato: um campeonato, uma data, um mandante e um visitante
select campeonato, data, clube_mandante_id, clube_visitante_id, count(*)
from {{ ref('fato_partida') }}
group by campeonato, data, clube_mandante_id, clube_visitante_id
having count(*) > 1
