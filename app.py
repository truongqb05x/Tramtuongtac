from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('user/index.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin/Admin.html')

@app.route('/admin/tasks')
def admin_tasks():
    return render_template('admin/tasks.html')

@app.route('/admin/transactions')
def admin_transactions():
    return render_template('admin/transactions.html')

@app.route('/admin/users')
def admin_users():
    return render_template('admin/users.html')

@app.route('/admin/reports')
def admin_reports():
    return render_template('admin/reports.html')

@app.route('/admin/user-config')
def admin_user_config():
    return render_template('admin/user_config.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('user/errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('user/errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
