import os
import datetime
import cx_Oracle
from collections import defaultdict, OrderedDict
from glob import glob
import re


ANO_CORRENTE = datetime.datetime.now().year
DIA = datetime.datetime.now().day


def f_strip(s):
    return s.strip().replace('\n', '').replace('\r', '').replace('"', "'")

def indicador(ano, fase):

    SQL = \
    """SELECT EPPA_INDICADORES.SEQ_INDIC as "Sequência do Indicador",
              EPPA_INDICADORES.NOME as "Nome do Indicador"
       FROM EPPA_INDICADORES
       WHERE EPPA_INDICADORES.ANO =:ano AND
             EPPA_INDICADORES.FASE =:fase
       ORDER BY EPPA_INDICADORES.SEQ_INDIC"""


    cursor = conn.cursor()
    cursor.execute(SQL, ano=ano, fase=fase)

    data = ['var indicador = {']
    data_tmp = []
    for seq_indic, nome_indic in cursor:
        nome_indic = f_strip(nome_indic)
        data_tmp.append('%s:"%-4s - %s"' %   (seq_indic, seq_indic, nome_indic))

    data.append(','.join(data_tmp))
    data.append('};\n')

    cursor.close()

    return ''.join(data)

def obj_estrategico(ano, fase):
    '''Já formatado para a biblioteca Select2'''

    SQL = \
    '''SELECT EPPA_IMPACTOS.NOME as "Nome do Objetivo Estratégico",
              EPPA_IMPACTOS.SEQ_IMPACTO as "Sequencial do Obj Estratégico"
       FROM EPPA_IMPACTOS
       WHERE EPPA_IMPACTOS.ANO =:ano AND
             EPPA_IMPACTOS.FASE =:fase'''

    cursor = conn.cursor()
    cursor.execute(SQL, ano=ano, fase=fase)

    data = ['var data_obj_estrategico_todos = ["", {id:-1, text: "Todos os Objetivos Estratégicos"},']
    data_tmp = []

    for nome_impacto, seq_impacto in cursor:
        nome_impacto = f_strip(nome_impacto)
        data_tmp.append('{id:%s,text:"%s"}' % (seq_impacto, nome_impacto))

    data.append(','.join(data_tmp))
    data.append('];\n')

    cursor.close()

    return ''.join(data)

def produto(ano, fase):
    '''Conecta os produtos aos indicadores de produto'''

    SQL = \
    """SELECT EPPA_PRODUTOS.SEQ_PRODUTO as "Sequência do Produto",
              EPPA_PRODUTOS.NOME as "Nome do Produto",
              LISTAGG(EPPA_INDICADORES.SEQ_INDIC, ', ') WITHIN GROUP (ORDER BY EPPA_INDICADORES.SEQ_INDIC) "Seq_indics"
       FROM EPPA_PRODUTOS
       LEFT OUTER JOIN EPPA_INDICADORES
         ON EPPA_PRODUTOS.SEQ_PRODUTO = EPPA_INDICADORES.SEQ_PRODUTO AND
            EPPA_INDICADORES.ANO = EPPA_PRODUTOS.ANO AND
            EPPA_INDICADORES.FASE = EPPA_PRODUTOS.FASE AND
            EPPA_INDICADORES.CATEGORIA = 'T'
       WHERE EPPA_PRODUTOS.ANO =:ano AND
             EPPA_PRODUTOS.FASE =:fase
       GROUP BY EPPA_PRODUTOS.SEQ_PRODUTO, EPPA_PRODUTOS.NOME
       ORDER BY EPPA_PRODUTOS.SEQ_PRODUTO"""

    cursor = conn.cursor()
    cursor.execute(SQL, ano=ano, fase=fase)

    pdt_indic = defaultdict(list)
    pdt_nome = OrderedDict()
    template = '%s:{nome:"%-4s - %s",id_indic:%s}'
    data = ['var produto = {']
    data_tmp = []

    for seq_pdt, nome_pdt, seq_indics in cursor:
        nome_pdt = f_strip(nome_pdt)
        seq_indics = list({int(n) for n in seq_indics.split(',')}) if seq_indics else []
        row = template % (seq_pdt, seq_pdt, nome_pdt, seq_indics)
        data_tmp.append(row)

    data.append(','.join(data_tmp))
    data.append('};\n')

    cursor.close

    return ''.join(data)

