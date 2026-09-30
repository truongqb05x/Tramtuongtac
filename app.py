from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('user/index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('user/errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('user/errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
