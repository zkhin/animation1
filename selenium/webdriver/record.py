import json
import time
import asyncio
import ui
import objc_util
from objc_util import ObjCInstance, ObjCClass, create_objc_class, on_main_thread
import scene
# ObjC bridge to WebKit
WKWebView = ObjCClass('WKWebView')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')
NSURLRequest = ObjCClass('NSURLRequest')
NSURL = ObjCClass('NSURL')
class RecordingWebView(ui.View):
    def __init__(self):
        super().__init__(frame=(0, 0, 50, 50))
        self.interaction_log = []
        self.flex = 'wh'
        self.create_webview()

    @on_main_thread
    def create_webview(self):
        try:
            screen_width, screen_height = ui.get_screen_size().width, ui.get_screen_size().height
            frame = (0, 0, screen_width, screen_height)
            self.view = ui.View(frame=frame)

            config = WKWebViewConfiguration.new()
            self.webview = WKWebView.alloc().initWithFrame_configuration_(((0, 0), (frame[2], frame[3])), config)

            ObjCInstance(self.view).addSubview_(self.webview)

            # Present the view
            def present_view():
                self.view.present('sheet', hide_title_bar=False)

            present_view()
            
            print("WebView presented.")
        except Exception as e:
            print(f"Error creating WebView: {str(e)}")
            raise

        
        print("WebView setup complete")
    @on_main_thread
    def setup_message_handler(self, config):
        @on_main_thread
        def message_handler(_self, _cmd, _controller, message):
            try:
                data = ObjCInstance(message).body()
                print(f"Received JS message: {data}")
                self.record_event(data['action'], data['element'], data.get('value'))
            except Exception as e:
                print(f"Error in message handler: {e}")

        MyMessageHandler = create_objc_class(
            'MyMessageHandler',
            methods=[message_handler],
            protocols=['WKScriptMessageHandler']
        )

        handler = MyMessageHandler.new()
        config.userContentController().addScriptMessageHandler_name_(handler, 'interactionHandler')
        print("Message handler setup complete")
    @on_main_thread
    def inject_javascript(self):
        
        self.load_url("https://www.google.com")
        js = '''
        function logEvent(action, element, value) {
            console.log("Logging event:", action, element, value);
            window.webkit.messageHandlers.interactionHandler.postMessage({
                action: action,
                element: element,
                value: value
            });
        }

        document.addEventListener('click', function(event) {
            console.log("Click event detected");
            logEvent('click', event.target.outerHTML, null);
        });

        document.addEventListener('input', function(event) {
            console.log("Input event detected");
            logEvent('input', event.target.outerHTML, event.target.value);
        });

        document.addEventListener('submit', function(event) {
            console.log("Submit event detected");
            logEvent('submit', event.target.outerHTML, null);
        });

        console.log("JavaScript injected and event listeners set up");
        logEvent('test', 'test-element', 'test-value');
        '''
        self.webview.evaluateJavaScript_completionHandler_(js, lambda error: print(f"JS injection error: {error}" if error else "JS injection successful"))
    @on_main_thread
    def record_event(self, action, element, value):
        log_entry = {
            'time': time.time(),
            'action': action,
            'element': element,
            'value': value
        }
        self.interaction_log.append(log_entry)
        print(f"Logged: {log_entry}")

    @on_main_thread
    def load_url(self, url):
        NSURL = ObjCClass('NSURL')
        NSURLRequest = ObjCClass('NSURLRequest')
        request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        self.webview.loadRequest_(request)
        print(f"URL loaded: {url}")

    def save_log(self, filename="interaction_log.json"):
        with open(filename, 'w') as f:
            json.dump(self.interaction_log, f, indent=4)
        print(f"Interactions saved to {filename}")

async def main():
    v = RecordingWebView()
    v.load_url('https://google.com')
    #v.present('panel')
    #v.bring_to_front()
    await asyncio.sleep(5)
    on_main_thread(v.inject_javascript)
    print("WebView presented. Interact with the page.")

    # Let it run for a while to capture user interactions
    await asyncio.sleep(30)

    # Save the log after 30 seconds of interactions
    v.save_log("user_interactions.json")
    print("Script execution completed")

if __name__ == '__main__':
    asyncio.run(main())
