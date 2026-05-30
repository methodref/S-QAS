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
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return jsonify([q.to_dict() for q in questions])

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
        {'question': '你好', 'answer': '你好！有什么可以帮助你的吗？', 'category': '问候'},
        {'question': '你是谁', 'answer': '我是一个智能问答系统，可以帮助你回答各种问题。', 'category': '介绍'},
        {'question': '怎么联系客服', 'answer': '你可以拨打客服热线400-123-4567，或者发送邮件到support@example.com', 'category': '联系'},
        {'question': '你们的工作时间是什么', 'answer': '我们的工作时间是周一至周五9:00-18:00。', 'category': '营业时间'},
        {'question': '如何重置密码', 'answer': '点击登录页面的"忘记密码"链接，输入注册邮箱，我们会发送重置链接给你。', 'category': '账户'},
        {'question': '忘记密码怎么办', 'answer': '点击登录页面的"忘记密码"链接，输入注册邮箱，我们会发送重置链接给你。', 'category': '账户'},
        {'question': '注册新账号', 'answer': '点击首页的"注册"按钮，填写邮箱和密码即可完成注册。', 'category': '账户'},
        {'question': '客服电话是多少', 'answer': '客服热线是400-123-4567，工作时间内都有人接听。', 'category': '联系'},
        {'question': '能帮我一下吗', 'answer': '当然可以！请告诉我您的问题，我会尽力帮助您。', 'category': '帮助'},
        {'question': '修改密码步骤', 'answer': '登录后进入个人中心，找到"修改密码"选项，按提示操作即可。', 'category': '账户'},
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
    print(f"📡 服务地址: http://localhost:8080")
    print(f"🔧 管理后台: http://localhost:8080/admin")
    print(f"✅ 模式: 完全离线")
    app.run(debug=True, host='0.0.0.0', port=8080)