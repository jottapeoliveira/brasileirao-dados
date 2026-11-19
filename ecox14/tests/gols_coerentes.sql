-- passa quando devolve ZERO linhas
-- os atributos derivados e o resultado precisam bater com os gols
select partida_id, gols_mandante, gols_visitante, total_gols, saldo_gols_mandante, resultado
from {{ ref('fato_partida') }}
where total_gols <> gols_mandante + gols_visitante
   or saldo_gols_mandante <> gols_mandante - gols_visitante
   or gols_mandante < 0 or gols_visitante < 0
   or (resultado = 'mandante') <> (gols_mandante > gols_visitante)
   or (resultado = 'empate') <> (gols_mandante = gols_visitante)
