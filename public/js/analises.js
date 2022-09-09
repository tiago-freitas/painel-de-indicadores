var categorias = {
 10: "Aguardando autorização superior",
 11: "Lentidão na tramitação",
 12: "Dependência de assinatura de contrato/convênio",
 13: "Cancelamento da licitação",

 20: "Pendências de decisões e/ou providências de outras esferas de governo",
 21: "Falta de atribuição específica para realização do produto",
 22: "Reformas administrativas",

 30: "Impedimentos legais",
 31: "Liminar ou recurso em vigência",
 32: "Ausência de regulamentação de lei/decreto",
 33: "Aguarda aprovação/publicação de documento legal",

 40: "Inexistência de dotação específica",
 41: "Contingenciamento de dotação",
 42: "Contrapartida do Tesouro inexistente",
 43: "Contrapartida do Tesouro insuficiente",
 44: "Insuficiência de dotação (redução/suplementação)",

 50: "Falta de equipamentos/veículos necessários",
 51: "Instalações inadequadas",
 52: "Instalações sem manutenção/conservação",
 53: "Materiais e suprimentos insuficientes",
 54: "Tecnologia obsoleta",

 60: "Concepção do produto/resultado face ao problema ou necessidade detectada",
 61: "Inadequação do produto/resultado",
 62: "Inadequação da estrutura do órgão",

 70: "Recursos Humanos",
 71: "Quantidade de pessoal inadequada",
 72: "Pessoal não qualificado",

 80: "Morosidade no processo de licenciamento",
 81: "Área de proteção ambiental",
 82: "Aprovação do EIA/RIMA"}

var categorias_html = '\
<select id="select-analise" class="form-control" name="select" required> \
<option value=0 disabled selected>Selecione uma categoria</option> \
<optgroup label="Administrativo"> \
    <option value=10>Aguardando autorização superior</option> \
    <option value=11>Lentidão na tramitação</option> \
    <option value=12>Dependência de assinatura de contrato/convênio</option> \
    <option value=13>Cancelamento da licitação</option> \
</optgroup> \
<optgroup label="Institucional"> \
    <option value=20>Pendências de decisões e/ou providências de outras esferas de governo</option> \
    <option value=21>Falta de atribuição específica para realização do produto</option> \
    <option value=22>Reformas administrativas</option> \
</optgroup> \
<optgroup label="Jurídico/legal"> \
    <option value=30>Impedimentos legais</option> \
    <option value=31>Liminar ou recurso em vigência</option> \
    <option value=32>Ausência de regulamentação de lei/decreto</option> \
    <option value=33>Aguarda aprovação/publicação de documento legal</option> \
</optgroup> \
<optgroup label="Orçamentário / Financeiro"> \
    <option value=40>Inexistência de dotação específica</option> \
    <option value=41>Contingenciamento de dotação</option> \
    <option value=42>Contrapartida do Tesouro inexistente</option> \
    <option value=43>Contrapartida do Tesouro insuficiente</option> \
    <option value=44>Insuficiência de dotação (redução/suplementação)</option> \
</optgroup> \
<optgroup label="Infraestrutura / Recursos Materiais"> \
    <option value=50>Falta de equipamentos/veículos necessários</option> \
    <option value=51>Instalações inadequadas</option> \
    <option value=52>Instalações sem manutenção/conservação</option> \
    <option value=53>Materiais e suprimentos insuficientes</option> \
    <option value=54>Tecnologia obsoleta</option> \
</optgroup> \
<optgroup label="Planejamento"> \
    <option value=60>Concepção do produto/resultado face ao problema ou necessidade detectada</option> \
    <option value=61>Inadequação do produto/resultado</option> \
    <option value=62>Inadequação da estrutura do órgão</option> \
</optgroup> \
<optgroup label="Recursos Humanos"> \
    <option value=71>Quantidade de pessoal inadequada</option> \
    <option value=72>Pessoal não qualificado</option> \
</optgroup> \
<optgroup label="Ambientais"> \
    <option value=80>Morosidade no processo de licenciamento</option> \
    <option value=81>Área de proteção ambiental</option> \
    <option value=82>Aprovação do EIA/RIMA</option> \
</optgroup> \
</select>'

