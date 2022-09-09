import os
from collections import defaultdict, namedtuple
import datetime
import pandas as pd
from helper import FASES, ANO_PPA
import cx_Oracle


with open('private/user.txt') as f:
    conn_user = f.read().strip()


# os.chdir('/var/www/painelPPA')
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8"
LIMITE_MAX = 1
LIMITE_MIN = 0
KEYS_AGG = (1, 2, 3, 4, 'total')
ANO_PROJETO_PPA = ANO_PPA - 1

metas_ppa = { }
metas_recentes = { }

indicadores_ppa = { }
indicadores_recente = { }

pdt_ppa = { }
pdt_recente = { }

pgm_pdt_ppa = { }
pgm_pdt_recente = { }
pgm_resultado_ppa = { }
pgm_resultado_recente = { }
pgm_geral_ppa = { }
pgm_geral_recente = { }

pgm_has_resultado = { }
pgm_has_produto = { }

orgao_ppa = { }
orgao_recente = { }

for agregado in [metas_ppa, metas_recentes, indicadores_ppa, indicadores_recente,
                 pdt_ppa, pdt_recente, pgm_pdt_ppa, pgm_pdt_recente,
                 pgm_resultado_ppa, pgm_resultado_recente, pgm_geral_ppa,
                 pgm_geral_recente, orgao_ppa, orgao_recente]:
    for key in KEYS_AGG:
        agregado[key] = { }

ESP_ppa = { }
ESP_recente = { }

periodicidades_dict = {'A': 1,
                       'S': 2,
                       'Q': 3,
                       'T': 4,
                       'B': 6,
                       'M': 12}

############################## sql ############################################

_PATH = 'indicadores-apuracao/sql/'

# metas
with open(_PATH + 'metas_PPA_todos_indicadores.sql') as f:
    _sql_metas_ppa = f.read()
with open(_PATH + 'metas_recentes_todos_indicadores.sql') as f:
    _sql_metas_recentes = f.read()

# meta aos indicadores de produto definidas pela LOA 2018
# meta_indicador_2018_produto = pd.read_csv('private/db/meta_loa_indic.csv',
#                                           delimiter='\t',
#                                           decimal='.',
#                                           index_col='CD_INDICADOR_PRODUTO')

# meta_acao_2018_produto = pd.read_csv('private/db/meta_loa_indic_acao.csv',
#                                           delimiter='\t',
#                                           decimal='.',
#                                           index_col=['CD_INDICADOR_PRODUTO',
#                                                      'CD_PROJ_ATIV'])

# meta_uo_2018_produto = pd.read_csv('private/db/meta_loa_indic_acao_uo.csv',
#                                           delimiter='\t',
#                                           decimal='.',
#                                           index_col=['CD_INDIC_PRODUTO',
#                                                      'CD_ACAO',
#                                                      'COD_UO'])

# indicadores
with open(_PATH + 'apurar_indicadores.sql') as f:
    _sql_indicadores = f.read()

# produtos
with open(_PATH + 'agregar_produtos.sql') as f:
    _sql_produtos = f.read()

# programas
with open(_PATH + 'agregar_programas_indicadores.sql') as f:
    _sql_pgm_indicadores = f.read()
with open(_PATH + 'agregar_programas_produtos.sql') as f:
    _sql_pgm_pdt = f.read()

# orgãos
with open(_PATH + 'agregar_orgao_programa.sql') as f:
    _sql_orgao_pgm = f.read()

# obter último ano e fase da base
sql_extrador_ano_fase = \
'''SELECT DISTINCT t1.FASE,
       t1.ANO
FROM EPPA_INDICADORES t1,
     (SELECT MAX(ANO) ANO FROM EPPA_INDICADORES) t2
WHERE t1.ANO = t2.ANO'''

fases_ordem_dict = {1: 1,
                    18: 2,
                    19: 3,
                    2: 4,
                    31: 5,
                    33: 6,
                    4: 7,
                    7: 8,
                    8: 9}

def ordem_fase(fase1, fase2):
    try:
        return fases_ordem_dict[fase1] > fases_ordem_dict[fase2]
    except KeyError:
        return False

