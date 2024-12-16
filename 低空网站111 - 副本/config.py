import os

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 管理后台配置
    FLASK_ADMIN_SWATCH = 'cerulean'
    
    # 静态文件配置
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

class ProductionConfig(Config):
    DEBUG = False
    # 生产环境特定配置
    
class DevelopmentConfig(Config):
    DEBUG = True
    # 开发环境特定配置 