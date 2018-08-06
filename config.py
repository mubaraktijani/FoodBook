import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SIZE = 128, 128
MIN_FILE_SIZE = 1
MAX_FILE_SIZE = 999000
UPLOAD_FOLDER = '/pics'
THUMB_FOLDER = '/static/thumb'
THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(12)
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    FLASKY_MAIL_SUBJECT_PREFIX = '[Facerek]'
    FLASKY_MAIL_SENDER = 'Facerek Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'canteen.db')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'canteen.db')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
