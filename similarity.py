from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import re

vectorizer = None
synonym_cache = {}

SYNONYMS = {
    "你好": ["您好", "嗨", "哈喽", "你好啊", "您好啊", "嗨喽", "你好呀", "您好呀"],
    "客服": ["客服人员", "客服中心", "客户服务", "在线客服", "客服热线", "客服支持"],
    "密码": ["口令", "pin码", "验证码", "密码重置", "登录密码", "账户密码"],
    "时间": ["工作时间", "营业时间", "上班时间", "服务时间", "办公时间"],
    "联系": ["联系方式", "联系我们", "如何联系", "联系客服", "联系电话"],
    "帮助": ["协助", "支援", "援助", "帮忙", "帮助中心", "帮助支持"],
    "问题": ["疑问", "难题", "困惑", "麻烦", "问题解答", "常见问题"],
    "重置": ["修改", "更改", "变更", "重新设置", "重新设定"],
    "账户": ["账号", "帐号", "用户", "个人中心", "个人账户", "用户账户"],
    "登录": ["登入", "登录系统", "进入系统", "登录账号", "登陆"],
    "注册": ["开户", "注册账号", "新用户", "注册账户", "用户注册"],
    "忘记": ["遗失", "丢失", "遗忘", "忘记了", "不记得"],
    "找回": ["恢复", "寻回", "取回", "找回密码", "找回账号"],
    "邮箱": ["电子邮件", "邮箱地址", "e-mail", "email", "电子邮箱"],
    "电话": ["热线", "电话咨询", "客服电话", "联系电话", "咨询电话"],
    "修改": ["更改", "变更", "改动", "修改密码", "修改信息"],
    "查询": ["查找", "搜索", "查一下", "查询信息", "查看"],
    "解决": ["处理", "解决问题", "搞定", "解决方法", "解决方案"],
    "申请": ["提交", "办理", "申请办理", "申请流程", "申请步骤"],
    "服务": ["服务中心", "售后服务", "在线服务", "客户服务", "服务支持"],
    "支持": ["技术支持", "帮助支持", "支持服务", "技术帮助"],
    "地址": ["联系地址", "公司地址", "地址信息", "详细地址"],
    "退款": ["退货", "退款申请", "退钱", "退款流程", "退换货"],
    "订单": ["订单查询", "订单状态", "我的订单", "订单信息"],
    "发货": ["配送", "物流", "快递", "发货时间", "送货"],
    "支付": ["付款", "支付方式", "在线支付", "支付流程"],
    "优惠": ["折扣", "优惠券", "促销", "优惠活动", "优惠码"],
    "会员": ["VIP", "会员服务", "会员权益", "会员中心"],
    "发票": ["开票", "电子发票", "纸质发票", "发票申请"],
    "保修": ["售后服务", "保修服务", "保修期限", "质保"],
    "安装": ["设置", "配置", "安装指南", "安装步骤"],
    "使用": ["操作", "使用方法", "使用教程", "使用说明"],
    "下载": ["获取", "下载链接", "下载地址", "下载安装"],
    "更新": ["升级", "新版本", "更新内容", "软件更新"],
    "错误": ["报错", "异常", "故障", "问题", "错误提示"],
    "反馈": ["意见", "建议", "反馈信息", "问题反馈"],
}

def get_synonyms(word, top_n=5):
    """获取单词的同义词"""
    return SYNONYMS.get(word, [])[:top_n]

def expand_with_synonyms(text, top_n=3):
    """使用同义词扩展文本"""
    if text in synonym_cache:
        return synonym_cache[text]
    
    expanded = text
    words = jieba.lcut(text)
    
    for word in words:
        if len(word) >= 2:
            syns = get_synonyms(word, top_n)
            for syn in syns:
                expanded += " " + syn
    
    synonym_cache[text] = expanded
    return expanded

def preprocess_text(text):
    """文本预处理：去除标点、分词"""
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    return text

def load_model():
    """加载TF-IDF模型"""
    global vectorizer
    if vectorizer is None:
        vectorizer = TfidfVectorizer(
            tokenizer=jieba.lcut,
            analyzer='word',
            ngram_range=(1, 2),
            stop_words=None,
            max_features=5000
        )
    return vectorizer

def encode_texts(texts):
    """编码文本为TF-IDF向量"""
    load_model()
    if not texts:
        return []
    return vectorizer.fit_transform(texts)

def find_best_match(query, questions, top_k=1, threshold=0.25):
    """查找最匹配的问题"""
    if not questions:
        return None, 0

    query = preprocess_text(query)
    query_expanded = expand_with_synonyms(query)
    
    question_texts = []
    original_questions = []
    
    for q in questions:
        processed = preprocess_text(q['question'])
        expanded = expand_with_synonyms(processed)
        question_texts.append(expanded)
        original_questions.append(q)

    all_texts = question_texts + [query_expanded]
    tfidf_matrix = encode_texts(all_texts)
    
    query_vector = tfidf_matrix[-1]
    question_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(query_vector, question_vectors)[0]
    
    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])

    if best_score < threshold:
        return None, 0

    return original_questions[best_idx], best_score

def batch_encode_questions(questions):
    """批量编码问题（用于缓存优化）"""
    if not questions:
        return []
    
    processed_texts = []
    for q in questions:
        processed = preprocess_text(q['question'])
        expanded = expand_with_synonyms(processed)
        processed_texts.append(expanded)
    
    return encode_texts(processed_texts)