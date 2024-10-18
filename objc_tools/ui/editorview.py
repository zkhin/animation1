from objc_util import ObjCInstance, ObjCInstanceMethod, create_objc_class, nsurl, on_main_thread, sel, UIApplication, ObjCClass
#import ui
# mostly from https://github.com/controversial/Pythonista-Tweaks/blob/master/pythonista/editor.py
UIViewController = ObjCClass('UIViewController')
import ui
app = UIApplication.sharedApplication()
rootVC = app.keyWindow().rootViewController()
tabVC = rootVC.detailViewController()
ui.View(app).present('panel', hide_title_bar=True)

class TabView(object):
    @on_main_thread
    def __init__(self):
        self.name = ""
        self.right_button_items = []
        self.newVC = self.customVC()
        self.makeSelf()

    @on_main_thread
    def makeSelf(self):
        pass

    @on_main_thread
    def customVC(self):
        return None

    @on_main_thread
    def present(self):
        pass


class Tab(TabView):
    @on_main_thread
    def makeSelf(self):
        self.name = "Tab"

    @on_main_thread
    def customVC(self):
        return create_objc_class(
                "CustomViewController",
                UIViewController,
                methods=[],
                protocols=["OMTabContent"],
        ).new().autorelease()
        
    @on_main_thread
    def setUIView(self, view):
        self.newVC.View = ObjCInstance(view)
        
    @on_main_thread
    def present(self):
        self.newVC.title = self.name
        self.newVC.navigationItem().rightBarButtonItems = self.right_button_items
        tabVC.addTabWithViewController_(self.newVC)
        

