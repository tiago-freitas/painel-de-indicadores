from string import Template
import pandas as pd
import os
import cx_Oracle
import datetime
from helper import ANO_PPA

import functools
open = functools.partial(open, encoding='utf-8')
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.UTF8"

################################## globais ####################################

FASE_PPA = 2
with open('private/user.txt') as f:
    conn_user = f.read().strip()

################################### doc #######################################

with open('private/html/documentacao.html') as f:
    doc_html = f.read()

################################## sqls #######################################
PATH_SQL = 'private/sql/'

# indicadores
with open(PATH_SQL + 'indicadores/indicador-geral.sql') as f:
    sql_indic = f.read()
with open(PATH_SQL + 'indicadores/indicador-acoes-uos.sql') as f:
    sql_acoes_uo_indic = f.read()
with open(PATH_SQL + 'indicadores/indicador-metas-acoes.sql') as f:
    sql_metas_acoes_indic = f.read()
with open(PATH_SQL + 'indicadores/indicador-metas-acoes-nao-ppa.sql') as f:
    sql_metas_acoes_nao_ppa_indic = f.read()
with open(PATH_SQL + 'indicadores/indicador-metas-uo.sql') as f:
    sql_metas_uo_indic = f.read()

# produtos
with open(PATH_SQL + 'produtos/produto-geral.sql') as f:
    sql_pdt = f.read()
with open(PATH_SQL + 'produtos/produto-indicadores.sql') as f:
    sql_pdt_indic = f.read()
with open(PATH_SQL + 'produtos/produto-acoes.sql') as f:
    sql_acao_pdt = f.read()
with open(PATH_SQL + 'produtos/produto-acoes-orc.sql') as f:
    sql_acao_pdt_orc = f.read()
with open(PATH_SQL + 'produtos/produto-acoes-uo-apur-fisica.sql') as f:
    sql_acao_pdt_uo_fisica = f.read()
with open(PATH_SQL + 'produtos/produto-uo-meta.sql') as f:
    sql_acao_pdt_uo_meta = f.read()
with open(PATH_SQL + 'produtos/produto-acoes-orc-sintetico.sql') as f:
    sql_acao_pdt_orc_sintetico = f.read()
with open(PATH_SQL + 'produtos/produto-acoes-apur-fisica.sql') as f:
    sql_acao_pdt_fisica = f.read()

# programas
with open(PATH_SQL + 'programas/programa-geral.sql') as f:
    sql_pgm = f.read()
with open(PATH_SQL + 'programas/programa-orgao.sql') as f:
    sql_pgm_orgs = f.read()
with open(PATH_SQL + 'programas/programa-obj-estrategico.sql') as f:
    sql_pgm_obj_estrat = f.read()
with open(PATH_SQL + 'programas/programa-risco.sql') as f:
    sql_risco = f.read()
with open(PATH_SQL + 'programas/programa-despesa-orcamentaria.sql') as f:
    sql_orcamento = f.read()
with open(PATH_SQL + 'programas/programa-despesa-nao-orcamentaria.sql') as f:
    sql_nao_orcamento = f.read()
with open(PATH_SQL + 'programas/programa-despesa-total.sql') as f:
    sql_geral = f.read()
with open(PATH_SQL + 'programas/programa-indicadores-resultado.sql') as f:
    sql_pgm_resultado = f.read()
with open(PATH_SQL + 'programas/programa-produtos.sql') as f:
    sql_pgm_produto = f.read()

# orgãos
with open(PATH_SQL + 'orgaos/orgao-geral.sql') as f:
    sql_orgao = f.read()

with open(PATH_SQL + 'orgaos/orgao-programas.sql') as f:
    sql_orgao_pgms = f.read()

# objetivos estratégicos
with open(PATH_SQL + 'obj-estrategico/obj-estrategico.sql') as f:
    sql_obj_estrat = f.read()
with open(PATH_SQL + 'obj-estrategico/obj-pgms.sql') as f:
    sql_obj_pgms = f.read()
with open(PATH_SQL + 'obj-estrategico/obj-indicadores.sql') as f:
    sql_obj_indic = f.read()

# Estado de São Paulo
with open(PATH_SQL + 'ESP/esp-orgaos.sql') as f:
    sql_esp_orgaos = f.read()

###############################################################################

