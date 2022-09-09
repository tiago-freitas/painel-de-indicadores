###############################################################################
# @Author: Tiago Barreiros de Freitas
# @Contact: tb.freitas@uol.com.br
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

import random
import locale
import datetime
import functools
import platform

import pandas as pd
import numpy as np

if platform.system() == 'Linux':
    locale.setlocale(locale.LC_NUMERIC, ('pt_BR', 'UTF-8'))
else:
    locale.setlocale(locale.LC_NUMERIC, 'Portuguese_Brazil.1252') #para windows

NA = 'ND'
ND = 'ND'
VAZIO = ''
ANO_PPA = 2016
FASES = {'lei PPA/LDO': 2, 'lei LOA': 7}

cores_despesa = ('y', 'y', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', ' ')




template_despesa = '''\
            <table class="despesa">
              <colgroup />
              <colgroup span="2" title="Previsão de despesa">
              <thead>
                <tr>
                 <th class="table-titulo" colspan="12">Programação Detalhada dos Recursos %s do Programa por Órgão</th>
                </tr>
               <tr>
                 <th>%s</th>
                 <th colspan="5" class='y'>Correntes</th>
                 <th colspan="5" class='r'>Capital</th>
                 <th rowspan="2">Total Geral</th>
               </tr>
               <tr>
                 <th></th>
                 <th class='y'>{ano1}</th>
                 <th class='y'>{ano2}</th>
                 <th class='y'>{ano3}</th>
                 <th class='y'>{ano4}</th>
                 <th class='y'>Total</th>
                 <th class='r'>{ano1}</th>
                 <th class='r'>{ano2}</th>
                 <th class='r'>{ano3}</th>
                 <th class='r'>{ano4}</th>
                 <th class='r'>Total</th>
               </tr>
              </thead>
              <tbody>'''.format(ano1=ANO_PPA, ano2=ANO_PPA+1, ano3=ANO_PPA+2, ano4=ANO_PPA+3)

template_despesa_geral = '''\
            <table id="despesa-geral" class="despesa">
              <thead>
               <tr>
                 <th class="table-titulo" colspan="5">Programação Total dos Recursos do Programa</th>
               </tr>
               <tr>
                 <th>{ano1}</th>
                 <th>{ano2}</th>
                 <th>{ano3}</th>
                 <th>{ano4}</th>
                 <th>Total</th>
               </tr>
              </thead>
              <tbody>\n<tr>'''.format(ano1=ANO_PPA, ano2=ANO_PPA+1, ano3=ANO_PPA+2, ano4=ANO_PPA+3)

orcamentos_nomes = ('Tesouro', 'Vinculados', 'Próprios',
                        'Operação de Crédito', 'Total')

nao_orcamento_nomes = ('Municípios', 'Privados', 'Próprios',
                          'Operação de Crédito','Total')

template_lista_orgaos = '''\
<li class="itens_select despesa_menu o{0} {1}" onclick="despesa_orgao({0})" style="position:relative">
<span data-hint="{2}" class="hint-top">{0}</span>
</li>\n'''

def despesa_tabela(orcamento, nao_orcamento, geral):

    table = ['<ul style="list-style-type: none;margin: 5px;text-align: center;">\n']
    table_geral = []
    despesa_geral = {}
    for i, orgao in enumerate(orcamento):
        cod_org = orgao[0]
        nome_org = orgao[1]
        table.append(template_lista_orgaos.format(cod_org, "inativo" if i else "ativo", nome_org))

    table.append('</ul>\n')
    table.append('<script>atual_cod_org = %d;</script>' % orcamento[0][0])

    display = 'block'
    for orc, nao_orc, geral in zip(orcamento, nao_orcamento, geral):
        table.append('<div id="o%d" style="display:%s">\n' % (orc[0], display))
        display = 'none'
        # tabela recursos orçamentários
        table.append(template_despesa % ('Orçamentários', 'Orçamentários'))
        i, n, j = 0, 0, 0
        for e in orc[2:-5]:
            if i % 12 == 0:
                table.append('<tr><td>%s</td>' % orcamentos_nomes[n])
                i += 1
                n += 1
            table.append('<td class="%c">%s</td>' % (
                cores_despesa[j % 11], formato_br_d(e)))
            j += 1
            i += 1
            if i % 12 == 0 and i != 0:
                table.append('</tr>\n')
        table.append('</tbody>\n</table>\n')

        # tabela recursos não orçamentários
        table.append(template_despesa % ('Não Orçamentários', 'Não Orçamentários'))
        i, n, j = 0, 0, 0
        for e in nao_orc:
            if i % 12 == 0:
                table.append('<tr><td>%s</td>' % nao_orcamento_nomes[n])
                i += 1
                n += 1
            table.append('<td class="%c">%s</td>' % (
                cores_despesa[j % 11], formato_br_d(e)))
            j += 1
            i += 1
            if i % 12 == 0 and i != 0:
                        table.append('</tr>\n')
        table.append('</tbody>\n</table>\n')

        table.append('</div>\n')

        for ano, e in enumerate(geral, ANO_PPA):
            e = e if e else 0
            despesa_geral[ano] = despesa_geral.get(ano, 0) + e

    table.append(template_despesa_geral)

    for ano in despesa_geral:
        table.append('<td>%s</td>\n' % formato_br_d(despesa_geral[ano]))
    table.append('</tr>\n</tbody>\n</table>\n')

    return ''.join(table)

def taxa_format(n):
    if pd.isnull(n):
        return ND
    if isinstance(n, str):
        return '-'
    if n is not None:
        if n != -1:
            return locale.format('%.2f', n * 100, grouping=True) + '%'
        else:
            return NA
    else:
        return '0,00%'

def formato_br_old(n):
    if isinstance(n, str):
        return '-'
    if n is not None:
        return locale.format('%.2f', n, grouping=True)
    else:
        return 0

def formato_br(n):
    if pd.isnull(n):
        return ND
    if n is not None or isinstance(n, str):
        if n < 1e6:
            if isinstance(n, int) or n.is_integer():
                formato = '%d'
            else:
                formato = '%.2f'
            return locale.format(formato, n, grouping=True)
        else:
            n /= 1e6
            return locale.format('%.2f', n, grouping=True) + 'mi'
    else:
        return ND

def formato_br_d(n):
    if n is not None:
        return locale.format('%d', n, grouping=True)
    else:
        return 0

def is_none(n):
    if n is None:
        return 'null'
    return n

template_pgms_link = ('<td class="link-handler">%s</td><td>%s</td>'
                      '<td class="number_row">%s</td>'
                      '<td class="number_row">%s</td>')
template_pgms_not_link = ('<td>%s</td><td>%s</td>'
                          '<td class="number_row">%s</td>'
                          '<td class="number_row">%s</td>')

def fazer_tabelas_anos(cursor,
                       conn,
                       taxas_1,
                       taxas_2,
                       ANO_PROJETO_PPA,
                       ANO_CORRENTE,
                       mes,
                       sql,
                       template,
                       table_template,
                       codigo=None,
                       FASE=None):

    head = (
    '<select id="sel_ano" class="form-control" '
    'style="width:125px;margin:auto;">'
    '<option selected value=%d>%d</option>' % (ANO_CORRENTE - ANO_PROJETO_PPA, ANO_CORRENTE)
    )

    for ano in range(ANO_CORRENTE - 1, ANO_PROJETO_PPA, -1):
        head += '<option value="%d">%d</option>' % (ano - ANO_PROJETO_PPA, ano)


    head += '</select>'

    if codigo is None:
        head += '<p style="text-align: right;margin: 0">Em R$ milhões</p>'
    else:
        head += '<p style="text-align: right;margin: 0">Em R$ mil</p>'

    script = (
        '\n<script>'
        '$("#sel_ano").change(hide_show_table);'
        'hide_show_table();'
    '</script>\n'
    )

    tabelas = ''
    apenso_tabelas = []
    for ano in range(ANO_PROJETO_PPA + 1, ANO_CORRENTE + 1):
    # obter órgãos do Estado de São Paulo
        args = {'ano': ano, 'mes': mes}
        if ano != ANO_CORRENTE:
            args['mes'] = 12
        if codigo is not None:
            args['fase'] = FASE
            args['cod_org'] = codigo
            df_tmp = pd.DataFrame(cursor.execute(sql, **args).fetchall())
            df_tmp['ano'] = ano
            apenso_tabelas.append(df_tmp)
        else:
            apenso_tabelas.append(cursor.execute(sql, **args).fetchall())
            # apenso_tabelas.append(cursor.execute(sql).fetchall())

    if codigo is not None:
        # apenso_tabelas[0] = apenso_tabelas[0][apenso_tabelas[0][2] != 1021]
        df_pgms_anos = (pd.concat(apenso_tabelas, ignore_index=True)
                          .set_index([2, 'ano'])
                          .unstack())

        inc_exc_series =  pd.DataFrame(data=np.nan,
                                       index=df_pgms_anos.index,
                                       columns=['incluido',
                                                'excluido',
                                                'i_ctl',
                                                'e_ctl'])

        for ano in range(ANO_PPA, ANO_CORRENTE + 1):
            inc_exc_series.loc[df_pgms_anos[(0, ano)].notnull() &
                               inc_exc_series['i_ctl'].isnull(),
                              ['incluido', 'i_ctl', 'e_ctl']] = ano, ano, np.nan

            inc_exc_series.loc[df_pgms_anos[(0, ano)].isnull() &
                               inc_exc_series['e_ctl'].isnull(),
                              ['i_ctl', 'excluido', 'e_ctl']] = np.nan, ano, ano

        df_pgms_anos = pd.concat([df_pgms_anos.stack().reset_index('ano'),
                                  inc_exc_series], axis=1)

    for ano in range(ANO_PPA, ANO_CORRENTE + 1):
        KEYS_AGG_TMP = (ano - ANO_PROJETO_PPA, 'total')
        membros_lista = []

        if codigo is None:
            for i, (cod, nome, *orc) in enumerate(apenso_tabelas[ano - ANO_PPA]):
                if i == 0:
                    row = ['<td>%s</td>' % nome]
                    for key in KEYS_AGG_TMP:
                        row.append(taxas_1.get(key, 0))
                else:
                    row = ['<td class="link-handler">' + template % (cod, nome) + '</td>']
                    for key in KEYS_AGG_TMP:
                        row.append(taxas_2[key].get(cod, 0))

                row.extend(orc)
                membros_lista.append(row)

        else:
            df_pgms_ano = (df_pgms_anos[(df_pgms_anos['ano'] == ano) |
                                         (df_pgms_anos['e_ctl'].notnull() &
                                          (df_pgms_anos['incluido'] < ano))]
                               .drop_duplicates(subset=1)
                               .reset_index()
                               .sort_values(by=[0, 2]))
            for i, (_, (cod, _, _, seq, nome, classificacao,
                 *orc, incluido, excluido, i_ctl, e_ctl)) in enumerate(df_pgms_ano.iterrows()):

                is_active = True
                if not np.isnan(e_ctl):
                    is_active = False


                inc = tratar_i_e(incluido)
                exc = tratar_i_e(excluido)

                if i == 0:
                    row = [template_pgms_not_link %
                           (nome, classificacao, inc, exc)]
                    for key in KEYS_AGG_TMP:
                        row.append(taxas_1[key].get(cod, 0))

                else:
                    if is_active:
                        row = [template_pgms_link %
                               (template % (cod, nome), classificacao, inc, exc)]
                    else:
                        row = [template_pgms_not_link %
                               (template % (cod, nome), classificacao, inc, exc)]
                    for key in KEYS_AGG_TMP:
                        row.append(taxas_2[key].get(seq, 0))

                row.extend(orc)
                membros_lista.append(row)

        rows = []
        row = membros_lista[0]

        rows = ['<tr style="font-weight:bold">\n' + row[0]] # nome e tlz classificação
        rows.append('<td class="number_row">%s</td>' % taxa_format(row[1]))
        rows.append('<td class="number_row" style="border-right: 3px black solid;">%s</td>'
                                          % taxa_format(row[2]))
        for elem in row[3:-1]:
            rows.append('<td class="number_row">%s</td>' % formato_br_old(elem))
        rows.append('<td class="number_row">%s</td></tr>' % taxa_format(row[-1]))


        for row in membros_lista[1:]:
            rows.append('<tr>\n' + row[0]) # nome
            rows.append('<td class="number_row">%s</td>' % taxa_format(row[1]))
            rows.append('<td class="number_row" style="border-right: 3px black solid;">%s</td>'
                                          % taxa_format(row[2]))
            for elem in row[3:-1]:
                rows.append('<td class="number_row">%s</td>' % formato_br_old(elem))
            rows.append('<td class="number_row">%s</td></tr>' % taxa_format(row[-1]))


        tabelas += (table_template.format(ano_id=ano-(ANO_PPA-1), ano=ano) +
                   '\n'.join(rows) +
                   '</tbody></table>')

    return head + tabelas + script

from collections import namedtuple

def fazer_tabelas_acoes(conn, params):
    row_acao = namedtuple('acao', 'cod_acao finalidade descricao produto formas_implementacao')
    sql = '''
SELECT TRUNC(COD_ACAO),
       FINALIDADE,
       DESCRICAO,
       PRODUTO,
       FORMAS_IMPLEMENTACAO
FROM EPA_ACOES
WHERE ANO =:ano AND
      FASE =:fase AND
      SEQ_ACAO in (%s)''' % ','.join(":x%d" % seq_acao for seq_acao in params['seq_acoes'])


    params.update({"x%d" % seq_acao:seq_acao for seq_acao in params['seq_acoes']})
    del params['seq_acoes']
    cursor = conn.cursor()
    cursor.execute(sql, params)

    with open('private/html/acoes/acao.html') as f:
        html_template  = f.read()

  
    html = [html_template.format(**row_acao(*r)._asdict()) for r in cursor]
    cursor.close()

    return ''.join(html)

format_pt_br = functools.partial(locale.format_string, f='%.2f', grouping=True)

def validador_metas(metas, ano_criacao):
    metas_2 = []
    for i, m in enumerate(metas):
        if isinstance(m, str):
            metas_2.append(NA)
        elif i >= ano_criacao - ANO_PPA:
            metas_2.append(formato_br(m))
        else:
            metas_2.append(NA)
    return metas_2

def tratar_i_e(n):
    if np.isnan(n) or n == ANO_PPA:
        return '-'
    else:
        return int(n)
