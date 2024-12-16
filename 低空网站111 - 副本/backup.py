import os
import shutil
from datetime import datetime

def backup_database():
    """备份数据库文件"""
    # 创建备份目录
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名（包含时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'database_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_file)
    
    # 复制数据库文件
    try:
        shutil.copy2('database.db', backup_path)
        print(f'数据库已备份到: {backup_path}')
    except Exception as e:
        print(f'备份失败: {str(e)}')

def backup_project():
    """备份整个项目"""
    # 创建备份目录
    backup_dir = 'project_backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'project_backup_{timestamp}'
    backup_path = os.path.join(backup_dir, backup_name)
    
    # 要备份的文件和目录
    items_to_backup = [
        'app.py',
        'config.py',
        'requirements.txt',
        'templates',
        'static',
        'database.db',
        'PROGRESS.md'
    ]
    
    # 创建备份目录
    os.makedirs(backup_path)
    
    # 复制文件和目录
    try:
        for item in items_to_backup:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_path, item))
                else:
                    shutil.copy2(item, backup_path)
        print(f'项目已备份到: {backup_path}')
    except Exception as e:
        print(f'备份失败: {str(e)}')

if __name__ == '__main__':
    backup_database()
    backup_project() 