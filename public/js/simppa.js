//////////////////////////////////////////////////////////////////////////////
// @Author: Tiago Barreiros de Freitas
// @Contact: tb.freitas@uol.com.br
//
// This file is part of PPAIndicatorPanel
//
// PPAIndicatorPanel is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 3, or (at your option)
// any later version.
//
// PPAIndicatorPanel is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, write to the Free Software Foundation,
// Inc., 51 Franklin Street, Boston, MA 02110-1301, USA.
//
// GNU General Public License is available at link:
// http://www.gnu.org/licenses/gpl-3.0.en.html
//////////////////////////////////////////////////////////////////////////////

// iniciar menu

var $orgao = $("#orgao");
var $pgm = $("#programa");
var $pdt = $("#produto");
var $indic = $("#indicador");
var $obj_estrat = $("#obj_estrat");

var len_orgao = Object.keys(orgao).length;
var len_pgm = Object.keys(programa).length;
var len_pdt = Object.keys(produto).length;
var len_indic = Object.keys(indicador).length;

var data_orgao_todos = ["", {id:-1, text: "Todos os órgãos"}];
var data_pgm_todos = ["", {id:-1, text: "Todos os programas"}];
var data_pdt_todos = ["", {id:-1, text: "Todos os produtos"}];
var data_indic_todos = ["", {id:-1, text: "Todos os indicadores"}];
var key;

for (var i = 0; i < len_orgao; i++) {
  key = Object.keys(orgao)[i];
  data_orgao_todos.push({id: key, text: orgao[key].nome});
}

Object.keys(programa)
// .map(Number).sort()
for (i = 0; i < len_pgm; i++) {
  key = Object.keys(programa)[i];
  data_pgm_todos.push({id: key, text: programa[key].nome});
}

for (i = 0; i < len_pdt; i++) {
  key = Object.keys(produto)[i];
  data_pdt_todos.push({id: key, text: produto[key].nome});
}

for (i = 0; i < len_indic; i++) {
  key = Object.keys(indicador)[i];
  data_indic_todos.push({id: key, text: indicador[key]});
}

$(function () {
  iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
  $orgao.select2({
    placeholder: "Órgão",
    data: data_orgao_todos,
    language: "pt-BR",
    width: '200px'
  });
});

function iniciar_menu(data_pgm, data_pdt, data_indic, data_obj_estrategico_todos, obj_estrat) {

  if (obj_estrat === undefined) {
      $obj_estrat.html("");
      $obj_estrat.select2({
        placeholder: "Obj. Estratégico",
        data: data_obj_estrategico_todos,
        language: "pt-BR",
        width: '200px'
      });
  }

  $pgm.html("");
  $pgm.select2({
    placeholder: "Programa",
    data: data_pgm,
    language: "pt-BR",
    width: '250px'
  });

  $pdt.html("");
  $pdt.select2({
    placeholder: "Produto",
    data: data_pdt,
    language: "pt-BR",
    width: '200px'
  });

  $indic.html("");
  $indic.select2({
    placeholder: "Indicador",
    data: data_indic,
    language: "pt-BR",
    width: '260px'
  });
}

// fim da preparação de ambiente do menu

// iniciar definição do menu dinâmico e circular

// globais
var id_pdt_previo = [];
var id_indic_previo = [];

