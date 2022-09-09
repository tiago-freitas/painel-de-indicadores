import sys
from collections import defaultdict
import locale
import os
import datetime
import platform
import cherrypy
import cx_Oracle

# sys.path.append('/var/www/painelPPA')
# os.chdir('/var/www/painelPPA')

from helper import formato_br, taxa_format, ND, FASES, VAZIO, NA, ANO_PPA
from agregador import *

if platform.system() == 'Linux':
    locale.setlocale(locale.LC_ALL, ('pt_BR', 'UTF-8'))
else:
    locale.setlocale(locale.LC_NUMERIC, 'Portuguese_Brazil.1252') #para windows

os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8"

############################# gerar templates html ############################

calendario_template = { }
calendario_template_row = { }
siglas = ('M', 'B', 'T', 'Q', 'S', 'A')

meses = ('Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul',
         'Ago', 'Set', 'Out', 'Nov', 'Dez')
bimestres = ('1º Bimestre', '2º Bimestre', '3º Bimestre', '4º Bimestre',
             '5º Bimestre', '6º Bimestre')
trimestres = ('1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre')
quadrimestres = ('1º Quadrimestre', '2º Quadrimestre', '3º Quadrimestre')
semestres = ('1º Semestre', '2º Semestre')
anual = ( )

periodicidades = [meses, bimestres, trimestres, quadrimestres, semestres, anual]

periodicidade_dict = {'M': 'Mensal',
                      'B': 'Bimestral',
                      'T': 'Trimestral',
                      'Q': 'Quadrimestral',
                      'S': 'Semestral',
                      'A': 'Anual'}

totalizacao_dict = {'U': 'Último Valor',
                    'A': 'Maior Valor',
                    'E': 'Menor Valor',
                    'I': 'Manual',
                    'M': 'Média',
                    'S': 'Somatória',
                    'N': 'Manual'}

titulo = 'Apurações do Indicador por Ano'
head_head = ('Ano',)
# head_foot = ('Resultado Anual', 'Forma de Totalização', 'Meta Prevista (PPA)',
#              'Meta Atual', 'Índice',) # 'Periodicidade')
head_foot = ('Resultado Anual', 'Forma de Totalização', 'Meta LDO/LOA', 'Taxa',) # 'Periodicidade')
head_foot_anual = head_foot[:1] + ('Ano de referência',) + head_foot[1:]

body_head = ('ano',)

# body_foot = ('%(saldo_ano{ano})s', '%(forma_totalizacao{ano})s',
#              '%(METAPPA{ano})s', '%(METAATUAL{ano})s',
#              '%(taxa_apuracao_recente{ano})s',) # '%(periodicidade_ano{ano})s')

body_foot = ('<td class="number_row">%(saldo_ano{ano})s',
             '<td>%(forma_totalizacao{ano})s',
             '<td class="number_row">%(METAATUAL{ano})s',
             '<td class="number_row">%(taxa_apuracao_recente{ano})s',)

body_foot_anual = body_foot[:1] + ('<td class="number_row">%(ref{ano})s',) + body_foot[1:]

tabela_attr = '''<table id="apuracoes_indicadores" class="table-painel-1">\
<thead><tr><th class="table-titulo" colspan="%d">%s</th></tr><tr>'''

for periodicidade, sigla in zip(periodicidades, siglas):
    row_head = [tabela_attr % (len(head_head) + len(head_foot if sigla != 'A' else head_foot_anual) + len(periodicidade), titulo)]
    for elem in head_head:
        row_head.append('<th>' + elem + '</th>')
    for periodo in periodicidade:
        row_head.append('<th>' + periodo + '</th>')
    for elem in head_foot if sigla != 'A' else head_foot_anual:
        row_head.append('<th>' + elem + '</th>')
    row_head.append('</tr></thead>')

    row_body_full = ['<tbody><tr>']
    row_body = []
    for elem in body_head:
        row_body.append('<td class="number_row">{' + elem + '}</td>')
    for n in range(1, len(periodicidade) + 1):
        row_body.append('<td class="number_row">%({ano}-' + sigla + str(n) + ')s</td>')
    for elem in body_foot if sigla != 'A' else body_foot_anual:
        row_body.append(elem + '</td>')
    row_body.append('</tr>{row}')
    row_body_full.extend(row_body)
    row_body_full.append('</tbody></table>')

    calendario_template_row[sigla] = ''.join(row_body)
    calendario_template[sigla] = ''.join(row_head + row_body_full)

