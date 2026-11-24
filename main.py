from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from jnius import autoclass
from android.runnable import run_on_ui_thread

URL = "https://onrender.com"

WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
activity = autoclass('org.kivy.android.PythonActivity').mActivity

class WebApp(App):
    def build(self):
        Clock.schedule_once(self.create_webview, 0)
        return Widget()

    @run_on_ui_thread
    def create_webview(self, *args):
        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        webview.setWebViewClient(WebViewClient())
        activity.setContentView(webview)
        webview.loadUrl(URL)

if __name__ == '__main__':
    WebApp().run()