// Filtar por órgão
$orgao.on("change", function() {

  if ($orgao.select2("val") === "") {
        return 0
  }

  $obj_estrat.select2("val", "");


  var key_org = $orgao.val();
  if (key_org === "-1") {
    iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
    return;
  }
  var data_pgm = ["", {id: -1, text: "Todos os programas"}];
  var data_pdt = ["", {id: -1, text: "Todos os produtos"}]
  var data_indic = ["", {id: -1, text: "Todos os indicadores"}];
  // iObject.keys(orgao).length;
  var len_id_pgm = Object.keys(orgaos_pgms[key_org]).length;

  var id_pdt = [];
  var id_indic = [];

  for (i = 0; i < len_id_pgm; i++) {
    key_pgm = Object.keys(orgaos_pgms[key_org])[i];
    data_pgm.push({id: key_pgm, text: orgaos_pgms[key_org][key_pgm].nome});
    id_pdt.push.apply(id_pdt, orgaos_pgms[key_org][key_pgm].id_pdt);
    id_indic.push.apply(id_indic, orgaos_pgms[key_org][key_pgm].id_indic);
  }

  $pgm.html("");
  $pgm.select2({
    placeholder: "Programa",
    data: data_pgm,
    language: "pt-BR",
    width: '250px'

  });

  id_pdt_previo = id_pdt.slice(0);
  var len_id_pdt = id_pdt.length;
  id_pdt.sort(function(a, b) {
    return a - b;
  });

  for (i = 0; i < len_id_pdt; i++) {
    data_pdt.push({id: id_pdt[i], text: produto[id_pdt[i]].nome});
    id_indic.push.apply(id_indic, produto[id_pdt[i]].id_indic);
  }

  $pdt.html("");
  $pdt.select2({
    placeholder: "Produto",
    data: data_pdt,
    language: "pt-BR",
    width: '200px'

  });

  //id_indic = $.unique(id_indic);
  id_indic_previo = id_indic.slice(0);
  var len_id_indic = id_indic.length;

  id_indic.sort(function(a, b) {
    return a - b;
  });

  for (i = 0; i < len_id_indic; i++) {
    data_indic.push({id: id_indic[i], text: indicador[id_indic[i]]});
  }

  $indic.html("");
  $indic.select2({
    placeholder: "Indicador",
    data: data_indic,
    language: "pt-BR",
    width: '260px'

  });
});

// Filtrar por programa
$pgm.on("change", function() {

  if ($pgm.select2("val") === "") {
        return 0
  }

  $obj_estrat.select2("val", "");
  var data_pdt = ["", {id: -1, text: "Todos os produtos"}]
  var data_indic = ["", {id: -1, text: "Todos os indicadores"}];

  var key_pgm = $pgm.val();
  var key_org = $orgao.val();

  if (key_pgm === "-1") {
    if (key_org === "-1" || key_org === "") {
      iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
      return 0;
    }
    else {
      var id_pdt = id_pdt_previo.slice(0);
      var id_indic = id_indic_previo.slice(0);
    }
  }
  else {
    if (key_org === "-1" || key_org === "") {
      var id_pdt = programa[key_pgm].id_pdt.slice(0);
      var id_indic = programa[key_pgm].id_indic.slice(0);
    }
    else{
      var id_pdt = orgaos_pgms[key_org][key_pgm].id_pdt.slice(0);
      var id_indic = orgaos_pgms[key_org][key_pgm].id_indic.slice(0);
    }
  }

  var len_id_pdt = id_pdt.length;
  id_pdt.sort(function(a, b) {
    return a - b;
  });
  for (i = 0; i < len_id_pdt; i++) {
    data_pdt.push({id: id_pdt[i], text: produto[id_pdt[i]].nome});
    id_indic.push.apply(id_indic, produto[id_pdt[i]].id_indic);
  }

  $pdt.html("");
  $pdt.select2({
    placeholder: "Produto",
    data: data_pdt,
    language: "pt-BR",
    width: '200px'

  });

  var len_id_indic = id_indic.length;
  id_indic.sort(function(a, b) {
    return a - b;
  });
  for (i = 0; i < len_id_indic; i++) {
    data_indic.push({id: id_indic[i], text: indicador[String(id_indic[i])]});
  }
  id_indic_previo = id_indic.slice(0);

  $indic.html("");
  $indic.select2({
    placeholder: "Indicador",
    data: data_indic,
    language: "pt-BR",
    width: '260px'

  });
});

