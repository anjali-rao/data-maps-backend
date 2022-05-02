from flask import (Flask, request, send_from_directory,
                   render_template, make_response, jsonify)

from config import Config
from MapGenerator.views import FileUploader


def build_app():


    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.APP_SECRET

    """
    defining web_admin
    """

    app.add_url_rule(
        '/upload-file/<api_version>/',
        view_func = FileUploader.as_view('upload-file')
    )

    @app.route("/")
    def status():
        return make_response(
            jsonify(
                success = True
            ),
            200
        )
    return app

app = build_app()


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=Config.PORT)