def extrator_ano_fase(cursor):
    max_fase = 1
    for fase, ano in cursor.execute(sql_extrador_ano_fase):
        if ordem_fase(fase, max_fase):
            max_fase = fase if fase not in (34, 4) else 18
    return ano, max_fase

def minimo(n):
    return max(LIMITE_MIN, n) if n != -1 else n

def maximo(n):
    return min(LIMITE_MAX, n) if n != -1 else n

def max_min(n):
    return minimo(maximo(n))

def agregar_indicadores():

    def agregar_pgm_indicadores(dicionario, seq_pgm, seq_indic):
        try:
            dicionario[seq_pgm].append(seq_indic)
        except KeyError:
            dicionario[seq_pgm] = [seq_indic]


    def apurar(ano,
               saldo,
               meta,
               polaridade,
               n_apuracoes,
               n_apuracoes_previstas,
               forma_totalizacao,
               ppa=False):

        # if ano == 2:
        #     return -1

        if meta is None:
            return -1

        # if n_apuracoes_previstas == 1:
        #     return -1

        if n_apuracoes == 0:
            return -1


            # if saldo == 0:
            #     return 1
            # else:
            #     return 0

        if saldo is None:
            return -1
        elif saldo < 0:
            return 0

        if polaridade == 'E':
            if meta == 0:
                if saldo == 0:
                    return 1
                else:
                    return 0
            return 1 + (1 - (saldo / meta))
        else:
            if meta == 0:
                return -1
            return saldo / meta

        multiplicador = n_apuracoes / n_apuracoes_previstas

        if forma_totalizacao == 'S':
            if polaridade == 'P':
                return saldo / meta
            else:
                projecao = saldo * n_apuracoes_previstas / n_apuracoes
                return max(LIMITE_MIN, (1 + (1 - (projecao / meta)))) * multiplicador
        else:
            if polaridade == 'P':
                return (saldo / meta) * multiplicador
            else:
                return max(LIMITE_MIN, (1 + (1 - (saldo / meta)))) * multiplicador

        return 0

    ANO_CORRENTE = datetime.datetime.now().year
    MES_CORRENTE = datetime.datetime.now().month
    DIA_CORRENTE = datetime.datetime.now().day
    # ANO_CORRENTE = 2022
    # MES_CORRENTE = 6
    # DIA_CORRENTE = 30

    conn = cx_Oracle.connect(conn_user)
    cursor = conn.cursor()
    ANO_MAX, FASE_MAX = extrator_ano_fase(cursor)

    if MES_CORRENTE <= 2 and DIA_CORRENTE <= 20:
        ANO_CORRENTE -= 1
        # ANO_MAX -= 1
        MES_CORRENTE = 12

    if ANO_CORRENTE - ANO_PPA > 4:
        ANO_CORRENTE = ANO_PPA + 3
        MES_CORRENTE = 12
        DIA_CORRENTE = 30
    
    sql_pgm_dict = '''
        SELECT CAST(SEQ_PGM AS INT),
               COD_PGM
        FROM EPA_PROGRAMAS
        WHERE ANO =:ano AND
              FASE = 34'''

    seq_pgm_dict = {}
    cursor.execute(sql_pgm_dict, ano=ANO_CORRENTE)
    for seq_pgm, cod_pgm in cursor:
        seq_pgm_dict[cod_pgm] = seq_pgm

    
    return ANO_MAX, FASE_MAX, seq_pgm_dict
###################################### metas ##################################

    cursor.execute(_sql_metas_ppa, ano_corrente=ANO_CORRENTE)
    for seq_indic, *metas in cursor:
        for meta, key in zip(metas, KEYS_AGG):
            metas_ppa[key][seq_indic] = meta

    cursor.execute(_sql_metas_recentes, ano2=ANO_PROJETO_PPA+2,
                                        ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4,
                                        ano_corrente=ANO_CORRENTE)
    for seq_indic, *metas in cursor:
        for meta, key in zip(metas, KEYS_AGG):
            metas_recentes[key][seq_indic] = meta

    ##### puxadinho para 2018 #####
    # for seq_indic, *_, meta in meta_indicador_2018_produto.itertuples(name=None):
    #     try:
    #         metas_recentes[3][seq_indic] = float(meta)
    #     except ValueError:
    #         metas_recentes[3][seq_indic] = None