############################### templates #####################################
PATH_HTML = 'private/html/'
with open(PATH_HTML + 'index.html') as f:
    html_url = f.read()


# gadgets
with open(PATH_HTML + 'gadgets.html') as f:
    gadgets_template = f.read()

# indicadores
gadget_indicador = gadgets_template.format(tipo_fonte='indicador',
                                           tipo_codigo='{seq_indic}')
produto_call_1 = '''\
<div class="row">
  <div class="pergunta-resposta">
    <div class="col-xs-1">Produto</div>
    <div class="col-xs-11 link-handler" onclick="ir_a_link($cod_pdt, 'produto')">$cod_pdt - $nome_pdt</div>
  </div>
</div>'''

produto_call_2 = '''\
<div class="pergunta-resposta">
  <div class="col-xs-2">Indicador PPA</div>
  <div class="col-xs-1">$indicador_loa</div>
</div>'''

table_uo_acao_inicio = f'''\
<table class="table-painel-1">
  <thead>
    <tr>
      <th class="table-titulo" colspan="8">Metas do Indicador por Ação e por Unidade Orçamentária</th>
    </tr>
    <tr>
     <th rowspan="2">Nível</th>
     <th rowspan="2">Ação Orçamentária?</th>
     <th rowspan="2">Soma UO?</th>
     <th colspan="4">Metas Fixadas (LOA)</th>
    </tr>
    <tr>
     <th>{ANO_PPA}</th>
     <th>{ANO_PPA+1}</th>
     <th>{ANO_PPA+2}</th>
     <th>{ANO_PPA+3}</th>
    </tr>
  </thead>
  <tbody>'''

template_acao_uo = '<tr>' + '<td>%s</td>' * 3 + '<td class="number_row">%s</td>' * 4 +  '</tr>'

with open(PATH_HTML + 'indicadores/graf-metas.js') as f:
    graf_metas_indic = f.read()
    graf_metas_indic = ''
with open(PATH_HTML + 'indicadores/indicador-pdt-e-pgm.html') as f:
    tmp = f.read()

    tmp_pdt = tmp.format(pdt1=produto_call_1, pdt2=produto_call_2, colspan='2')
    tmp_resultado = tmp.format(pdt1='', pdt2='', colspan='5')

    html_indic_pdt = Template(tmp_pdt + graf_metas_indic)
    html_indic_resultado = Template(tmp_resultado + graf_metas_indic)

with open(PATH_HTML + 'indicadores/indicador-impacto.html') as f:
    html_indic_impacto = Template(f.read())

with open(PATH_HTML + 'indicadores/indicador-tabela-ppa.html') as f:
    html_tabela_ppa = Template(f.read())

# produtos

table_indic_pdt = f'''\
<table class="table-painel-1">
  <thead>
    <tr>
      <th class="table-titulo" colspan="7">Taxa de Cumprimento das Metas dos Indicadores de Produto</th>
    </tr>
    <tr>
      <th>Nome do Indicador</th>
      <th>Publicado no PPA?</th>
      <th>Taxa {ANO_PPA}</th>
      <th>Taxa {ANO_PPA+1}</th>
      <th>Taxa {ANO_PPA+2}</th>
      <th>Taxa {ANO_PPA+3}</th>
      <th>Taxa PPA</th>
    </tr>
  </thead>
  <tbody>'''

template_pdt_indic = '<span onclick="ir_a_link(%d, \'indicador\')">%s</span>'


gadget_pdt = gadgets_template.format(tipo_fonte='produto',
                                     tipo_codigo='$seq_produto')

with open(PATH_HTML + 'produtos/produto.html') as f:
    html_produto = Template(gadget_pdt + f.read())

table_pdt_acoes = '''\
<table class="table-painel-1">
  <thead>
    <tr>
      <th class="table-titulo" colspan="3">Ações do Produto</th>
    </tr>
    <tr>
      <th>Código da Ação</th>
      <th>Nome da Ação</th>
      <th>Ação Orçamentária?</th>
    </tr>
  </thead>
  <tbody>'''

# programas
gadget_pgm = gadgets_template.format(tipo_fonte='programa',
                                     tipo_codigo='$seq_pgm')

template_objs_pgms = '<span onclick="ir_a_link(%d, \'obj_estrat\')">%s</span>'
template_orgs = '<span onclick="ir_a_link({0}, \'orgao\')">{0} - {1}</span>'.format
template_pdt = '<span onclick="ir_a_link(%d, \'produto\')">%s</span>'