// Filtrar por produto
$pdt.on("change", function() {

  if ($pdt.select2("val") === "") {
        return 0
  }
  $obj_estrat.select2("val", "");
  data_indic = ["", {id: -1, text: "Todos os indicadores"}];
  var key_pdt = $pdt.val();
  var key_pgm = $pgm.val();
  var key_org =$orgao.val();
  if (key_pdt === "-1") {
    if ((key_org === "-1" || key_org === "") && (key_pgm === "-1" || key_pgm === "")) {
      iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
      return 0;
    }
    else {
      var id_indic = id_indic_previo.slice(0);
    }
  }
  else { var id_indic = produto[key_pdt].id_indic.slice(0); }

  //id_indic = $.unique(id_indic);
  var len_id_indic = id_indic.length;

  for (i = 0; i < len_id_indic; i++) {
    data_indic.push({id: id_indic[i], text: indicador[id_indic[i]]});
  }

  $indic.html("");
  $indic.select2({
    placeholder: "Indicador",
    data: data_indic,
    language: "pt-BR",
    width: '260px'

  });
});

$indic.on("change", function() {
    if ($indic.select2("val") === "") {
        return 0
    }
    $obj_estrat.select2("val", "");
});

$obj_estrat.on("change", function() {
    if ($obj_estrat.select2("val") === "") {
        return 0
    }

    if ($indic.val() || $pdt.val() || $pgm.val() || $orgao.val()) {
      iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos, true);
    }

    $orgao.html("");
    $orgao.select2({
    placeholder: "Órgão",
    data: data_orgao_todos,
    language: "pt-BR",
    width: '200px'
    });
});

////////////////////////////////// Fim das definições do menu //////////////////////////////////

var bUpdateURL = true;

function ajax_post(tipo, codigo) {
  $(".nvtooltip").remove(); // eliminar resíduo da biblioteca nv3d
  $("article").html('<img src="img/loading.gif" alt="carregando...">');
  $.post("/obterInfo", {"tipo": tipo, "codigo": codigo}).done( function(texto) {
      $("article").html(texto);
      $('html, body').animate({scrollTop: '0px'}, 0);
      if (bUpdateURL) {
        if (tipo && codigo) {
          history.pushState({'tipo': tipo, 'codigo': codigo}, 'title', '/' + tipo + '/' + codigo);
        }
        else {
          history.pushState({'tipo': '', 'codigo': ''}, 'title', '/');
        }
      }
      // iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
      // select(codigo, '#' + tipo);
    });
}

$(".form-control").on("select2:close", function() {
    btnIR();
});

function btnIR() {
    if ($indic.val() || $pdt.val() || $pgm.val() || $orgao.val() || $obj_estrat.val()) {
            var _orgao = $orgao.val();
            var _pgm = $pgm.val();
            var _pdt = $pdt.val();
            var _indic = $indic.val();
            var _obj_estrat = $obj_estrat.val();
            var tipo = '';
            var codigo = '';
            if (_indic && _indic != '-1') {tipo = 'indicador'; codigo = _indic;}
            else if (_pdt && _pdt != '-1') {tipo = 'produto'; codigo = _pdt;}
            else if (_pgm && _pgm != '-1') {tipo = 'programa'; codigo = _pgm;}
            else if (_orgao && _orgao != '-1') {tipo = 'orgao'; codigo = _orgao;}
            else if (_obj_estrat && _obj_estrat != '-1') {tipo = 'obj_estrat'; codigo = _obj_estrat;}
            bUpdateURL = true;
            ajax_post(tipo, codigo);
        }
}
// Botão ir
// $("#btnIR").click(function() {

//     if ($indic.val() || $pdt.val() || $pgm.val() || $orgao.val() || $obj_estrat.val()) {
//             var _orgao = $orgao.val();
//             var _pgm = $pgm.val();
//             var _pdt = $pdt.val();
//             var _indic = $indic.val();
//             var _obj_estrat = $obj_estrat.val();
//             var tipo = '';
//             var codigo = '';
//             if (_indic && _indic != '-1') {tipo = 'indicador'; codigo = _indic;}
//             else if (_pdt && _pdt != '-1') {tipo = 'produto'; codigo = _pdt;}
//             else if (_pgm && _pgm != '-1') {tipo = 'programa'; codigo = _pgm;}
//             else if (_orgao && _orgao != '-1') {tipo = 'orgao'; codigo = _orgao;}
//             else if (_obj_estrat && _obj_estrat != '-1') {tipo = 'obj_estrat'; codigo = _obj_estrat;}
//             bUpdateURL = true;
//             ajax_post(tipo, codigo);
//         }
// });

