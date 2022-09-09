###############################################################################
# @Author: Tiago Barreiros de Freitas
# 
# This file is part of PPAIndicatorPanel
#
# PPAIndicatorPanel is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PPAIndicatorPanel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Boston, MA 02110-1301, USA.
#
# GNU General Public License is available at link:
# http://www.gnu.org/licenses/gpl-3.0.en.html
###############################################################################

import datetime
import sys
import atexit
import os
import platform
import random
import locale
import json
import re
import time
from string import Template
from collections import namedtuple, deque, defaultdict
from xml.etree import ElementTree as ET
from statistics import mean
import functools

import cherrypy
import pandas as pd
from cherrypy.process.plugins import Monitor

import cx_Oracle

# sys.path.append('/var/www/painelPPA/')
# os.chdir('/var/www/painelPPA')

import helper
from indicadores import taxas_indicadores
from agregador import *
from comentarios import comentarios_indicadores, justificativa_indicadores
from templates import *
# from analises import Analises, Analises_delete, AuthController, Key, SESSION_KEY

import numpy as np

__author__ = 'Tiago Barreiros de Freitas'
__license__ = 'GNU'
__version__ = '2.4.1'
__date__ = '8 de Agosto de 2022'


if platform.system() == 'Linux':
    locale.setlocale(locale.LC_ALL, ('pt_BR', 'UTF-8'))
else:
    locale.setlocale(locale.LC_NUMERIC, 'Portuguese_Brazil.1252') #para windows
    os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8" # set unicode in env

FASE = 8 # fase de monitoramento
ANO_MAX, FASE_MAX, seq_pgm_dict = agregar_indicadores()

RELOAD_AGG = 60 * 60 * 24 # define a taxa de atualização em segundos das agregações

########################### namedtuples #######################################

row_indic = namedtuple('indicador', '''seq_indic nome_indic cod_org nome_org \
cod_pgm nome_pgm descricao categoria indicador_loa periodo unid_medida \
forma_total_ppa base_ meta1_raw_ meta2_raw_ meta3_raw_ meta4_raw_ metaTotal_raw_ \
cod_pdt nome_pdt seq_pgm nome_obj_estrat data_ref fonte seq_obj_estrat limitacoes \
descricao_calculo, apuracaoTotal_raw_ ano_criacao''')

row_uo_indic = namedtuple('indicador_uo_metas', '''cod_acao cod_uo \
meta_uo_1 meta_uo_2 meta_uo_3 meta_uo_4 meta_uo_total seq_acao''')

row_acao_indic = namedtuple('indicador_acao_metas', '''meta_acao_1 \
meta_acao_2 meta_acao_3 meta_acao_4 meta_acao_total acao_orc soma_uo''')

row_pdt = namedtuple('produto', '''cod_org nome_org seq_pgm cod_pgm nome_pgm \
seq_pdt nome_pdt descricao beneficiarios classificacao''')

row_pgm = namedtuple('programa', '''cod_pgm nome_pgm obj_pgm publico_alvo \
tp_pgm diagnostico classificacao tipo''')


###############################################################################

config = {

    '/': {
         'tools.staticdir.root': os.path.abspath(os.getcwd()),
         'tools.sessions.on': True,
         'tools.etags.on': True,
         'tools.etags.autotags': True,
    },

    '/obterInfo': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'text/html')]
    },

    '/static': {
         'tools.staticdir.on': True,
         'tools.staticdir.dir': './public',
         'tools.etags.on': True,
         'tools.etags.autotags': True
    },

    # '/analises': {
    #     'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    #     'tools.response_headers.on': True,
    #     'tools.response_headers.headers': [('Content-Type', 'application/javascript')]
    # },

    # '/analises_delete': {
    #     'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    #     'tools.response_headers.on': True,
    #     'tools.response_headers.headers': [('Content-Type', 'application/javascript')]
    # },

    # '/key': {
    #     'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    #     'tools.response_headers.on': True,
    #     'tools.response_headers.headers': [('Content-Type', 'application/javascript')]
    # },
}

############################# funções de apoio ################################