templateRisco = '''\
<div class="row">
  <div class="pergunta-resposta">
    <div class="col-xs-2">Risco %s %s</div>
    <div class="col-xs-10">%s</div>
  </div>
</div>'''

table_resultado_pgm = f'''\
<table class="table-painel-1 pgm">
  <thead>
      <tr>
        <th class="table-titulo" colspan="6">Taxa de Cumprimento das Metas dos Indicadores de Resultado</th>
      </tr>
      <tr>
        <th>Nome do Indicador</th>
        <th>Taxa {ANO_PPA}</th>
        <th>Taxa {ANO_PPA+1}</th>
        <th>Taxa {ANO_PPA+2}</th>
        <th>Taxa {ANO_PPA+3}</th>
        <th>Taxa PPA</th>
      </tr>
  </thead>
  <tbody>'''

table_produto_pgm = f'''\
<table class="table-painel-1 pgm">
  <thead>
    <tr>
      <th class="table-titulo" colspan="7">Taxa de Cumprimento  das Metas dos Produtos</th>
    </tr>
    <tr>
        <th>Nome do Produto</th>
        <th>Classificação</th>
        <th>Taxa {ANO_PPA}</th>
        <th>Taxa {ANO_PPA+1}</th>
        <th>Taxa {ANO_PPA+2}</th>
        <th>Taxa {ANO_PPA+3}</th>
        <th>Taxa PPA</th>
    </tr>
  </thead>
  <tbody>'''

with open(PATH_HTML + 'programa/programa.html') as f:
    html_pgm = Template(gadget_pgm + f.read())

# orgãos
template_orgao_pgm = '<span onclick="ir_a_link(%d, \'programa\')">%s</span>'

table_orgao_pgms = '''\
<table id="org_ano_{ano_id}" class="table-painel-1 table-painel-2">
    <thead>
      <tr>
        <th class="table-titulo" colspan="11">Análise da Execução Física e Aplicação de Recursos por Programa em {ano}</th>
      </tr>
      <tr>
        <th class="table-titulo" rowspan="2">Nome do Programa</th>
        <th class="table-titulo" rowspan="2">Classificação do Programa</th>
        <th class="table-titulo" rowspan="2">Incluído em</th>
        <th class="table-titulo" rowspan="2">Excluído em</th>
        <th class="table-titulo" colspan="2">Taxa Agregada de Cumprimento das Metas por Programa</th>
        <th class="table-titulo" colspan="5">Aplicação de Recursos por Programa</th>
      </tr>
      <tr>
        <th>Taxa {ano}</th>
        <th>Taxa PPA</th>
        <th>Dotação Inicial</th>
        <th>Dotação Atual</th>
        <th>Empenhado</th>
        <th>Liquidado</th>
        <th>Liquidado / Atual</th>
      </tr>
    </thead>
  <tbody>'''


gadget_orgao = gadgets_template.format(tipo_fonte='orgao',
                                     tipo_codigo='$cod_org')

with open(PATH_HTML + 'orgaos/orgao.html') as f:
    html_orgao = Template(gadget_orgao + f.read())

# objetivos estratégicos
template_pgms_objs = '<span onclick="ir_a_link(%d, \'programa\')">%s</span>'
template_objs_indic = '<tr class="link-handler" onclick="ir_a_link(%d, \'indicador\')">'
gadget_obj = gadgets_template.format(tipo_fonte='todos',
                                     tipo_codigo='todos')

with open(PATH_HTML + 'obj-estrategicos/obj-estrategico.html') as f:
    html_obj_estrategico = Template(gadget_obj + f.read())

# Estado de São Paulo
gadget_esp = gadgets_template.format(tipo_fonte='todos',
                                     tipo_codigo='todos')

template_esp_orgao = '<span onclick="ir_a_link(%d, \'orgao\')">%s</span>'
table_orgaos_esp = '''\
<table id="org_ano_{ano_id}" class="table-painel-1 table-painel-2">
  <thead>
    <tr>
      <th class="table-titulo" colspan="8">Análise da Execução Física e Aplicação de Recursos por Órgão em {ano}</th>
    </tr>
    <tr>
      <th class="table-titulo" rowspan="2">Nome do Órgão</th>
      <th class="table-titulo" colspan="2">Taxa Agregada de Cumprimento das Metas dos Órgãos</th>
      <th class="table-titulo" colspan="5">Aplicação de Recursos por Órgão</th>
    </tr>
    <tr>
      <th>Taxa {ano}</th>
      <th>Taxa PPA</th>
      <th>Dotação Inicial</th>
      <th>Dotação Atual</th>
      <th>Empenhado</th>
      <th>Liquidado</th>
      <th>Liquidado / Atual</th>
    </tr>
  </thead>
  <tbody>'''

