from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faltas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Falta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    horas = db.Column(db.Float, nullable=False)

# Criação do banco ao iniciar (correto para Render.com)
with app.app_context():
    if not os.path.exists('faltas.db'):
        db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        funcionario = request.form['funcionario']
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        motivo = request.form['motivo']
        horas = float(request.form['horas'])
        falta = Falta(funcionario=funcionario, data=data, motivo=motivo, horas=horas)
        db.session.add(falta)
        db.session.commit()
        return redirect(url_for('index'))

    filtro_funcionario = request.args.get('filtro_funcionario')
    filtro_mes = request.args.get('filtro_mes')

    faltas = Falta.query

    if filtro_funcionario:
        faltas = faltas.filter(Falta.funcionario.ilike(f"%{filtro_funcionario}%"))

    if filtro_mes:
        try:
            ano, mes = map(int, filtro_mes.split('-'))
            faltas = faltas.filter(
                db.extract('year', Falta.data) == ano,
                db.extract('month', Falta.data) == mes
            )
        except:
            pass

    faltas = faltas.order_by(Falta.data.desc()).all()

    return render_template('index.html', faltas=faltas)

@app.route('/excluir/<int:id>', methods=['POST'])
def excluir_falta(id):
    falta = Falta.query.get_or_404(id)
    db.session.delete(falta)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/relatorio')
def relatorio():
    mes_param = request.args.get('mes')
    if mes_param:
        try:
            ano, mes = map(int, mes_param.split('-'))
        except:
            return redirect(url_for('relatorio'))
    else:
        hoje = datetime.today()
        ano, mes = hoje.year, hoje.month
        mes_param = f"{ano}-{mes:02d}"

    faltas = Falta.query.filter(
        db.extract('year', Falta.data) == ano,
        db.extract('month', Falta.data) == mes
    ).all()

    resumo = {}
    for falta in faltas:
        if falta.funcionario not in resumo:
            resumo[falta.funcionario] = {'total_faltas': 0, 'total_horas': 0}
        resumo[falta.funcionario]['total_faltas'] += 1
        resumo[falta.funcionario]['total_horas'] += falta.horas

    return render_template('relatorio.html', resumo=resumo, mes=mes_param)

if __name__ == '__main__':
    app.run()

