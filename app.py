import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'super_secret_fishing_key'

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

init_db()

@app.context_processor
def inject_settings():
    try:
        conn = get_db()
        settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
        conn.close()
        return dict(app_settings=settings)
    except:
        return dict()

@app.route('/')
def dashboard():
    conn = get_db()
    
    search_query = request.args.get('q', '')
    if search_query:
        teams = conn.execute('SELECT * FROM teams WHERE name LIKE ? ORDER BY id DESC', ('%' + search_query + '%',)).fetchall()
    else:
        teams = conn.execute('SELECT * FROM teams ORDER BY id DESC').fetchall()
    
    total_teams = len(teams)
    total_rulers = sum([1 for t in teams if t['has_ruler']])
    approved_payments = sum([1 for t in teams if t['payment_status'] == 'Aprovado'])
    
    # Calculate total collected from approved payments
    total_collected = sum([t['payment_amount'] or 0.0 for t in teams if t['payment_status'] == 'Aprovado'])
    
    conn.close()
    return render_template('dashboard.html', teams=teams, total_teams=total_teams, total_rulers=total_rulers, approved_payments=approved_payments, total_collected=total_collected, search_query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        has_ruler = 1 if request.form.get('has_ruler') else 0
        p1 = request.form.get('participant1')
        p2 = request.form.get('participant2')
        p3 = request.form.get('participant3')
        p4 = request.form.get('participant4')
        is_courtesy = 1 if request.form.get('is_courtesy') else 0
        
        payment_amount_str = request.form.get('payment_amount', '0')
        try:
            payment_amount = float(payment_amount_str)
        except ValueError:
            payment_amount = 0.0
        
        if not is_courtesy:
            if 'receipt' not in request.files:
                flash('Nenhum arquivo enviado.')
                return redirect(request.url)
            file = request.files.get('receipt')
            if not file or file.filename == '':
                flash('Nenhum arquivo selecionado.')
                return redirect(request.url)
            if not allowed_file(file.filename):
                flash('Tipo de arquivo não permitido.')
                return redirect(request.url)
            
            filename = secure_filename(file.filename)
            safe_name = secure_filename(name)
            if not safe_name:
                safe_name = "equipe"
            unique_filename = f"{safe_name}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
        else:
            unique_filename = "cortesia.png"
            
        conn = get_db()
        settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
        circuit_name = settings['circuit_name'] if settings else 'N/A'
        stage_name = settings['stage_name'] if settings else 'N/A'
        year = settings['year'] if settings else 'N/A'

        payment_status = 'Aprovado' if is_courtesy else 'Pendente'

        conn.execute('INSERT INTO teams (name, contact, has_ruler, receipt_filename, participant1, participant2, participant3, participant4, circuit_name, stage_name, year, is_courtesy, payment_status, payment_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (name, contact, has_ruler, unique_filename, p1, p2, p3, p4, circuit_name, stage_name, year, is_courtesy, payment_status, payment_amount))
        conn.commit()
        conn.close()
        
        flash('Equipe cadastrada com sucesso!')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/update_status/<int:team_id>', methods=['POST'])
def update_status(team_id):
    status = request.form.get('status')
    if status in ['Pendente', 'Aprovado']:
        conn = get_db()
        conn.execute('UPDATE teams SET payment_status = ? WHERE id = ?', (status, team_id))
        conn.commit()
        conn.close()
        flash('Status atualizado com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    conn = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        has_ruler = 1 if request.form.get('has_ruler') else 0
        p1 = request.form.get('participant1')
        p2 = request.form.get('participant2')
        p3 = request.form.get('participant3')
        p4 = request.form.get('participant4')
        is_courtesy = 1 if request.form.get('is_courtesy') else 0
        
        payment_amount_str = request.form.get('payment_amount', '0')
        try:
            payment_amount = float(payment_amount_str)
        except ValueError:
            payment_amount = 0.0
        
        conn.execute('UPDATE teams SET name = ?, contact = ?, has_ruler = ?, participant1 = ?, participant2 = ?, participant3 = ?, participant4 = ?, is_courtesy = ?, payment_amount = ? WHERE id = ?', 
                     (name, contact, has_ruler, p1, p2, p3, p4, is_courtesy, payment_amount, team_id))
        
        if is_courtesy:
            conn.execute("UPDATE teams SET payment_status = 'Aprovado' WHERE id = ?", (team_id,))
            
        conn.commit()
        conn.close()
        flash('Equipe atualizada com sucesso!')
        return redirect(url_for('dashboard'))
        
    team = conn.execute('SELECT * FROM teams WHERE id = ?', (team_id,)).fetchone()
    conn.close()
    if not team:
        flash('Equipe não encontrada.')
        return redirect(url_for('dashboard'))
    return render_template('edit_team.html', team=team)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        circuit_name = request.form.get('circuit_name')
        stage_name = request.form.get('stage_name')
        year = request.form.get('year')
        conn = get_db()
        conn.execute('UPDATE settings SET circuit_name = ?, stage_name = ?, year = ? WHERE id = 1', (circuit_name, stage_name, year))
        conn.commit()
        conn.close()
        flash('Configurações salvas!')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    conn.close()
    return render_template('settings.html', settings=settings)
@app.route('/results', methods=['GET'])
def results():
    conn = get_db()
    
    circuits = conn.execute('SELECT DISTINCT circuit_name FROM teams WHERE circuit_name IS NOT NULL').fetchall()
    stages = conn.execute('SELECT DISTINCT stage_name FROM teams WHERE stage_name IS NOT NULL').fetchall()
    years = conn.execute('SELECT DISTINCT year FROM teams WHERE year IS NOT NULL').fetchall()
    
    selected_circuit = request.args.get('circuit_name', '')
    selected_stage = request.args.get('stage_name', '')
    selected_year = request.args.get('year', '')
    
    query = "SELECT * FROM teams WHERE payment_status = 'Aprovado'"
    params = []
    
    if selected_circuit:
        query += " AND circuit_name = ?"
        params.append(selected_circuit)
    if selected_stage:
        query += " AND stage_name = ?"
        params.append(selected_stage)
    if selected_year:
        query += " AND year = ?"
        params.append(selected_year)
        
    query += " ORDER BY id DESC"
    
    teams = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('results.html', 
                           teams=teams, 
                           circuits=[c['circuit_name'] for c in circuits],
                           stages=[s['stage_name'] for s in stages],
                           years=[y['year'] for y in years],
                           selected_circuit=selected_circuit,
                           selected_stage=selected_stage,
                           selected_year=selected_year)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