def indicador(cursor, codigo):
    # informações gerais do indicador

    cursor.execute(sql_indic, seq_indic=codigo, ano=ANO_CORRENTE, fase=FASE)
    try:
        i = row_indic(*cursor.fetchone()) # i == 'indicador'
    except TypeError:
        return html_erro.substitute(erro='Não foram encontrados os dados do indicador %s' % codigo)

    if i.categoria == 'Produto':
        template_indicador = html_indic_pdt
    elif i.categoria == 'Resultado':
        template_indicador = html_indic_resultado
    elif i.categoria == 'Impacto':
        template_indicador = html_indic_impacto

    info_indicadores = { }
    info_indicadores.update(i._asdict())

    for key in KEYS_AGG:
        ppa_dict = {'Programa': max(pgm_geral_ppa[key].get(i.seq_pgm, 0), 0),
                    'Órgão': max(orgao_ppa[key].get(i.cod_org, 0), 0),
                    'Estado de São Paulo': max(ESP_ppa.get(key, 0), 0)}
        if i.categoria != 'Impacto':
            recente_dict = {'Programa': max(pgm_geral_recente[key].get(seq_pgm_dict[i.cod_pgm], 0), 0),
                            'Órgão': max(orgao_recente[key].get(i.cod_org, 0), 0),
                            'Estado de São Paulo': max(ESP_recente.get(key, 0), 0)}
        else:
            recente_dict = ppa_dict

        agp = [str(round(n * 100, 2)) for n in sorted(ppa_dict.values())]
        alp = ['"%s"' % s for s in sorted(ppa_dict, key=ppa_dict.get, reverse=True)]
        agr = [str(round(n * 100, 2)) for n in sorted(recente_dict.values())]
        alr = ['"%s"' % s for s in sorted(recente_dict, key=recente_dict.get, reverse=True)]
        taxa_ppa_indicador = round(min(indicadores_ppa[key].get(codigo, 0), LIMITE_MAX), 2) * 100
        taxa_recente_indicador = round(min(indicadores_recente[key].get(codigo, 0), LIMITE_MAX), 2) * 100

        info_indicadores['apuracoes_agregadas_ppa_%s' % key] = ','.join(agp)
        info_indicadores['agregados_labels_ppa_%s' % key] = ','.join(alp)
        info_indicadores['apuracoes_agregadas_recente_%s' % key] = ','.join(agr)
        info_indicadores['agregados_labels_recente_%s' % key] = ','.join(alr)
        info_indicadores['taxa_ppa_%s' % key] = taxa_ppa_indicador if taxa_ppa_indicador > 0 else 0
        info_indicadores['taxa_recente_%s' % key] = taxa_recente_indicador if taxa_recente_indicador > 0 else 0

        info_indicadores['n_pgm_ppa_%s' % key] = alp.index('"Programa"') + 1
        info_indicadores['n_org_ppa_%s' % key] = alp.index('"Órgão"') + 1
        info_indicadores['n_esp_ppa_%s' % key] = alp.index('"Estado de São Paulo"') + 1

        info_indicadores['n_pgm_recente_%s' % key] = alr.index('"Programa"') + 1
        info_indicadores['n_org_recente_%s' % key] = alr.index('"Órgão"') + 1
        info_indicadores['n_esp_recente_%s' % key] = alr.index('"Estado de São Paulo"') + 1

    html_tabela_metas, *apuracao, meta_ppa = taxas_indicadores(
                        cursor,
                        ANO_CORRENTE,
                        FASE_MAX,
                        ANO_MAX,
                        codigo,
                        i.categoria)

    html = gadget_indicador.format(seq_indic=codigo)
    html += template_indicador.substitute(info_indicadores,
                                meta1_raw=helper.is_none(i.meta1_raw_),
                                meta2_raw=helper.is_none(i.meta2_raw_),
                                meta3_raw=helper.is_none(i.meta3_raw_),
                                meta4_raw=helper.is_none(i.meta4_raw_),
                                metaTotal_raw=helper.is_none(i.metaTotal_raw_),
                                meta1=helper.formato_br(i.meta1_raw_),
                                meta2=helper.formato_br(i.meta2_raw_),
                                meta3=helper.formato_br(i.meta3_raw_),
                                meta4=helper.formato_br(i.meta4_raw_),
                                metaTotal=helper.formato_br(i.metaTotal_raw_),
                                base=helper.formato_br(i.base_),
                                seq_indic=codigo,
                                apur1=apuracao[0],
                                apur2=apuracao[1],
                                apur3=apuracao[2],
                                apur4=apuracao[3])


    taxa_ppa = indicadores_recente['total'].get(codigo, 0)
    html += html_tabela_ppa.substitute(
             forma_total_ppa=i.forma_total_ppa,
             apuracaoTotal=helper.formato_br(i.apuracaoTotal_raw_),
             metaTotal=helper.formato_br(metas_ppa['total'].get(codigo, None)),
             taxa_ppa_total=helper.taxa_format(taxa_ppa),
             apur1=helper.formato_br(metas_ppa[1].get(codigo, None)),
             apur2=helper.formato_br(metas_ppa[2].get(codigo, None)),
             apur3=helper.formato_br(metas_ppa[3].get(codigo, None)),
             apur4=helper.formato_br(metas_ppa[4].get(codigo, None)),
             ano_1=ANO_PPA,
             ano_2=ANO_PPA+1,
             ano_3=ANO_PPA+2,
             ano_4=ANO_PPA+3)

    html += html_tabela_metas

    if i.categoria == 'Produto':
        acoes_uo = defaultdict(list)
        rows_a_u = list(cursor.execute(sql_acoes_uo_indic,
                                                  seq_indic=codigo,
                                                  ano=ANO_CORRENTE,
                                                  fase=FASE).fetchall())

        for seq_acao, cod_acao, acao_orc, cod_uo, soma in rows_a_u:
            acoes_uo[(seq_acao, cod_acao, acao_orc, soma)].append(cod_uo)

        rows_acao_uo = []

        for key, values in acoes_uo.items():
            seq_acao = key[0]
            try:
                cod_acao = int(key[1].split()[-1])
            except ValueError:
                cod_acao = 0

            if i.indicador_loa[0] == 'S':
                acao_metas = cursor.execute(sql_metas_acoes_indic,
                                                  seq_acao=seq_acao).fetchone()


                if acao_metas is not None:
                    acao_metas = list(acao_metas)
                    acao_metas = helper.validador_metas(acao_metas, i.ano_criacao)

                    rows_acao_uo.append(template_acao_uo % (*key[1:], *acao_metas))
                else:
                    rows_acao_uo.append(template_acao_uo % (*key[1:], 'ND', 'ND', 'ND', 'ND'))

                for cod_uo in values:
                    if cod_uo is None:
                        continue

                    uo_metas = cursor.execute(sql_metas_uo_indic,
                                    seq_acao=seq_acao, cod_uo=cod_uo).fetchone()

                    if uo_metas is not None:

                        uo_metas = list(uo_metas)
                        ##### puxadinho #####
                        # try:
                        #     uo_metas[2] = float(meta_uo_2018_produto.at[(codigo, cod_acao, cod_uo),
                        #                            'VL_META_APROVADA_LOA'])
                        # except (ValueError, KeyError):
                        #     pass

                        ##### fim do puxadinho #####
                        uo_metas = helper.validador_metas(uo_metas, i.ano_criacao)
                        rows_acao_uo.append(template_acao_uo % (*['⊢ UO %d' % cod_uo,
                                                           '-', '-'], *uo_metas))
                    else:
                        rows_acao_uo.append(template_acao_uo % ('⊢ UO %d' % cod_uo,
                                                           '-', '-', 'ND', 'ND', 'ND', 'ND'))
            else:
                acao_metas = cursor.execute(sql_metas_acoes_nao_ppa_indic,
                                seq_acao=seq_acao, seq_indic=codigo).fetchone()
                if acao_metas is not None:
                    acao_metas = helper.validador_metas(acao_metas, i.ano_criacao)
                    rows_acao_uo.append(template_acao_uo % (key[1], '-', '-', *acao_metas))
                else:
                    rows_acao_uo.append(template_acao_uo % (key[1], '-', '-', 'ND', 'ND', 'ND', 'ND'))

        html += table_uo_acao_inicio + ''.join(rows_acao_uo) + '</tbody></table>'

    html += justificativa_indicadores(cursor, codigo, ANO_CORRENTE)
    html += comentarios_indicadores(cursor, codigo)

    return html + '</div>'

