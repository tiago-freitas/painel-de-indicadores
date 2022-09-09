function hide_show_table() {
  $("#org_ano_1").hide();
  $("#org_ano_2").hide();
  $("#org_ano_3").hide();
  $("#org_ano_4").hide();
  $("#org_ano_" + $("#sel_ano option:selected").val()).show();
}