with open(PATH_HTML + 'ESP/ESP.html') as f:
    html_esp = Template(gadget_esp + f.read())

with open(PATH_HTML + 'erro.html') as f:
    html_erro = Template(gadget_obj + f.read())

############################ Categorias Orçamentárias #########################

categoria_despesa = {3: 'Despesas Correntes',
                     4: 'Despesas de Capital'}
grupo_despesa = {1: 'Pessoal e Encargos Sociais',
                 2: 'Juros e Encargos da Dívida',
                 3: 'Outras Despesas Correntes',
                 4: 'Investimentos',
                 5: 'Inversões Financeiro',
                 6: 'Amortização da Dívida'}
elemento_despesa = {1:   'Aposen.do Rpps,reser.renum.e Ref.do Militar',
                    3:   'Pensões do Rpps e do Militar',
                    4:   'Contratação por Tempo Determinado',
                    5:   'Outros Benefícios Prev.do Serv. ou do Militar',
                    7:   'Contribuição Entidades Fechadas Previdência',
                    8:   'Outros Benef.assist.do Servidor e do Militar',
                    11:  'Vencimentos e Vantagens Fixas - Pessoal Civil',
                    12:  'Vencimentos e Vantagens Fixas - Pessoal Militar',
                    13:  'Obrigações Patronais',
                    14:  'Diárias - Civil',
                    15:  'Diárias - Militar',
                    16:  'Outras Despesas Variaveis - Pessoal Civil',
                    17:  'Outras Despesas Variáveis - Pessoal Militar',
                    18:  'Auxílio Financeiro a Estudantes',
                    20:  'Auxílio Financeiro a Pesquisadores',
                    21:  'Juros sobre a Dívida por Contrato',
                    22:  'Outros Encargos sobre a Dívida por Contrato',
                    23:  'Juros, Deságios e Descontos da Dívida Mobiliária',
                    24:  'Outros Encargos sobre a Dívida Mobiliária',
                    25:  'Encargos sobre Operações de Crédito por Antecipação da Receita',
                    27:  'Encargos P.honra de Avais,garantias e Seguro',
                    30:  'Material de Consumo',
                    31:  'Premiacoes Culturais Art.cient.despor. Outra',
                    31:  'Classif.do Exercicio Anterior',
                    32:  'Material, Bem Ou Serv.p/distribuição Gratuito',
                    33:  'Passagens e Despesas com Locomoção',
                    35:  'Serviços de Consultoria',
                    36:  'Outros Serviços de Terceiros - Pessoa Física',
                    37:  'Serviços de Limpeza,vigil.e Outros-pes.jurídica',
                    38:  'Arrendamento Mercantil',
                    39:  'Outros Serviços de Terceiros - Pessoa Jurídica',
                    41:  'Contribuições',
                    42:  'Auxílios',
                    43:  'Subvenções Sociais',
                    45:  'Subvenções Econômicas',
                    46:  'Auxílio-alimentação',
                    47:  'Obrigações Tributárias e Contributivas',
                    48:  'Outros Auxílios Financeiros a Pes.físicas',
                    49:  'Auxílio-transporte',
                    50:  'Serviços de Utilidade Pública',
                    51:  'Obras e Instalações',
                    52:  'Equipamentos e Material Permanente',
                    59:  'Pensões Especiais',
                    61:  'Aquisição de Imóveis',
                    62:  'Aquisição de Produtos para Revenda',
                    63:  'Aquisição de Titulos de Crédito',
                    64:  'Aquis.de Tits.repr.de Cap.já Integralizado',
                    65:  'Const.ou Aumento de Capital de Empresas',
                    71:  'Principal da Dívida Contratual Resgatada',
                    73:  'Correção Monetária e Cambial da Dívida Contratual Resgatada',
                    75:  'Correção Monetária da Dívida de Operações de Crédito por Antecipação da Receita',
                    81:  'Distribuição de Receitas',
                    91:  'Sentenças Judiciais',
                    92:  'Despesas de Exercícios Anteriores',
                    93:  'Indenizações e Restituições',
                    94:  'Indenizações e Restituições Trabalhistas',
                    96:  'Ressarc.de Despesas de Pessoal Requisitado'}