def fazer_tabelas_orc(cursor,
                      seq_pgm,
                      cod_acoes,
                      seq_acoes,
                      conn,
                      params,
                      seq_indic_tmp,
                      seq_pdt):
    padding = 4


    cursor.execute(sql_acao_pdt_orc % ','.join(cod_acoes), **params)
    columns = [col[0] for col in cursor.description]

    df = pd.DataFrame(cursor.fetchall(), columns=columns)


    df.COD_CAT = df.COD_CAT.map(categoria_despesa)
    df.COD_GRUPO = df.COD_GRUPO.map(grupo_despesa)
    df.COD_ELEM = df.COD_ELEM.map(elemento_despesa)
    df.DOT_INICIAL_MENSAL = df.DOT_INICIAL_MENSAL.astype(np.float64)

    u = 'unidade'
    apuracoes_fisicas = []

    orc_tabelas = ''
    if not df.empty:
        df_tmp = df.pivot_table(values=VALUE_NAMES_ORC,
                        index=INDEX_NAMES_ORC,
                        columns='MES',
                        aggfunc='sum')
        df_tmp.reset_index('DOT_INICIAL_MENSAL', inplace=True)

    for cod_acao, seq_acao in zip(cod_acoes, seq_acoes):
        cod_acao = int(float(cod_acao))
        t, u, totais_uo = fazer_tabelas_metas_uo(seq_acao, cod_acao, cursor)

        if totais_uo is not None:
            apuracoes_fisicas.append(totais_uo)

        if df.empty:
            orc_tabelas = t
            continue

        try:
            df_acao = df_tmp.loc[cod_acao]
        except KeyError:
            continue

        if df_acao.empty:
            continue

        soma_horizontal = df_acao.sum().to_frame('Acumulado').T
        soma_horizontal.index = dummy_multiIndex
        df_orc = pd.concat([df_acao, soma_horizontal])

        for coluna, coluna_nome in zip(COLUNAS_ORC, COLUNAS_ORC_NOMES):
            df_orc_coluna = df_orc[['DOT_INICIAL_MENSAL', coluna]]
            df_orc_coluna = df_orc_coluna.assign(Total=df_orc[coluna].sum(axis='columns'))
            df_orc_coluna.columns = COLUMNS_NAMES_ORC
            df_orc_coluna.index.names = INDEX_LABELS_ORC
            if coluna == 'DOT_ATUAL_ACUM':
                df_orc_coluna.rename(columns={'Acumulado': 'Total'}, inplace=True)

            table_orc = df_orc_coluna.to_html(
                    index=True,
                    float_format=lambda x: helper.format_pt_br(val=x) if not np.isnan(x) else '0',
                    bold_rows=False,
                    classes='table-painel-1 table-orc %s' % coluna,
                    justify='left')

            table_orc = table_orc.replace('<thead>',
                    '<thead><tr><th colspan="18" style="text-align: center;">%s</th></tr>' %
                    (coluna_nome % (ANO_CORRENTE, cod_acao))) # verificar depois

            orc_tabelas += (
                ('<div id="%s%s"class="orcamento-tables">' % (
                 cod_acao, coluna)) + table_orc + '</div>')

        orc_tabelas += t
 
    if apuracoes_fisicas:
        df = pd.concat(apuracoes_fisicas)
    else:
        df = pd.DataFrame(columns=['UO', 'Realizado'], index=['COD_ACAO'])


    suma = fazer_tabela_sintetica(
             df,
             conn,
             cursor,
             cod_acoes,
             seq_acoes,
             seq_pgm,
             params,
             u,
             seq_indic_tmp,
             seq_pdt)
    
    return orc_tabelas, u, suma

def fazer_tabela_sintetica(totais_fisicos,
                           conn,
                           cursor,
                           cod_acoes,
                           seq_acoes,
                           seq_pgm,
                           params,
                           unidade,
                           seq_indic_tmp,
                           seq_pdt):

 
    acoes = ','.join(str(x) for x in seq_acoes)

    # Verificar a FASE_MAX!
    # re(FASE_MAX)
    # if FASE_MAX not in (7, 8):
    #     ano_loa = ANO_CORRENTE - 1
    # else:
    
    ano_loa = ANO_CORRENTE

    # verificar var ano_loa
    params_uo = {'cod_org': params['cod_org'],
                 'seq_pgm': seq_pgm,
                 'ano_ppa': ANO_PPA,
                 'fase_ppa': FASE_PPA,
                 'ano_loa': ano_loa, 
                 'fase_loa': 7 } # fase da loa

    cursor.execute(sql_acao_pdt_uo_meta.format(acoes=acoes), **params_uo)
    columns = [col[0] for col in cursor.description]

    uo_meta = pd.DataFrame(cursor.fetchall(), columns=columns)    
    uo_meta.set_index(['COD_ACAO', 'UO', 'FASE'], inplace=True)

    uo_meta = uo_meta.unstack()

    uo_meta.columns = uo_meta.columns.droplevel()
    uo_meta = uo_meta.reset_index('UO')
    uo_meta.columns.name = None
    uo_meta = uo_meta.reindex(['UO', 'META LOA', 'META PPA'], axis=1)

    acoes = ','.join(cod_acoes)
    params_uo_orc = {'ano': ANO_CORRENTE,
                     'mes': MES_CORRENTE,
                     'cod_org': params['cod_org'],
                     'cod_pgm': params['cod_pgm']}


    cursor.execute(sql_acao_pdt_orc_sintetico % acoes, **params_uo_orc)
    columns = [col[0] for col in cursor.description]
    uo_orc = pd.DataFrame(cursor.fetchall(), columns=columns)

    uo_orc = uo_orc.replace(-1, np.nan)

    blocos = []
    total_acoes = uo_orc.groupby('COD_ACAO')
    for n, g in total_acoes:
        total_acao = g.sum(numeric_only=True)
        total_acao['UO'] = 'Ação %s' % n

        g = pd.concat([g, total_acao.to_frame().T], ignore_index=True)

        if int(n) in totais_fisicos.index:
            if not totais_fisicos.empty:
                chunk = totais_fisicos.loc[int(n)]
                if isinstance(chunk, pd.Series):
                    chunk = chunk.to_frame('COD_ACAO').T
                g = g.merge(chunk, how='outer')
            else:
                g = g.merge(totais_fisicos, how='outer')

        if n in uo_meta.index:
            if not uo_meta.empty and uo_meta.shape[0] > 1:
                g = g.merge(uo_meta.loc[n], how='outer')
            else:
                g = g.merge(uo_meta, how='outer')
        g.loc[~g.UO.str.startswith('A'), 'COD_ACAO'] = '⊢   UO ' + g.UO[~g.UO.str.startswith('A')]
        g.loc[g.UO.str.startswith('A'), 'COD_ACAO'] = g.UO[g.UO.str.startswith('A')]
        g = g.sort_values('COD_ACAO', ascending=True).drop('UO', axis=1)
        blocos.append(g)
    if blocos:
        t = pd.concat(blocos, ignore_index=True)
        t = t.reindex(['COD_ACAO', 'INICIAL', 'ATUAL', 'EMPENHADO',
                            'LIQUIDADO', 'Realizado', 'VALOR', 'FASE',
                            'META LOA', 'META PPA'], axis=1)
    else:
        t = pd.DataFrame(columns=['COD_ACAO', 'INICIAL', 'ATUAL', 'EMPENHADO',
                                  'LIQUIDADO', 'Realizado', 'VALOR', 'FASE',
                                  'META LOA', 'META PPA'])

    produto = t.loc[t.COD_ACAO.str.startswith('A'), ['INICIAL', 'ATUAL', 'EMPENHADO','LIQUIDADO']].sum()
    produto['COD_ACAO'] = 'Produto ' + str(seq_pdt)
    produto['META LOA'] = 0
    produto['Realizado'] = 0
    produto['FASE'] = ''
    produto['META PPA'] = ''

    t = pd.concat([t, produto.to_frame().T])

    t['Liquidado / Empenhado'] = (t.LIQUIDADO /
                                  t.EMPENHADO.replace(0, np.nan)) * 100
    t['Liquidado / Atual'] = (t.LIQUIDADO /
                              t.ATUAL.replace(0, np.nan)) * 100
    t['Realizado / Meta LOA'] = (t['Realizado'] /
                                 t['META LOA'].replace(0, np.nan)) * 100
    t['Físico / Orçamento'] = (t['Realizado / Meta LOA'] /
                               t['Liquidado / Atual'].replace(0, np.nan)) * 100

    t = t.rename(columns={'COD_ACAO': 'Nível',
                          'INICIAL': 'Dotação Inicial (LOA)',
                          'ATUAL': 'Dotação Atual',
                          'EMPENHADO': 'Empenhado',
                          'LIQUIDADO': 'Liquidado',
                          'META LOA': 'Meta LOA',
                          'META PPA': 'Referência PPA'})

    t = t[['Nível', 'Físico / Orçamento', 'Meta LOA',
           'Realizado', 'Realizado / Meta LOA', 'Dotação Inicial (LOA)',
           'Dotação Atual', 'Empenhado', 'Liquidado',
           'Liquidado / Atual', 'Liquidado / Empenhado']]

    if unidade == 'unidade':
        t['Meta LOA']  = t['Meta LOA'].map(lambda x: locale.format_string('%d', x, grouping=True),
                                                     na_action='ignore')
        t['Realizado'] = t['Realizado'].map(lambda x: locale.format_string('%d', x, grouping=True),
                                                     na_action='ignore')

    t = t.fillna('ND')

    table = t.to_html(
             index=False,
             bold_rows=False,
             float_format=lambda x: helper.format_pt_br(val=x) if not np.isnan(x) else '0',
             classes='table-painel-1 table-orc table-suma',
             justify='left')

    table = table.replace('<thead>',
            '<thead><tr><th colspan="%d" style="text-align: center;">%s em %d</th></tr>'
            '<tr><th rowspan="2" style="text-align: center;">Nível</th>'
            '<th rowspan="2" style="text-align: center;">Físico / Orçamento</th>'
            '<th colspan="3" style="text-align: center;">Dimensão Física</th>'
            '<th colspan="6" style="text-align: center;">Dimensão Orçamentária</th></tr>' %
            (len(t.columns), TABELA_ANALISE, ANO_CORRENTE))

    table = table.replace('<th>Nível</th>', '')
    table = table.replace('<th>Físico / Orçamento</th>', '')

    return "<p style='text-align: right;margin: 0'>Em R$ mil</p>" + table

