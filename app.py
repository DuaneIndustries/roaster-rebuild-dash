import plotly.express as px
import pandas as pd
import dash
from dash.dependencies import Input, Output
from dash import dash_table
from dash import html
from dash import dcc

df = pd.read_csv('https://raw.githubusercontent.com/DuaneIndustries/SSRoasterRebuild/main/STACK%20STREET%20BUDGET%20-%20Gantt%202.csv')

#ID column - Creating an Index column by taking the first letter from the first two columns and adding a sequential number
df['index_col'] = df['Project Section'].str.findall(r'[A-Z]').str.join('') + df['Labor / Materials'].str.findall(r'[A-Z]').str.join('')
df['index_col'] = df['index_col'] + (df.groupby('index_col').cumcount() + 1).astype(str)
df.set_index('index_col',inplace=True, drop=False)

# clean data for Gantt Chart ----------------------------------------------------------------------------
df.dropna(subset=['Labor / Materials'],inplace=True)

df['Start'] = pd.to_datetime(df['Start'], format="%m/%d/%Y")
df['End'] = pd.to_datetime(df['End'], format="%m/%d/%Y")
df['Start'] = df['Start'].dt.normalize()
df['End'] = df['End'].dt.normalize()

df['Budget Number'] = df['Budget Number'].str.replace(",","")
df['Cost to Date'] = df['Cost to Date'].str.replace(",","")
df['Budget Number'] = df['Budget Number'].str.replace("?","0.0").astype(float)
df['Cost to Date'] = df['Cost to Date'].str.replace("?","0.0").astype(float)

df['item'] = df['item'].str.replace('re-assembly','Reassembly').str.replace('reassembly','Reassembly').str.replace('Labor','Reassembly')
df['item'] = df['item'].str.replace('Reassembly ','Reassembly')

#App creation-------------------------------------------------------------------------

app = dash.Dash(__name__, prevent_initial_callbacks=True)
server = app.server

app.layout = html.Div([
    html.Br(),
    html.Div(id='gantt-container'),
    html.Br(),
    html.Div(id='pie-container'),
    #html.H1('Stack Street Roaster Rebuiild', style={'color': 'indianred', 'fontSize': 40,'textAlign': 'center'}),

    #html.H3("Project Section"),
    html.Div(children=[
        section_drop := dcc.Dropdown([x for x in sorted(df['Project Section'].unique())],
                              value=['Feed Hopper','Roaster Body','Recirculating System','Cooling Stoning System','Installation'],
                             clearable=False,
                             multi=True,
                             style={'width':'65%'},
                             id='section-dropdown'),
        dcc.Dropdown([x for x in sorted(df['Labor / Materials'].unique())],
                 value='Labor',
                 multi=False,
                 style={'width': '35%'},
                 id='labmat-dropdown'),
        ], style={'display': 'flex'}),
    my_table := dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": False, "selectable": True, "hideable": True}
                if i == "index_col"
                else {"name": i, "id": i, "deletable": False, "selectable": True}
                for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="single",
            column_selectable="multi",
            row_selectable="multi",
            row_deletable=False,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=20,
            style_cell={
                'minWidth': 95, 'maxWidth': 95, 'width': 95},
    style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['index_col', 'Project Section','Labor / Materials', 'item']
        ],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'}
        ),


])


#table filtering via dropdown menus
@app.callback(
    Output(my_table,'data'),
    Input('labmat-dropdown','value'),
    Input('section-dropdown','value')

)

def filter_table(labmat_v, sect_v):
    dff = df.copy()
    if labmat_v :
        dff = dff[dff["Labor / Materials"] == labmat_v]
    if sect_v :
        dff = dff[dff["Project Section"].isin(sect_v)]

        return dff.to_dict('records')
    else :
        return dff.to_dict('records')

# Gantt Chart
@app.callback(
    Output(component_id='gantt-container', component_property='children'),
    [Input(component_id='datatable-interactivity', component_property="derived_virtual_data"),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_rows'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_selected_row_ids'),
     Input(component_id='datatable-interactivity', component_property='selected_rows'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_indices'),
     Input(component_id='datatable-interactivity', component_property='derived_virtual_row_ids'),
     Input(component_id='datatable-interactivity', component_property='active_cell'),
     Input(component_id='datatable-interactivity', component_property='selected_cells'),

     ]
)

def update_gantt(all_rows_data, slctd_row_indices, slct_rows_names, slctd_rows,
               order_of_rows_indices, order_of_rows_names, actv_cell, slctd_cell):

    print('***************************************************************************')
    print('Data across all pages pre or post filtering: {}'.format(all_rows_data))
    print('---------------------------------------------')
    print("Indices of selected rows if part of table after filtering:{}".format(slctd_row_indices))
    print("Names of selected rows if part of table after filtering: {}".format(slct_rows_names))
    print("Indices of selected rows regardless of filtering results: {}".format(slctd_rows))
    print('---------------------------------------------')
    print("Indices of all rows pre or post filtering: {}".format(order_of_rows_indices))
    print("Names of all rows pre or post filtering: {}".format(order_of_rows_names))
    print("---------------------------------------------")
    print("Complete data of active cell: {}".format(actv_cell))
    print("Complete data of all selected cells: {}".format(slctd_cell))

    dff = pd.DataFrame(all_rows_data)
    # dff.dropna(subset=['Start'], inplace=True)
    dff['Budget Number'] = dff["Budget Number"].astype(float)
    labor = "Labor"
    colors = ["red","darkred","oldlace", "rosybrown","indianred","crimson","midnightblue", "royalblue","steelblue"]


    if labor in dff['Labor / Materials'].values:
        dfa = dff
        dfa.dropna(subset=['Start'], inplace=True)
        return [
            dcc.Graph(id="gantt-chart",
             figure = px.timeline(
                 data_frame=dfa,
                 x_start='Start',
                 x_end='End',
                 y='Project Section',
                 color='item',
                 title='Stack Street Roaster Rebuild',
                 opacity=.5,
                 color_discrete_map={
                "powder coating and painting": "red",
                "Reassembly": "darkred",
                "Mechanical Install": "blue",
                "trucking -  collect parts and material ": "rosybrown",
                "Sandlbasting ": "indianred",
                "Insulation" : "crimson",
                "Mobilization" : "midnightblue",
                "Utilities": "royalblue",
                "Start up and Commissioning" : "steelblue",
                },
                hover_name='item',
                hover_data=['Status','Budget Number','Cost to Date']).update_yaxes(autorange='reversed').update_layout(
    hovermode="closest",
    title_x=0.45,
    xaxis_title="Schedule",
    yaxis_title="Task",
    title_font_size=24,
    paper_bgcolor='dimgray',
    plot_bgcolor='dimgray',
    font_color='linen',
    hoverlabel=dict(
        bgcolor='linen',
        font_size=9,
    )))]
    else:
        return [
            dcc.Graph(id="pie-chart",
                      figure=px.pie(
                          data_frame=dff,
                          values="Budget Number",
                          names="Project Section",
                          opacity=.75
                      ).update_layout(
                          title='Materials',
                          title_x=0.50,
                          title_font_size=24,
                          paper_bgcolor='dimgray',
                          plot_bgcolor='dimgray',
                          font_color='linen',
                          hoverlabel=dict(
                              bgcolor='linen',
                              font_size=9,
                      )
                      ).update_traces(marker=dict(colors=colors,line=dict(color='linen',width=1)))
                      )]

if __name__ == '__main__':
    app.run_server(debug=True)
