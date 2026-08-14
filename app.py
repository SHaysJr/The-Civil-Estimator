from decimal import Decimal, InvalidOperation
from flask import Flask, flash, redirect, render_template, request, url_for

from db import init_db, connect
from services import (
    add_crew, add_equipment, add_line_from_catalog, add_section, bedding_jurisdictions, bedding_rules_for, catalog_materials, catalog_materials_with_companions, companion_rules,
    compute_project, compute_section_from_db, create_project, delete_record,
    equipment_catalog, get_project, get_section, labor_catalog, list_projects,
    project_sections, update_project,
)
from services_assembly import get_primary_line, update_line_item

app=Flask(__name__)
app.config['SECRET_KEY']='local-estimator-v4-development-key'


def f(name, default=0):
    raw=request.form.get(name,'').strip()
    if raw=='': return default
    try: return float(Decimal(raw))
    except (InvalidOperation,ValueError): raise ValueError(f'{name.replace("_"," ").title()} must be a number.')


def pct(name, default):
    return f(name, default*100)/100


def project_form():
    name=request.form.get('name','').strip()
    if not name: raise ValueError('Project name is required.')
    return {
        'name':name,'customer':request.form.get('customer','').strip(),'address_line':request.form.get('address_line','').strip(),
        'city':request.form.get('city','').strip(),'state':request.form.get('state','').strip(),'zip_code':request.form.get('zip_code','').strip(),
        'estimator':request.form.get('estimator','').strip(),'bid_date':request.form.get('bid_date','').strip(),'date_due':request.form.get('date_due','').strip(),
        'description':request.form.get('description','').strip(),'status':request.form.get('status','active').strip(),
        'tax_rate':pct('tax_rate',.10),'overhead_rate':pct('overhead_rate',.10),'profit_rate':pct('profit_rate',.20),
        'bedding_jurisdiction':request.form.get('bedding_jurisdiction','').strip(),
    }


@app.template_filter('money')
def fmt_money(v): return f'${float(v or 0):,.2f}'

@app.template_filter('pct')
def fmt_pct(v): return f'{float(v or 0)*100:.1f}'

@app.template_filter('num')
def fmt_num(v): return f'{float(v or 0):,.2f}'


@app.route('/')
def index(): return render_template('index.html',projects=list_projects())

@app.route('/projects/new',methods=['GET','POST'])
def new_project():
    if request.method=='POST':
        try:
            pid=create_project(project_form()); flash('Project created.','success'); return redirect(url_for('project',project_id=pid))
        except ValueError as e: flash(str(e),'error')
    return render_template('project_form.html',project=None,bedding_jurisdictions=bedding_jurisdictions())

@app.route('/projects/<int:project_id>/edit',methods=['GET','POST'])
def edit_project(project_id):
    p=get_project(project_id)
    if not p: return 'Project not found',404
    if request.method=='POST':
        try:
            update_project(project_id,project_form()); flash('Project saved.','success'); return redirect(url_for('project',project_id=project_id))
        except ValueError as e: flash(str(e),'error')
    return render_template('project_form.html',project=get_project(project_id),bedding_jurisdictions=bedding_jurisdictions())

@app.route('/projects/<int:project_id>')
def project(project_id):
    if not get_project(project_id): return 'Project not found',404
    return render_template('project.html',data=compute_project(project_id))

@app.post('/projects/<int:project_id>/sections')
def create_section_route(project_id):
    scope=request.form.get('scope_name','').strip()
    if not scope: flash('Scope name is required.','error')
    else:
        sid=add_section(project_id,scope); return redirect(url_for('section',section_id=sid))
    return redirect(url_for('project',project_id=project_id))

@app.route('/sections/<int:section_id>')
def section(section_id):
    data=compute_section_from_db(section_id)
    if not data: return 'Section not found',404
    scope=data['section']['scope_name']
    system_type='Storm' if scope=='Storm Drain' else ('Sanitary' if scope=='Sewer' else None)
    rules=[]
    if system_type:
        rules=bedding_rules_for(state=data['project']['state'] or None,
                                jurisdiction=data['project']['bedding_jurisdiction'] or None,
                                system_type=system_type)
    return render_template('section.html',data=data,labor_rates=labor_catalog(),equipment_rates=equipment_catalog(),
                           materials=catalog_materials_with_companions(scope),bedding_rules=rules,depth_bands=__import__('domain').DEPTH_BANDS)