def fazer_tabelas_metas_uo(seq_acao, cod_acao, cursor):
    def formatador(x):
        if not x:
            return '0'
        if u == 'unidade':
            return locale.format_string('%d', x, grouping=True)
        else:
            return locale.format_string('%.2f', x, grouping=True)


    cursor.execute(sql_acao_pdt_fisica, **{'ano': ANO_CORRENTE,
                                      'fase': FASE,
                                      'seq_acao': seq_acao})
    columns = [col[0] for col in cursor.description]
    acao_fisica = pd.DataFrame(cursor.fetchall(), columns=columns)

    cursor.execute(sql_acao_pdt_uo_fisica, **{'seq_acao': seq_acao,
                                    'ano': ANO_CORRENTE})
    columns = [col[0] for col in cursor.description]
    uo_fisica = pd.DataFrame(cursor.fetchall(), columns=columns)

    if not len(acao_fisica) and not len(uo_fisica):
        return '', '', None

    if len(acao_fisica):
        p = acao_fisica.PERIOD_APURACAO[0] # periodicidade
        u = acao_fisica.UNID_MEDIDA[0] # unidade de medida
        s = acao_fisica.TOTALIZACAO_ANO[0] # forma de totalização
    else:
        p = uo_fisica.PERIOD_APURACAO[0] # periodicidade
        u = uo_fisica.UNID_MEDIDA[0] # unidade de medida
        s = uo_fisica.TOTALIZACAO_ANO[0] # forma de totalização


    fitro_sanitizacao = uo_fisica.PERIODO_REFERENCIA.str.contains(p)
    uo_fisica = uo_fisica[fitro_sanitizacao]
    fitro_sanitizacao = acao_fisica.PERIODO_REFERENCIA.str.contains(p)
    acao_fisica = acao_fisica[fitro_sanitizacao]

    uo_fisica = pd.concat([acao_fisica, uo_fisica], sort=False)

    if s == 'S':
        total = uo_fisica.groupby('UO').VALOR.sum()
    elif s == 'U':
        total = uo_fisica.groupby('UO').VALOR.last()
    elif s == 'M':
        meses = MES_CORRENTE - 1
        if p == 'M':
            divisor = meses // 1
        elif p == 'B':
            divisor = meses // 2
        elif p == 'T':
            divisor = meses // 3
        elif p == 'Q':
            divisor = meses // 4
        elif p == 'S':
            divisor = meses // 6
        elif p == 'A':
            divisor = meses // 12
        total = uo_fisica.groupby('UO').VALOR.sum() / divisor
    else:
        total = np.nan

    if total is not np.nan:
        t = (total.to_frame()
                  .reset_index()
                  .assign(COD_ACAO=cod_acao)
                  .set_index('COD_ACAO')
                  .rename(columns={'VALOR': 'Realizado'}))
    else:
        t = None

    uo_fisica = (uo_fisica[['UO', 'PERIODO_REFERENCIA', 'VALOR']]
                          .set_index(['UO', 'PERIODO_REFERENCIA'])
                          .unstack(1))
    
    uo_fisica.columns = uo_fisica.columns.droplevel()
   
    if p == 'M':
        index_ = iM.format(ano=ANO_CORRENTE).split()
    elif p == 'B':
        index_ = iB.format(ano=ANO_CORRENTE).split()
    elif p == 'T':
        index_ = iT.format(ano=ANO_CORRENTE).split()
    elif p == 'Q':
        index_ = iQ.format(ano=ANO_CORRENTE).split()
    elif p == 'S':
        index_ = iS.format(ano=ANO_CORRENTE).split()
    elif p == 'A':
        index_ = [iA.format(ano=ANO_CORRENTE)]
    uo_fisica = uo_fisica.reindex(index_, axis=1)

    uo_fisica['Total'] = total
    uo_fisica = uo_fisica.fillna('ND')
    uo_fisica = uo_fisica.reset_index()

    uo_fisica.loc[~uo_fisica.UO.str.startswith('A'), 'UO'] = '⊢   UO ' + uo_fisica.UO[~uo_fisica.UO.str.startswith('A')]
    uo_fisica = uo_fisica.sort_values(by='UO', ascending=True)

    table = uo_fisica.to_html(
         index=False,
         index_names=False,
         float_format=formatador,
         bold_rows=False,
         classes='table-painel-1 table-orc',
         justify='left')

    table = table.replace('<thead>',
            '<thead><tr><th colspan="%d" style="text-align: center;">%s</th></tr>' %
            (len(uo_fisica.columns), COLUNA_UO_FISICO))
    header = '<div id="%sFISICO"class="orcamento-tables">' % cod_acao

    return header + table + '</div>', u, t