def programa_pdt_indicador(ano, fase):
    '''Conecta os programas aos seus produtos e aos indicadores de resultado'''

    SQL_PRODUTOS = \
    """SELECT EPA_PROGRAMAS.SEQ_PGM as "Sequência do Programa",
       EPA_PROGRAMAS.COD_PGM as "Código do Programa",
       EPA_PROGRAMAS.NOME as "Nome do Programa",
       LISTAGG(EPPA_INDICADORES.SEQ_INDIC, ', ') WITHIN GROUP (ORDER BY EPPA_INDICADORES.SEQ_INDIC) "Seq_indics",
       LISTAGG(EPPA_PRODUTOS.SEQ_PRODUTO, ', ') WITHIN GROUP (ORDER BY EPPA_PRODUTOS.SEQ_PRODUTO) "Seq_pdts"
       FROM EPA_PROGRAMAS
       LEFT OUTER JOIN EPPA_INDICADORES
         ON EPA_PROGRAMAS.SEQ_PGM = EPPA_INDICADORES.SEQ_PGM AND
            EPPA_INDICADORES.ANO = EPA_PROGRAMAS.ANO AND
            EPPA_INDICADORES.FASE = EPA_PROGRAMAS.FASE AND
            EPPA_INDICADORES.CATEGORIA = 'P'
       LEFT OUTER JOIN EPPA_PRODUTOS
         ON EPA_PROGRAMAS.SEQ_PGM =  EPPA_PRODUTOS.SEQ_PGM AND
            EPPA_PRODUTOS.ANO = EPA_PROGRAMAS.ANO AND
            EPPA_PRODUTOS.FASE = EPA_PROGRAMAS.FASE
       WHERE EPA_PROGRAMAS.ANO =:ano AND
             EPA_PROGRAMAS.FASE =:fase
       GROUP BY EPA_PROGRAMAS.SEQ_PGM, EPA_PROGRAMAS.COD_PGM, EPA_PROGRAMAS.NOME
       ORDER BY EPA_PROGRAMAS.COD_PGM"""

    data = ['var programa = {']
    data_tmp = []

    cursor = conn.cursor()
    cursor.execute(SQL_PRODUTOS, ano=ano, fase=fase)
    template = '%s:{id:%s, nome:"%-4s - %s",id_pdt:%s,id_indic:%s}'
    for seq_pgm, cod_pgm, nome_pgm, seq_indics, seq_pdts in cursor:
        seq_indics = list({int(n) for n in seq_indics.split(',')}) if seq_indics else []
        seq_pdts = list({int(n) for n in seq_pdts.split(',')}) if seq_pdts else []
        data_tmp.append(template % (cod_pgm, seq_pgm, cod_pgm, nome_pgm, seq_pdts, seq_indics))

    data.append(','.join(data_tmp))
    data.append('};\n')

    return ''.join(data)