############################### apurações indicador ###########################
    cursor.execute(_sql_indicadores, ano1=ANO_PROJETO_PPA+1, ano2=ANO_PROJETO_PPA+2,
                                     ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4)
    for (ano, seq_indic, periodicidade, polaridade, saldo_ano, saldo_total,
         forma_tot_ano, forma_tot_ppa, n_apuracoes_ano, n_apuracoes_total,
         periodicidades_ppa) in cursor:

        if not seq_indic or not ano:
            continue

        # if isinstance(ano, int) and ano < 2020:
        #     continue

        # troquei polaridade por 'P'
        # polaridade = 'P'
        # if seq_indic in (1588, 1314, 634, 829, 824): # exceções
        #     polaridade = 'P'
        if ano == ANO_CORRENTE:
            n_apuracoes_previstas = 0
            p_tmp = 'M'
            for p in periodicidades_ppa.split(','):
                if p:
                    n_apuracoes_previstas += periodicidades_dict[p]
                    p_tmp = p
                else:
                    n_apuracoes_previstas += periodicidades_dict[p_tmp]

            # indicadores_ppa['total'][seq_indic] = apurar(ano, saldo_total,
            #         metas_ppa['total'].get(seq_indic, None), polaridade, n_apuracoes_total,
            #         n_apuracoes_previstas, forma_tot_ppa, True)
            indicadores_recente['total'][seq_indic] = apurar(ano, saldo_total,
                    metas_recentes['total'].get(seq_indic, None), polaridade, n_apuracoes_total,
                    n_apuracoes_previstas, forma_tot_ppa)
        ano -= ANO_PROJETO_PPA
        n_apuracoes_previstas = periodicidades_dict[periodicidade]
        # indicadores_ppa[ano][seq_indic] = apurar(ano, saldo_ano,
        #             metas_ppa[ano].get(seq_indic, None), polaridade, n_apuracoes_ano,
        #             n_apuracoes_previstas, forma_tot_ano)
        indicadores_recente[ano][seq_indic] = apurar(ano, saldo_ano,
                    metas_recentes[ano].get(seq_indic, None), polaridade, n_apuracoes_ano,
                    n_apuracoes_previstas, forma_tot_ano, False)

  
################################ apurações produto ############################

    pdt_indic = set()
    cursor.execute(_sql_produtos, ano1=ANO_PROJETO_PPA+1, ano2=ANO_PROJETO_PPA+2,
                                  ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4)

    for ano, seq_pdt, seq_indic in cursor:
        if not ano:
            continue

        # if isinstance(ano, int) and  ano < 2020:
        #     continue

        if ano == ANO_CORRENTE:
            pdt_indic.add((seq_pdt, seq_indic))

        ano -= ANO_PROJETO_PPA

        if not seq_indic:
            # pdt_ppa[ano][seq_pdt] = -1
            pdt_recente[ano][seq_pdt] = -1

        else:
            # pdt_ppa[ano][seq_pdt] = min(indicadores_ppa[ano].get(seq_indic, 0), LIMITE_MAX)
            pdt_recente[ano][seq_pdt] = max_min(indicadores_recente[ano].get(seq_indic, 0))

    for seq_pdt, seq_indic in pdt_indic:
        soma = sum(indicadores_recente[key].get(seq_indic, -1) for key in KEYS_AGG[:-1])
        if soma != -4:
            # pdt_ppa['total'][seq_pdt] = min(indicadores_ppa['total'].get(seq_indic, 0), LIMITE_MAX)
            pdt_recente['total'][seq_pdt] = max_min(indicadores_recente['total'].get(seq_indic, 0))
        else:
            # pdt_ppa['total'][seq_pdt] = -1
            pdt_recente['total'][seq_pdt] = -1