######################### Monitor de indicadores agregados #####################
def ret_data():
    ano_corrente = datetime.datetime.now().year
    mes_corrente = datetime.datetime.now().month
    dia_corrente = datetime.datetime.now().day
    return ano_corrente, mes_corrente, dia_corrente

ANO_CORRENTE, MES_CORRENTE, DIA_CORRENTE = ret_data()
if ANO_CORRENTE - ANO_PPA > 4:
    ANO_CORRENTE = ANO_PPA + 3
    MES_CORRENTE = 12
    DIA_CORRENTE = 30

def mnt_data():
    global ANO_CORRENTE, MES_CORRENTE, DIA_CORRENTE, ANO_MAX, FASE_MAX, seq_pgm_dict
    ANO_CORRENTE, MES_CORRENTE, DIA_CORRENTE = ret_data()
    if ANO_CORRENTE - ANO_PPA > 4:
        ANO_CORRENTE = ANO_PPA + 3
        MES_CORRENTE = 12
        DIA_CORRENTE = 30

    if ANO_CORRENTE - ANO_PPA <= 4:
        ANO_MAX, FASE_MAX, seq_pgm_dict = agregar_indicadores()

    # for i in range(len(conn_list)):
    #     conn_list[i].close()
    #     conn_list[i] = cx_Oracle.connect(conn_user)

Monitor(cherrypy.engine, mnt_data, frequency=RELOAD_AGG).start()


conn_list = []

def connect(thread_index):
    # cria uma conexão e armazena no atual thread
    conn = cx_Oracle.connect(conn_user)
    cherrypy.thread_data.db_i = thread_index - 1
    conn_list.append(conn)

################################ web app ######################################

# CherryPy chama "connect" ao início de cada thread
cherrypy.engine.subscribe('start_thread', connect)


class simPPA(object):
    def __init__(self):
        self.obterInfo = obterInfo()
        self.webservice = WebService()
        # self.analises = Analises()
        # self.analises_delete = Analises_delete()
        # self.auth = AuthController()
        # self.key = Key()


    @cherrypy.expose
    def default(self, tipo='', codigo='',  **kwargs):
        # sanity checks
        if tipo not in ('', 'indicador', 'produto', 'programa',
                        'orgao', 'obj_estrat'):
            tipo = ''

        if tipo != '':
            try:
                codigo = int(codigo)
            except ValueError:
                tipo = ''
                codigo = ''

        return html_url.format(corpo=self.obterInfo.POST(tipo, codigo),
                               tipo="'%s'" % tipo, codigo="'%s'" % codigo,
                               versao=__version__, data=__date__)

    @cherrypy.expose(['documentacao', 'docs'])
    def doc(self):
        return doc_html