##################### tables orçamentárias ####################################

table_orc = '''\
<table  class="display table-painel-1" cellspacing="0" width="100%" style="display:none;">
  <thead>
    <tr>
      <th class="table-titulo" colspan="18">%s</th>
    </tr>
    <tr>
      <th>UO</th>
      <th>Categoria de Despesa</th>
      <th>Grupo de Despesa</th>
      <th>Elemento de Despesa</th>
      <th>Dotação Inicial</th>
      <th>Total</th>
      <th>Jan</th>
      <th>Fev</th>
      <th>Mar</th>
      <th>Abr</th>
      <th>Mai</th>
      <th>Jun</th>
      <th>Jul</th>
      <th>Ago</th>
      <th>Set</th>
      <th>Out</th>
      <th>Nov</th>
      <th>Dez</th>
  </tr>
  </thead>'''

COLUNAS_ORC = ('LIQUIDADO_MENSAL', 'EMPENHADO_MENSAL', 'DOT_ATUAL_ACUM')

COLUNAS_ORC_NOMES = (
'Despesas Liquidadas em %d por UO e Elemento de Despesa da Ação %s',
'Despesas Empenhadas em %d por UO e Elemento de Despesa da Ação %s',
'Dotação Atual em %d por UO e Elemento de Despesa da Ação %s')

COLUNA_UO_FISICO = 'Apurações do Indicador por UO'
TABELA_ANALISE = 'Análise da Execução Física e Aplicação de Recursos por Ação e UO'

NOMES_ORC_PANDAS = [
'UO', 'Categoria de Despesa', 'Grupo de Despesa',
'Elemento de Despesa', 'Dotação Inicial', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai',
'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez', 'Acumulado']

ORDEM_ORC_PANDAS = [
'UO', 'Categoria de Despesa', 'Grupo de Despesa',
'Elemento de Despesa', 'Dotação Inicial', 'Acumulado', 'Jan', 'Fev', 'Mar', 'Abr',
'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

INDEX_NAMES_ORC = ['COD_ACAO', 'COD_UO', 'COD_CAT', 'COD_GRUPO', 'COD_ELEM', 'DOT_INICIAL_MENSAL']
VALUE_NAMES_ORC = ['LIQUIDADO_MENSAL', 'EMPENHADO_MENSAL', 'DOT_ATUAL_ACUM']
COLUMNS_NAMES_ORC = ['Dotação Inicial', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez', 'Acumulado']
INDEX_LABELS_ORC = ['UO', 'Categoria de Despesa',
                'Grupo de Despesa', 'Elemento de Despesa']


dummy_multiIndex = pd.MultiIndex(levels=[[''], ['Acumulado'], [''], [''], ['']],
                                          codes=[[0], [0], [0], [0], [0]],
                                          names=INDEX_NAMES_ORC[:-1])

iM = '{ano}-M1 {ano}-M2 {ano}-M3 {ano}-M4 {ano}-M5 {ano}-M6 {ano}-M7 {ano}-M8 {ano}-M9 {ano}-M10 {ano}-M11 {ano}-M12'
iB = '{ano}-B1 {ano}-B2 {ano}-B3 {ano}-B4 {ano}-B5 {ano}-B6'
iT = '{ano}-T1 {ano}-T2 {ano}-T3 {ano}-T4'
iQ = '{ano}-Q1 {ano}-Q2 {ano}-Q3'
iS = '{ano}-S1 {ano}-S2'
iA =  '{ano}-A1'

################################# Análises ####################################

script_analise_conn = '''<script>
    $("#login").hide();
    $("#logout").show();
    $("#send").show();
    $("#username").html('Você está logado como: <b>{usuario}</b>');
    usuario = '{usuario}';
    encrypted = null;
    $('.selected').removeClass('selected');
</script>'''

script_analise_n_conn = '''<script>
    $("#username").html('');
    $("#login").show();
    $('#logout').hide();
    $('#send').hide();
    $('#del').hide();
    $('#edit').hide();
    usuario = null;
</script>'''
