# /// script
# requires-python = ">=3.11"
# dependencies = ["openconnect-sso==0.8.1", "pyotp==2.9.0", "setuptools>=40,<81"]
# [tool.uv]
# override-dependencies = ["lxml>=5,<6"]
# ///

import asyncio
from typing import Any

from PyQt6.QtWebEngineCore import QWebEngineScript
from openconnect_sso.browser import webengine_process
from openconnect_sso.cli import main


class PasswordBrowser(webengine_process.WebBrowser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # hide passkeys from Microsoft, so it falls back to password and TOTP
        script = QWebEngineScript()
        script.setName("vpn-password-totp")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        script.setSourceCode("""
(() => {
    if (!["login.microsoftonline.com", "login.live.com"].includes(location.hostname)) {
        return;
    }
    Object.defineProperty(window, "PublicKeyCredential", {
        configurable: true,
        value: undefined
    });

    // the auto-fill rule clicks "Next" on the passkey setup prompt,
    // so press "Not now" first and hide "Next" from that rule
    const clicked = new WeakSet();
    const skipPasskeySetup = () => {
        const skip = [...document.querySelectorAll("a, button, input[type=button], input[type=submit]")]
            .find((el) => el.offsetParent !== null
                && /^not now$/i.test((el.value || el.textContent || "").trim()));
        if (!skip) {
            return;
        }
        for (const el of document.querySelectorAll("[data-report-event=Signin_Submit]")) {
            el.removeAttribute("data-report-event");
        }
        if (!clicked.has(skip)) {
            clicked.add(skip);
            skip.click();
        }
    };
    new MutationObserver(skipPasskeySetup).observe(document, {
        attributes: true,
        childList: true,
        subtree: true
    });

    if (!navigator.credentials) {
        return;
    }
    // reject passkey calls, because they never finish in this Qt browser
    for (const method of ["create", "get"]) {
        const original = navigator.credentials[method].bind(navigator.credentials);
        Object.defineProperty(navigator.credentials, method, {
            configurable: true,
            value(options) {
                if (options && options.publicKey) {
                    return Promise.reject(new DOMException(
                        "Passkeys are unavailable in this Qt browser.",
                        "NotAllowedError"
                    ));
                }
                return original(options);
            }
        });
    }
})();
""")
        self.page().scripts().insert(script)


# apply in both the CLI and the spawned Qt process
webengine_process.WebBrowser = PasswordBrowser

if __name__ == "__main__":
    # openconnect-sso 0.8.1 expects an event loop before main starts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        raise SystemExit(main())
    finally:
        loop.close()