class obterInfo(object):
    exposed = True

    @cherrypy.tools.accept(media='text/plain')
    def POST(self, tipo='', codigo='', **kwargs):
        # sanity checks
        if tipo not in ('', 'indicador', 'produto', 'programa',
                        'orgao', 'obj_estrat'):
            return ''

        cursor = conn_list[cherrypy.thread_data.db_i].cursor()

        # sanity checks
        if tipo != '':
            try:
                codigo = int(codigo)
            except ValueError:
                return ''

        if tipo == 'indicador':
            html = indicador(cursor, codigo)


        elif tipo == 'produto':

            # obter dados gerais do produto

            cursor.execute(sql_pdt, seq_produto=codigo, ano=ANO_CORRENTE, fase=FASE)
            try:
                p = row_pdt(*cursor.fetchone())
            except TypeError:
                cursor.close()
                return html_erro.substitute(erro='Não foram encontrados os dados do produto %s' % codigo)


            # obter indicadores do produto
            cursor.execute(sql_pdt_indic, seq_produto=codigo, ano=ANO_CORRENTE, fase=FASE)
            rows = []
            seq_indic_tmp = None
            for seq_indic, nome_indic, is_ppa in cursor:
                if not seq_indic:
                    continue
                if is_ppa == 'S':
                    seq_indic_tmp = seq_indic
                row = '<tr>\n<td class="link-handler">' + template_pdt_indic % (seq_indic, nome_indic) + '</td>'
                row += '<td>Sim</td>' if is_ppa == 'S' else '<td>Não</td>'
                for key in KEYS_AGG:
                    raw_taxa = indicadores_recente[key].get(seq_indic, 0)
                    taxa = helper.taxa_format(raw_taxa) if raw_taxa != -1 else helper.ND
                    row += '<td class="number_row">%s</td>' % taxa
                row += '</tr>'
                rows.append(row)
            if rows:
                indicadores_tabela = table_indic_pdt + '\n'.join(rows) + '</tbody></table>'
            else:
                indicadores_tabela = ''


            rows = []
            cod_acoes = []
            seq_acoes = []
            cursor.execute(sql_acao_pdt, seq_produto=codigo, ano=ANO_CORRENTE, fase=FASE)
            for seq_acao, cod_acao, nome_acao, is_orc in cursor:
                if not cod_acao:
                    continue
                row = ('<tr onclick="orc_acao(%d)" class="link-handler"'
                       'style="cursor: pointer;">\n<td>%d</td><td>%s</td>' % (
                            cod_acao, cod_acao, nome_acao))
                row += '<td>Sim</td>' if is_orc == 'S' else '<td>Não</td>'
                row += '</tr>'
                rows.append(row)
                cod_acoes.append(str(cod_acao))
                seq_acoes.append(seq_acao)
            if rows:
                acoes_tabela = table_pdt_acoes + '\n'.join(rows) + '</tbody></table>'
            else:
                acoes_tabela = ''


            params = dict(ano=ANO_CORRENTE,
                          cod_org=p.cod_org,
                          cod_pgm=p.cod_pgm)

            
            if seq_acoes and seq_indic_tmp is not None:
                orc_tabelas, u, suma = fazer_tabelas_orc(
                                               cursor,
                                               p.seq_pgm,
                                               cod_acoes,
                                               seq_acoes,
                                               conn_list[cherrypy.thread_data.db_i],
                                               params,
                                               seq_indic_tmp, 
                                               codigo)

                acoes_descricao = helper.fazer_tabelas_acoes(conn_list[cherrypy.thread_data.db_i],
                                        {'ano': ANO_CORRENTE,
                                         'fase': FASE,
                                         'seq_acoes': seq_acoes})
    
            else:
                orc_tabelas, u, suma = '', '', ''
                acoes_descricao = ''

            info_pdt = { }
            info_pdt.update(p._asdict())

            graph_pdt_data = { }
            for key in KEYS_AGG:
                raw_taxa = pdt_recente[key].get(codigo, 0)
                label_taxa = helper.taxa_format(raw_taxa)
                graph_pdt_data['data_%s' % key] = raw_taxa * 100 if raw_taxa != -1 else 0
                graph_pdt_data['title_%s' % key] = label_taxa
            info_pdt.update(graph_pdt_data)

            ############### Autenticação Módulo de Monitoramento ##############

            # usuario =  cherrypy.session.get(SESSION_KEY)
            # script_analise = ''
            # if usuario is not None:
            #     script_analise = script_analise_conn.format(usuario=usuario)
            # else:
            #     script_analise = script_analise_n_conn

            ################# Compor HTML final de produto ####################

            # html = html_produto.substitute(info_pdt,
            #                                indic_tabela=indicadores_tabela,
            #                                acao_tabela=acoes_tabela,
            #                                seq_produto=codigo,
            #                                tipo=tipo,
            #                                orc_tabelas=orc_tabelas,
            #                                script_analise=script_analise,
            #                                unidade_medida=u,
            #                                suma=suma)


            html = html_produto.substitute(info_pdt,
                               indic_tabela=indicadores_tabela,
                               acao_tabela=acoes_tabela,
                               acao_descricao=acoes_descricao,
                               seq_produto=codigo,
                               tipo=tipo,
                               orc_tabelas=orc_tabelas,
                               unidade_medida=u,
                               suma=suma,
                               ano_1=ANO_PPA,
                               ano_2=ANO_PPA+1,
                               ano_3=ANO_PPA+2,
                               ano_4=ANO_PPA+3)

        elif tipo == 'programa':
            try:
                cod_pgm = codigo
                codigo = seq_pgm_dict[codigo]
            except KeyError:
                cursor.close()
                return html_erro.substitute(erro='Não foram encontrados dados do programa %s' % codigo)
            # sql informações do programa
            cursor.execute(sql_pgm, seq_pgm=codigo, fase=FASE, ano=ANO_CORRENTE)
            try:
                programaT = row_pgm(*cursor.fetchone())
            except TypeError:
                cursor.close()
                return html_erro.substitute(erro='Não foram encontrados dados do programa %s' % codigo)

            # órgãos relacionados com o programa
            cursor.execute(sql_pgm_orgs, seq_pgm=codigo, fase=FASE, ano=ANO_CORRENTE)
            orgaos = '<br>'.join([template_orgs(cod_org, nome_org)
                                   for cod_org, nome_org in cursor.fetchall()])

            # objetivos estratégicos do programa
            cursor.execute(sql_pgm_obj_estrat, seq_pgm=codigo, fase=FASE, ano=ANO_CORRENTE)
            objs_estrat = '<br>'.join(template_objs_pgms % (seq_obj_estrat, nome_obj)
                                          for nome_obj, _, seq_obj_estrat in cursor)

            if not objs_estrat:
                objs_estrat = helper.ND
                has_objs = ''
            else:
                has_objs = 'link-handler'

            # fatores de risco do programa
            cursor.execute(sql_risco, seq_pgm=codigo, fase=FASE, ano=ANO_CORRENTE)

            fatores_risco = '\n'.join(templateRisco %
               (tipo, gravidade, comentario if comentario.strip() else helper.ND)
                                      for tipo, gravidade, comentario in cursor)

            # coleta as apurações produto, resultado e geral do programa
            info_pgm = programaT._asdict()

            if pgm_has_resultado.get(codigo, False):
                info_pgm.update({'taxa_recente_resultado_%s' % key:helper.taxa_format(
                  pgm_resultado_recente[key].get(codigo, 0)) for key in KEYS_AGG})
            else:
                info_pgm.update({'taxa_recente_resultado_%s' % key: helper.ND for key in KEYS_AGG})

            if pgm_has_produto.get(codigo, False):
                info_pgm.update({'taxa_recente_pdt_%s' % key:helper.taxa_format(
                     pgm_pdt_recente[key].get(codigo, 0)) for key in KEYS_AGG})
            else:
                info_pgm.update({'taxa_recente_pdt_%s' % key: helper.ND for key in KEYS_AGG})

            info_pgm.update({'taxa_recente_geral_%s' % key:helper.taxa_format(
                   pgm_geral_recente[key].get(codigo, 0)) for key in KEYS_AGG})

            #indicadores de resultado
            indic_resultado_tabela = ''
            cursor.execute(sql_pgm_resultado, seq_pgm=codigo, ano=ANO_CORRENTE, fase=FASE)
            rows = []
            for seq_indic, nome_indic in cursor:
                if seq_indic is None:
                    continue
                row = '<tr>\n<td class="link-handler">' + template_pdt_indic % (seq_indic, nome_indic) + '</td>'
                for key in KEYS_AGG:
                    row += '<td class="number_row">%s</td>' % helper.taxa_format(indicadores_recente[key].get(seq_indic, 0))
                row += '</tr>'
                rows.append(row)
            if rows:
                indic_resultado_tabela = table_resultado_pgm + '\n'.join(rows) + '</tbody></table>'

            #indicadores de produto
            indic_produto_tabela = ''
            cursor.execute(sql_pgm_produto, seq_pgm=codigo, ano=ANO_CORRENTE, fase=FASE)
            rows = []
            for seq_pdt, nome_pdt, classificacao in cursor:
                if seq_pdt is None:
                    continue
                row = '<tr>\n<td class="link-handler">' + template_pdt % (seq_pdt, nome_pdt) + '</td>'
                row += '<td>%s</td>' % classificacao
                for key in KEYS_AGG:
                    row += '<td class="number_row">%s</td>' % helper.taxa_format(pdt_recente[key].get(seq_pdt, 0))
                row += '</tr>'
                rows.append(row)
            if rows:
                indic_produto_tabela = table_produto_pgm + '\n'.join(rows) + '</tbody></table>'


            html = html_pgm.substitute(info_pgm,
             orgaos=orgaos,
             seq_pgm=codigo,
             objs_estrat=objs_estrat,
             risco=fatores_risco,
             has_objs=has_objs,
             tabela_resultado=indic_resultado_tabela,
             tabela_produto=indic_produto_tabela,
             ano_1=ANO_PPA,
             ano_2=ANO_PPA+1,
             ano_3=ANO_PPA+2,
             ano_4=ANO_PPA+3)

        elif tipo == 'orgao':
            cursor.execute(sql_orgao, cod_org=codigo)
            try:
                nome_org = cursor.fetchone()[0]
            except TypeError:
                cursor.close()
                return html_erro.substitute(erro='Não foram encontrados dados do órgão %s' % codigo)

            # temporariamente com apenas as metas correntes
            dados_orgao = { }
            dados_orgao.update({'data_%s' % key:
                  orgao_recente[key].get(codigo, 0) * 100 for key in KEYS_AGG})
            dados_orgao.update({'title_%s' % key:'%s' % helper.taxa_format(
                      orgao_recente[key].get(codigo, 0))  for key in KEYS_AGG})
            
            pgms_tabela = helper.fazer_tabelas_anos(
                cursor,
                conn_list[cherrypy.thread_data.db_i],
                orgao_recente,
                pgm_geral_recente,
                ANO_PROJETO_PPA,
                ANO_CORRENTE,
                MES_CORRENTE,
                sql_orgao_pgms,
                template_orgao_pgm,
                table_orgao_pgms,
                codigo,
                FASE
            )

            html = html_orgao.substitute(dados_orgao,
                                         nome_org=nome_org,
                                         cod_org=codigo,
                                         pgms_tabela=pgms_tabela,
                                         ano_1=ANO_PPA,
                                         ano_2=ANO_PPA+1,
                                         ano_3=ANO_PPA+2,
                                         ano_4=ANO_PPA+3)


        elif tipo == 'obj_estrat':
            cursor.execute(sql_obj_estrat,
                           seq_obj_estrat=codigo,
                           fase=FASE,
                           ano=ANO_CORRENTE)
            try:
                nome, descricao = cursor.fetchone()
            except TypeError:
                cursor.close()
                return html_erro.substitute(erro='Não foram encontrados dados do Objetivo Estratégico %s' % codigo)

            # programas associados ao objetivo estratégico
            cursor.execute(sql_obj_pgms, seq_obj_estrat=codigo, fase=FASE, ano=ANO_CORRENTE)
            programas = '<br>'.join(template_pgms_objs % (seq_pgm, nome)
                                    for seq_pgm, nome in cursor)

            # indicadores associados ao objetivo estratégico
            cursor.execute(sql_obj_indic, seq_obj_estrat=codigo, fase=FASE, ano=ANO_CORRENTE)
            rows = []
            for seq_indic, *elems_indic in cursor:
                row = [template_objs_indic % seq_indic]
                for elem in elems_indic:
                    if not isinstance(elem, str):
                        elem = helper.formato_br(elem)
                    row.append('<td>%s</td>' % elem)
                row.append('</tr>')
                rows.append('\n'.join(row))
            indicadores = ''.join(rows)

            html = html_obj_estrategico.substitute(nome=nome, descricao=descricao,
                                      programas=programas, indicadores=indicadores)

        # dados do Estado de São Paulo
        elif tipo == '':
            info_esp = {'data_%s' % key: ESP_recente.get(key, 0) * 100 for key in KEYS_AGG}
            info_esp.update({'title_%s' % key:'%s' % helper.taxa_format(
                           ESP_recente.get(key, 0)) for key in KEYS_AGG})

            orgaos_tabela = helper.fazer_tabelas_anos(
                cursor,
                conn_list[cherrypy.thread_data.db_i],
                ESP_recente,
                orgao_recente,
                ANO_PROJETO_PPA,
                ANO_CORRENTE,
                MES_CORRENTE,
                sql_esp_orgaos,
                template_esp_orgao,
                table_orgaos_esp
            )

            html = html_esp.substitute(info_esp, orgaos_tabela=orgaos_tabela, ano_1=ANO_PPA,
             ano_2=ANO_PPA+1,
             ano_3=ANO_PPA+2,
             ano_4=ANO_PPA+3)

        cursor.close()
        return html


