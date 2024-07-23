# flake8: noqa
import re
from urllib.parse import urlparse

from prometheus_async.aio import time
from prometheus_client import Histogram, Summary

from repour.config import config

REQ_TIME = Summary(
    "external_to_internal_req_time", "time spent with external_to_internal endpoint"
)
REQ_HISTOGRAM_TIME = Histogram(
    "external_to_internal_req_histogram", "Histogram for external_to_internal endpoint"
)

SCP_LIKE_URL_REGEX = (
    r"^(\w+://)?(.+):[A-Za-z_](.*)\.git$"  # There is ":" in the middle of url
)


@time(REQ_TIME)
@time(REQ_HISTOGRAM_TIME)
async def translate(external_to_internal_spec, repo_provider):
    external_url = external_to_internal_spec["external_url"]

    internal_url = await translate_external_to_internal(external_url)

    result = {"external_url": external_url, "internal_url": internal_url}

    return result


async def translate_external_to_internal(external_git_url):
    """Logic from original maitai code to do this: found in GitUrlParser.java#generateInternalGitRepoName"""

    c = await config.get_configuration()

    # Gerrit / GitLab
    git_backend = c.get("git_backend")

    if git_backend in c:
        git_server = c.get(git_backend).get("git_url_internal_template", None)
        # c.get(git_backend).get("git_url_internal_template", None) --> "gerrit"."git_url_internal_template"
        # or None, if not specified
    else:
        raise Exception(
            "git backend type " + git_backend + " missing in the configuration."
        )

    if git_server is None:
        raise Exception("git_url_internal_template not specified in the Repour config!")
    elif not git_server.endswith("/"):
        git_server = git_server + "/"

    # SCP like: git format of the URL -- it's having ':' in the middle, which is however not followed by the port,
    # for instance: git@github.com:myproject/myrepo.git
    is_scp_like = re.match(SCP_LIKE_URL_REGEX, external_git_url)
    print("***** is SCP like: ", is_scp_like)

    result = urlparse(external_git_url)
    print("***** URL parse result: ", result)
    scheme = result.scheme if not external_git_url.startswith("git@") else "git"
    path = result.path

    acceptable_schemes = ["https", "http", "git", "git+ssh", "ssh"]

    if scheme == "":
        raise Exception("Scheme in url is empty! Error!")

    if scheme not in acceptable_schemes:
        raise Exception("Scheme '{0}' not accepted!'".format(scheme))
    # print("***** scheme: ", scheme)

    # list comprehension is to remove empty strings
    path_parts = [x for x in path.split("/") if x]
    # print("***** path parts: ", path_parts)

    repository = None

    # extract repository part
    if path_parts[-1]:
        repository = re.sub(r"\.git$", "", path_parts[-1])
    # print("***** repository", repository)

    print("***** git backend: ", git_backend)
    print("***** git server: ", git_server)
    print("***** path parts: ", path_parts)

    if len(path_parts) > 1:
        print("***** path_parts[-2]: ", path_parts[-2])

    organization = None
    # if organization name is 'gerrit' (in gerrit) or the same as workspace group name (in gitlab), don't use it then
    if (
        len(path_parts) > 1
        and (
            (git_backend == "gerrit" and path_parts[-2] != "gerrit")
            or (
                git_backend == "gitlab"
                and not git_server.endswith(path_parts[-2] + "/")
            )
        )
        and path_parts[-2]
    ):
        organization = (
            path_parts[-2] if not is_scp_like else path_parts[-2].split(":")[-1]
        )

    org_res = organization if organization is not None else "None provided"
    print("***** organization: ", org_res)

    if organization and repository:
        repo_name = organization + "/" + repository
    elif repository:
        repo_name = repository
    else:
        raise Exception("Could not translate the URL: No repository specified!")

    computed_internal = git_server + repo_name + ".git"
    print("***** computed internal: ", computed_internal)
    return computed_internal
    # return git_server + repo_name + ".git"
