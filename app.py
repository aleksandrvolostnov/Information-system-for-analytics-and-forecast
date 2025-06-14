from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask import send_file
from io import BytesIO
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from flask import request
import itertools


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1111@localhost/yield'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)



# Форма входа
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Форма регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

from flask_login import current_user  # Добавляем импорт

# Форма для изменения логина и пароля
from wtforms import ValidationError

class SettingsForm(FlaskForm):
    new_username = StringField('Новый логин', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')

    def validate_new_username(self, field):
        # Проверка на уникальность логина (исключая текущего пользователя)
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Этот логин уже занят')

# Маршрут для страницы настроек
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        # Проверка текущего пароля (без хэширования)
        if form.current_password.data != current_user.password:
            flash('Неверный текущий пароль', 'error')
            return redirect(url_for('settings'))

        # Обновление логина
        if form.new_username.data:
            current_user.username = form.new_username.data

        # Обновление пароля
        if form.new_password.data:
            current_user.password = form.new_password.data  # Сохраняем в открытом виде

        db.session.commit()
        flash('Настройки успешно обновлены', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', form=form)
# Загрузка пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# Полные данные урожайности (2000-2022 + прогноз до 2028)
crop_data = {
    "Горох": {
        2000: 13.6, 2001: 22.8, 2002: 19.6, 2003: 9.7, 2004: 23.3,
        2005: 21.9, 2006: 26.2, 2007: 13.7, 2008: 30.2, 2009: 22.0,
        2010: 20.6, 2011: 29.7, 2012: 16.2, 2013: 14.6, 2014: 19.4,
        2015: 24.4, 2016: 26.7, 2017: 32.1, 2018: 16.5, 2019: 17.4,
        2020: 21.4, 2021: 31.7, 2022: 19.45,
        2023: 20.5, 2024: 21.0, 2025: 21.5, 2026: 22.0, 2027: 22.5, 2028: 23.0
    },
    "Гречиха": {
        2000: 6.2, 2001: 6.7, 2002: 7.3, 2003: 5.8, 2004: 10.3,
        2005: 7.6, 2006: 7.1, 2007: 6.6, 2008: 8.3, 2009: 8.2,
        2010: 7.8, 2011: 11.1, 2012: 10.5, 2013: 9.9, 2014: 9.9,
        2015: 10.4, 2016: 9.5, 2017: 8.5, 2018: 8.0, 2019: 10.1,
        2020: 14.1, 2021: 16.5, 2022: 14.35,
        2023: 15.0, 2024: 15.5, 2025: 16.0, 2026: 16.5, 2027: 17.0, 2028: 17.5
    },
    "Картофель": {
        2000: 59.0, 2001: 66.0, 2002: 79.5, 2003: 71.2, 2004: 95.3,
        2005: 95.0, 2006: 90.8, 2007: 81.5, 2008: 100.7, 2009: 92.3,
        2010: 106.2, 2011: 123.8, 2012: 128.6, 2013: 143.5, 2014: 144.9,
        2015: 148.0, 2016: 166.6, 2017: 163.1, 2018: 164.9, 2019: 157.5,
        2020: 168.1, 2021: 180.2, 2022: 201.04,
        2023: 205.0, 2024: 210.0, 2025: 215.0, 2026: 220.0, 2027: 225.0, 2028: 230.0
    },
    "Кукуруза на зерно": {
        2000: 18.1, 2001: 14.8, 2002: 32.1, 2003: 28.0, 2004: 44.3,
        2005: 36.1, 2006: 35.8, 2007: 24.7, 2008: 39.6, 2009: 35.5,
        2010: 34.8, 2011: 53.1, 2012: 43.7, 2013: 45.9, 2014: 44.9,
        2015: 41.6, 2016: 64.1, 2017: 45.0, 2018: 35.0, 2019: 42.3,
        2020: 34.6, 2021: 52.4, 2022: 62.55,
        2023: 65.0, 2024: 67.0, 2025: 69.0, 2026: 71.0, 2027: 73.0, 2028: 75.0
    },
    "Овес": {
        2000: 20.9, 2001: 22.7, 2002: 22.4, 2003: 13.0, 2004: 21.5,
        2005: 20.8, 2006: 24.3, 2007: 17.6, 2008: 26.6, 2009: 16.8,
        2010: 18.4, 2011: 25.3, 2012: 18.3, 2013: 18.6, 2014: 23.2,
        2015: 23.3, 2016: 27.4, 2017: 28.6, 2018: 20.0, 2019: 21.0,
        2020: 15.9, 2021: 28.0, 2022: 17.72,
        2023: 18.0, 2024: 18.5, 2025: 19.0, 2026: 19.5, 2027: 20.0, 2028: 20.5
    },
    "Овощи открытого грунта": {
        2000: 60.02, 2001: 62.75, 2002: 60.23, 2003: 64.7, 2004: 70.72,
        2005: 78.61, 2006: 73.17, 2007: 36.3, 2008: 105.2, 2009: 120.9,
        2010: 130.5, 2011: 150.5, 2012: 186.0, 2013: 184.4, 2014: 168.8,
        2015: 196.6, 2016: 171.3, 2017: 172.9, 2018: 143.1, 2019: 169.5,
        2020: 137.5, 2021: 145.4, 2022: 156.32,
        2023: 160.0, 2024: 165.0, 2025: 170.0, 2026: 175.0, 2027: 180.0, 2028: 185.0
    },
    "Подсолнечник": {
        2000: 8.2, 2001: 9.5, 2002: 11.5, 2003: 9.8, 2004: 13.7,
        2005: 15.8, 2006: 14.5, 2007: 12.5, 2008: 16.6, 2009: 12.2,
        2010: 14.0, 2011: 16.7, 2012: 15.9, 2013: 16.8, 2014: 17.0,
        2015: 16.4, 2016: 20.7, 2017: 19.4, 2018: 17.1, 2019: 17.5,
        2020: 13.4, 2021: 19.4, 2022: 19.67,
        2023: 20.0, 2024: 20.5, 2025: 21.0, 2026: 21.5, 2027: 22.0, 2028: 22.5
    },
    "Просо": {
        2000: 7.9, 2001: 11.2, 2002: 15.6, 2003: 11.6, 2004: 17.0,
        2005: 13.4, 2006: 11.7, 2007: 11.3, 2008: 18.5, 2009: 10.7,
        2010: 13.1, 2011: 19.5, 2012: 16.1, 2013: 10.8, 2014: 15.6,
        2015: 12.9, 2016: 20.2, 2017: 16.6, 2018: 13.9, 2019: 10.1,
        2020: 6.3, 2021: 24.7, 2022: 10.9,
        2023: 11.5, 2024: 12.0, 2025: 12.5, 2026: 13.0, 2027: 13.5, 2028: 14.0
    },
    "Пшеница озимая": {
        2000: 23.4, 2001: 28.6, 2002: 33.1, 2003: 24.0, 2004: 34.9,
        2005: 37.1, 2006: 33.3, 2007: 35.8, 2008: 38.6, 2009: 32.3,
        2010: 34.1, 2011: 38.8, 2012: 22.8, 2013: 30.6, 2014: 39.4,
        2015: 39.5, 2016: 42.8, 2017: 43.7, 2018: 39.6, 2019: 34.7,
        2020: 26.3, 2021: 37.4, 2022: 40.13,
        2023: 41.0, 2024: 42.0, 2025: 43.0, 2026: 44.0, 2027: 45.0, 2028: 46.0
    },
    "Пшеница яровая": {
        2000: 16.3, 2001: 16.2, 2002: 15.8, 2003: 10.0, 2004: 15.9,
        2005: 15.2, 2006: 19.8, 2007: 18.6, 2008: 20.7, 2009: 18.0,
        2010: 16.8, 2011: 27.9, 2012: 17.1, 2013: 19.9, 2014: 26.5,
        2015: 31.8, 2016: 35.2, 2017: 29.0, 2018: 27.0, 2019: 23.4,
        2020: 13.6, 2021: 19.6, 2022: 23.59,
        2023: 24.0, 2024: 24.5, 2025: 25.0, 2026: 25.5, 2027: 26.0, 2028: 26.5
    },
    "Сахарная свекла": {
        2000: 224.1, 2001: 283.8, 2002: 382.1, 2003: 292.3, 2004: 480.5,
        2005: 383.6, 2006: 436.0, 2007: 352.4, 2008: 504.8, 2009: 507.9,
        2010: 449.0, 2011: 534.6, 2012: 524.0, 2013: 603.2, 2014: 623.9,
        2015: 518.1, 2016: 707.9, 2017: 598.7, 2018: 489.7, 2019: 534.9,
        2020: 330.6, 2021: 599.7, 2022: 637.84,
        2023: 650.0, 2024: 660.0, 2025: 670.0, 2026: 680.0, 2027: 690.0, 2028: 700.0
    },
    "Соя": {
        2000: 9.2, 2001: 10.8, 2002: 15.4, 2003: 11.1, 2004: 14.6,
        2005: 10.6, 2006: 10.4, 2007: 9.7, 2008: 11.8, 2009: 15.0,
        2010: 10.3, 2011: 15.9, 2012: 13.0, 2013: 15.7, 2014: 10.4,
        2015: 12.7, 2016: 18.1, 2017: 15.2, 2018: 15.0, 2019: 14.0,
        2020: 14.7, 2021: 19.3, 2022: 20.81,
        2023: 21.5, 2024: 22.0, 2025: 22.5, 2026: 23.0, 2027: 23.5, 2028: 24.0
    },
    "Ячмень озимый": {
        2000: 26.8, 2001: 30.1, 2002: 34.3, 2003: 21.1, 2004: 33.8,
        2005: 31.5, 2006: 33.3, 2007: 36.5, 2008: 38.4, 2009: 32.5,
        2010: 33.6, 2011: 40.7, 2012: 24.5, 2013: 39.3, 2014: 38.5,
        2015: 41.3, 2016: 43.3, 2017: 40.1, 2018: 41.0, 2019: 39.8,
        2020: 27.1, 2021: 38.2, 2022: 45.79,
        2023: 46.5, 2024: 47.0, 2025: 47.5, 2026: 48.0, 2027: 48.5, 2028: 49.0
    },
    "Ячмень яровой": {
        2000: 19.9, 2001: 22.2, 2002: 23.5, 2003: 14.4, 2004: 19.4,
        2005: 18.1, 2006: 22.8, 2007: 19.4, 2008: 29.4, 2009: 18.9,
        2010: 16.5, 2011: 24.5, 2012: 18.0, 2013: 18.6, 2014: 20.4,
        2015: 23.7, 2016: 27.2, 2017: 27.5, 2018: 21.0, 2019: 23.3,
        2020: 18.2, 2021: 25.5, 2022: 21.33,
        2023: 22.0, 2024: 22.5, 2025: 23.0, 2026: 23.5, 2027: 24.0, 2028: 24.5
    }
}


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Аналитика
@app.route('/analytics')
@login_required
def analytics():
    crops = list(crop_data.keys())
    years = sorted({year for data in crop_data.values() for year in data.keys()})
    return render_template(
        'analytics.html',
        crops=crops,
        min_year=min(years),
        max_year=max(years)
    )


# API для аналитики
@app.route('/api/analytics', methods=['POST'])
@login_required
def analytics_data():
    data = request.get_json()
    selected_crops = data.get('crops', [])
    start_year = data.get('start_year', 2000)
    end_year = data.get('end_year', 2023)

    response_data = []

    for crop in selected_crops:
        if crop in crop_data:
            crop_yields = crop_data[crop]
            filtered = {
                year: yield_value
                for year, yield_value in crop_yields.items()
                if start_year <= year <= end_year
            }
            response_data.append({
                'name': crop,
                'years': list(filtered.keys()),
                'values': list(filtered.values())
            })

    return jsonify(response_data)
# Дэшборд
@app.route('/dashboard')
@login_required
def dashboard():
    crops = list(crop_data.keys())
    return render_template('dashboard.html', crops=crops)


# API: Список всех культур
@app.route('/api/crops')
@login_required
def get_crops():
    return jsonify(list(crop_data.keys()))


# API: Данные по конкретной культуре
@app.route('/api/crop/<crop_name>')
@login_required
def get_crop(crop_name):
    if crop_name in crop_data:
        return jsonify(crop_data[crop_name])
    return jsonify({"error": "Crop not found"}), 404


# API: Данные по культуре за диапазон лет
@app.route('/api/crop/<crop_name>/<int:start_year>/<int:end_year>')
@login_required
def get_crop_by_years(crop_name, start_year, end_year):
    if crop_name in crop_data:
        filtered_data = {
            year: yield_value
            for year, yield_value in crop_data[crop_name].items()
            if start_year <= year <= end_year
        }
        return jsonify(filtered_data)
    return jsonify({"error": "Crop not found"}), 404


# API: Средняя урожайность по культурам
@app.route('/api/average_yield')
@login_required
def get_average_yield():
    averages = {
        crop: sum(yields.values()) / len(yields)
        for crop, yields in crop_data.items()
    }
    return jsonify(averages)


# API: Топ-5 культур за год
@app.route('/api/top_crops/<int:year>')
@login_required
def get_top_crops(year):
    # Получаем данные для всех культур за указанный год
    crops_for_year = {crop: yields.get(year, 0) for crop, yields in crop_data.items()}
    return jsonify(crops_for_year)


# Прогнозирование
@app.route('/forecast', methods=['GET', 'POST'])
@login_required
def forecast():
    if request.method == 'POST':
        crop = request.form['crop']
        year = int(request.form['year'])

        # Получаем данные для выбранной культуры
        crop_yields = crop_data.get(crop, {})

        # Фильтруем данные до выбранного года
        filtered_data = {
            y: yield_value
            for y, yield_value in crop_yields.items()
            if y <= year
        }

        if filtered_data:
            return render_template('forecast.html',
                                   crop=crop,
                                   year=year,
                                   prediction=crop_yields.get(year, "Нет данных"),
                                   years=list(filtered_data.keys()),
                                   values=list(filtered_data.values()),
                                   crop_data=crop_data  # Передаем данные в шаблон
                                   )
        flash('Нет данных для прогноза')

    # Для GET-запроса просто отображаем форму
    return render_template('forecast.html', crop_data=crop_data)


@app.route('/reports')
@login_required
def reports():
    crops = list(crop_data.keys())
    years = sorted(set(itertools.chain.from_iterable(
        crop.keys() for crop in crop_data.values()
    )))
    return render_template('reports.html', crops=crops, years=years)


@app.route('/download_report', methods=['POST'])
@login_required
def download_report():
    try:
        # Получаем выбранные параметры
        selected_crops = request.form.getlist('crops')
        start_year = int(request.form.get('start_year'))
        end_year = int(request.form.get('end_year'))

        # Фильтруем данные
        report_data = []
        for crop in selected_crops:
            if crop in crop_data:
                crop_years = crop_data[crop]
                for year in range(start_year, end_year + 1):
                    if year in crop_years:
                        report_data.append({
                            'Культура': crop,
                            'Год': year,
                            'Урожайность (ц/га)': crop_years[year]
                        })

        # Создаем DataFrame
        df = pd.DataFrame(report_data)
        if df.empty:
            flash('Нет данных для выбранных параметров')
            return redirect(url_for('reports'))

        # Создаем Excel файл в памяти
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Отчет')

            # Форматирование
            workbook = writer.book
            worksheet = writer.sheets['Отчет']
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'border': 1
            })

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)

        output.seek(0)

        # Отправляем файл
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name=f'report_{start_year}-{end_year}.xlsx',
            as_attachment=True
        )

    except Exception as e:
        flash(f'Ошибка при формировании отчета: {str(e)}')
        return redirect(url_for('reports'))


@app.route('/compare')
@login_required
def compare():
    crops = list(crop_data.keys())
    years = sorted({year for data in crop_data.values() for year in data.keys()})
    return render_template('compare.html',
                           crops=crops,
                           min_year=min(years),
                           max_year=max(years))


@app.route('/api/compare', methods=['POST'])
@login_required
def compare_data():
    data = request.get_json()
    selected_crops = data.get('crops', [])
    selected_years = data.get('years', [])

    response_data = {
        "labels": selected_years,
        "datasets": []
    }

    for crop in selected_crops:
        if crop in crop_data:
            dataset = {
                "label": crop,
                "data": [crop_data[crop].get(year, 0) for year in selected_years]
            }
            response_data["datasets"].append(dataset)

    return jsonify(response_data)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)