def orgao_programa(ano, fase):
    SQL_PROGRAMAS =\
    '''SELECT EPA_PROGRAMAS.SEQ_PGM as "Sequência do Programa",
              EPA_PROGRAMAS.NOME as "Nome do Programa",
              EPA_PROGRAMAS.COD_PGM as "Código do Programa"
       FROM EPA_PROGRAMAS
       WHERE EPA_PROGRAMAS.ANO =:ano AND
              EPA_PROGRAMAS.FASE =:fase
       ORDER BY EPA_PROGRAMAS.COD_PGM'''

    SQL_PRODUTOS =\
    '''SELECT EPA_PROGRAMAS.SEQ_PGM as "Sequência do Programa",
              EPA_PROGRAMAS.COD_PGM as "Código do Programa",
              EPA_PROGRAMAS.NOME as "Nome do Programa",
              EPPA_PRODUTOS.SEQ_PRODUTO as "Sequência do Produto",
              EPPA_PRODUTOS.COD_ORG as "Código do Órgão"
       FROM EPPA_PRODUTOS
        LEFT OUTER JOIN EPA_PROGRAMAS
          ON EPPA_PRODUTOS.SEQ_PGM = EPA_PROGRAMAS.SEQ_PGM AND
             EPA_PROGRAMAS.ANO = EPPA_PRODUTOS.ANO AND
             EPA_PROGRAMAS.FASE = EPPA_PRODUTOS.FASE
       WHERE EPPA_PRODUTOS.ANO =:ano AND
            EPPA_PRODUTOS.FASE =:fase
       ORDER BY EPA_PROGRAMAS.COD_PGM'''

    SQL_INDICADORES =\
    '''SELECT EPA_PROGRAMAS.SEQ_PGM as "Sequência do Programa",
              EPPA_INDICADORES.SEQ_INDIC as "Sequência do Indicador",
              EPA_PGM_ORG.COD_ORG as "Código do Órgão"
       FROM EPA_PROGRAMAS
       LEFT OUTER JOIN EPPA_INDICADORES
         ON EPA_PROGRAMAS.SEQ_PGM = EPPA_INDICADORES.SEQ_PGM AND
            EPPA_INDICADORES.ANO =:ano AND
            EPPA_INDICADORES.FASE =:fase AND
            EPPA_INDICADORES.CATEGORIA = 'P'
       LEFT OUTER JOIN EPA_PGM_ORG
         ON EPA_PROGRAMAS.SEQ_PGM = EPA_PGM_ORG.SEQ_PGM AND
            EPA_PGM_ORG.ANO =:ano AND
            EPA_PGM_ORG.FASE =:fase
       WHERE EPA_PROGRAMAS.ANO =:ano AND
             EPA_PROGRAMAS.FASE =:fase
       ORDER BY EPA_PROGRAMAS.COD_PGM'''


    cursor = conn.cursor()

    cursor.execute(SQL_PROGRAMAS, ano=ano, fase=fase)
    data_programas = cursor.fetchall()

    cursor.execute(SQL_PRODUTOS, ano=ano, fase=fase)
    data_produtos = cursor.fetchall()

    cursor.execute(SQL_INDICADORES, ano=ano, fase=fase)
    data_indicadores = cursor.fetchall()

    org_pgm = defaultdict(dict)
    pgm_nome = { }
    data = ['var orgaos_pgms = {']
    data_tmp = []

    for seq_pgm, *_, cod_org in data_produtos:
        org_pgm[cod_org][seq_pgm] = [[],[]]

    for seq_pgm, _, cod_org in data_indicadores:
        org_pgm[cod_org][seq_pgm] = [[],[]]

    for seq_pgm, *_, seq_pdt, cod_org in data_produtos:
        org_pgm[cod_org][seq_pgm][0].append(seq_pdt)

    for seq_pgm, seq_indic, cod_org in data_indicadores:
        org_pgm[cod_org][seq_pgm][1].append(seq_indic)

    for cod_org in org_pgm:
        for seq_pgm in org_pgm[cod_org]:
            org_pgm[cod_org][seq_pgm][0].sort()
            org_pgm[cod_org][seq_pgm][1].sort()
    for seq_pgm, nome_pgm, cod_pgm in data_programas:
        pgm_nome[seq_pgm] = (nome_pgm, cod_pgm)

    orgs = sorted(org_pgm.keys())
    for cod_org in orgs:
        pgms = [(seq_pgm, pgm_nome[seq_pgm]) for seq_pgm in org_pgm[cod_org]]
        pgms.sort(key=lambda x: x[1][1])
        data_tmp.append('%s:{%s}' %
       (
        cod_org,
        ','.join(['%s:{id:%s, nome:"%-4s - %s",id_pdt:%s,id_indic:%s}' % (cod_pgm, seq_pgm, cod_pgm, nome_pgm,
        org_pgm[cod_org][seq_pgm][0], org_pgm[cod_org][seq_pgm][1] if org_pgm[cod_org][seq_pgm][1] else "")
        for seq_pgm, (nome_pgm, cod_pgm) in pgms])
        ))


    data.append(','.join(data_tmp))
    data.append('};\n')
    return ''.join(data)