with open('indicadores-apuracao/sql/metas_recentes_todos_indicadores.sql') as f:
    metas_sql = f.read()
    metas_sql += ' AND loa_atual.SEQ_INDIC =:seq_indic'


def taxas_indicadores(cursor, ANO_CORRENTE, FASE_MAX, ANO_MAX, codigo, categoria):

    cursor.execute('''\
    SELECT ANO,
           PERIOD_APURACAO,
           SALDO_PARCIAL_ANO,
           TOTALIZACAO_ANO
    FROM EPPA_INDICADORES
    WHERE ANO IN ({ano1}, {ano2}, {ano3}, {ano4}) AND
          FASE = 8 AND
          SEQ_INDIC =:seq_indic
    ORDER BY ANO'''.format(ano1=ANO_PPA, ano2=ANO_PPA+1, ano3=ANO_PPA+2, ano4=ANO_PPA+3), seq_indic=codigo)

    periodicidade_ano = { }
    indicadores_dict = { }

    for ano, periodicidade, saldo, forma_totalizacao in cursor:

        ano = str(ano)

        periodicidade_ano[ano] = periodicidade
        indicadores_dict['periodicidade_ano' + ano] = periodicidade_dict[periodicidade]

        indicadores_dict['saldo_ano' + ano + '_raw'] = saldo if saldo else 'null'
        indicadores_dict['saldo_ano' + ano] = formato_br(saldo)
        if forma_totalizacao is not None:
            indicadores_dict['forma_totalizacao' + ano] = totalizacao_dict[forma_totalizacao]

        indicadores_dict['taxa_apuracao_ppa' + ano] = taxa_format(indicadores_ppa[int(ano) - (ANO_PPA-1)].get(codigo, 0))
        indicadores_dict['taxa_apuracao_recente' + ano] = taxa_format(indicadores_recente[int(ano) - (ANO_PPA-1)].get(codigo, 0))

    if str(ANO_PPA) not in periodicidade_ano:
        for a in (str(ANO_PPA+1), str(ANO_PPA+2), str(ANO_PPA+3)):
            if a in periodicidade_ano:
                periodicidade_ano[str(ANO_PPA)] = 'A'

    periodicidade_ano[str(ANO_PPA+1)] = periodicidade_ano.get(str(ANO_PPA+1), periodicidade_ano[str(ANO_PPA)])
    periodicidade_ano[str(ANO_PPA+2)] = periodicidade_ano.get(str(ANO_PPA+2), periodicidade_ano[str(ANO_PPA+1)])
    periodicidade_ano[str(ANO_PPA+3)] = periodicidade_ano.get(str(ANO_PPA+3), periodicidade_ano[str(ANO_PPA+2)])

    apuracoes = defaultdict(str)
    cursor.execute('''\
   SELECT x.PERIODO_REFERENCIA,
       x.MENSURACAO_TOT,
       COALESCE(TO_CHAR(x.ANO_REFERENCIA), 'ND')
FROM EPPA_INDIC_PERIODOS x
JOIN (SELECT PERIODO_REFERENCIA, MAX(PERIODO_LANCAMENTO) as PERIODO_LANCAMENTO
      FROM EPPA_INDIC_PERIODOS
      WHERE SEQ_INDIC =:seq_indic
      GROUP BY SEQ_INDIC, PERIODO_REFERENCIA) y ON y.PERIODO_LANCAMENTO = x.PERIODO_LANCAMENTO AND
                                                   y.PERIODO_REFERENCIA = x.PERIODO_REFERENCIA
WHERE x.SEQ_INDIC =:seq_indic
    ''', seq_indic=codigo)
    for periodo_referencia, apuracao, ano_referencia in cursor:
        apuracoes[periodo_referencia] = formato_br(apuracao)
        apuracoes['ref' + periodo_referencia[:4]] = ano_referencia

    metas = { }

    cursor.execute(metas_sql, seq_indic=codigo, 
                                        ano2=ANO_PPA+1,
                                        ano3=ANO_PPA+2, ano4=ANO_PPA+3,
                                        ano_corrente=ANO_CORRENTE)
    description = cursor.description
    metas_lista = cursor.fetchone()
    try:
        metas_lista = list(metas_lista)
    except TypeError:
        metas_lista = [codigo, None, None, None, None, None]

    # if categoria == 'Produto':

    #     ##### puxadinho #####
    #     try:
    #         metas_lista[3] = float(meta_indicador_2018_produto.at[codigo, 'VL_META_APROVADA_LOA'])
    #     except (ValueError, KeyError):
    #         metas_lista[3] = None

    #     if pd.isnull(metas_lista[3]):
    #         metas_lista[3] = None

    #     ##### fim do puxadinho #####


    for i, (etapa, meta) in enumerate(zip(description, metas_lista)):
        if i == 0: # hack para utilizar apenas um sql, elimina o seq_indic
          continue
        # index 0 em metas pois cursor.description retorna uma lista
        if etapa[0][-5:] == 'TOTAL':
            metas[etapa[0]] = formato_br(meta)
        elif meta is None:
            metas[etapa[0]] = VAZIO
        elif int(etapa[0][-4:]) > ANO_MAX:
             metas[etapa[0]] = ND
        else:
            metas[etapa[0]] = formato_br(meta)

    
    apuracoes.update(metas)
    apuracoes.update(indicadores_dict)

    cursor.execute('''SELECT
       t.TOTAL_SUBSTITUTO_ANO1,
       t.TOTAL_SUBSTITUTO_ANO2,
       t.TOTAL_SUBSTITUTO_ANO3

FROM EPPA_INDICADORES t
WHERE t.SEQ_INDIC =:seq_indic AND
      (t.SUBSTITUTO = 'S' OR t.NOVO = 'S') AND
      t.FASE = 8 AND
      t.ANO =:ano''', seq_indic=codigo, ano=ANO_CORRENTE)

    indic_subs = cursor.fetchall()
    if any(indic_subs):
        for indic_sub in indic_subs:
            for i in range(3):
                if indic_sub[i] is None:
                    continue
                ano = ANO_PPA + i
                apuracoes['saldo_ano%d' % ano] = formato_br(indic_sub[i])
                apuracoes['forma_totalizacao%d' % ano] = 'NA'
                apuracoes['METAATUAL%d' % ano] = 'NA'
                apuracoes['taxa_apuracao_recente%d' % ano] = 'NA'
                apuracoes['ref%d' % ano] = 'NA'

    template = calendario_template[periodicidade_ano[str(ANO_PPA)]]
 
    for ano in (str(ANO_PPA), str(ANO_PPA+1), str(ANO_PPA+2)):
        ano_seguinte = str(int(ano) + 1)
        if periodicidade_ano[ano] == periodicidade_ano[ano_seguinte]:
            marcador_prox_ano = '{row}'
            if ano == str(ANO_PPA+2):
                marcador_prox_ano =''
            row = calendario_template_row[periodicidade_ano[ano_seguinte]].format(ano=ano_seguinte, row=marcador_prox_ano)
            template = template.format(ano=ano, row=row)

        else:
            template = template.format(ano=ano, row='')
            template += calendario_template[periodicidade_ano[ano_seguinte]]
            if ano == str(ANO_PPA+3):
                template = template.format(ano=ano, row='')



    return (template % apuracoes,
            indicadores_dict.get(f'saldo_ano{ANO_PPA}_raw', 'null'),
            indicadores_dict.get(f'saldo_ano{ANO_PPA+1}_raw', 'null'),
            indicadores_dict.get(f'saldo_ano{ANO_PPA+2}_raw', 'null'),
            indicadores_dict.get(f'saldo_ano{ANO_PPA+3}_raw', 'null'),
            metas.get('METAPPATOTAL', 'ND'))
