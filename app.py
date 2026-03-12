from flask import Flask, jsonify, render_template, request,url_for, session,redirect
import oracledb
from flask import send_file
import pandas as pd
import io


oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_0")

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'

# Oracle connection
connection = oracledb.connect(
    user="apps",
    password="appstest12",
    dsn="10.10.12.15:1521/PERPROD"
)



@app.route("/download/<query_name>")
def download(query_name):

    sql = queries.get(query_name)

    data = run_query(sql)

    df = pd.DataFrame(data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

    output.seek(0)

    return send_file(
        output,
        download_name=query_name + ".xlsx",
        as_attachment=True
    )


USERS = {
    "admin": "pesco123"
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401
            
    return render_template('login.html')

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


queries = {


"Grade_Wise_Vacancy": """
WITH position_data AS (
    SELECT 
        grade.grade_id,
        grade.name AS GRADE,
        SUM(pos.max_persons) AS sanctioned
    FROM per_grades grade 
    JOIN   hr.hr_all_positions_f#   pos
      ON TRIM(UPPER(grade.name)) = TRIM(UPPER(pos.attribute6))
    WHERE NVL(pos.location_id, -1) <> 27625
      AND SYSDATE BETWEEN pos.effective_start_date AND pos.effective_end_date
    GROUP BY  grade.grade_id,grade.name
ORDER BY grade.name
),

assignment_data AS (
    SELECT 
        ass.grade_id,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'REG' THEN 1 ELSE 0 END) AS regular,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'COT' THEN 1 ELSE 0 END) AS contract,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'CONSLSM' THEN 1 ELSE 0 END) AS lumpsum,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'XX_DEP' THEN 1 ELSE 0 END) AS deputation,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'DW' THEN 1 ELSE 0 END) AS daily_wages
    FROM per_assignments_x ass
    WHERE NVL(ass.location_id, -1) <> 27625
      AND ass.primary_flag = 'Y'
      AND ass.assignment_type = 'E'
      AND SYSDATE BETWEEN ass.effective_start_date AND ass.effective_end_date
    GROUP BY ass.grade_id
)

SELECT 
    p.GRADE,
    p.sanctioned,
    NVL(a.regular, 0) AS regular,
    NVL(a.contract, 0) AS contract,
    NVL(a.lumpsum, 0) AS lumpsum,
    NVL(a.deputation, 0) AS deputation,
    NVL(a.daily_wages, 0) AS daily_wages,

    NVL(a.regular, 0)
  + NVL(a.contract, 0)
  + NVL(a.lumpsum, 0)
  + NVL(a.deputation, 0)
  + NVL(a.daily_wages, 0) AS working,

    GREATEST(
        p.sanctioned -
        ( NVL(a.regular, 0)
        + NVL(a.contract, 0)
        + NVL(a.lumpsum, 0)
        + NVL(a.deputation, 0)
        + NVL(a.daily_wages, 0) ),
        0
    ) AS vacant

FROM position_data p
LEFT JOIN assignment_data a
    ON p.grade_id = a.grade_id
ORDER BY p.grade_id,p.GRADE

""",

"Circle_Wise_Vacancy": """
WITH circle_orgs AS (
    
    SELECT organization_id, name
    FROM hr_all_organization_units
   
   where organization_id='1189' or organization_id='1104' or organization_id='1107' or organization_id='1105' or organization_id='794' or organization_id='1684' or organization_id='503' or organization_id='821' or organization_id='1670' or organization_id='1604' or organization_id='1073'
),

org_tree (circle_id, organization_id) AS (
    
    SELECT c.organization_id, c.organization_id
    FROM circle_orgs c

    UNION ALL

    
    SELECT ot.circle_id,
           pose.organization_id_child
    FROM org_tree ot
    JOIN per_org_structure_elements pose
        ON pose.organization_id_parent = ot.organization_id
),

position_data AS (
    SELECT 
        pos.organization_id,
        SUM(pos.max_persons) AS sanctioned
    FROM hr.hr_all_positions_f pos
    WHERE NVL(pos.location_id, -1) <> 27625 
    GROUP BY pos.organization_id
),

assignment_data AS (
    SELECT 
        ass.organization_id,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'REG' THEN 1 ELSE 0 END) AS regular,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'COT' THEN 1 ELSE 0 END) AS contract,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'CONSLSM' THEN 1 ELSE 0 END) AS lumpsum,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'XX_DEP' THEN 1 ELSE 0 END) AS deputation,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'DW' THEN 1 ELSE 0 END) AS daily_wages
    FROM per_assignments_x ass
    WHERE NVL(ass.location_id, -1) <> 27625
    GROUP BY ass.organization_id
)

SELECT 
    c.name AS circle_name,
   c.organization_id,
    SUM(NVL(p.sanctioned,0)) AS total_sanctioned,
    SUM(NVL(a.regular,0)) AS total_regular,
    SUM(NVL(a.contract,0)) AS total_contract,
    SUM(NVL(a.lumpsum,0)) AS total_lumpsum,
    SUM(NVL(a.deputation,0)) AS total_deputation,
    SUM(NVL(a.daily_wages,0)) AS total_daily_wages,

    SUM(NVL(a.regular,0)
      + NVL(a.contract,0)
      + NVL(a.lumpsum,0)
      + NVL(a.deputation,0)
      + NVL(a.daily_wages,0)) AS total_working,

    SUM(
        GREATEST(
            NVL(p.sanctioned,0) -
            (NVL(a.regular,0)
           + NVL(a.contract,0)
           + NVL(a.lumpsum,0)
           + NVL(a.deputation,0)
           + NVL(a.daily_wages,0)), 0)
    ) AS total_vacant

FROM org_tree ot
JOIN circle_orgs c
    ON c.organization_id = ot.circle_id
LEFT JOIN position_data p
    ON p.organization_id = ot.organization_id
LEFT JOIN assignment_data a
    ON a.organization_id = ot.organization_id
GROUP BY c.name,c.organization_id
ORDER BY c.name

""",

"Job_Wise_Vacancy": """
WITH position_data AS (
    SELECT 
        pos.job_id,
        job.name AS job_name,
        SUM(pos.max_persons) AS sanctioned
    FROM 
        hr.hr_all_positions_f pos
    JOIN per_jobs job 
        ON job.job_id = pos.job_id
    WHERE 
        NVL(pos.location_id, -1) <> 27625
    GROUP BY 
        pos.job_id, job.name
),

assignment_data AS (
    SELECT 
        ass.job_id,

        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'REG' THEN 1 ELSE 0 END) AS regular,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'COT' THEN 1 ELSE 0 END) AS contract,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'CONSLSM' THEN 1 ELSE 0 END) AS lumpsum,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'XX_DEP' THEN 1 ELSE 0 END) AS deputation,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'DW' THEN 1 ELSE 0 END) AS daily_wages

    FROM 
        per_assignments_x ass
    WHERE 
        NVL(ass.location_id, -1) <> 27625
    GROUP BY 
        ass.job_id
)

SELECT 
    p.job_name,
    p.sanctioned,

    NVL(a.regular, 0) AS regular,
    NVL(a.contract, 0) AS contract,
    NVL(a.lumpsum, 0) AS lumpsum,
    NVL(a.deputation, 0) AS deputation,
    NVL(a.daily_wages, 0) AS daily_wages,

    NVL(a.regular, 0)
  + NVL(a.contract, 0)
  + NVL(a.lumpsum, 0)
  + NVL(a.deputation, 0)
  + NVL(a.daily_wages, 0) AS working,

    GREATEST(
        p.sanctioned -
        ( NVL(a.regular, 0)
        + NVL(a.contract, 0)
        + NVL(a.lumpsum, 0)
        + NVL(a.deputation, 0)
        + NVL(a.daily_wages, 0) ),
        0
    ) AS vacant

FROM 
    position_data p
LEFT JOIN 
    assignment_data a
ON 
    p.job_id = a.job_id
ORDER BY 
    p.job_name,p.job_id
""",

"3_Levels_of_Organization_Hierarchy_Vacancy": """
WITH org_hierarchy AS (
    SELECT
        child.organization_id    AS org_id,
        child.name               AS org_name,
        parent.name              AS parent_name,
        grandparent.name         AS grandparent_name
    FROM per_all_organization_units child

    LEFT JOIN per_org_structure_elements_v h1
        ON child.organization_id = h1.organization_id_child

    LEFT JOIN per_all_organization_units parent
        ON parent.organization_id = h1.organization_id_parent

    LEFT JOIN per_org_structure_elements_v h2
        ON parent.organization_id = h2.organization_id_child

    LEFT JOIN per_all_organization_units grandparent
        ON grandparent.organization_id = h2.organization_id_parent
),

position_data AS (
    SELECT 
        pos.organization_id,
        SUM(pos.max_persons) AS sanctioned
    FROM hr.hr_all_positions_f pos
    WHERE NVL(pos.location_id, -1) <> 27625
      AND TRUNC(SYSDATE) BETWEEN pos.effective_start_date AND pos.effective_end_date
    GROUP BY pos.organization_id
),

assignment_data AS (
    SELECT 
        ass.organization_id,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'REG' THEN 1 ELSE 0 END) AS regular,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'COT' THEN 1 ELSE 0 END) AS contract,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'CONSLSM' THEN 1 ELSE 0 END) AS lumpsum,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'XX_DEP' THEN 1 ELSE 0 END) AS deputation,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'DW' THEN 1 ELSE 0 END) AS daily_wages
    FROM per_assignments_x ass
    WHERE NVL(ass.location_id, -1) <> 27625
      AND TRUNC(SYSDATE) BETWEEN ass.effective_start_date AND ass.effective_end_date
      AND ass.primary_flag = 'Y'
    GROUP BY ass.organization_id
)

SELECT
    oh.grandparent_name AS level_1,
    oh.parent_name      AS level_2,
    oh.org_name         AS level_3,

    NVL(p.sanctioned,0) AS total_sanctioned,
    NVL(a.regular,0)    AS total_regular,
    NVL(a.contract,0)   AS total_contract,
    NVL(a.lumpsum,0)    AS total_lumpsum,
    NVL(a.deputation,0) AS total_deputation,
    NVL(a.daily_wages,0) AS total_daily_wages,

    ( NVL(a.regular,0)
    + NVL(a.contract,0)
    + NVL(a.lumpsum,0)
    + NVL(a.deputation,0)
    + NVL(a.daily_wages,0) ) AS total_working,

    GREATEST(
        NVL(p.sanctioned,0) -
        ( NVL(a.regular,0)
        + NVL(a.contract,0)
        + NVL(a.lumpsum,0)
        + NVL(a.deputation,0)
        + NVL(a.daily_wages,0) ), 0
    ) AS total_vacant

FROM org_hierarchy oh
LEFT JOIN position_data p
    ON oh.org_id = p.organization_id
LEFT JOIN assignment_data a
    ON oh.org_id = a.organization_id

WHERE oh.grandparent_name IS NOT NULL
  AND oh.parent_name IS NOT NULL

ORDER BY level_1, level_2, level_3
""",

"Retirement_Forecast": """
WITH retirement_data AS (
    SELECT
        paf.grade_id,
        EXTRACT(YEAR FROM (papf.date_of_birth + INTERVAL '60' YEAR)) AS retirement_year
    FROM per_all_people_f papf
    JOIN per_all_assignments_f paf
        ON papf.person_id = paf.person_id
    WHERE paf.assignment_type = 'E'
      AND paf.primary_flag = 'Y'
      AND TRUNC(SYSDATE) BETWEEN paf.effective_start_date AND paf.effective_end_date
      AND papf.current_employee_flag = 'Y'
      AND EXTRACT(YEAR FROM (papf.date_of_birth + INTERVAL '60' YEAR))
          BETWEEN EXTRACT(YEAR FROM SYSDATE)
              AND EXTRACT(YEAR FROM SYSDATE) + 4
)
SELECT
    g.name AS grade_name,
    SUM(CASE WHEN retirement_year = EXTRACT(YEAR FROM SYSDATE) THEN 1 ELSE 0 END) AS "2026",
    SUM(CASE WHEN retirement_year = EXTRACT(YEAR FROM SYSDATE) + 1 THEN 1 ELSE 0 END) AS "2027",
    SUM(CASE WHEN retirement_year = EXTRACT(YEAR FROM SYSDATE) + 2 THEN 1 ELSE 0 END) AS "2028",
    SUM(CASE WHEN retirement_year = EXTRACT(YEAR FROM SYSDATE) + 3 THEN 1 ELSE 0 END) AS "2029",
    SUM(CASE WHEN retirement_year = EXTRACT(YEAR FROM SYSDATE) + 4 THEN 1 ELSE 0 END) AS "2030",
    COUNT(*) AS "Total"
FROM retirement_data r
LEFT JOIN per_grades g
    ON g.grade_id = r.grade_id
GROUP BY g.name
""",

"Sub_Division_Wise_Vacancy": """
WITH position_data AS (
    SELECT 
        pos.organization_id,
        org.name,
        SUM(pos.max_persons) AS sanctioned
    FROM hr.hr_all_positions_f pos
    JOIN per_all_organization_units org 
        ON org.organization_id = pos.organization_id
    WHERE NVL(pos.location_id, -1) <> 27625
      AND TRUNC(SYSDATE) BETWEEN pos.effective_start_date AND pos.effective_end_date
    GROUP BY pos.organization_id, org.name
),

assignment_data AS (
    SELECT 
        ass.organization_id,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'REG' THEN 1 ELSE 0 END) AS regular,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'COT' THEN 1 ELSE 0 END) AS contract,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'CONSLSM' THEN 1 ELSE 0 END) AS lumpsum,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'XX_DEP' THEN 1 ELSE 0 END) AS deputation,
        SUM(CASE WHEN UPPER(TRIM(ass.employment_category)) = 'DW' THEN 1 ELSE 0 END) AS daily_wages
    FROM per_assignments_x ass
    WHERE NVL(ass.location_id, -1) <> 27625
      AND TRUNC(SYSDATE) BETWEEN ass.effective_start_date AND ass.effective_end_date
      AND ass.primary_flag = 'Y'
    GROUP BY ass.organization_id
)

SELECT 
    p.name,
    NVL(p.sanctioned,0) AS total_sanctioned,
    NVL(a.regular,0) AS total_regular,
    NVL(a.contract,0) AS total_contract,
    NVL(a.lumpsum,0) AS total_lumpsum,
    NVL(a.deputation,0) AS total_deputation,
    NVL(a.daily_wages,0) AS total_daily_wages,

    ( NVL(a.regular,0)
    + NVL(a.contract,0)
    + NVL(a.lumpsum,0)
    + NVL(a.deputation,0)
    + NVL(a.daily_wages,0) ) AS total_working,

    GREATEST(
        NVL(p.sanctioned,0) -
        ( NVL(a.regular,0)
        + NVL(a.contract,0)
        + NVL(a.lumpsum,0)
        + NVL(a.deputation,0)
        + NVL(a.daily_wages,0) ), 0
    ) AS total_vacant

FROM position_data p
LEFT JOIN assignment_data a
    ON p.organization_id = a.organization_id
ORDER BY p.name"""

}

def run_query(sql):

    cursor = connection.cursor()
    cursor.execute(sql)

    columns = [col[0] for col in cursor.description]

    data = []

    for row in cursor:
        data.append(dict(zip(columns,row)))

    cursor.close()

    return data


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/<query_name>")
def get_data(query_name):

    search = request.args.get("search","")
    page = int(request.args.get("page",1))

    sql = queries.get(query_name)

    data = run_query(sql)

    page_size = 500
    start = (page-1)*page_size
    end = start + page_size

    return jsonify(data[start:end])


if __name__ == "__main__":
    app.run(debug=True)
