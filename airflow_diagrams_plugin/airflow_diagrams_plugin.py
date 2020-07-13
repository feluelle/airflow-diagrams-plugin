import os

from airflow import conf
from airflow.plugins_manager import AirflowPlugin
from airflow_diagrams import generate_diagram_from_dag
from flask_appbuilder import expose, has_access, BaseView as AppBuilderBaseView
from markupsafe import Markup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer


class DiagramsView(AppBuilderBaseView):
    dagbag = None
    template_folder = conf.get("core", "plugins_folder")

    @expose('/diagrams')
    @has_access
    def list(self):
        if os.environ.get('AIRFLOW_DIAGRAMS__DEFAULT_TO_BLANK', 'False') == 'False':
            os.environ['AIRFLOW_DIAGRAMS__DEFAULT_TO_BLANK'] = 'True'

        if not self.dagbag:
            from airflow.www_rbac.views import dagbag

            self.dagbag = dagbag

        diagrams = []
        for dag_id, dag in self.dagbag.dags.items():
            # Create the diagram..
            generate_diagram_from_dag(dag=dag, diagram_file=f'diagrams/{dag_id}.py')
            # ..get its python code..
            with open(f'diagrams/{dag_id}.py', 'r') as fh:
                diagram_code = fh.read()
            # ..as html..
            html_code = Markup(highlight(diagram_code, PythonLexer(), HtmlFormatter(linenos=True)))
            # ..and save it.
            diagrams.append({'title': dag_id, 'code': html_code})

        return self.render_template('diagram.html', diagrams=diagrams)


class AirflowDiagramsPlugin(AirflowPlugin):
    name = 'airflow_diagrams'
    appbuilder_views = [{
        "name": "Diagrams View",
        "category": "Diagrams",
        "view": DiagramsView()
    }]
