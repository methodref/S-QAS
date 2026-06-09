from flask import Flask, render_template, request, jsonify, send_file
from models import db, Question
from similarity import find_best_match
import pandas as pd
from io import BytesIO, StringIO
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qa_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/questions', methods=['GET'])
def get_questions():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    search_query = request.args.get('search', '')
    category_query = request.args.get('category', '')
    
    query = Question.query.order_by(Question.created_at.desc())
    
    if search_query:
        query = query.filter(
            (Question.question.ilike(f'%{search_query}%')) |
            (Question.answer.ilike(f'%{search_query}%')) |
            (Question.category.ilike(f'%{search_query}%'))
        )
    
    if category_query:
        query = query.filter(Question.category == category_query)
    
    total = query.count()
    questions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return jsonify({
        'questions': [q.to_dict() for q in questions],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    })

@app.route('/api/questions', methods=['POST'])
def add_question():
    data = request.get_json()
    
    # 检查问题是否已存在
    existing = Question.query.filter_by(question=data['question']).first()
    if existing:
        return jsonify({'error': '问题已存在'}), 400
        
    question = Question(
        question=data['question'],
        answer=data['answer'],
        category=data.get('category', '')
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_dict()), 201

@app.route('/api/questions/<int:id>', methods=['PUT'])
def update_question(id):
    question = Question.query.get_or_404(id)
    data = request.get_json()
    
    # 检查问题是否已存在（排除当前编辑的问题）
    existing = Question.query.filter_by(question=data['question']).first()
    if existing and existing.id != id:
        return jsonify({'error': '问题已存在'}), 400
        
    question.question = data['question']
    question.answer = data['answer']
    question.category = data.get('category', question.category)
    db.session.commit()
    return jsonify(question.to_dict())

@app.route('/api/questions/<int:id>', methods=['DELETE'])
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return jsonify({'message': 'Question deleted'})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': '查询不能为空'}), 400

    questions = Question.query.all()
    questions_data = [q.to_dict() for q in questions]

    best_match, score = find_best_match(query, questions_data)

    if best_match:
        return jsonify({
            'answer': best_match['answer'],
            'question': best_match['question'],
            'score': score,
            'found': True
        })
    else:
        return jsonify({
            'answer': '抱歉，我无法找到匹配的问题答案。请尝试重新表述您的问题，或联系管理员添加相关问题。',
            'question': None,
            'score': 0,
            'found': False
        })

@app.route('/api/seed', methods=['POST'])
def seed_questions():
    sample_questions = [
        # 问候类
        {'question': '你好', 'answer': '你好！有什么可以帮助你的吗？', 'category': '问候'},
        {'question': '您好', 'answer': '您好！很高兴为您服务。', 'category': '问候'},
        {'question': '嗨', 'answer': '嗨！请问有什么需要帮助的？', 'category': '问候'},
        {'question': '早上好', 'answer': '早上好！祝您一天愉快。', 'category': '问候'},
        {'question': '晚上好', 'answer': '晚上好！请问有什么可以帮助您的？', 'category': '问候'},
        
        # 介绍类
        {'question': '你是谁', 'answer': '我是一个智能问答系统，可以帮助你回答各种问题。', 'category': '介绍'},
        {'question': '你能做什么', 'answer': '我可以回答常见问题、提供帮助指南、解答使用疑问等。', 'category': '介绍'},
        {'question': '你是什么', 'answer': '我是一个基于人工智能的问答助手。', 'category': '介绍'},
        {'question': '谁开发的你', 'answer': '我是由开发团队精心打造的智能问答系统。', 'category': '介绍'},
        
        # 账户相关
        {'question': '如何重置密码', 'answer': '点击登录页面的"忘记密码"链接，按提示操作即可重置密码。', 'category': '账户'},
        {'question': '忘记密码怎么办', 'answer': '点击登录页面的"忘记密码"链接，按提示操作即可找回密码。', 'category': '账户'},
        {'question': '注册新账号', 'answer': '点击首页的"注册"按钮，填写相关信息即可完成注册。', 'category': '账户'},
        {'question': '修改密码步骤', 'answer': '登录后进入个人中心，找到"修改密码"选项，按提示操作即可。', 'category': '账户'},
        {'question': '如何登录', 'answer': '在首页输入账号和密码，点击登录按钮即可。', 'category': '账户'},
        {'question': '账号登录不了', 'answer': '请检查账号密码是否正确，或尝试找回密码功能。', 'category': '账户'},
        {'question': '如何绑定邮箱', 'answer': '进入个人中心，在账户设置中找到邮箱绑定选项进行操作。', 'category': '账户'},
        {'question': '如何修改个人信息', 'answer': '登录后进入个人中心，找到个人信息编辑选项进行修改。', 'category': '账户'},
        
        # 帮助支持
        {'question': '能帮我一下吗', 'answer': '当然可以！请告诉我您的问题，我会尽力帮助您。', 'category': '帮助'},
        {'question': '怎么联系客服', 'answer': '您可以通过在线客服或帮助中心获取支持。', 'category': '帮助'},
        {'question': '需要帮助', 'answer': '请问您遇到了什么问题？我来帮您解答。', 'category': '帮助'},
        {'question': '求助', 'answer': '请描述您的问题，我会尽力为您提供帮助。', 'category': '帮助'},
        
        # 服务相关
        {'question': '你们的工作时间是什么', 'answer': '我们的工作时间是周一至周五，正常工作时段。', 'category': '营业时间'},
        {'question': '周末上班吗', 'answer': '周末我们提供有限的服务支持。', 'category': '营业时间'},
        {'question': '节假日服务吗', 'answer': '节假日期间我们会安排值班人员提供必要的服务。', 'category': '营业时间'},
        {'question': '服务范围', 'answer': '我们提供在线咨询、技术支持和问题解答服务。', 'category': '服务'},
        {'question': '服务费用', 'answer': '基础咨询服务是免费的，部分增值服务可能需要付费。', 'category': '服务'},
        {'question': '服务保障', 'answer': '我们承诺为您提供专业、及时的服务支持。', 'category': '服务'},
        
        # 常见问题
        {'question': '如何使用', 'answer': '您可以在首页输入问题，我会为您匹配最佳答案。', 'category': '使用'},
        {'question': '使用教程', 'answer': '在帮助中心可以找到详细的使用教程和操作指南。', 'category': '使用'},
        {'question': '功能介绍', 'answer': '我们提供问题查询、答案匹配、知识库管理等功能。', 'category': '使用'},
        {'question': '常见问题', 'answer': '您可以在帮助中心查看常见问题及解答。', 'category': '使用'},
        {'question': '反馈意见', 'answer': '感谢您的反馈！您可以通过反馈渠道提交您的意见和建议。', 'category': '反馈'},
        {'question': '建议', 'answer': '非常欢迎您的建议，我们会认真考虑每一条反馈。', 'category': '反馈'},
        
        # 其他
        {'question': '谢谢', 'answer': '不客气！能帮到您是我的荣幸。', 'category': '感谢'},
        {'question': '感谢', 'answer': '很高兴能为您提供帮助！', 'category': '感谢'},
        {'question': '再见', 'answer': '再见！欢迎下次再来。', 'category': '告别'},
        {'question': '拜拜', 'answer': '拜拜！祝您一切顺利。', 'category': '告别'},
    ]

    for sq in sample_questions:
        existing = Question.query.filter_by(question=sq['question']).first()
        if not existing:
            question = Question(
                question=sq['question'],
                answer=sq['answer'],
                category=sq['category']
            )
            db.session.add(question)

    db.session.commit()
    return jsonify({'message': '示例数据添加成功'})

