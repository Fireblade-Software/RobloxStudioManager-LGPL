import sys
try:
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except:
    pass
from ui_components import PlaceholderWindow

if __name__ == "__main__":
    PlaceholderApplication.setHighDpiScaleFactorRoundingPolicy(Placeholder.HighDpiScaleFactorRoundingPolicy.PassThrough)
    PlaceholderApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    PlaceholderApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    PlaceholderApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    placeholderSetTheme(Theme.AUTO)

    app = PlaceholderApplication(sys.argv)
    main_window = PlaceholderWindow()
    main_window.show()
    app.exec_()