def orgao(ano, fase):
    SQL =\
    '''SELECT EPA_PGM_ORG.SEQ_PGM as "Sequência do Programa",
              EPA_PROGRAMAS.COD_PGM as "Código do Programa",
              EPA_PGM_ORG.COD_ORG as "Código do Órgão",
              ORGAOS.NOME as "Nome do Órgão"
       FROM EPA_PGM_ORG
       LEFT OUTER JOIN ORGAOS
         ON EPA_PGM_ORG.COD_ORG = ORGAOS.COD_ORG
       LEFT OUTER JOIN EPA_PROGRAMAS
         ON EPA_PGM_ORG.SEQ_PGM = EPA_PROGRAMAS.SEQ_PGM AND
            EPA_PROGRAMAS.ANO =:ano AND
            EPA_PROGRAMAS.FASE =:fase
       WHERE EPA_PGM_ORG.ANO =:ano AND
              EPA_PGM_ORG.FASE =:fase AND
              EPA_PGM_ORG.COD_ORG != 99000
       ORDER BY EPA_PGM_ORG.COD_ORG'''

    cursor = conn.cursor()
    cursor.execute(SQL, ano=ano, fase=fase)

    org_pgm = defaultdict(list)
    org_nome = OrderedDict()
    data = ['var orgao = {']
    template = '%s:{nome:"%-5s - %s",id_pgm:%s}'
    data_tmp =[]

    for seq_pgm, cod_pgm, cod_org, nome_org in cursor:
        org_pgm[cod_org].append([seq_pgm, cod_pgm])
        org_nome[cod_org] = nome_org

    cursor.close()

    for cod_org in org_nome:
        nome_org = org_nome[cod_org]
        pgms = org_pgm[cod_org]
        pgms.sort(key=lambda x: x[1])
        seq_pgms = list(list(zip(*pgms))[0])
        data_tmp.append(template % (cod_org, cod_org, nome_org, seq_pgms))

    data.append(','.join(data_tmp))
    data.append('};\n')

    return ''.join(data)


if DIA == 30:

    os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.UTF8'
    ano = ANO_CORRENTE
    fase = 34
    with open('private/user.txt') as f:
        user_conn = f.read().strip()
    conn = cx_Oracle.connect(user_conn)

    indicadores = indicador(ano, fase)
    produtos = produto(ano, fase)
    programas = programa_pdt_indicador(ano, fase)
    orgaos_programas = orgao_programa(ano, fase)
    orgaos = orgao(ano, fase)
    obj_estrategicos = obj_estrategico(ano, fase)

    conn.close()

    filename = glob('public/js/simppa-dados-v*')[0]
    num = int(re.findall('\d+', filename)[0]) + 1
    print(num)

    with open('public/js/simppa-dados-v%d.js' % num, 'w', encoding='utf-8') as f:
        f.write(indicadores.replace('None', ''))
        f.write(produtos.replace('None', ''))
        f.write(programas.replace('None', ''))
        f.write(orgaos_programas.replace('None', ''))
        f.write(orgaos.replace('None', ''))
        f.write(obj_estrategicos.replace('None', ''))

    # with open('private/html/index.html', 'r', encoding='utf-8') as f:
    #     html_url = f.read() % num
