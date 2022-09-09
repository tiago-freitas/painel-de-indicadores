function hide_show_table() {
  $("#org_ano_2020").hide();
  $("#org_ano_2021").hide();
  $("#org_ano_2022").hide();
  $("#org_ano_2023").hide();
  $("#org_ano_" + $("#sel_ano option:selected").text()).show();
}