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

@app.route('/admin/config')
def admin_config():
    return render_template('admin/config.html')

@app.route('/admin/logs')
def admin_logs():
    return render_template('admin/logs.html')

@app.route('/admin/stats')
def admin_stats():
    return render_template('admin/stats.html')

@app.route('/home')
def user_home():
    return render_template('user/home.html')

@app.route('/login')
def user_login():
    return render_template('user/auth/login.html')

@app.route('/billing/buy-credits')
def user_buy_credits():
    return render_template('user/billing/buy_credits.html')

@app.route('/jobs/create')
def user_create_job():
    return render_template('user/jobs/create_job.html')

@app.route('/jobs')
def user_job_list():
    return render_template('user/jobs/job_list.html')

@app.route('/api-docs')
def user_api_docs():
    return render_template('user/pages/api_docs.html')

@app.route('/blog')
def user_blog():
    return render_template('user/pages/blog.html')

@app.route('/faq')
def user_faq():
    return render_template('user/pages/faq.html')

@app.route('/privacy')
def user_privacy_policy():
    return render_template('user/pages/privacy_policy.html')

@app.route('/terms')
def user_terms():
    return render_template('user/pages/terms.html')

@app.route('/settings/account')
def user_settings_account():
    return render_template('user/settings/account.html')

@app.route('/settings/config')
def user_settings_config():
    return render_template('user/settings/config.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('user/errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('user/errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