########################## apurações dos programas ############################
    pgms = set()
    pgm_pdts = []

    # apuracao dos produtos do programa
    cursor.execute(_sql_pgm_pdt, ano1=ANO_PROJETO_PPA+1, ano2=ANO_PROJETO_PPA+2,
                                 ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4)
    for ano, seq_pgm, seq_pdts in cursor:
        # if isinstance(ano, int) and  ano < 2020:
        #     continue

        if ano == ANO_CORRENTE:
            pgm_has_produto[seq_pgm] = bool(seq_pdts)
        if not all([ano, seq_pgm, seq_pdts]):
            continue
        pgms.add(seq_pgm)

        seq_pdts = [int(seq_pdt) for seq_pdt in seq_pdts.split(',')]
        qtd_pdt = len(seq_pdts)

        if ano == ANO_CORRENTE:
            pgm_pdts.append([seq_pgm, seq_pdts])

        ano -= ANO_PROJETO_PPA
        if qtd_pdt > 0:

            # soma = 0
            # has_pdt = False
            # qtd_pdt = 0
            # for seq_pdt in seq_pdts:
            #     raw_pdt_ppa = pdt_ppa[ano].get(seq_pdt, 0)
            #     if raw_pdt_ppa != -1:
            #         has_pdt = True
            #         soma += raw_pdt_ppa
            #         qtd_pdt += 1
            # if has_pdt:
            #     pgm_pdt_ppa[ano][seq_pgm] = soma / qtd_pdt
            # else:
            #     pgm_pdt_ppa[ano][seq_pgm] = -1

            has_pdt = False
            soma = 0
            qtd_pdt = 0
            for seq_pdt in seq_pdts:
                raw_pdt_recente = pdt_recente[ano].get(seq_pdt, 0)
                if raw_pdt_recente != -1:
                    has_pdt = True
                    soma += minimo(raw_pdt_recente)
                    qtd_pdt += 1
            if has_pdt:
                pgm_pdt_recente[ano][seq_pgm] = soma / qtd_pdt
            else:
                pgm_pdt_recente[ano][seq_pgm] = -1

    for seq_pgm, seq_pdts in pgm_pdts:
        qtd_pdt = len(seq_pdts)

        if qtd_pdt > 0:

            # soma = 0
            # has_pdt = False
            # for seq_pdt in seq_pdts:
            #     raw_pdt_ppa = pdt_ppa['total'].get(seq_pdt, -1)
            #     if raw_pdt_ppa != -1:
            #         has_pdt = True
            #         soma += raw_pdt_ppa
            # if has_pdt:
            #     pgm_pdt_ppa['total'][seq_pgm] = soma / qtd_pdt
            # else:
            #     pgm_pdt_ppa['total'][seq_pgm] = -1

            soma = 0
            has_pdt = False
            for seq_pdt in seq_pdts:
                raw_pdt_recente = pdt_recente['total'].get(seq_pdt, -1)
                if raw_pdt_recente != -1:
                    has_pdt = True
                    soma += minimo(raw_pdt_recente)
            if has_pdt:
                pgm_pdt_recente['total'][seq_pgm] = soma / qtd_pdt
            else:
                pgm_pdt_recente['total'][seq_pgm] = -1

    # apuracao dos indicadores de resultado do programa
    cursor.execute(_sql_pgm_indicadores, ano1=ANO_PROJETO_PPA+1, ano2=ANO_PROJETO_PPA+2,
                                         ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4)
    for ano, seq_pgm, seq_indics in cursor:
        # if isinstance(ano, int) and  ano < 2020:
        #     continue

        if ano == ANO_CORRENTE:
            pgm_has_resultado[seq_pgm] = bool(seq_indics)
        if not all([ano, seq_pgm, seq_indics]):
            continue
        pgms.add(seq_pgm)
        seq_indics = [int(seq_indic) for seq_indic in seq_indics.split(',')]
        qtds_indics = len(seq_indics)
        if ano == ANO_CORRENTE:
            # try:
            #     pgm_resultado_ppa['total'][seq_pgm] = sum(min(indicadores_ppa['total'].get(seq_indic, 0), LIMITE_MAX)
            #         for seq_indic in seq_indics if indicadores_ppa['total'].get(seq_indic, 0) != -1) / qtds_indics
            # except TypeError: # empty sum()
            #     pgm_resultado_ppa['total'][seq_pgm] = 0
            try:
                pgm_resultado_recente['total'][seq_pgm] = sum(maximo(minimo(indicadores_recente['total'].get(seq_indic, 0)))
                    for seq_indic in seq_indics if indicadores_recente['total'].get(seq_indic, 0) != -1) / qtds_indics
            except TypeError:
                pgm_resultado_recente['total'][seq_pgm] = 0

        ano -= ANO_PROJETO_PPA



        # try:
        #     apuracoes_resultado_ppa = [indicadores_ppa[ano][seq_indic] for seq_indic in seq_indics
        #                            if (seq_indic in indicadores_ppa[ano]
        #                            and indicadores_ppa[ano][seq_indic] != -1)]
        #     if apuracoes_resultado_ppa:
        #         pgm_resultado_ppa[ano][seq_pgm] = sum(min(a, LIMITE_MAX)
        #         for a in apuracoes_resultado_ppa) / qtds_indics
        #     else:
        #         pgm_resultado_ppa[ano][seq_pgm] = -1
        # except TypeError:
        #     pgm_resultado_ppa[ano][seq_pgm] = -1
        try:
            apuracoes_resultado_recente = [indicadores_recente[ano][seq_indic] for seq_indic in seq_indics
                                   if (seq_indic in indicadores_recente[ano]
                                   and indicadores_recente[ano][seq_indic] != -1)]
            if apuracoes_resultado_recente:
                pgm_resultado_recente[ano][seq_pgm] = sum(minimo(maximo(a))
                for a in apuracoes_resultado_recente) / qtds_indics
            else:
                pgm_resultado_recente[ano][seq_pgm] = -1
        except TypeError:
            pgm_resultado_recente[ano][seq_pgm] = -1

    # apuracao dos programas = média de simples de pgm_resultado e pgm_produto
    for seq_pgm in pgms:

        for key in KEYS_AGG:
            _len = 0
            if pgm_has_resultado.get(seq_pgm, False):
                # _resultado_ppa = pgm_resultado_ppa[key].get(seq_pgm, 0)
                _resultado_recente = minimo(pgm_resultado_recente[key].get(seq_pgm, 0))
                _len += 1
            else:
                # _resultado_ppa = -1
                _resultado_recente = -1

            if pgm_has_produto.get(seq_pgm, False):
                # _produto_ppa = pgm_pdt_ppa[key].get(seq_pgm, 0)
                _produto_recente = minimo(pgm_pdt_recente[key].get(seq_pgm, 0))
                _len += 1
            else:
                # _produto_ppa = -1
                _produto_recente = -1

            if _len:
                if _resultado_recente == _produto_recente == -1:
                    pgm_geral_recente[key][seq_pgm] = -1
                elif _produto_recente == -1:
                    pgm_geral_recente[key][seq_pgm] = _resultado_recente
                elif _resultado_recente == -1:
                    pgm_geral_recente[key][seq_pgm] = _produto_recente
                else:
                    pgm_geral_recente[key][seq_pgm] = (_resultado_recente + _produto_recente) / _len

                # if _resultado_ppa == _produto_ppa == -1:
                #     pgm_geral_ppa[key][seq_pgm] = -1
                # elif _produto_ppa == -1:
                #     pgm_geral_ppa[key][seq_pgm] = _resultado_ppa
                # elif _resultado_ppa == -1:
                #     pgm_geral_ppa[key][seq_pgm] = _produto_ppa
                # else:
                #     pgm_geral_ppa[key][seq_pgm] = (_resultado_ppa + _produto_ppa) / _len

            else:
                # pgm_geral_ppa[key][seq_pgm] = -1
                pgm_geral_recente[key][seq_pgm] = -1

    # exceções!!!
    for key in KEYS_AGG:
        # pgm_geral_ppa[key][215] = -1
        pgm_geral_recente[key][215] = -1
        # pgm_geral_ppa[key][5] = -1
        pgm_geral_recente[key][5] = -1
        # pgm_geral_ppa[key][134] = -1
        pgm_geral_recente[key][134] = -1
