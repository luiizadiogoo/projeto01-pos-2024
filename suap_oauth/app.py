from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import logging

app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

# Registro do cliente OAuth para o SUAP
oauth.register(
    name='suap',
    client_id="6JaHJ35xJKex5arVyQPzhcFbmfJp32zOgG2aBms1",
    client_secret="Z3kkY76x6jLomsOiDI2np552WYjaGwlZIbFIzKjgX3z2kvf1y86QcXNsH18nRLhJPV3Lf080lOUkgh2Lrwh4zRbDXoddXlFtGYBczAdtEv0yfKYoTOjICNrhx9oChVWu",
    api_base_url='https://suap.ifrn.edu.br/api/',
    access_token_method='POST',
    access_token_url='https://suap.ifrn.edu.br/o/token/',
    authorize_url='https://suap.ifrn.edu.br/o/authorize/',
    fetch_token=lambda: session.get('suap_token')
)

@app.route('/')
def index():
    if 'suap_token' in session:
        try:
            meus_dados = oauth.suap.get('v2/minhas-informacoes/meus-dados')
            meus_dados.raise_for_status()
            return render_template('user.html', user_data=meus_dados.json())
        except Exception as e:
            app.logger.error(f"Erro ao obter dados do usuário: {e}")
            return "Erro ao obter dados do perfil", 500
    else:
        return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.suap.authorize_redirect(redirect_uri)

@app.route('/logout')
def logout():
    session.pop('suap_token', None)
    return redirect(url_for('index'))

@app.route('/login/authorized')
def auth():
    token = oauth.suap.authorize_access_token()
    session['suap_token'] = token
    return redirect(url_for('index'))

@app.route('/boletim', methods=['POST'])
def boletim():
    if 'suap_token' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        ano_letivo = request.form['ano_letivo']
        app.logger.debug(f"Recebendo ano letivo: {ano_letivo}")
        try:
            token = session.get('suap_token')['access_token']
            headers = {
                "Authorization": f'Bearer {token}'
            }
            response = oauth.suap.get(f"v2/minhas-informacoes/boletim/{ano_letivo}/1", headers=headers)
            response.raise_for_status()
            boletim_data = response.json()
            app.logger.debug(f"Dados do boletim recebidos: {boletim_data}")
            # Renderiza o user.html com o boletim
            meus_dados = oauth.suap.get('v2/minhas-informacoes/meus-dados')
            meus_dados.raise_for_status()
            return render_template('user.html', user_data=meus_dados.json(), boletim=boletim_data, ano_letivo=ano_letivo)
        except Exception as e:
            app.logger.error(f"Erro ao obter boletim: {e}")
            return "Erro ao obter boletim", 500

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
