# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import (
    bug,
    context,
    coverage,
    interfaces,
    irrelevant,
    missing_feature,
    released,
    rfc,
    scenarios,
    weblog,
    flaky,
)

# Compatibility matrix for blocking across Java variants, to be reused for multiple test suites.
# Body and path parameters not included, since they were added later.
_released_java_blocking = {
    "spring-boot": "0.110.0",
    "spring-boot-jetty": "0.111.0",
    "spring-boot-undertow": "0.111.0",
    # Supported since 0.111.0 but bugged in <0.115.0.
    "spring-boot-openliberty": "0.115.0",
    "ratpack": "1.6.0",
    "jersey-grizzly2": "1.7.0",
    "resteasy-netty3": "1.7.0",
    "vertx3": "1.7.0",
    "vertx4": "1.7.0",
    "*": "?",
}


@released(
    cpp="?",
    dotnet="2.27.0",
    php_appsec="0.7.0",
    python={"django-poc": "1.10", "flask-poc": "1.10", "*": "?"},
    nodejs="3.19.0",
    golang="1.51.0",
    ruby="1.0.0",
    java=_released_java_blocking,
)
@coverage.basic
@scenarios.appsec_blocking
@bug(context.library < "java@0.111.0", reason="Missing handler for default block action")
@missing_feature(weblog_variant="spring-boot-3-native", reason="GraalVM. Tracing support only")
@missing_feature(weblog_variant="akka-http", reason="Missing support")
class Test_BlockingAddresses:
    """Test the addresses supported for blocking"""

    def setup_request_method(self):
        self.rm_req = weblog.request("OPTIONS")

    @missing_feature(context.library < "ruby@1.12.0")
    def test_request_method(self):
        """can block on server.request.method"""

        interfaces.library.assert_waf_attack(self.rm_req, rule="tst-037-006")
        assert self.rm_req.status_code == 403

    def setup_request_uri(self):
        self.ruri_req = weblog.get("/waf/foo.git")

    def test_request_uri(self):
        """can block on server.request.uri.raw"""

        interfaces.library.assert_waf_attack(self.ruri_req, rule="tst-037-002")
        assert self.ruri_req.status_code == 403

    def setup_path_params(self):
        self.pp_req = weblog.get("/params/AiKfOeRcvG45")

    @missing_feature(
        context.library < "java@1.15.0", reason="When supported, path parameter detection happens on subsequent WAF run"
    )
    @missing_feature(library="nodejs", reason="Not supported yet")
    @irrelevant(context.library == "ruby" and context.weblog_variant == "rack")
    @irrelevant(context.library == "golang" and context.weblog_variant == "net-http")
    def test_path_params(self):
        """can block on server.request.path_params"""

        interfaces.library.assert_waf_attack(self.pp_req, rule="tst-037-007")
        assert self.pp_req.status_code == 403

    def setup_request_query(self):
        self.rq_req = weblog.get("/waf", params={"foo": "xtrace"})

    def test_request_query(self):
        """can block on server.request.query"""

        interfaces.library.assert_waf_attack(self.rq_req, rule="tst-037-001")
        assert self.rq_req.status_code == 403

    def setup_cookies(self):
        self.c_req = weblog.get("/", headers={"Cookie": "mycookie=jdfoSDGFkivRG_234"})

    @missing_feature(library="nodejs", reason="Not supported yet")
    def test_cookies(self):
        """can block on server.request.cookies"""

        interfaces.library.assert_waf_attack(self.c_req, rule="tst-037-008")
        assert self.c_req.status_code == 403

    def setup_request_body_urlencoded(self):
        self.rbue_req = weblog.post("/waf", data={"foo": "bsldhkuqwgervf"})

    @missing_feature(context.library < "java@1.15.0", reason="Happens on a subsequent WAF run")
    def test_request_body_urlencoded(self):
        """can block on server.request.body (urlencoded variant)"""

        interfaces.library.assert_waf_attack(self.rbue_req, rule="tst-037-004")
        assert self.rbue_req.status_code == 403

    def setup_request_body_multipart(self):
        self.rbmp_req = weblog.post("/waf", files={"foo": (None, "bsldhkuqwgervf")})

    @missing_feature(context.library == "dotnet", reason="Don't support multipart yet")
    @missing_feature(context.library == "php", reason="Don't support multipart yet")
    @missing_feature(context.library < "java@1.15.0", reason="Happens on a subsequent WAF run")
    @missing_feature(library="nodejs", reason="Not supported yet")
    @missing_feature(
        context.weblog_variant
        in (
            "spring-boot-jetty",
            "spring-boot-undertow",
            "spring-boot-openliberty",
            "jersey-grizzly2",
            "resteasy-netty3",
            "ratpack",
        ),
        reason="Blocking on multipart not supported yet",
    )
    @bug(context.library == "python" and context.weblog_variant == "django-poc", reason="Django bug in multipart body")
    @irrelevant(context.library == "golang", reason="Body blocking happens through SDK")
    def test_request_body_multipart(self):
        """can block on server.request.body (multipart/form-data variant)"""

        interfaces.library.assert_waf_attack(self.rbmp_req, rule="tst-037-004")
        assert self.rbmp_req.status_code == 403

    def setup_response_status(self):
        self.rss_req = weblog.get(path="/status", params={"code": "418"})

    @missing_feature(context.library < "dotnet@2.32.0")
    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library == "golang", reason="No blocking on server.response.*")
    @missing_feature(context.library < "ruby@1.10.0")
    @missing_feature(library="nodejs", reason="Not supported yet")
    def test_response_status(self):
        """can block on server.response.status"""

        interfaces.library.assert_waf_attack(self.rss_req, rule="tst-037-005")
        assert self.rss_req.status_code == 403

    def setup_not_found(self):
        self.rnf_req = weblog.get(path="/finger_print")

    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library == "ruby", reason="Not working")
    @missing_feature(library="nodejs", reason="Not supported yet")
    @missing_feature(context.library == "golang", reason="No blocking on server.response.*")
    def test_not_found(self):
        """can block on server.response.status"""

        interfaces.library.assert_waf_attack(self.rnf_req, rule="tst-037-010")
        assert self.rnf_req.status_code == 403

    def setup_response_header(self):
        self.rsh_req = weblog.get(path="/headers")

    @missing_feature(context.library < "dotnet@2.32.0")
    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library == "ruby")
    @missing_feature(context.library == "php", reason="Headers already sent at this stage")
    @missing_feature(library="nodejs", reason="Not supported yet")
    @missing_feature(context.library == "golang", reason="No blocking on server.response.*")
    def test_response_header(self):
        """can block on server.response.headers.no_cookies"""

        interfaces.library.assert_waf_attack(self.rsh_req, rule="tst-037-009")
        assert self.rsh_req.status_code == 403

    @missing_feature(reason="No endpoint defined yet")
    def test_response_cookies(self):
        assert False
