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

        # report unsupported passkeys before Microsoft chooses a sign-in method
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
    if (!navigator.credentials) {
        return;
    }
    const originalGet = navigator.credentials.get.bind(navigator.credentials);
    Object.defineProperty(navigator.credentials, "get", {
        configurable: true,
        value(options) {
            if (options && options.publicKey) {
                return Promise.reject(new DOMException(
                    "Passkey sign-in is unavailable in this Qt browser.",
                    "NotAllowedError"
                ));
            }
            return originalGet(options);
        }
    });
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
