from flask import Flask, render_template, request, jsonify
from models import db, Question
from similarity import find_best_match

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
    
    query = Question.query.order_by(Question.created_at.desc())
    
    if search_query:
        query = query.filter(
            (Question.question.ilike(f'%{search_query}%')) |
            (Question.answer.ilike(f'%{search_query}%')) |
            (Question.category.ilike(f'%{search_query}%'))
        )
    
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

if __name__ == '__main__':
    print("🚀 启动智能问答系统...")
    print(f"📡 服务地址: http://localhost:5001")
    print(f"🔧 管理后台: http://localhost:5001/admin")
    print(f"✅ 模式: 完全离线")
    app.run(debug=True, host='0.0.0.0', port=5001)