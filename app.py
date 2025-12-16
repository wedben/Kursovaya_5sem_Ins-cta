from flask import Flask, render_template, request, jsonify
from database import Database
import os

app = Flask(__name__)
db = Database()

@app.route('/')
def index():
    """Главная страница с формой поиска"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_insects():
    """API endpoint для поиска насекомых по параметрам"""
    try:
        data = request.json
        
        insect_type = data.get('type')  # 'dragonfly', 'beetle', 'butterfly'
        params = data.get('params', {})
        
        if not insect_type:
            return jsonify({'error': 'Тип насекомого не указан'}), 400
        
        # Валидация типа
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        # Поиск в базе данных
        results = db.search_insects(insect_type, params)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all/<insect_type>', methods=['GET'])
def get_all_insects(insect_type):
    """Получить все насекомые определенного типа"""
    try:
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        results = db.get_all_insects(insect_type)
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter-options/<insect_type>', methods=['GET'])
def get_filter_options(insect_type):
    """Получить уникальные значения для фильтров"""
    try:
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        options = db.get_filter_options(insect_type)
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