@app.post('/sections/<int:section_id>/crew')
def section_add_crew(section_id):
    try: add_crew(section_id,int(request.form['labor_rate_id']),int(f('count',1)))
    except Exception as e: flash(str(e),'error')
    return redirect(url_for('section',section_id=section_id))

@app.post('/sections/<int:section_id>/equipment')
def section_add_equipment(section_id):
    try: add_equipment(section_id,int(request.form['equipment_rate_id']))
    except Exception as e: flash(str(e),'error')
    return redirect(url_for('section',section_id=section_id))

@app.post('/sections/<int:section_id>/lines')
def section_add_line(section_id):
    try:
        result=add_line_from_catalog(section_id,int(request.form['material_rate_id']),f('quantity'),
                              request.form.get('unit_cost_override',''),request.form.get('production_rate_override',''),
                              request.form.get('depth_band',''),request.form.get('bedding_rule_id',''),
                              request.form.get('bedding_unit_cost_per_cy',''))
        if result.get('companions_added'):
            flash(f"Item added with {result['companions_added']} automatic companion item(s).",'success')
    except Exception as e: flash(str(e),'error')
    return redirect(url_for('section',section_id=section_id))

@app.route('/lines/<int:line_item_id>/edit',methods=['GET','POST'])
def edit_line(line_item_id):
    try:
        line=get_primary_line(line_item_id)
    except ValueError as e:
        return str(e),404
    data=compute_section_from_db(line['section_id'])
    scope=data['section']['scope_name']
    system_type='Storm' if scope=='Storm Drain' else ('Sanitary' if scope=='Sewer' else None)
    rules=[]
    if system_type:
        rules=bedding_rules_for(state=data['project']['state'] or None,
                                jurisdiction=data['project']['bedding_jurisdiction'] or None,
                                system_type=system_type)
    if request.method=='POST':
        try:
            result=update_line_item(line_item_id,f('quantity'),request.form.get('unit_cost_override',''),
                                    request.form.get('production_rate_override',''),request.form.get('depth_band',''),
                                    request.form.get('bedding_rule_id',''),request.form.get('bedding_unit_cost_per_cy',''))
            flash(f"Line item updated; {result['companions_synced']} automatic companion item(s) synchronized.",'success')
            return redirect(url_for('section',section_id=result['section_id']))
        except Exception as e:
            flash(str(e),'error')
            line=get_primary_line(line_item_id)
    return render_template('line_edit.html',line=line,data=data,bedding_rules=rules,depth_bands=__import__('domain').DEPTH_BANDS)

@app.post('/delete/<table>/<int:record_id>')
def delete_route(table,record_id):
    section_id=request.form.get('section_id',type=int); project_id=request.form.get('project_id',type=int)
    try: delete_record(table,record_id)
    except ValueError as e: flash(str(e),'error')
    if section_id: return redirect(url_for('section',section_id=section_id))
    return redirect(url_for('project',project_id=project_id))

@app.route('/bedding')
def bedding_catalog():
    state=request.args.get('state','').strip().upper()
    jurisdiction=request.args.get('jurisdiction','').strip()
    with connect() as conn:
        sql='SELECT * FROM bedding_rules WHERE 1=1'; args=[]
        if state: sql+=' AND state=?'; args.append(state)
        if jurisdiction: sql+=' AND jurisdiction=?'; args.append(jurisdiction)
        sql+=' ORDER BY state,jurisdiction,system_type,pipe_material,nominal_diameter_in,bedding_class LIMIT 1000'
        rows=conn.execute(sql,args).fetchall()
    return render_template('bedding.html',rows=rows,jurisdictions=bedding_jurisdictions(state or None),state=state,jurisdiction=jurisdiction)

@app.route('/companions')
def companions_catalog(): return render_template('companions.html', rows=companion_rules())

@app.route('/rates')
def rates():
    with connect() as conn:
        counts={t:conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['labor_rates','equipment_rates','material_rates','material_companions','bedding_rules','pipe_materials','pipe_sizes','pipe_fittings','city_counties']}
        scopes=[r[0] for r in conn.execute('SELECT DISTINCT scope FROM material_rates ORDER BY scope')]
    return render_template('rates.html',counts=counts,scopes=scopes,labor=labor_catalog(),equipment=equipment_catalog(),materials=catalog_materials())

if __name__=='__main__':
    init_db(); app.run(host='127.0.0.1',port=5052,debug=True)