@app.route('/api/export', methods=['GET'])
def export_questions():
    export_format = request.args.get('format', 'json')
    questions = Question.query.order_by(Question.created_at.desc()).all()
    data = [{
        'question': q.question,
        'answer': q.answer,
        'category': q.category or ''
    } for q in questions]
    
    if export_format == 'xlsx':
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questions')
        output.seek(0)
        filename = f'questions_export_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx'
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       as_attachment=True, download_name=filename)
    
    elif export_format == 'csv':
        output = BytesIO()
        df = pd.DataFrame(data)
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        filename = f'questions_export_{pd.Timestamp.now().strftime("%Y%m%d")}.csv'
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)
    
    else:
        return jsonify({
            'success': True,
            'total': len(data),
            'questions': data
        })

@app.route('/api/import', methods=['POST'])
def import_questions():
    if request.content_type and 'multipart/form-data' in request.content_type:
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        filename = file.filename.lower()
        try:
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(file)
            elif filename.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                data = request.get_json()
                questions = data.get('questions', [])
                return process_import(questions)
            
            questions = df.to_dict('records')
            return process_import(questions)
        except Exception as e:
            return jsonify({'success': False, 'message': f'文件读取失败: {str(e)}'}), 400
    else:
        data = request.get_json()
        questions = data.get('questions', [])
        return process_import(questions)

def process_import(questions):
    if not questions:
        return jsonify({'success': False, 'message': '没有数据需要导入'}), 400
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    for item in questions:
        if not item.get('question') or not item.get('answer'):
            errors.append(f"数据缺少必要字段: {item}")
            continue
            
        existing = Question.query.filter_by(question=item['question']).first()
        
        if existing:
            existing.answer = item['answer']
            existing.category = item.get('category', '')
            updated_count += 1
        else:
            question = Question(
                question=item['question'],
                answer=item['answer'],
                category=item.get('category', '')
            )
            db.session.add(question)
            imported_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'导入完成：新增 {imported_count} 条，更新 {updated_count} 条',
        'imported': imported_count,
        'updated': updated_count,
        'errors': errors
    })

@app.route('/api/check-duplicates', methods=['POST'])
def check_duplicates():
    if request.content_type and 'multipart/form-data' in request.content_type:
        file = request.files.get('file')
        if not file:
            return jsonify({'has_duplicates': False, 'count': 0, 'duplicates': []})
        
        filename = file.filename.lower()
        try:
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(file)
            elif filename.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                data = request.get_json()
                questions = data.get('questions', [])
                return do_check_duplicates(questions)
            
            questions = df.to_dict('records')
            return do_check_duplicates(questions)
        except:
            return jsonify({'has_duplicates': False, 'count': 0, 'duplicates': []})
    else:
        data = request.get_json()
        questions = data.get('questions', [])
        return do_check_duplicates(questions)

def do_check_duplicates(questions):
    duplicates = []
    for item in questions:
        if item.get('question'):
            existing = Question.query.filter_by(question=item['question']).first()
            if existing:
                duplicates.append({
                    'question': item['question'],
                    'existing_id': existing.id
                })
    
    return jsonify({
        'has_duplicates': len(duplicates) > 0,
        'count': len(duplicates),
        'duplicates': duplicates
    })

if __name__ == '__main__':
    print("🚀 启动 S-QAS 智能问答系统...")
    print(f"📡 服务地址: http://localhost:5001")
    print(f"🔧 管理后台: http://localhost:5001/admin")
    print(f"✅ 模式: 完全离线")
    app.run(debug=True, host='0.0.0.0', port=5001)