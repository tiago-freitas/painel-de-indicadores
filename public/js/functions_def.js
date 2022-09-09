function hide_show_table() {
  $("#org_ano_2016").hide();
  $("#org_ano_2017").hide();
  $("#org_ano_2018").hide();
  $("#org_ano_2019").hide();
  $("#org_ano_" + $("#sel_ano option:selected").text()).show();
}