############################# apuracões dos órgãos ############################

    cursor.execute(_sql_orgao_pgm, ano1=ANO_PROJETO_PPA+1, ano2=ANO_PROJETO_PPA+2,
                                   ano3=ANO_PROJETO_PPA+3, ano4=ANO_PROJETO_PPA+4)
    for ano, cod_org, seq_pgms in cursor:
        # if isinstance(ano, int) and  ano < 2020:
        #     continue

        if ano > ANO_CORRENTE:
            continue
        seq_pgms = [int(seq_pgm) for seq_pgm in seq_pgms.split(',')]

        _ano = ano - ANO_PROJETO_PPA
        # orgao_ppa['total'][cod_org] = 0
        orgao_recente['total'][cod_org] = 0
        # orgao_ppa[_ano][cod_org] = 0
        orgao_recente[_ano][cod_org] = 0
        # i_ppa_total = 0
        i_ppa_recente = 0
        # i_ppa = 0
        i_recente = 0
        for seq_pgm in seq_pgms:
            if ano == ANO_CORRENTE:
                # total_ppa = pgm_geral_ppa['total'].get(seq_pgm, -1)
                total_recente = pgm_geral_recente['total'].get(seq_pgm, -1)
                # if total_ppa != -1:
                #     # orgao_ppa['total'][cod_org] += total_ppa
                #     i_ppa_total += 1
                if total_recente != -1:
                    orgao_recente['total'][cod_org] += total_recente
                    i_ppa_recente += 1

            # ppa = pgm_geral_ppa[_ano].get(seq_pgm, -1)
            recente = pgm_geral_recente[_ano].get(seq_pgm, -1)
            # if ppa != -1:
            #     orgao_ppa[_ano][cod_org] += ppa
            #     i_ppa += 1
            if recente != -1:
                orgao_recente[_ano][cod_org] += recente
                i_recente += 1

        if ano == ANO_CORRENTE:
            # if i_ppa_total:
            #     orgao_ppa['total'][cod_org] /= i_ppa_total
            # else:
            #     orgao_ppa['total'][cod_org] = -1

            if i_ppa_recente:
                orgao_recente['total'][cod_org] /= i_ppa_recente
            else:
                orgao_recente['total'][cod_org] = -1

        # if i_ppa:
        #         orgao_ppa[_ano][cod_org] /= i_ppa
        # else:
        #         orgao_ppa[_ano][cod_org] = -1

        if i_recente:
                orgao_recente[_ano][cod_org] /= i_recente
        else:
                orgao_recente[_ano][cod_org] = -1


        # if ano == ANO_CORRENTE:
        #     orgao_ppa['total'][cod_org] = sum(pgm_geral_ppa['total'].get(seq_pgm, 0)
        #         for seq_pgm in seq_pgms if pgm_geral_ppa['total'].get(seq_pgm, 0) != -1) / length
        #     orgao_recente['total'][cod_org] = sum(pgm_geral_recente['total'].get(seq_pgm, 0)
        #         for seq_pgm in seq_pgms if pgm_geral_recente['total'].get(seq_pgm, 0) != -1) / length

        # orgao_ppa[ano][cod_org] = sum(pgm_geral_ppa[ano].get(seq_pgm, 0)
        #         for seq_pgm in seq_pgms if pgm_geral_ppa[ano].get(seq_pgm, 0) != -1) / length
        # orgao_recente[ano][cod_org] = sum(pgm_geral_recente[ano].get(seq_pgm, 0)
        #         for seq_pgm in seq_pgms if pgm_geral_recente[ano].get(seq_pgm, 0) != -1) / length

###################### apuração do Estado de São Paulo ########################
    for key in KEYS_AGG:
        # ppa = orgao_ppa[key]
        recente = orgao_recente[key]
        # if ppa:
        #     values_ppa = [ppa[cod_org] for cod_org in ppa if cod_org != 99000 and ppa[cod_org] != -1]
        #     if len(values_ppa) > 0:
        #         ESP_ppa[key] = sum(values_ppa) / len(values_ppa)
        #     else:
        #         ESP_ppa[key] = -1

        if recente:
            values_recente = [recente[cod_org] for cod_org in recente if cod_org != 99000 and recente[cod_org] != -1]
            if len(values_recente) > 0:
                ESP_recente[key] = sum(values_recente) / len(values_recente)
            else:
                ESP_recente[key] = -1
    cursor.close()
    conn.close()
  
    return ANO_MAX, FASE_MAX, seq_pgm_dict

if __name__ == '__main__':
    agregar_indicadores()