function login(call, msg) {
    msg = msg || '';
    vex.dialog.open({
        message: 'Insira seu nome de usuário e senha:',
        input: [
            msg,
            '<input name="username" type="text" placeholder="Username" required />',
            '<input name="password" type="password" placeholder="Password" required />'
        ].join(''),
        buttons: [
            $.extend({}, vex.dialog.buttons.YES, { text: 'Login' }),
            $.extend({}, vex.dialog.buttons.NO, { text: 'Back' })
        ],
        callback: function (data) {
            if (!data) {
                console.log('Cancelled')
            } else {
                $.ajax({
                    type: 'post',
                    url: '/key',
                    success: function(chaves) {
                        msg = CryptoJS.enc.Hex.parse(chaves.msg);
                        iv = CryptoJS.enc.Hex.parse(chaves.iv);
                        encrypted = CryptoJS.AES.encrypt(msg,
            CryptoJS.enc.Latin1.parse(data.password + Array(16 - data.password.length % 16 + 1).join('_')),
                                           { iv: iv, mode: CryptoJS.mode.CBC });
                        encrypted = encrypted.toString();

                        $.ajax({
                            type: 'post',
                            url: '/auth/login',
                            data: {'user': data.username, 'encrypted': encrypted},
                            success: function(status) {
                                if (status === 'y') {
                                    $('#login').hide();
                                    $('#logout').show();
                                    $('#send').show();
                                    $('#del').hide();
                                    $('#edit').hide();
                                    usuario = data.username;
                                    encrypted = null;
                                    $('.selected').removeClass('selected');
                                    $("#username").html('Você está logado como: <b>' + usuario + '</b>');
                                }
                                else if (status === 'n') {
                                    vex.closeTop();
                                    login(call, 'Usuário ou senha incorretos');
                                }
                            },
                        });
                    }
                });
            }
        }
    })
}

function logout() {
    $.ajax({
        type: 'post',
        url: '/auth/logout',
        success: function() {
            $('#login').show();
            $('#logout').hide();
            $("#username").html('');
            $('#send').hide();
            $('#del').hide();
            $('#edit').hide();
            usuario = null;
        }
    });
}

moment.locale('pt-br');
$.fn.dataTable.moment('DD/MM/YYYY HH:mm', 'pt-br');

$(document).ready(function(){
    $('#login').on('click', login);
    $('#logout').on('click', logout);

    $('#send').on('click', function(){
         $.ajax({
            type: 'get',
            url: '/auth/status',
            success: function(status) {
                if (status === 'n') {
                    vex.closeTop();
                    login(null, 'Sessão expirada!');
                    $('#send').hide();
                    $('#del').hide();
                    $('#edit').hide();
                }
                else if (status === 'y') {
                    vex.dialog.open({
                        message: 'Insira sua Análise:',
                        input: [categorias_html,
                            '<textarea class="form-control" rows="5" cols="50" name="analise" placeholder="Análise" style="resize: none;margin-top: 10px" required></textarea>',
                        ].join(''),
                        buttons: [
                            $.extend({}, vex.dialog.buttons.YES, { text: 'Enviar' }),
                            $.extend({}, vex.dialog.buttons.NO, { text: 'Cancelar' })
                        ],
                        callback: function (data) {
                            data.user_client = usuario;
                            data.tipo = tipo;
                            data.codigo = codigo;
                            if (!data) {
                                console.log('Cancelled')
                            } else {

                                $.ajax({
                                    type: 'post',
                                    url: '/analises',
                                    data: data,
                                    success: function(analise) {
                                if (analise) {
                                    t.row.add([analise.ID,
                                               analise.tag,
                                               moment().format('DD/MM/YYYY HH:mm'),
                                               analise.usuario,
                                               categorias[analise.tag],
                                               analise.analise]).draw();
                                }
                                },
                                });

                            }
                        }
                    })
                    //  $('.s300').multipleSelect({
                    //     selectAll: false,
                    //     width: 300,
                    // });
                }
            }
        });
    });

    $('#del').click(function(){
        $.ajax({
            type: 'post',
            url: '/analises_delete',
            data: {ID: t.row('.selected').data()[columns.id],
                   user_client: t.row('.selected').data()[columns.nome]},
            success: function(status) {
                if (status === 'y') {
                    t.row('.selected').remove().draw();
                    $('#del').hide();
                    $('#edit').hide();
                }
            },
        });
    });

    $('#edit').click(function(){
        vex.dialog.open({
            message: 'Insira sua Análise:',
            input: [
                 categorias_html,
                ('<textarea rows="5" cols="50" minlength=200 name="analise" placeholder="Análise" style="resize: none;" required>'
                    +  t.row('.selected').data()[columns.analise]  + '</textarea>')
            ].join(''),
            buttons: [
                $.extend({}, vex.dialog.buttons.YES, { text: 'Enviar' }),
                $.extend({}, vex.dialog.buttons.NO, { text: 'Cancelar' })
            ],
            callback: function (data) {
                data.user_client = usuario;
                data.ID = t.row('.selected').data()[columns.id];
                if (!data) {
                    console.log('Cancelled')
                }
                else {
                    $.ajax({
                        type: 'put',
                        url: '/analises',
                        data: data,
                        success: function(analise) {
                            if (analise === 'y') {
                                t.row('.selected').data([
                                      data.ID,
                                      data.select,
                                      t.row('.selected').data()[columns.data],
                                      t.row('.selected').data()[columns.nome],
                                      categorias[data.select],
                                      data.analise] ).draw();
                            }
                        },
                    });
                }
            }
        })
        // $('#edit-select').multipleSelect({
        //     selectAll: false,
        // });
        $('#select-analise').val(t.row('.selected').data()[columns.id_categoria]);
    });
});