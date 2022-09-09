import base64
import os
import sqlite3
import time

import cherrypy
from Crypto import Random
from Crypto.Cipher import AES

SESSION_KEY = '_cp_username'
IV = '_cp_iv'
MSG = '_cp_msg'
DB = 'private/db/analises.db'

users = {'salvador': 'consulta',
         'tiago': 'consulta',
         'meyer': 'consulta',
         'marialba': 'consulta',
         'otaviano': 'consulta',
         'avaneide': 'consulta',
         'cecilia': 'consulta',
         'stella': 'consulta',
         'regina': 'consulta'}

ids = {'salvador': 0,
       'tiago': 1,
       'meyer': 2,
       'marialba': 3,
       'otaviano': 4,
       'avaneide': 5,
       'cecilia': 6,
       'stella': 7,
       'regina': 8}

def check_auth(session, user_client):
    usuario_server = session.get(SESSION_KEY)

    if usuario_server is None or not usuario_server:
        return False

    if usuario_server != user_client:
        return False

    return usuario_server

def pad(key):
    return key + b'_' * (16 - len(key) % 16)

class AuthController():

    @cherrypy.expose
    def login(self, encrypted, user):
        if not (encrypted and user):
            return 'n'
        if user not in users:
            return 'n'

        key = pad(bytes(users[user], 'latin-1'))

        iv = cherrypy.session.get(IV)
        msg = cherrypy.session.get(MSG)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = base64.standard_b64decode(bytes(encrypted, 'utf-8'))
        msg_client, *_ = cipher.decrypt(encrypted).split(b':')

        if msg == msg_client:
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = user
            return 'y'
        else:
            return 'n'

    @cherrypy.expose
    def status(self):
        if cherrypy.session.get(SESSION_KEY) is None:
            return 'n'
        return 'y'

    @cherrypy.expose
    def logout(self):
        session = cherrypy.session
        username = session.get(SESSION_KEY)
        del session[SESSION_KEY]
        if username:
            cherrypy.request.login = None

class Key():
    exposed = True

    @cherrypy.tools.accept(media='application/javascript')
    @cherrypy.tools.json_out()
    def POST(self):
        msg = Random.new().read(AES.block_size) + b':'
        iv = Random.new().read(AES.block_size)
        cherrypy.session[MSG] = msg[:-1]
        cherrypy.session[IV] = iv

        return {'msg': msg.hex(), 'iv': iv.hex()}


class Analises():
    exposed = True

    def __init__(self):
        self.select_sql = """SELECT id,
                                    tag,
                                    strftime('%d/%m/%Y %H:%M', data, 'localtime'),
                                    usuario,
                                    categorias.nome_categoria,
                                    analise
                             FROM analises
                             LEFT OUTER JOIN categorias
                                ON analises.tag = categorias.id_categoria
                             WHERE tipo = ? AND
                                   codigo = ?"""

        self.insert_sql = """INSERT INTO analises
                            (tipo,
                             codigo,
                             id_usuario,
                             usuario,
                             analise,
                             tag) VALUES (?, ?, ?, ?, ?, ?)"""

        self.update_sql = """UPDATE analises
                             SET analise = ?,
                                 tag = ?
                             WHERE ID = ?"""

    @cherrypy.tools.accept(media='application/javascript')
    @cherrypy.tools.json_out()
    def GET(self, **data):
        with sqlite3.connect(DB) as conn:
            dados = conn.execute(self.select_sql, (data['tipo'], data['codigo'])).fetchall()
        return {'data': dados}

    @cherrypy.tools.accept(media='application/javascript')
    @cherrypy.tools.json_out()
    def POST(self, **data):
        user_server = check_auth(cherrypy.session, data['user_client'])
        if not user_server:
            return False

        tags = (','.join(data['select'])
                if isinstance(data['select'], list)
                else data['select'])

        with sqlite3.connect(DB) as conn:
            conn.execute(self.insert_sql, (data['tipo'],
                                           data['codigo'],
                                           ids[user_server],
                                           user_server,
                                           data['analise'],
                                           tags))

            ID = conn.execute('SELECT last_insert_rowid()').fetchone()

        return {'ID': ID[0],
                'usuario': user_server,
                'analise': data['analise'],
                'tag': tags}

    @cherrypy.tools.accept(media='application/javascript')
    @cherrypy.tools.json_out()
    def PUT(self, **data):
        user_server = check_auth(cherrypy.session, data['user_client'])
        if not user_server:
            return 'n'

        try:
            tags = (','.join(data['select'])
                    if isinstance(data['select'], list)
                    else data['select'])

            with sqlite3.connect(DB) as conn:
                conn.execute(self.update_sql, (data['analise'],
                                               tags,
                                               data['ID']))
            return 'y'

        except:
            return 'n'

class Analises_delete():
    exposed = True

    def __init__(self):
        self.delete_sql = 'DELETE FROM analises WHERE id = ? AND usuario = ?'

    @cherrypy.tools.accept(media='application/javascript')
    @cherrypy.tools.json_out()
    def POST(self, user_client, ID):
        user_server = check_auth(cherrypy.session, user_client)
        if not user_server:
            return 'n'

        with sqlite3.connect(DB) as conn:
            conn.execute(self.delete_sql, (ID, user_server))
        return 'y'
