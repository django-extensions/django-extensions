# -*- coding: utf-8 -*-
import json
import os
import re
from distutils.version import LooseVersion

import pip
from django.core.management.base import BaseCommand, CommandError

try:
    from pip._internal.download import PipSession
    from pip._internal.req.req_file import parse_requirements
    from pip._internal.utils.misc import get_installed_distributions
except ImportError:
    # pip < 10
    try:
        from pip import get_installed_distributions
        from pip.download import PipSession
        from pip.req import parse_requirements
    except ImportError:
        raise CommandError("Pip version 6 or higher is required")

from django_extensions.management.color import color_style
from django_extensions.management.utils import signalcommand

try:
    from urllib.parse import urlparse
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
    from xmlrpc.client import ServerProxy
except ImportError:
    # Python 2
    from urlparse import urlparse  # type: ignore
    from urllib2 import HTTPError, Request, urlopen  # type: ignore
    from xmlrpclib import ServerProxy  # type: ignore

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Command(BaseCommand):
    help = "Scan pip requirement files for out-of-date packages."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-t", "--github-api-token", action="store",
            dest="github_api_token", help="A github api authentication token."
        )
        parser.add_argument(
            "-r", "--requirement", action="append", dest="requirements",
            default=[], metavar="FILENAME",
            help="Check all the packages listed in the given requirements "
                 "file. This option can be used multiple times."
        ),
        parser.add_argument(
            "-n", "--newer", action="store_true", dest="show_newer",
            help="Also show when newer version then available is installed."
        )

    @signalcommand
    def handle(self, *args, **options):
        self.style = color_style()

        self.options = options
        if options["requirements"]:
            req_files = options["requirements"]
        elif os.path.exists("requirements.txt"):
            req_files = ["requirements.txt"]
        elif os.path.exists("requirements"):
            req_files = ["requirements/{0}".format(f) for f in os.listdir("requirements")
                         if os.path.isfile(os.path.join("requirements", f)) and
                         f.lower().endswith(".txt")]
        elif os.path.exists("requirements-dev.txt"):
            req_files = ["requirements-dev.txt"]
        elif os.path.exists("requirements-prod.txt"):
            req_files = ["requirements-prod.txt"]
        else:
            raise CommandError("Requirements file(s) not found")

        self.reqs = {}
        with PipSession() as session:
            for filename in req_files:
                for req in parse_requirements(filename, session=session):
                    # url attribute changed to link in pip version 6.1.0 and above
                    if LooseVersion(pip.__version__) > LooseVersion('6.0.8'):
                        self.reqs[req.name] = {
                            "pip_req": req,
                            "url": req.link,
                        }
                    else:
                        self.reqs[req.name] = {
                            "pip_req": req,
                            "url": req.url,
                        }

        if options["github_api_token"]:
            self.github_api_token = options["github_api_token"]
        elif os.environ.get("GITHUB_API_TOKEN"):
            self.github_api_token = os.environ.get("GITHUB_API_TOKEN")
        else:
            self.github_api_token = None  # only 50 requests per hour

        self.check_pypi()
        if HAS_REQUESTS:
            self.check_github()
        else:
            print(self.style.ERROR("Cannot check github urls. The requests library is not installed. ( pip install requests )"))
        self.check_other()

    def _urlopen_as_json(self, url, headers=None):
        """Shorcut for return contents as json"""
        req = Request(url, headers=headers)
        return json.loads(urlopen(req).read())

    def _is_stable(self, version):
        return not re.search(r'([ab]|rc)\d+$', str(version))

    def _available_version(self, dist_version, available):
        if self._is_stable(dist_version):
            stable = [v for v in available if self._is_stable(LooseVersion(v))]
            if stable:
                return LooseVersion(stable[0])

        return LooseVersion(available[0]) if available else None

    def check_pypi(self):
        """
        If the requirement is frozen to pypi, check for a new version.
        """
        for dist in get_installed_distributions():
            name = dist.project_name
            if name in self.reqs.keys():
                self.reqs[name]["dist"] = dist

        pypi = ServerProxy("https://pypi.python.org/pypi")
        for name, req in list(self.reqs.items()):
            if req["url"]:
                continue  # skipping github packages.
            elif "dist" in req:
                dist = req["dist"]
                dist_version = LooseVersion(dist.version)
                available = pypi.package_releases(req["pip_req"].name, True) or pypi.package_releases(req["pip_req"].name.replace('-', '_'), True)
                available_version = self._available_version(dist_version, available)

                if not available_version:
                    msg = self.style.WARN("release is not on pypi (check capitalization and/or --extra-index-url)")
                elif self.options['show_newer'] and dist_version > available_version:
                    msg = self.style.INFO("{0} available (newer installed)".format(available_version))
                elif available_version > dist_version:
                    msg = self.style.INFO("{0} available".format(available_version))
                else:
                    msg = "up to date"
                    del self.reqs[name]
                    continue
                pkg_info = self.style.BOLD("{dist.project_name} {dist.version}".format(dist=dist))
            else:
                msg = "not installed"
                pkg_info = name
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_github(self):
        """
        If the requirement is frozen to a github url, check for new commits.

        API Tokens
        ----------
        For more than 50 github api calls per hour, pipchecker requires
        authentication with the github api by settings the environemnt
        variable ``GITHUB_API_TOKEN`` or setting the command flag
        --github-api-token='mytoken'``.

        To create a github api token for use at the command line::
             curl -u 'rizumu' -d '{"scopes":["repo"], "note":"pipchecker"}' https://api.github.com/authorizations

        For more info on github api tokens:
            https://help.github.com/articles/creating-an-oauth-token-for-command-line-use
            http://developer.github.com/v3/oauth/#oauth-authorizations-api

        Requirement Format
        ------------------
        Pipchecker gets the sha of frozen repo and checks if it is
        found at the head of any branches. If it is not found then
        the requirement is considered to be out of date.

        Therefore, freezing at the commit hash will provide the expected
        results, but if freezing at a branch or tag name, pipchecker will
        not be able to determine with certainty if the repo is out of date.

        Freeze at the commit hash (sha)::
            git+git://github.com/django/django.git@393c268e725f5b229ecb554f3fac02cfc250d2df#egg=Django
            https://github.com/django/django/archive/393c268e725f5b229ecb554f3fac02cfc250d2df.tar.gz#egg=Django
            https://github.com/django/django/archive/393c268e725f5b229ecb554f3fac02cfc250d2df.zip#egg=Django

        Freeze with a branch name::
            git+git://github.com/django/django.git@master#egg=Django
            https://github.com/django/django/archive/master.tar.gz#egg=Django
            https://github.com/django/django/archive/master.zip#egg=Django

        Freeze with a tag::
            git+git://github.com/django/django.git@1.5b2#egg=Django
            https://github.com/django/django/archive/1.5b2.tar.gz#egg=Django
            https://github.com/django/django/archive/1.5b2.zip#egg=Django

        Do not freeze::
            git+git://github.com/django/django.git#egg=Django

        """
        for name, req in list(self.reqs.items()):
            req_url = req["url"]
            if not req_url:
                continue
            req_url = str(req_url)
            if req_url.startswith("git") and "github.com/" not in req_url:
                continue
            if req_url.endswith((".tar.gz", ".tar.bz2", ".zip")):
                continue

            headers = {
                "content-type": "application/json",
            }
            if self.github_api_token:
                headers["Authorization"] = "token {0}".format(self.github_api_token)
            try:
                path_parts = urlparse(req_url).path.split("#", 1)[0].strip("/").rstrip("/").split("/")

                if len(path_parts) == 2:
                    user, repo = path_parts

                elif 'archive' in path_parts:
                    # Supports URL of format:
                    # https://github.com/django/django/archive/master.tar.gz#egg=Django
                    # https://github.com/django/django/archive/master.zip#egg=Django
                    user, repo = path_parts[:2]
                    repo += '@' + path_parts[-1].replace('.tar.gz', '').replace('.zip', '')

                else:
                    self.style.ERROR("\nFailed to parse %r\n" % (req_url, ))
                    continue
            except (ValueError, IndexError) as e:
                print(self.style.ERROR("\nFailed to parse %r: %s\n" % (req_url, e)))
                continue

            try:
                test_auth = requests.get("https://api.github.com/django/", headers=headers).json()
            except HTTPError as e:
                print("\n%s\n" % str(e))
                return

            if "message" in test_auth and test_auth["message"] == "Bad credentials":
                print(self.style.ERROR("\nGithub API: Bad credentials. Aborting!\n"))
                return
            elif "message" in test_auth and test_auth["message"].startswith("API Rate Limit Exceeded"):
                print(self.style.ERROR("\nGithub API: Rate Limit Exceeded. Aborting!\n"))
                return

            frozen_commit_sha = None
            if ".git" in repo:
                repo_name, frozen_commit_full = repo.split(".git")
                if frozen_commit_full.startswith("@"):
                    frozen_commit_sha = frozen_commit_full[1:]
            elif "@" in repo:
                repo_name, frozen_commit_sha = repo.split("@")

            if frozen_commit_sha is None:
                msg = self.style.ERROR("repo is not frozen")

            if frozen_commit_sha:
                branch_url = "https://api.github.com/repos/{0}/{1}/branches".format(user, repo_name)
                branch_data = requests.get(branch_url, headers=headers).json()

                frozen_commit_url = "https://api.github.com/repos/{0}/{1}/commits/{2}".format(
                    user, repo_name, frozen_commit_sha
                )
                frozen_commit_data = requests.get(frozen_commit_url, headers=headers).json()

                if "message" in frozen_commit_data and frozen_commit_data["message"] == "Not Found":
                    msg = self.style.ERROR("{0} not found in {1}. Repo may be private.".format(frozen_commit_sha[:10], name))
                elif frozen_commit_data["sha"] in [branch["commit"]["sha"] for branch in branch_data]:
                    msg = self.style.BOLD("up to date")
                else:
                    msg = self.style.INFO("{0} is not the head of any branch".format(frozen_commit_data["sha"][:10]))

            if "dist" in req:
                pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
            elif frozen_commit_sha is None:
                pkg_info = name
            else:
                pkg_info = "{0} {1}".format(name, frozen_commit_sha[:10])
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_other(self):
        """
        If the requirement is frozen somewhere other than pypi or github, skip.

        If you have a private pypi or use --extra-index-url, consider contributing
        support here.
        """
        if self.reqs:
            print(self.style.ERROR("\nOnly pypi and github based requirements are supported:"))
            for name, req in self.reqs.items():
                if "dist" in req:
                    pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
                elif "url" in req:
                    pkg_info = "{url}".format(url=req["url"])
                else:
                    pkg_info = "unknown package"
                print(self.style.BOLD("{pkg_info:40} is not a pypi or github requirement".format(pkg_info=pkg_info)))