class WebService(object):

    filetype = 'attachment;filename=%s-%s.%s'

    dict_fonte = {
            'orgao': 'COD_ORG',
            'programa': 'SEQ_PGM',
            'produto': 'SEQ_PRODUTO',
            'indicador': 'SEQ_INDIC',
            'todos': ''
    }

    mime_types = {
            'csv': 'text/plain;charset=utf-8',
            'tab': 'text/plain;charset=utf-8',
            'json': 'application/json;charset=utf-8',
            'xml': 'application/xml;charset=utf-8'
    }

    with open('private/sql/relatorios/inconsistencias.sql', encoding='utf-8') as f:
        inconsistencias_sql = f.read()

    with open('private/sql/relatorios/fases.sql', encoding='utf-8') as f:
        fases_sql = f.read()

    def create_branch(self, keys, values, item_name):
            item = ET.Element(item_name)
            for key, value in zip(keys, values):
                field = ET.Element(key)
                field.text = value
                item.append(field)
            return item

    def to_treat(self, elem):
        if elem:
            if isinstance(elem, int):
                return str(elem)
            elif isinstance(elem, float):
                return locale.format_string('%.2f', elem).strip()
            elif isinstance(elem, str):
                return re.sub('[\n\t\r;]', '', elem)
            else:
                return elem
        else:
            return '-'

    @cherrypy.tools.gzip(compress_level=3, mime_types=['text/plain',
                                        'application/json', 'application/xml'])
    @cherrypy.expose
    def index(self, dado='indicador', fonte='todos', cod_fonte='todos',
                                                download='nao', formato='csv'):

        default_dict_sql = {'ANO': ANO_CORRENTE, 'FASE': FASE}
        l_cod_fonte = 0
        hora_ext = time.strftime('%H-%M_%d-%m-%Y', time.localtime())
        # sanity checkings
        if fonte not in ('programa', 'produto', 'indicador', 'orgao', 'todos'):
            return 'Erro no pedido: %s não é uma fonte válida.' % fonte
        if formato not in ('csv', 'tab', 'json', 'xml'):
            return 'Erro no pedido: %s não é um formato válido.' % formato
        if fonte == 'todos' and cod_fonte != 'todos':
            return 'Erro no pedido: especifique uma fonte para o filtro'
        fonte = self.dict_fonte[fonte]

        if cod_fonte != 'todos':
            cod_fonte = cod_fonte.split()
            for cod in cod_fonte:
                if not cod.isdigit():
                    return 'Erro no pedido: %s não é um código válido.' % cod
            l_cod_fonte = len(cod_fonte)

        if dado in 'indicador':
            if cod_fonte != 'todos':
                sql_filter = ' AND\n\tEPPA_INDICADORES.%s IN (%s)' % (fonte,
                            ','.join(':cod%d' % n for n in range(l_cod_fonte)))
            else:
                sql_filter = ''


            with open('private/sql/webservice/indicadores.sql') as sql_file:
                sql_script = sql_file.read() + sql_filter


        elif dado == 'produto':
            if fonte == 'SEQ_INDIC':
                return 'Erro no pedido: só é possível o filtro de produto por órgãos, programas ou produtos.'
            if cod_fonte != 'todos':
                sql_filter = ' AND\n\tEPPA_PRODUTOS.%s IN (%s)' % (fonte,
                            ','.join(':cod%d' % n for n in range(l_cod_fonte)))
            else:
                sql_filter = ''

            with open('private/sql/webservice/produtos.sql') as sql_file:
                sql_script = sql_file.read() + sql_filter

        elif dado == 'programa':
            if fonte in ('SEQ_INDIC', 'SEQ_PRODUTO'):
                return 'Erro no pedido: só é possível o filtro de programa por órgãos ou programas.'
            if cod_fonte != 'todos':
                sql_filter = ' AND\n\tEPA_PGM_ORG.%s IN (%s)' % (fonte,
                            ','.join(':cod%d' % n for n in range(l_cod_fonte)))
                with open('private/sql/webservice/programas_filtro_orgaos.sql') as sql_file:
                    sql_script = sql_file.read() + sql_filter
            else:
                with open('private/sql/webservice/programas.sql') as sql_file:
                    sql_script = sql_file.read()

        elif dado == 'inconsistencias':
            if cod_fonte != 'todos':
                if fonte == 'COD_ORG':
                    fonte = 'EPA_PGM_ORG.COD_ORG'
                elif fonte == 'SEQ_PGM':
                    fonte = 'EPA_PROGRAMAS.SEQ_PGM'
                sql_filter = 'WHERE %s IN (%s)' % (
                            fonte,
                            ','.join(':cod%d' % n for n in range(l_cod_fonte)))
            else:
                sql_filter = ''
            sql_script = self.inconsistencias_sql % sql_filter

        elif dado == 'fases':
            default_dict_sql = {}
            if cod_fonte != 'todos':
                if fonte == 'COD_ORG':
                    fonte = 'ORGAOS.COD_ORG'
                elif fonte == 'SEQ_PGM':
                    fonte = 'EPA_PROGRAMAS.SEQ_PGM'
                elif fonte == 'SEQ_PRODUTO':
                    fonte = 'EPPA_PRODUTOS.SEQ_PRODUTO'
                sql_filter = 'AND %s IN (%s)' % (
                            fonte,
                            ','.join(':cod%d' % n for n in range(l_cod_fonte)))
            else:
                sql_filter = ''
            sql_script = self.fases_sql % sql_filter

        default_dict_sql.update({'cod%d' % n:cod_fonte[n] for n in range(l_cod_fonte)})
        c = conn_list[cherrypy.thread_data.db_i].cursor()
        c.execute(sql_script, default_dict_sql)
        variable_names = (re.sub('[\s-]', '', head) for head, *_ in c.description)
        rows = ((self.to_treat(element) for element in row) for row in c)

        if not rows:
            return 'Não foi possível encontrar resultados para a busca!'

        headers = cherrypy.response.headers

        headers['Content-Type'] = self.mime_types[formato]
        if download == 'sim':
            headers['Content-Disposition'] = self.filetype % (dado, hora_ext, formato)
            if formato == 'csv':
                headers['Content-Type'] = 'text/csv;charset=windows-1252'
            elif formato == 'tab':
                headers['Content-Type'] = 'text/tab-separated-values;charset=windows-1252'

        if formato in ('csv', 'tab'):
            delimiter = ';' if formato == 'csv' else '\t'
            head = delimiter.join(variable_names) + '\n'
            body = '\n'.join(delimiter.join(elem for elem in row) for row in rows)
            body += '\nExtração realizada em ' + hora_ext
            output = head + body
            if download == 'sim':
                encode = 'windows-1252'
            else:
                encode = 'utf-8'
            output = output.encode(encode)

        elif formato == 'json':
            rows = [{key:value for key, value in zip(variable_names, row)} for row in rows]
            output = bytes(json.dumps(rows), 'utf-8')

        # https://pymotw.com/2/xml/etree/ElementTree/create.html
        elif formato == 'xml':
            root = ET.Element(dado)
            root.set('versão', '0.1a')
            root.append(ET.Comment('Gerado pelo webservice do SimPPA'))
            for row in rows:
                root.append(self.create_branch(variable_names, row, dado))
            output = b"<?xml version='1.0' encoding='utf-8'?>" + ET.tostring(root, 'utf-8')

        # elif tipo == 'rdf':
            # TODO
            # headers['Content-Type']= 'application/rdf+xml'
            # headers['Content-Disposition'] = filetype % 'rdf'

        c.close()
        return output

    @cherrypy.expose(['documentacao', 'doc'])
    def docs(self):
        return f'Documentação do webservice PPA {ANO_PPA}'

    # @cherrypy.expose
    # def relatorios(self, tipo):
    #     c = cherrypy.thread_data.db.cursor()
    #     c.execute(self.inconsistencias_sql)
    #     variable_names = (head for head, *_ in c.description)
    #     rows = ((self.to_treat(element) for element in row) for row in c)
    #     head = ';'.join(variable_names) + '\n'
    #     body = '\n'.join(';'.join(elem for elem in row) for row in rows)
    #     output = head + body
    #     c.close()
    #     headers = cherrypy.response.headers
    #     headers['Content-Type'] = 'text/csv;charset=windows-1252'
    #     headers['Content-Disposition'] = self.filetype % ('inconsistências', '.csv')
    #     return output.encode('windows-1252')


# cherrypy.server.socket_host = '0.0.0.0'
# cherrypy.server.socket_port = 80
cherrypy.server.socket_port = 8080


# fecha explicitamente as conexões ao sair do webapp
@atexit.register
def close_connections():
    for conn in conn_list:
        try:
            conn.close()
        except cx_Oracle.InterfaceError:
            continue
# https://oracle.github.io/odpi/doc/installation.html#linux -- corrige problemas com wsgi apache e oracle

# cherrypy.config.update({'environment': 'production'})
webapp = simPPA()
cherrypy.quickstart(webapp, '', config)
# application = cherrypy.Application(webapp, '', config)
