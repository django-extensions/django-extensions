#!/usr/bin/env python
import os
import pip
try:
    import requests
except ImportError:
    print("The request library is not installed. To continue:\n"
          "   pip install requests")
import sys
import urlparse
import xmlrpclib

from optparse import make_option

from django.core.management.base import NoArgsCommand

from pip.req import parse_requirements


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            "-t", "--github-api-token", action="store", dest="github_api_token",
            help="A github api authentication token."),
        make_option(
            "-r", "--requirement", action="append", dest="requirements",
            default=[], metavar="FILENAME",
            help="Check all the packages listed in the given requirements file. "
                 "This option can be used multiple times."),
    )
    help = "Scan pip requirement files for out-of-date packages."

    def handle_noargs(self, **options):
        if options["requirements"]:
            req_files = options["requirements"]
        elif os.path.exists("requirements.txt"):
            req_files = ["requirements.txt"]
        elif os.path.exists("requirements"):
            req_files = ["requirements/{0}".format(f) for f in os.listdir("requirements")
                         if os.path.isfile(os.path.join("requirements", f)) and
                         f.lower().endswith(".txt")]
        else:
            sys.exit("requirements not found")

        self.reqs = {}
        for filename in req_files:
            class Object(object):
                pass
            mockoptions = Object()
            mockoptions.default_vcs = "git"
            mockoptions.skip_requirements_regex = None
            for req in parse_requirements(filename, options=mockoptions):
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
        self.check_github()
        self.check_other()

    def check_pypi(self):
        """
        If the requirement is frozen to pypi, check for a new version.
        """
        for dist in pip.get_installed_distributions():
            name = dist.project_name
            if name in self.reqs.keys():
                self.reqs[name]["dist"] = dist

        pypi = xmlrpclib.ServerProxy("http://pypi.python.org/pypi")
        for name, req in self.reqs.items():
            if req["url"]:
                continue  # skipping github packages.
            elif "dist" in req.keys():
                dist = req["dist"]
                available = pypi.package_releases(req["pip_req"].url_name)
                if not available:
                    msg = "release is not on pypi (check capitalization and/or --extra-index-url)"
                elif available[0] != dist.version:
                    msg = "{0} available".format(available[0])
                else:
                    msg = "up to date"
                    del self.reqs[name]
                    continue
                pkg_info = "{dist.project_name} {dist.version}".format(dist=dist)
            else:
                msg = "not installed"
                pkg_info = name
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_github(self):
        """
        If the requirement is frozen to a github url, check for new commits.

        For more than 50 github api calls per hour, pipchecker requires
        authentication with the github api by settings the environemnt
        variable ``GITHUB_API_TOKEN`` or setting the command flag
        --github-api-token='mytoken'``.

        Freeze at the commit hash (sha)::
            git+git://github.com/django/django.git@393c268e725f5b229ecb554f3fac02cfc250d2df#egg=Django

        Freeze with a branch name::
            git+git://github.com/django/django.git@master#egg=Django

        Freeze with a tag::
            git+git://github.com/django/django.git@1.5b2#egg=Django

        Do not freeze::
            git+git://github.com/django/django.git#egg=Django

        This script will get the sha of frozen repo and check if that same
        sha if found at the head of any branches. If it is not found then
        the requirement is considered to be out of date.

        Therefore, freezing at the commit hash will provide the expected
        results, but if freezing at a branch or tag name, pipchecker will
        not be able to determine with certainty if the repo is out of date.

        """
        for name, req in self.reqs.items():
            if "github.com/" not in req["url"]:
                continue
            headers = {
                "content-type": "application/json",
            }
            if self.github_api_token:
                headers["Authorization"] = "token {0}".format(self.github_api_token)
            user, repo = urlparse.urlparse(req["url"]).path.split("#")[0].strip("/").rstrip("/").split("/")

            if ".git" in repo:
                repo_name, frozen_commit = repo.split(".git")
                if frozen_commit.startswith("@"):
                    frozen_commit = frozen_commit[1:]
            elif "@" in repo:
                repo_name, frozen_commit = repo.split("@")
            else:
                frozen_commit = None
                msg = "repo is not frozen"

            if frozen_commit:
                branches = requests.get("https://api.github.com/repos/{0}/{1}/branches".format(
                    user, repo_name), headers=headers).json()
                frozen_commit = requests.get("https://api.github.com/repos/{0}/{1}/commits/{2}".format(
                    user, repo_name, frozen_commit), headers=headers).json()
                if "sha" not in frozen_commit and "API Rate Limit Exceeded" in frozen_commit["message"]:
                    sys.exit("\n Aborting! Github API Rate Limit Exceeded.\n")
                if frozen_commit["sha"] in [b["commit"]["sha"] for b in branches]:
                    msg = "up to date"
                    del self.reqs[name]
                    continue
                else:
                    msg = "{0} is not the head of any branch.".format(frozen_commit["sha"][:10])

            pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_other(self):
        """
        If the requirement is frozen somewhere other than pypi or github, skip.

        If you have a private pypi or use --extra-index-url, consider contributing
        support here.
        """
        if self.reqs:
            print("\nOnly pypi and github based requirements are supported.")
            for name, req in self.reqs.items():
                pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
                print("{pkg_info:40} is not a pypi or github requirement".format(pkg_info=pkg_info))