// https://developer.mozilla.org/en-US/docs/Web/API/History_API/Example
// http://cacheandquery.com/blog/2012/02/the-right-way-for-now-to-use-html5-history-api/
onpopstate = function(oEvent) {
  bUpdateURL = false;
  iniciar_menu(data_pgm_todos, data_pdt_todos, data_indic_todos, data_obj_estrategico_todos);
  if (oEvent.state !== null){
    ajax_post(oEvent.state.tipo, oEvent.state.codigo);
    select(oEvent.state.codigo, '#' + oEvent.state.tipo);
  }
  else {
    ajax_post('', '');
    select('', '#');
  }

}

function ir_a_link(codigo, tipo) {
    bUpdateURL = true;
    ajax_post(tipo, codigo);
    select(codigo, '#' + tipo);
}

function select(codigo, tipo){
  var selects = [$obj_estrat, $orgao, $pgm, $pdt, $indic];
  var flag = false;
  if (codigo === '' && tipo === '#') {flag = true; $orgao.select2("val", '-1')}
  for (var i = 0; i < selects.length; i++) {
    if (selects[i].selector === tipo) {
        selects[i].select2("val", codigo);
        flag = true;
    }
    else if (flag) {
        selects[i].select2("val", '');
    }
  }
}

function despesa_orgao(cod_org) {
    $("#o" + atual_cod_org).css("display", "none");
    $(".o" + atual_cod_org).toggleClass("ativo inativo");
    $("#o" + cod_org).css("display", "block");
    $(".o" + cod_org).toggleClass("inativo ativo");
    atual_cod_org = cod_org;
}

function update_bullet_chart(n) {
    $(".l" + atual_bullet_chart).toggleClass("ativo inativo");
    $(".l" + n).toggleClass("inativo ativo");
    atual_bullet_chart = n;
    // var d1;
    var d2;
    if (n === '1') {d2 = dataWithLabelsRecente1;}
    else if (n === '2') {d2 = dataWithLabelsRecente2;}
    else if (n === '3') {d2 = dataWithLabelsRecente3;}
    else if (n === '4') {d2 = dataWithLabelsRecente4;}
    else if (n === 'total') {d2 = dataWithLabelsRecentetotal;}

    // chartBulletPPA = null;
    // d3.select('#chart-bullet-ppa svg').html('');

    // nv.addGraph(function() {

    // chartBulletPPA = nv.models.bulletChart()
    //     .options({
    //         useInteractiveGuideline: true,
    // });

    // chartBulletPPA.margin({'left': marginleft});
    // d3.select('#chart-bullet-ppa svg')
    //   .data(d1)
    //   .transition().duration(200)
    //   .call(chartBulletPPA);
    // nv.utils.windowResize(chartBulletPPA.update);

    // });

    chartBulletRecente = null;
    d3.select('#chart-bullet-recente svg').html('');
    nv.addGraph(function() {

    chartBulletRecente = nv.models.bulletChart()
        .options({
            useInteractiveGuideline: true,
    });

    chartBulletRecente.margin({'left': marginleft});
    d3.select('#chart-bullet-recente svg')
      .data(d2)
      .transition().duration(200)
      .call(chartBulletRecente);
    nv.utils.windowResize(chartBulletRecente.update);

    });

    setTimeout(function(){
    // $('#chart-bullet-ppa .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_pgm_ppa_' + n ] + ')' ).attr("fill", "white").attr("stroke-width","1px");
    // $('#chart-bullet-ppa .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_org_ppa_' + n ] + ')' ).attr("d", "M 0,0 m -5,-5 L 5,-5 L 5,5 L -5,5 Z").attr("fill", "white").attr("stroke-width","1px");
    // $('#chart-bullet-ppa .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_esp_ppa_' + n ] + ')' ).attr("d", "M 0, 0  m -5, 0  a 5,5 0 1,0 10,0  a 5,5 0 1,0 -10,0").attr("fill", "white").attr("stroke-width","1px");

    $('#chart-bullet-recente .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_pgm_recente_' + n] + ')' ).attr("fill", "white").attr("stroke-width","1px");
    $('#chart-bullet-recente .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_org_recente_' + n] + ')' ).attr("d", "M 0,0 m -5,-5 L 5,-5 L 5,5 L -5,5 Z").attr("fill", "white").attr("stroke-width","1px");
    $('#chart-bullet-recente .nv-markerTriangle:nth-of-type(' + n_formas_bullet['n_esp_recente_' + n] + ')' ).attr("d", "M 0, 0  m -5, 0  a 5,5 0 1,0 10,0  a 5,5 0 1,0 -10,0").attr("fill", "white").attr("stroke-width","1px");
    }, 50);
}


