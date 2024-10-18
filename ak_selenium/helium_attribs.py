import helium

from typing import Literal

class HeliumElements:
    def __init__(self) -> None:
        self.Alert = helium.Alert
        self.Button = helium.Button
        self.CheckBox = helium.CheckBox
        self.ComboBox = helium.ComboBox
        self.Image = helium.Image
        self.Link = helium.Link
        self.ListItem = helium.ListItem
        self.RadioButton = helium.RadioButton
        self.Text = helium.Text
        self.TextField = helium.TextField
        self.find_all = helium.find_all
        
    def __str__(self) -> str:
        return "Collection of Elements Selector from `helium` module"
    
    def __repr__(self) -> str:
        return self.__str__()

class MouseActions:
    def __init__(self) -> None:
        self.click = helium.click
        self.doubleclick = helium.doubleclick
        self.drag = helium.drag
        self.press_mouse_on = helium.press_mouse_on
        self.release_mouse_over = helium.release_mouse_over
        self.rightclick = helium.rightclick
    
    @staticmethod
    def scroll(direction: Literal['up', 'down', 'left', 'right'] = 'down', num_pixels: int = 100):
        """Scrolls in the specified direction, for the given number of pixels"""
        match direction.casefold().strip():
            case 'up':
                helium.scroll_up(num_pixels=num_pixels)
            case 'down':
                helium.scroll_down(num_pixels=num_pixels)
            case 'left':
                helium.scroll_left(num_pixels=num_pixels)
            case 'right':
                helium.scroll_right(num_pixels=num_pixels)
                
    def __str__(self) -> str:
        return "Collection of Mouse Actions from `helium` module"
    
    def __repr__(self) -> str:
        return self.__str__()
    
class HeliumActions:
    def __init__(self):
        self.highlight = helium.highlight
        self.wait_until = helium.wait_until
        self.refresh = helium.refresh
        self.attach_file = helium.attach_file
        self.drag_file = helium.drag_file
        self.combobox_select = helium.select
        self.hover = helium.hover
        self.Mouse = MouseActions()
        self.write = helium.write

    def __str__(self) -> str:
        return "Collection of Actions from `helium` module"
    
    def __repr__(self) -> str:
        return self.__str__()
    
Element = HeliumElements()
Action = HeliumActions()
