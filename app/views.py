# Copyright 2014 SolidBuilds.com. All rights reserved
#
# Authors: Ling Thio <ling.thio@gmail.com>


from flask import redirect, render_template, render_template_string, Blueprint
from flask import request, url_for, jsonify
from flask_user import current_user, login_required, roles_accepted
from app.init_app import app, db
from app.models import UserProfileForm, Post
import flask_excel as excel
import pygal
from pygal.style import Style
import json
from tempfile import NamedTemporaryFile

pyconfig = pygal.Config()

custom_css = '''
    {{id}} {
        background-color: rgba(249, 249, 249, 0);
    }
    {{ id }}text {
        fill: green;
        font-family: sans-serif;
        font-size:1rem;
    }
    {{ id }} .title {
        font-size: 2rem;
        fill: #35baf6;
        font-family: sans-serif;
        font-weight: bold;
    }
    {{ id }}.legends .legend text {
        font-size: 15px;;
    }
    {{ id }}.axis {
        stroke: #666;
    }
    {{ id }} .axis .guides:hover text {
        fill: rgb(86, 230, 82);
    }
    {{ id }}.axis text {
        font-size: 17px;
        fill: rgb(251, 251, 251);
    }
    {{ id }} .axis text.major {
        font-size: 20px;
        fill: rgb(251, 251, 251);
    }
    {{ id }}.axis.y text {
        text-anchor: end;
    }
    {{ id }} .tooltip rect {
        fill: rgb(255, 255, 255);
        stroke: #2d2d2d;
    }
    {{ id }}#tooltip text {
        font-size: 25px;
    }
    {{ id }} .tooltip .legend {
        font-size: 1.8rem;
    }
    {{ id }} .tooltip .value {
        font-size: 1.5rem;
    }
    {{ id }} .tooltip .x_label {
        font-size: 1em;
    }
    {{ id }} .graph > .background {
        fill: rgba(249, 249, 249, 0);
    }
    {{ id }} .plot > .background {
        fill: rgba(255, 255, 255, 0);
    }
'''

def chart_func(id, legend=False):
    site = request.url.split('/chart/')[0]
    post = Post.query.get(id)
    if post:
        data = json.loads(post.data)
        title = post.title
        chart_type = post.chart_type
        pyconfig.js = ['https://en.dailypakistan.com.pk/wp-content/themes/century/js/pygal-tooltips.min.js']
        pyconfig.legend_at_bottom=True
        pyconfig.legend_at_bottom_columns=1
        pyconfig.stroke_style={'width': 3}
        if legend is False:
            pyconfig.show_legend = False
        else:
            pyconfig.show_legend = True
        custom_css_file = '/tmp/pygal_custom_style.css'
        with open(custom_css_file, 'w') as f:
            f.write(custom_css)
        pyconfig.css.append('file://' + custom_css_file)

        if chart_type == 'line':
            chart = pygal.Line(pyconfig)
            chart.x_labels = data['result'][0][1:]
            for idx,item in enumerate(data['result']):
                if idx == 0:
                    continue
                chart.add(data['result'][idx][0], data['result'][idx][1:])


        elif chart_type == 'bar':
            chart = pygal.Bar(pyconfig)
            chart.x_labels = data['result'][0][1:]
            for idx,item in enumerate(data['result']):
                if idx == 0:
                    continue
                chart.add(data['result'][idx][0], data['result'][idx][1:])


        elif chart_type == 'hbar':
            chart = pygal.HorizontalBar(pyconfig)
            for idx,item in enumerate(data['result']):
                if idx == 0:
                    continue
                chart.add(data['result'][idx][0], data['result'][idx][1:])

        elif chart_type == 'pie':
            chart = pygal.Pie(pyconfig)
            for idx,item in enumerate(data['result']):
                if idx == 0:
                    continue
                chart.add(data['result'][idx][0], data['result'][idx][1:])

        elif chart_type == 'donut':
            pyconfig.inner_radius = 0.5
            chart = pygal.Pie(pyconfig)
            for idx,item in enumerate(data['result']):
                if idx == 0:
                    continue
                chart.add(data['result'][idx][0], data['result'][idx][1:])

        else:
            chart = pygal.Line(pyconfig)

        chart.title = title

        xchart = chart.render_data_uri()
        if legend is False:
            chart.render_to_file('app/static/charts/{}_embed.svg'.format(id))
        else:
            chart.render_to_file('app/static/charts/{}.svg'.format(id))

        embed = '<embed type="image/svg+xml" src="{}">'.format(xchart)

        return embed
    else:
        return "None"

app.jinja_env.globals.update(chart_func=chart_func)

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    posts = Post.query.all()
    return render_template('pages/home_page.html', posts=posts)


# The User page is accessible to authenticated users (users that have logged in)
@app.route('/user')
@login_required  # Limits access to authenticated users
def user_page():
    return render_template('pages/user_page.html')


# The Admin page is accessible to users with the 'admin' role
@app.route('/admin')
@roles_accepted('admin')  # Limits access to users with the 'admin' role
def admin_page():
    return render_template('pages/admin_page.html')

# The Admin page is accessible to users with the 'admin' role
@app.route('/new', methods=['GET', 'POST'])
@roles_accepted('admin')  # Limits access to users with the 'admin' role
def new_page():
    if request.method == 'POST':
        sheet = request.get_array(field_name='file')
        title = request.form.get("title")
        chart_type = request.form.get("chart_type")
        data = {"result": sheet}

        entry = Post(title, chart_type, json.dumps(data))
        db.session.add(entry)
        db.session.commit()
        id = entry.id
        return redirect(url_for('chart', id=id))

    return render_template('pages/new.html')

# The Admin page is accessible to users with the 'admin' role
@app.route('/chart/<int:id>')
def chart(id):
    post = Post.query.get(id)
    data = json.loads(post.data)
    title = post.title
    embed = chart_func(id, legend=True)

    return render_template('pages/chart.html', data=data, title=title, id=str(id), embed=embed)


@app.route('/chart/<int:id>/embed')
def chart_embed(id):
    return chart_func(id)


@app.route('/delete/<int:id>', methods=['POST'])
@roles_accepted('admin')
def delete(id):
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for('home_page'))

@app.route('/pages/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    # Initialize form
    form = UserProfileForm(request.form, current_user)

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(current_user)

        # Save user_profile
        db.session.commit()

        # Redirect to home page
        return redirect(url_for('home_page'))

    # Process GET or invalid POST
    return render_template('pages/user_profile_page.html',
                           form=form)

# The Admin page is accessible to users with the 'admin' role
@app.route('/maps')
@roles_accepted('admin')  # Limits access to users with the 'admin' role
def maps_page():
    return render_template('pages/maps.html')
