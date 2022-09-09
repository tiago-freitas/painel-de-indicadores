import os

import cx_Oracle
import requests
import time

ANO = 2022
FASE = 34
PATH = 'http://127.0.0.1:8080/%s/%d'
# PATH = 'http://localhost:8080/%s/%d'
testes = []

# os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8"
conn = cx_Oracle.connect('SYSTEM/ls31tB22@192.168.15.24:1539/XE.ELORPRD')
c = conn.cursor()

print('{:<30}{:<10}{}'.format('Tipo','Código', 'Status'))
print('{:-<60}'.format(''))
sql = '''SELECT SEQ_IMPACTO FROM EPPA_IMPACTOS WHERE ANO =:ano AND FASE =:fase'''
for seq_obj, *_ in c.execute(sql, ano=ANO, fase=FASE):
    r = requests.get(PATH % ('obj_estrat', seq_obj))
    print('{:<30}{:<10}{}'.format('Objetivo Estratégico', seq_obj, r.status_code))
    testes.append(r.status_code)

print()
print('{:<30}{:<10}{}'.format('Tipo','Código', 'Status'))
print('{:-<60}'.format(''))
sql = '''SELECT DISTINCT EPA_PGM_ORG.COD_ORG as "Código do Órgão"
         FROM EPA_PGM_ORG
         LEFT OUTER JOIN ORGAOS
           ON EPA_PGM_ORG.COD_ORG = ORGAOS.COD_ORG
         WHERE EPA_PGM_ORG.ANO =:ano AND
               EPA_PGM_ORG.FASE =:fase'''
for seq_obj, *_ in c.execute(sql, ano=ANO, fase=FASE):
    r = requests.get(PATH % ('orgao', seq_obj))
    print('{:<30}{:<10}{}'.format('Órgão', seq_obj, r.status_code))
    if r.text.find('Não foram encontrados os dados') != -1:
        print('{:<30}{:<10}{}'.format('Órgão', seq_obj, 'Não há dados'))
    testes.append(r.status_code)

print()
print('{:<30}{:<10}{}'.format('Tipo','Código', 'Status'))
print('{:-<60}'.format(''))
sql = '''SELECT SEQ_PGM as "Sequência do Programa"
         FROM EPA_PROGRAMAS
         WHERE ANO =:ano AND
               FASE =:fase'''
for seq_obj, *_ in c.execute(sql, ano=ANO, fase=FASE):
    r = requests.get(PATH % ('programa', seq_obj))
    print('{:<30}{:<10}{}'.format('Programa', seq_obj, r.status_code))
    if r.text.find('Não foram encontrados os dados') != -1:
        print('{:<30}{:<10}{}'.format('Programa', seq_obj, 'Não há dados'))
    testes.append(r.status_code)

print()
print('{:<30}{:<10}{}'.format('Tipo','Código', 'Status'))
print('{:-<60}'.format(''))
sql = '''SELECT DISTINCT SEQ_PRODUTO
         FROM EPPA_PRODUTOS
         WHERE ANO =:ano AND
               FASE =:fase'''
for seq_obj, *_ in c.execute(sql, ano=ANO, fase=FASE):
    s = time.time()
    r = requests.get(PATH % ('produto', seq_obj))
    tempo = time.time() - s
    print('{:<30}{:<10}{:<10}{}'.format('Produto', seq_obj, r.status_code, tempo))
    if r.text.find('Não foram encontrados os dados') != -1:
        print('{:<30}{:<10}{}'.format('Produto', seq_obj, 'Não há dados'))
    testes.append(r.status_code)

print()
print('{:<30}{:<10}{}'.format('Tipo','Código', 'Status'))
print('{:-<60}'.format(''))
sql = '''SELECT DISTINCT SEQ_INDIC
         FROM EPPA_INDICADORES
         WHERE ANO =:ano AND
               FASE =:fase'''
for seq_obj, *_ in c.execute(sql, ano=ANO, fase=FASE):
    s = time.time()
    r = requests.get(PATH % ('indicador', seq_obj))
    tempo = time.time() - s
    print('{:<30}{:<10}{:<10}{}'.format('Indicador', seq_obj, r.status_code, tempo))
    if r.text.find('Não foram encontrados os dados') != -1:
        print('{:<30}{:<10}{}'.format('Indicador', seq_obj, 'Não há dados'))
    testes.append(r.status_code)

c.close()
conn.close()

from collections import Counter

c = Counter(testes)
print(c)
