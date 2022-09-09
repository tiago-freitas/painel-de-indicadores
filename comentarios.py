from helper import ANO_PPA

sql_comentarios = '''\
SELECT COALESCE(EPPA_INDIC_COMENTARIO.PERIODO_REFERENCIA, t.PERIODO_REFERENCIA) as "Periodo de Referência",
       COALESCE(COMENTARIO, 'ND'),
       COALESCE(JUSTIFICATIVA, 'ND')
FROM EPPA_INDIC_PERIODOS t
INNER JOIN
    (SELECT SEQ_INDIC, PERIODO_REFERENCIA, MAX(PERIODO_LANCAMENTO) as p
     FROM EPPA_INDIC_PERIODOS
     WHERE SEQ_INDIC =:seq_indic
     GROUP BY SEQ_INDIC, PERIODO_REFERENCIA ) t2
 ON t.seq_indic = t2.seq_indic and
    t.PERIODO_REFERENCIA = t2.PERIODO_REFERENCIA and
    t.PERIODO_LANCAMENTO = t2.p
FULL OUTER JOIN EPPA_INDIC_COMENTARIO
ON t.PERIODO_REFERENCIA = EPPA_INDIC_COMENTARIO.PERIODO_REFERENCIA AND
   t.SEQ_INDIC = EPPA_INDIC_COMENTARIO.SEQ_INDIC
WHERE t.SEQ_INDIC =:seq_indic AND
       (EPPA_INDIC_COMENTARIO.COMENTARIO IS NOT NULL OR t.JUSTIFICATIVA IS NOT NULL) AND
       t.ANO >=:ano_1 AND t.ANO <=:ano_4
ORDER BY TO_NUMBER(SUBSTR("Periodo de Referência", 1, 4)), TO_NUMBER(SUBSTR("Periodo de Referência", 7, 8))'''

sql_TCE = '''\
SELECT ANO, COALESCE(JUSTIFIC_SEP_TCE, 'ND')
FROM EPPA_INDICADORES
WHERE ANO >=:ano_1 AND ANO <=:ano_4 AND
      FASE = 8 AND
      SEQ_INDIC =:seq_indic
ORDER BY ANO ASC'''

table_format_comentarios_sem_problemas = (
               '<table id="justificativa_indicadores" class="table-painel-1">'
               '<thead><tr><th class="table-titulo" colspan="2">'
               'Comentários da execução</th></tr><tr><th>'
               'Período</th><th>Comentários da execução</th></thead>'
               '<tbody>%s</tbody></table>')

table_format_comentarios_problemas = (
               '<table id="comentarios_indicadores" class="table-painel-1">'
               '<thead><tr><th class="table-titulo" colspan="3">'
               'Comentários da execução e Problemas na apuração</th></tr><tr><th>'
               'Período</th><th>Comentários da execução</th><th>Problemas na apuração</th></thead>'
               '<tbody>%s</tbody></table>')

table_format_justificativa = (
               '<table id="justificativa_indicadores" class="table-painel-1">'
               '<thead><tr><th class="table-titulo" colspan="2">'
               'Justificativas Final TCE</th></tr><tr><th>'
               'Ano</th><th>Justificativa</th></thead>'
               '<tbody>%s</tbody></table>')

tr_format_comentarios_sem_problemas = '<tr><td>%s</td><td>%s</td></tr>'
tr_format_comentarios_problemas = '<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
tr_format_justificativa = '<tr><td>%s</td><td>%s</td></tr>'

def comentarios_indicadores(cursor, codigo):
    cursor.execute(sql_comentarios, seq_indic=codigo, ano_1=ANO_PPA, ano_4=ANO_PPA+3)
    n_rows_problemas = 0
    periodos = []
    comentarios = []
    justificativas = []
    n_rows = 0
    for periodo, comentario, justificativa in cursor:
        periodos.append(periodo)
        comentarios.append(comentario)
        justificativas.append(justificativa)
        n_rows += 1
        if justificativa == 'ND':
            n_rows_problemas +=1
    if n_rows == n_rows_problemas:
        rows = [tr_format_comentarios_sem_problemas % (periodo, comentario)
            for periodo, comentario in zip(periodos, comentarios)]
        return table_format_comentarios_sem_problemas % '\n'.join(rows) if rows else ''
    else:
        rows = [tr_format_comentarios_sem_problemas % (periodo, comentario, justificativa)
            for periodo, comentario, justificativa in zip(periodos, comentarios, justificativas)]
        return table_format_comentarios_problemas % '\n'.join(rows) if rows else ''

    

def justificativa_indicadores(cursor, codigo, ANO):
    cursor.execute(sql_TCE, seq_indic=codigo, ano_1=ANO_PPA, ano_4=ANO_PPA+3)
    rows = [tr_format_justificativa % (ano, justificativa)
            for ano, justificativa  in cursor if ano <= ANO]
    return table_format_justificativa % '\n'.join(rows) if rows else ''
