import pandas as pd
from html import escape
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, PackageLoader, select_autoescape

from giskard.utils.analytics_collector import analytics, anonymize
from .visualization.custom_jinja import pluralize, format_metric


class ScanResult:
    def __init__(self, issues):
        self.issues = issues

    def has_issues(self):
        return len(self.issues) > 0

    def __repr__(self):
        if not self.has_issues():
            return "<PerformanceScanResult (no issues)>"

        return f"<PerformanceScanResult ({len(self.issues)} issue{'s' if len(self.issues) > 1 else ''})>"

    def _ipython_display_(self):
        from IPython.core.display import display_html

        html = self._repr_html_()
        display_html(html, raw=True)

    def _repr_html_(self):
        return self.to_html(embed=True)

    def to_html(self, filename=None, embed=False):
        env = Environment(
            loader=PackageLoader("giskard.scanner", "templates"),
            autoescape=select_autoescape(),
        )
        env.filters["pluralize"] = pluralize
        env.filters["format_metric"] = format_metric

        tpl = env.get_template("scan_results.html")

        issues_by_group = defaultdict(list)
        for issue in self.issues:
            issues_by_group[issue.group].append(issue)

        html = tpl.render(
            issues=self.issues,
            issues_by_group=issues_by_group,
            num_major_issues={
                group: len([i for i in issues if i.level == "major"]) for group, issues in issues_by_group.items()
            },
            num_medium_issues={
                group: len([i for i in issues if i.level == "medium"]) for group, issues in issues_by_group.items()
            },
            num_info_issues={
                group: len([i for i in issues if i.level == "info"]) for group, issues in issues_by_group.items()
            },
        )

        if embed:
            # Put the HTML in an iframe
            escaped = escape(html)
            uid = id(self)

            with Path(__file__).parent.joinpath("templates", "static", "external.js").open("r") as f:
                js_lib = f.read()

            html = f"""<iframe id="scan-{uid}" srcdoc="{escaped}" style="width: 100%; border: none;" class="gsk-scan"></iframe>
<script>
{js_lib}
(function(){{iFrameResize({{ checkOrigin: false }}, '#scan-{uid}');}})();
</script>"""

        if filename is not None:
            with open(filename, "w") as f:
                f.write(html)
            return

        return html

    def to_dataframe(self):
        df = pd.DataFrame(
            [
                {
                    "domain": issue.domain,
                    "metric": issue.metric,
                    "deviation": issue.deviation,
                    "description": issue.description,
                }
                for issue in self.issues
            ]
        )
        return df

    def generate_tests(self, with_names=False):
        tests = sum([issue.generate_tests(with_names=with_names) for issue in self.issues], [])
        return tests

    def generate_test_suite(self, name=None):
        from giskard import Suite

        suite = Suite(name=name or "Test suite (generated by automatic scan)")
        for test, test_name in self.generate_tests(with_names=True):
            suite.add_test(test, test_name)

        self._track_suite(suite, name)
        return suite

    def _track_suite(self, suite, name):
        tests_cnt = {}
        if suite.tests:
            for t in suite.tests:
                try:
                    name = t.giskard_test.meta.full_name
                    if name not in tests_cnt:
                        tests_cnt[name] = 1
                    else:
                        tests_cnt[name] += 1
                except:  # noqa
                    pass
        analytics.track(
            "scan:generate_test_suite",
            {"suite_name": anonymize(name), "tests_cnt": len(suite.tests), **tests_cnt},
        )