function hint_copied() {
    $("#unique_url").attr('data-hint', 'copiado!');
    setTimeout(function(){$("#unique_url").removeAttr('data-hint');}, 500);
}

var pt_BR = {
              "decimal": ",",
              "thousands": ".",
              "grouping": [3],
              "currency": ["R$", ""],
              "dateTime": "%d/%m/%Y %H:%M:%S",
              "date": "%d/%m/%Y",
              "time": "%H:%M:%S",
              "periods": ["AM", "PM"],
              "days": ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
              "shortDays": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
              "months": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
              "shortMonths": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            }

var BR = d3.locale(pt_BR);

// var colorsBom = ["#236323", "white"];
// var colorsMedio = ["#ffda47", "white"];
// var colorsRuim = ["#bc2525", "white"];

var table_orc = null;
var button_orc, cod_acao_control, liLiq, liEmp, liDot, liFis, unidade, unidade_medida;

function orc_acao(cod_acao) {
  if (cod_acao_control !== null & cod_acao_control === cod_acao) {
  	cod_acao_control = null;
  	$('#opcoes-orc').hide();
  	table_orc.hide();
    $('#acao-' + cod_acao).hide();
  	table_orc = false;
  }
  else {
    $('#acao-' + cod_acao_control).hide();
    $('#acao-' + cod_acao).show();
  	cod_acao_control = cod_acao;
  	liLiq.attr('onclick', 'orc_func(' + cod_acao + ',"LIQUIDADO_MENSAL")')
  	liEmp.attr('onclick', 'orc_func(' + cod_acao + ',"EMPENHADO_MENSAL")')
  	liDot.attr('onclick', 'orc_func(' + cod_acao + ',"DOT_ATUAL_ACUM")')
  	liFis.attr('onclick', 'orc_func(' + cod_acao + ',"FISICO")')
	  $('#opcoes-orc').show();
	  if (table_orc) {
	  	table_orc.hide();
	  }
	  liLiq.addClass('ativo').removeClass('inativo');
	  liEmp.addClass('inativo').removeClass('ativo');
	  liDot.addClass('inativo').removeClass('ativo');
	  liFis.addClass('inativo').removeClass('ativo');
	  button_orc = $('.liLIQUIDADO_MENSAL');
	  $('#' + cod_acao + 'LIQUIDADO_MENSAL').show();
	  table_orc = $('#' + cod_acao + 'LIQUIDADO_MENSAL');
	  unidade.html('Em R$ mil')
  }
}

function orc_func(cod_acao, df) {
  if (table_orc) {
    table_orc.hide();
    button_orc.addClass('inativo').removeClass('ativo');
  }
  if (df === 'FISICO') {
  	unidade.html('Em ' + unidade_medida)
  }
  else {
  	unidade.html('Em R$ mil')
  }
  $('#' + cod_acao + df).show();
  $('.li' + df).addClass('ativo').removeClass('inativo');
  table_orc = $('#' + cod_acao + df);
  button_orc = $('.li' + df);
}
