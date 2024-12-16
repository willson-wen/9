from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # 用于session加密
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'  # 管理界面主题

db = SQLAlchemy(app)

# 先定义所有模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 定义EVTOL公司模型
class EvtolCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50))
    description = db.Column(db.Text)
    certification_status = db.Column(db.String(100))
    
# 定义EVTOL产品模型
class EvtolProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('evtol_company.id'))
    model_name = db.Column(db.String(100), nullable=False)
    max_range = db.Column(db.Float)
    max_speed = db.Column(db.Float)
    passenger_capacity = db.Column(db.Integer)
    
# 添加Job模型定义
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
# 在所有模型定义之后再导入和配置 Flask-Admin
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

# 初始化 Flask-Admin
admin = Admin(
    app, 
    name='EVTOL管理后台', 
    template_mode='bootstrap3',
    index_view=SecureAdminIndexView()
)

# 添加视图
admin.add_view(SecureModelView(User, db.session, name='用户管理'))
admin.add_view(SecureModelView(EvtolCompany, db.session, name='EVTOL公司'))
admin.add_view(SecureModelView(EvtolProduct, db.session, name='EVTOL产品'))
admin.add_view(SecureModelView(Job, db.session, name='招聘信息'))

# 添加管理员登录路由
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_user = AdminUser.query.filter_by(username=username).first()
        if admin_user and admin_user.check_password(password):
            session['is_admin'] = True
            return redirect('/admin')
        
        flash('用户名或密码错误')
    return render_template('admin/login.html')

# 创建默认管理员账号
def create_admin():
    if not AdminUser.query.filter_by(username='admin').first():
        admin_user = AdminUser(username='admin')
        admin_user.set_password('admin123')  # 设置默认密码
        db.session.add(admin_user)
        db.session.commit()

# 在路由部分之前添加辅助函数
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# 修改首页路由
@app.route('/')
def home():
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/search')
def search():
    try:
        query = request.args.get('q', '')
        print(f"搜索查询: {query}")
        
        companies = EvtolCompany.query.filter(
            db.or_(
                EvtolCompany.name.like(f'%{query}%'),
                EvtolCompany.country.like(f'%{query}%'),
                EvtolCompany.description.like(f'%{query}%')
            )
        ).all()
        
        results = {
            'companies': [{
                'name': c.name,
                'country': c.country,
                'description': c.description,
                'certification_status': c.certification_status
            } for c in companies]
        }
        
        print(f"搜索结果: {results}")
        return jsonify(results)
    
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        return jsonify({'error': '搜索出错'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已被注册'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': '注册成功'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return jsonify({'message': '登录成功'})
        
        return jsonify({'error': '用户名或密码错误'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# 添加密钥用于session加密
app.secret_key = 'your-secret-key'  # 在生产环境中使用更安全的密钥

# 添加招聘相关路由
@app.route('/jobs')
def jobs_list():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    user = get_current_user()
    return render_template('jobs.html', jobs=jobs, user=user)

@app.route('/jobs/post', methods=['GET', 'POST'])
def post_job():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        job = Job(
            title=request.form.get('title'),
            company=request.form.get('company'),
            location=request.form.get('location'),
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            salary_range=request.form.get('salary_range'),
            contact_email=request.form.get('contact_email'),
            user_id=user.id
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('jobs_list'))
    
    return render_template('post_job.html', user=user)

def init_db_data():
    """初始化数据库数据"""
    # 检查是否已有数据
    if EvtolCompany.query.count() > 0:
        return
        
    # 中国公司数据
    chinese_companies = [
        {
            "name": "亿航智能",
            "country": "中国",
            "description": "全球领先的自动驾驶飞行器制造商，主打EH216系列自动驾驶航空器",
            "certification_status": "已获得中国民航局型号合格证"
        },
        {
            "name": "小鹏汇天",
            "country": "中国",
            "description": "专注于低空载人飞行器研发，推出X2系列飞行汽车",
            "certification_status": "正在申请适航认证"
        },
        {
            "name": "极飞科技",
            "country": "中国",
            "description": "农业无人机龙头企业，正在开发载人eVTOL项目",
            "certification_status": "研发阶段"
        },
        {
            "name": "华夏天信",
            "country": "中国",
            "description": "专注于开发新一代电动垂直起降飞行器",
            "certification_status": "原型机测试阶段"
        },
        {
            "name": "德事隆航空",
            "country": "中国",
            "description": "致力于研发新型电动垂直起降飞行器，主打城市空中交通",
            "certification_status": "概念验证阶段"
        },
        {
            "name": "航天科工",
            "country": "中国",
            "description": "国家级航空航天企业，正在开发多款eVTOL产品",
            "certification_status": "研发测试阶段"
        },
        {
            "name": "锐翔航空",
            "country": "中国",
            "description": "专注于电动垂直起降技术研发，已有多个原型机",
            "certification_status": "飞行测试阶段"
        },
        {
            "name": "零度智控",
            "country": "中国",
            "description": "从无人机起步，正在开发载人级eVTOL产品",
            "certification_status": "原型机开发阶段"
        },
        {
            "name": "大疆创新",
            "country": "中国",
            "description": "全球领先的无人机制造商，正在布局载人eVTOL领域",
            "certification_status": "研发阶段"
        },
        {
            "name": "中航工业",
            "country": "中国",
            "description": "国家级航空工业集团，开发多款新型电动空器",
            "certification_status": "多个项目并行推进中"
        }
    ]
    
    # 国外公司数据
    foreign_companies = [
        {
            "name": "Joby Aviation",
            "country": "美国",
            "description": "领先的eVTOL开发商，已获得重要适航认证里程碑",
            "certification_status": "FAA认证最后阶段"
        },
        {
            "name": "Lilium",
            "country": "德国",
            "description": "开发创新的喷气式eVTOL，采用独特的矢量推进系统",
            "certification_status": "EASA认证进行中"
        },
        {
            "name": "Volocopter",
            "country": "德国",
            "description": "专注于城市空中交通，开发VoloCity空中出租车",
            "certification_status": "EASA认证进行中"
        },
        {
            "name": "Archer Aviation",
            "country": "美国",
            "description": "开发Maker电动空中出租车，获得联合航空投资",
            "certification_status": "FAA认证进行中"
        },
        {
            "name": "Beta Technologies",
            "country": "美国",
            "description": "开发ALIA电动飞机，主打货运和客市场",
            "certification_status": "FAA认证测试阶段"
        },
        {
            "name": "Vertical Aerospace",
            "country": "英国",
            "description": "开发VX4 eVTOL，已获得大量预订单",
            "certification_status": "CAA/EASA认证进行中"
        },
        {
            "name": "Eve Air Mobility",
            "country": "巴西",
            "description": "巴西航空工业子公司，开发新一代eVTOL",
            "certification_status": "ANAC认证进行中"
        },
        {
            "name": "Wisk Aero",
            "country": "美国",
            "description": "波音支持的自动驾驶eVTOL开发商",
            "certification_status": "FAA认证早期阶段"
        },
        {
            "name": "SkyDrive",
            "country": "日本",
            "description": "开发SD-03型飞行汽车，计划2025年商用",
            "certification_status": "JCAB认证进行中"
        },
        {
            "name": "Overair",
            "country": "美国",
            "description": "开发Butterfly eVTOL采用独特的推进系统",
            "certification_status": "FAA认证早期段"
        }
    ]
    
    # 添加公司数据到数据库
    for company_data in chinese_companies + foreign_companies:
        company = EvtolCompany(**company_data)
        db.session.add(company)
    
    # 提交更改
    db.session.commit()
    
def add_sample_jobs():
    """添加示例招聘信息"""
    if Job.query.count() > 0:
        return
        
    sample_jobs = [
        {
            "title": "EVTOL飞行器测试工程师",
            "company": "亿航智能",
            "location": "广州",
            "description": "负责EH216系列EVTOL飞行器的飞行测试和性能评估，确保飞行安全性和可靠性。",
            "requirements": "1. 航空工程相关专业本科及以上学历\n2. 3年以上飞行器测试经验\n3. 熟悉适航条例和测试规范\n4. 具有试飞经验者优先",
            "salary_range": "25k-35k",
            "contact_email": "hr@ehang.com"
        },
        {
            "title": "电机系统工程师",
            "company": "小鹏汇天",
            "location": "深圳",
            "description": "负责X2系列飞行器电机系统开发和优化，提升动力系统效率。",
            "requirements": "1. 电气工程专业硕士及以上学历\n2. 精通电机控制系统设计\n3. 具有新能源汽车电机开发经验优先",
            "salary_range": "30k-45k",
            "contact_email": "careers@xiaopeng.com"
        },
        {
            "title": "飞控软件工程师",
            "company": "大疆创新",
            "location": "深圳",
            "description": "开发EVTOL飞行控制系统，实现自动驾驶功能。",
            "requirements": "1. 计算机或航空专业硕士\n2. 精通C++编程\n3. 具有飞控算法开发经验",
            "salary_range": "35k-50k",
            "contact_email": "jobs@dji.com"
        },
        {
            "title": "结构设计工程师",
            "company": "Joby Aviation",
            "location": "上海",
            "description": "负责EVTOL机体结构设计和优化，确保结构强度和轻量化。",
            "requirements": "1. 机械工程专业\n2. 熟练使用CATIA等设计软件\n3. 具有复合材料设计经验",
            "salary_range": "40k-60k",
            "contact_email": "china@jobyaviation.com"
        },
        {
            "title": "系统集成工程师",
            "company": "Lilium",
            "location": "北京",
            "description": "负责EVTOL各系统集成和测试，确保系统兼容性。",
            "requirements": "1. 航空工程相关专业\n2. 具有系统集成经验\n3. 熟悉航空系统架构",
            "salary_range": "35k-50k",
            "contact_email": "beijing@lilium.com"
        },
        {
            "title": "适航认证专员",
            "company": "中航工业",
            "location": "西安",
            "description": "负责EVTOL适航认证相关工作，与民航局对接。",
            "requirements": "1. 航空法规相关专业\n2. 熟悉适航条例\n3. 具有认证项目经验",
            "salary_range": "25k-40k",
            "contact_email": "cert@avic.com"
        },
        {
            "title": "动力系统工程师",
            "company": "Beta Technologies",
            "location": "苏州",
            "description": "负责EVTOL动力系统开发和测试。",
            "requirements": "1. 动力工程专业\n2. 熟悉电动推进系统\n3. 具有新能源动力系统开发经验",
            "salary_range": "30k-45k",
            "contact_email": "suzhou@beta.com"
        },
        {
            "title": "空气动力工程师",
            "company": "Vertical Aerospace",
            "location": "成都",
            "description": "负责EVTOL气动设计和优化，提升飞行性能。",
            "requirements": "1. 航空工程专业\n2. 精通CFD分析\n3. 具有气动设计经验",
            "salary_range": "28k-43k",
            "contact_email": "aero@vertical-aerospace.com"
        },
        {
            "title": "航电系统工程师",
            "company": "航天科工",
            "location": "天津",
            "description": "负责EVTOL航电系统开发和集成。",
            "requirements": "1. 航空电子专业\n2. 熟悉航电系统架构\n3. 具有DO-254认证经验",
            "salary_range": "25k-38k",
            "contact_email": "avionics@casic.com"
        },
        {
            "title": "电池系统工程师",
            "company": "Eve Air Mobility",
            "location": "武汉",
            "description": "负责EVTOL动力电池系统开发和管理。",
            "requirements": "1. 电化学相关专业\n2. 熟悉电池管理系统\n3. 具有动力电池开发经验",
            "salary_range": "28k-42k",
            "contact_email": "battery@eveairmobility.com"
        }
    ]
    
    for job_data in sample_jobs:
        job = Job(**job_data)
        db.session.add(job)
    db.session.commit()

def add_sample_products():
    """添加示例EVTOL产品信息"""
    if EvtolProduct.query.count() > 0:
        return
        
    sample_products = [
        {
            "company_id": 1,  # 亿航智能
            "model_name": "EH216-S",
            "max_range": 35,
            "max_speed": 130,
            "passenger_capacity": 2
        },
        {
            "company_id": 1,
            "model_name": "EH216-F",
            "max_range": 40,
            "max_speed": 130,
            "passenger_capacity": 0  # 货运版本
        },
        {
            "company_id": 2,  # 小鹏汇天
            "model_name": "X2",
            "max_range": 35,
            "max_speed": 130,
            "passenger_capacity": 2
        },
        {
            "company_id": 2,
            "model_name": "X3",
            "max_range": 45,
            "max_speed": 150,
            "passenger_capacity": 4
        },
        {
            "company_id": 11,  # Joby Aviation
            "model_name": "S4",
            "max_range": 240,
            "max_speed": 320,
            "passenger_capacity": 4
        },
        {
            "company_id": 12,  # Lilium
            "model_name": "Lilium Jet",
            "max_range": 250,
            "max_speed": 280,
            "passenger_capacity": 6
        },
        {
            "company_id": 13,  # Volocopter
            "model_name": "VoloCity",
            "max_range": 35,
            "max_speed": 110,
            "passenger_capacity": 2
        },
        {
            "company_id": 14,  # Archer Aviation
            "model_name": "Maker",
            "max_range": 100,
            "max_speed": 240,
            "passenger_capacity": 4
        },
        {
            "company_id": 15,  # Beta Technologies
            "model_name": "ALIA-250",
            "max_range": 250,
            "max_speed": 270,
            "passenger_capacity": 6
        },
        {
            "company_id": 16,  # Vertical Aerospace
            "model_name": "VX4",
            "max_range": 160,
            "max_speed": 320,
            "passenger_capacity": 4
        },
        {
            "company_id": 17,  # Eve Air Mobility
            "model_name": "eVTOL v1",
            "max_range": 100,
            "max_speed": 240,
            "passenger_capacity": 4
        },
        {
            "company_id": 18,  # Wisk Aero
            "model_name": "Generation 6",
            "max_range": 140,
            "max_speed": 230,
            "passenger_capacity": 4
        },
        {
            "company_id": 19,  # SkyDrive
            "model_name": "SD-03",
            "max_range": 30,
            "max_speed": 100,
            "passenger_capacity": 1
        },
        {
            "company_id": 20,  # Overair
            "model_name": "Butterfly",
            "max_range": 160,
            "max_speed": 280,
            "passenger_capacity": 5
        },
        {
            "company_id": 3,  # 极飞科技
            "model_name": "V40",
            "max_range": 50,
            "max_speed": 150,
            "passenger_capacity": 2
        },
        {
            "company_id": 4,  # 华夏天信
            "model_name": "HX-1",
            "max_range": 60,
            "max_speed": 180,
            "passenger_capacity": 3
        },
        {
            "company_id": 5,  # 德事隆航空
            "model_name": "DX-20",
            "max_range": 80,
            "max_speed": 200,
            "passenger_capacity": 4
        },
        {
            "company_id": 6,  # 航天科工
            "model_name": "天行者",
            "max_range": 100,
            "max_speed": 220,
            "passenger_capacity": 4
        },
        {
            "company_id": 7,  # 锐翔航空
            "model_name": "RX-100",
            "max_range": 70,
            "max_speed": 190,
            "passenger_capacity": 3
        },
        {
            "company_id": 8,  # 零度智控
            "model_name": "Z-1",
            "max_range": 40,
            "max_speed": 140,
            "passenger_capacity": 2
        }
    ]
    
    for product_data in sample_products:
        product = EvtolProduct(**product_data)
        db.session.add(product)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()  # 创建管理员账号
        init_db_data()  # 初始化EVTOL公司数据
        add_sample_jobs()  # 添加示例招聘信息
        add_sample_products()  # 添加示例产品信息
    app.run(debug=True) 