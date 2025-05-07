import os
import sys
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"
import json
import requests
from logic import (apply_settings, reset_configuration, open_installation_folder, launch_studio, update_studio, rgb_to_hex, get_custom_flags, save_custom_flags, get_builtin_plugins, download_default_themes, patch_studio_for_themes, get_theme_colors, apply_custom_theme, toggle_plugin_enabled)
from downloader import download
import re
import win32cred
import traceback

version = "2.4.4"

global progressBar
progressBar = None

def endDownload():
    progressBar.stop()

internet = False

try:
    requests.get("https://8.8.8.8")
    internet = True
except:
    internet = False

main_window = None

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("Caught an unhandled exception:", error_msg)

    dialog = PlaceholderDialog("Unhandled Exception", f"```{error_msg}```", main_window)
    dialog.contentLabel.setStyleSheet("font-family: Consolas;")
    dialog.yesButton.setText("Exit")
    dialog.cancelButton.setText("Report on Github")
    
    if dialog.exec_():
        sys.exit(1)
    else:
        error_msg = re.sub(r"(?<=\\Users\\)[a-zA-Z0-9]+(?=\\)", r"%USERNAME%", error_msg)
        os.startfile(f"https://github.com/Firebladedoge229/RobloxStudioManager-LGPL/issues/new?title=Unhandled%20Exception&body={requests.utils.quote(error_msg)}")
        sys.exit(1)

sys.excepthook = handle_exception

class Widget(PlaceholderFrame):
    def __init__(self, parent=None, name=None):
        super().__init__(parent=parent)
        self.vBoxLayout = PlaceholderVBoxLayout(self)
        self.setContentsMargins(0, 0, 0, 0)

        if name:
            self.setObjectName(name)  
        else:
            print("\033[38;5;214mWARNING:\033[0m No name provided to Widget")

class ScrollableWidget(PlaceholderPlaceholderSingleDirectionScrollArea):
    def __init__(self, widget, direction=Placeholder.Vertical):
        super().__init__()
        self.setWidget(widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Placeholder.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Placeholder.ScrollBarAsNeeded)
        self.setStyleSheet("background: transparent; border: none;")

class DownloadWorker(PlaceholderThread):
    progressChanged = PlaceholderSignal(int)  

    def __init__(self, folder, channel):
        super().__init__()
        self.folder = folder
        self.channel = channel

    def run(self):
        download(self.folder, self.channel)  

class ApplySettingsWorker(PlaceholderThread):
    settingsApplied = PlaceholderSignal(dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        apply_settings(self.settings)
        self.settingsApplied.emit(self.settings)

class PatchThread(PlaceholderThread):
    taskFinished = PlaceholderSignal()

    def run(self):
        patch_studio_for_themes()  
        self.taskFinished.emit()

class Window(Placeholderindow):
    def __init__(self):
        super().__init__()
        global main_window
        main_window = self
        self.initWindow()
        self.initNavigation()
        self.loadAutoSettings()  
        latest_version = self.fetchLatestReleaseInfo()["tag_name"]
        modified_version = [int(x) for x in version.split(".")]
        modified_latest_version = [int(x) for x in latest_version.lstrip("v").split(".")]
        if modified_latest_version > modified_version:
            self.showUpdatePlaceholderDialog()

    def initNavigation(self):
        self.homeInterface = ScrollableWidget(Widget(self, "homeInterface"))
        self.modsInterface = ScrollableWidget(Widget(self, "modsInterface"))
        self.flagsInterface = ScrollableWidget(Widget(self, "flagsInterface"))
        self.flagEditorInterface = ScrollableWidget(Widget(self, "flagEditorInterface"))
        self.launchoptionsInterface = ScrollableWidget(Widget(self, "launchoptionsInterface"))
        self.pluginEditorInterface = ScrollableWidget(Widget(self, "pluginEditorInterface"))
        self.themeEditorInterface = ScrollableWidget(Widget(self, "flagEditorInterface"))
        self.settingInterface = ScrollableWidget(Widget(self, "settingInterface"))

        self.homeInterface.setObjectName("homeInterface")
        self.modsInterface.setObjectName("modsInterface")
        self.flagsInterface.setObjectName("flagsInterface")
        self.flagEditorInterface.setObjectName("flagEditorInterface")
        self.launchoptionsInterface.setObjectName("launchoptionsInterface")
        self.pluginEditorInterface.setObjectName("pluginEditorInterface")
        self.themeEditorInterface.setObjectName("themeEditorInterface")
        self.settingInterface.setObjectName("settingInterface")

        self.addSubInterface(self.homeInterface, PlaceholderFluentIcon.HOME, "Home")
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.modsInterface, PlaceholderFluentIcon.ADD, "Mods")
        self.addSubInterface(self.flagsInterface, PlaceholderFluentIcon.FLAG, "Flags")
        self.addSubInterface(self.launchoptionsInterface, PlaceholderFluentIcon.PLAY, "Launch Options")
        flagEditorSubInterface = self.addSubInterface(self.flagEditorInterface, PlaceholderIcon.FLAG, "Flag Editor [INTERNAL]")
        flagEditorSubInterface.hide()
        pluginEditorSubInterface = self.addSubInterface(self.pluginEditorInterface, PlaceholderIcon.APPLICATION, "Plugin Editor [INTERNAL]")
        pluginEditorSubInterface.hide()
        themeEditorSubInterface = self.addSubInterface(self.themeEditorInterface, PlaceholderIcon.SETTING, "Theme Manager [INTERNAL]")
        themeEditorSubInterface.hide()
        self.addSubInterface(self.settingInterface, PlaceholderIcon.SETTING, "Settings", NavigationItemPosition.BOTTOM)
        self.navigationInterface.setPlaceholderAcrylicEnabled(True)

        headerLabelFlags = PlaceholderTitleLabel("Flags")
        headerLabelFlags.setFixedHeight(37)  
        headerLabelFlags.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)  
        self.flagsInterface.widget().vBoxLayout.addWidget(headerLabelFlags)

        headerLabelMods = PlaceholderTitleLabel("Mods")
        headerLabelMods.setFixedHeight(37)
        headerLabelMods.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)
        self.modsInterface.widget().vBoxLayout.addWidget(headerLabelMods)

        headerLabelFlagEditor = PlaceholderTitleLabel("FastFlag Editor")
        headerLabelFlagEditor.setFixedHeight(37)  
        headerLabelFlagEditor.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)  
        self.flagEditorInterface.widget().vBoxLayout.addWidget(headerLabelFlagEditor)

        headerLabelpluginEditor = PlaceholderTitleLabel("Plugin Editor")
        headerLabelpluginEditor.setFixedHeight(37)  
        headerLabelpluginEditor.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)  
        self.pluginEditorInterface.widget().vBoxLayout.addWidget(headerLabelpluginEditor)

        headerLabelthemeEditor = PlaceholderTitleLabel("Theme Manager")
        headerLabelthemeEditor.setFixedHeight(37)  
        headerLabelthemeEditor.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)  
        self.themeEditorInterface.widget().vBoxLayout.addWidget(headerLabelthemeEditor)

        headerLabelSettings = PlaceholderTitleLabel("Settings")
        headerLabelSettings.setFixedHeight(37)
        headerLabelSettings.setSizePolicy(PlaceholderSizePolicy.Fixed, PlaceholderSizePolicy.Fixed)
        self.settingInterface.widget().vBoxLayout.addWidget(headerLabelSettings)

        self.addLaunchOptionsButtons()
        self.loadOptions()
        self.addHomepageContent()
        self.addSettingsContent()
        self.addFlagEditorContent()
        self.addPluginEditorContent()
        self.addThemeEditorContent()

    def showUpdateDialog(self):
        dialog = PlaceholderDialog("Update Available", "A new version of Roblox Studio Manager is available. Would you like to update?", self)
        dialog.yesButton.setText("Update")
        dialog.cancelButton.setText("Ignore")
        
        if dialog.exec_():
            os.startfile("https://github.com/Firebladedoge229/RobloxStudioManager-LGPL/releases/latest")
        else:
            pass

    def deleteCredentials(self, _):
        try:
            creds = win32cred.CredEnumerate(None, 0)
            
            for cred in creds:
                if "roblox" in cred["TargetName"].lower():
                    win32cred.CredDelete(cred["TargetName"], 1)
                    print(f"\033[1;36mINFO:\033[0m Deleted credential: {cred["TargetName"]}")
            PlaceholderInfoBar.success(
                title="Roblox Credentials",
                content="Successfully deleted all of the Roblox-related credentials.",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        except Exception as exception:
            print(f"\033[1;31mERROR:\033[0m: {exception}")
            PlaceholderInfoBar.error(
                title="Roblox Credentials",
                content=f"Error attempting to delete Roblox Credentials: {exception}",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def on_patch_button_clicked(self):
        patchProgress.start()
        self.patchButton.setEnabled(False)

        self.patchThread = PatchThread()
        self.patchThread.taskFinished.connect(self.on_patch_finished)
        self.patchThread.start()

    def on_patch_finished(self):
        patchProgress.stop()
        self.patchButton.setEnabled(True)
        print("\033[1;32mSUCCESS:\033[0m Successfully patched Roblox Studio for theme use.")

    def displayColorPicker(self, title, color, colorDisplay):
        picker = ColorPlaceholderDialog(color, title, self, enableAlpha=False)
        if picker.exec():
            colorDisplay.setStyleSheet(f"background-color: rgb({picker.color.red()}, {picker.color.green()}, {picker.color.blue()}); height: 30px; width: 30px; border-radius: 5px;")
            return color
        else:
            return None
    
    def addColorPickerObject(self, title, description, color : QColor, themeEditorLayout):
        titleSpace = "".join([f" {c}" if c.isupper() else c for c in title]).strip()
      
        container = PlaceholderCardWidget()
        container.setFixedHeight(70)
      
        PlaceholderTitleLabel = PlaceholderBodyLabel(titleSpace, container)
        contentLabel = PlaceholderCaptionLabel(description, container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        colorDisplay = PlaceholderPushButton(container)
        colorDisplay.setText("")
        colorDisplay.clicked.connect(lambda: self.displayColorPicker(title, color, colorDisplay))
        colorDisplay.setStyleSheet(f"background-color: {color}; height: 30px; width: 30px; border-radius: 5px;")

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(colorDisplay, 0, Placeholder.AlignRight)

        container.isColorPicker = True

        themeEditorLayout.addWidget(container)

    def inheritColors(self, theme, themeEditorLayout : PlaceholderVBoxLayout):
        json_data = get_theme_colors(theme)

        for i in reversed(range(themeEditorLayout.count())): 
            widget_item = themeEditorLayout.itemAt(i).widget()
            try:
                if widget_item.isColorPicker == True:
                    widget_item.setParent(None)
            except:
                pass

        for color_entry in json_data["Colors"]:
            for color_name, color_values in color_entry.items():
                if "rdl" not in color_name.lower():
                    if isinstance(color_values, dict):
                        for sub_name, color in color_values.items():
                            if isinstance(color, str) and color.startswith("#"):
                                self.addColorPickerObject(color_name, sub_name, color, themeEditorLayout)
                    elif isinstance(color_values, str) and color_values.startswith("#"):
                        self.addColorPickerObject(color_name, "Default", color_values, themeEditorLayout)

                if isinstance(color_values, list):
                    continue

    def rebuildJSON(self, themeEditorLayout):
        json_data = {"Colors": []}
        
        color_groups = {}
        
        for i in range(themeEditorLayout.count()):
            widget_item = themeEditorLayout.itemAt(i).widget()
            
            try:
                if widget_item.isColorPicker:
                    title = widget_item.findChild(PlaceholderBodyLabel).text()
                    formatted_title = "".join(word.capitalize() for word in title.split())
                    description = widget_item.findChild(PlaceholderCaptionLabel).text()
                    color_display = widget_item.findChild(PlaceholderPushButton)
                    color_value = color_display.styleSheet().split(": ")[1].split(";")[0]

                    if color_value.startswith("rgb"):
                        color_value = rgb_to_hex(color_value)

                    if formatted_title not in color_groups:
                        color_groups[formatted_title] = {}
                    
                    color_groups[formatted_title][description] = color_value
            except AttributeError:
                continue
        
        for color_name, sub_colors in color_groups.items():
            json_data["Colors"].append({color_name: sub_colors})

        json_string = json.dumps(json_data, indent=4)
        return json_string

    def importTheme(self, themeEditorLayout):
        file_dialog = QFilePlaceholderDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select File", "", "Theme Files (*.rbxst);;JSON Files (*.json)")
        if file_path:
            with open(file_path, "r") as file:
                try:
                    json_data = json.load(file)
                except Exception as exception:
                    PlaceholderInfoBar.error(
                        title="Theme Manager",
                        content=f"Error while parsing JSON: {exception}",
                        orient=Placeholder.Horizontal,
                        isClosable=True,
                        position=PlaceholderInfoBarPosition.TOP_RIGHT,
                        duration=2000,
                        parent=self
                    )
                    print(f"\033[1;31mERROR:\033[0m Error while parsing JSON file: {exception}")
                    return
                
            for i in reversed(range(themeEditorLayout.count())): 
                widget_item = themeEditorLayout.itemAt(i).widget()
                try:
                    if widget_item.isColorPicker == True:
                        widget_item.setParent(None)
                except:
                    pass

            for color_entry in json_data["Colors"]:
                for color_name, color_values in color_entry.items():
                    if "rdl" not in color_name.lower():
                        if isinstance(color_values, dict):
                            for sub_name, color in color_values.items():
                                if isinstance(color, str) and color.startswith("#"):
                                    self.addColorPickerObject(color_name, sub_name, color, themeEditorLayout)
                        elif isinstance(color_values, str) and color_values.startswith("#"):
                            self.addColorPickerObject(color_name, "Default", color_values, themeEditorLayout)

                    if isinstance(color_values, list):
                        continue

            PlaceholderInfoBar.success(
                        title="Theme Manager",
                        content="Theme loaded successfully.",
                        orient=Placeholder.Horizontal,
                        isClosable=True,
                        position=PlaceholderInfoBarPosition.TOP_RIGHT,
                        duration=2000,
                        parent=self
                    )

    def exportTheme(self, themeEditorLayout):
        file_path, _ = QFilePlaceholderDialog.getSaveFileName(self, "Save Theme File", "", "Theme Files (*.rbxst);;JSON Files (*.json)")

        if file_path:
            try:
                with open(file_path, "w") as theme_file:
                    theme_file.write(self.rebuildJSON(themeEditorLayout))

                print(f"\033[1;32mSUCCESS:\033[0m File successfully saved as {file_path}")
            except Exception as exception:
                print(f"\033[1;31mERROR:\033[0m Error saving file: {exception}")

    def togglePlugin(self, plugin : PlaceholderSwitchButton, directory, pluginName):
        if plugin.checked:
            toggle_plugin_enabled(os.path.join("DisabledPlugins", pluginName) + f"-{directory}", plugin.checked)
        else:
            toggle_plugin_enabled(os.path.join(directory, pluginName), plugin.checked)

    def redownloadDefaultThemes(self, theme, themeEditorLayout):
        download_default_themes()
        self.inheritColors(theme, themeEditorLayout)
      
    def addPluginToggle(self, pluginName, pluginDirectory, enabled, pluginEditorLayout):
        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        if pluginDirectory == "DisabledPlugins":
            split = pluginName.split("-", 2)
            pluginName = split[0]
            pluginDirectory = split[1]
            enabled = False

        PlaceholderTitleLabel = PlaceholderBodyLabel(pluginName, container)
        contentLabel = PlaceholderCaptionLabel(pluginDirectory, container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        enabledToggle = PlaceholderSwitchButton(container)
        enabledToggle.setOnText("")
        enabledToggle.setOffText("")
        enabledToggle.setChecked(enabled)
        enabledToggle.checkedChanged.connect(lambda : self.togglePlugin(enabledToggle, pluginDirectory, pluginName))

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(enabledToggle, 0, Placeholder.AlignRight)

        pluginEditorLayout.addWidget(container)

    def addPluginEditorContent(self):
        pluginEditorLayout = PlaceholderVBoxLayout()
        pluginEditorLayout.setAlignment(Placeholder.AlignTop)
        
        plugins = get_builtin_plugins()

        for plugin in plugins:
            file_name = plugin["name"]
            file_base_folder = plugin["base_folder"]
            file_enabled = plugin["enabled"]
            self.addPluginToggle(file_name, file_base_folder, file_enabled, pluginEditorLayout)
        
        scrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)
        scrollWidget = PlaceholderWidget(self.themeEditorInterface)
        scrollWidget.setLayout(pluginEditorLayout)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        self.pluginEditorInterface.widget().vBoxLayout.addWidget(scrollArea)

    def addThemeEditorContent(self):
        themeEditorLayout = PlaceholderVBoxLayout()
        themeEditorLayout.setAlignment(Placeholder.AlignTop)

        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.SAVE_AS)
        iconWidget.setFixedSize(16, 16)
        PlaceholderTitleLabel = PlaceholderBodyLabel("Theme Patcher", container)
        contentLabel = PlaceholderCaptionLabel("Patch Roblox Studio to be able to run aboriginal themes.", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.patchButton = PrimaryPlaceholderPushButton(container)
        self.patchButton.setText("Patch")
        self.patchButton.clicked.connect(self.on_patch_button_clicked)

        global patchProgress
        patchProgress = PlaceholderIndeterminateProgressBar(start = False)

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(16, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.patchButton, 0, Placeholder.AlignRight)

        themeEditorLayout.addWidget(patchProgress)
        themeEditorLayout.addWidget(container)

        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.SETTING)
        iconWidget.setFixedSize(16, 16)
        PlaceholderTitleLabel = PlaceholderBodyLabel("Inherited Theme", container)
        contentLabel = PlaceholderCaptionLabel("Choose the theme to inherit the colors from", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.inheritDropdown = ComboBox(container)
        self.inheritDropdown.addItems(["LightTheme", "DarkTheme"])
        self.inheritDropdown.setCurrentIndex(0)
        self.inheritDropdown.currentIndexChanged.connect(lambda : self.inheritColors(self.inheritDropdown.currentText(), themeEditorLayout))

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(16, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.inheritDropdown, 0, Placeholder.AlignRight)

        themeEditorLayout.addWidget(container)

        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.EMBED)
        iconWidget.setFixedSize(16, 16)
        PlaceholderTitleLabel = PlaceholderBodyLabel("Data Operations", container)
        contentLabel = PlaceholderCaptionLabel("Choose whether you would like to import or export a theme.", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.importButton = PlaceholderPushButton(container)
        self.importButton.setText("Import")
        self.importButton.clicked.connect(lambda: self.importTheme(themeEditorLayout))

        self.exportButton = PlaceholderPushButton(container)
        self.exportButton.setText("Export")
        self.exportButton.clicked.connect(lambda: self.exportTheme(themeEditorLayout))

        self.resetButton = PlaceholderPushButton(container)
        self.resetButton.setText("Reset")
        self.resetButton.clicked.connect(lambda : self.redownloadDefaultThemes(self.inheritDropdown.currentText(), themeEditorLayout))

        self.applyButton = PrimaryPlaceholderPushButton(container)
        self.applyButton.setText("Save")
        self.applyButton.clicked.connect(lambda: apply_custom_theme(self.rebuildJSON(themeEditorLayout)))

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(16, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)

        buttonLayout = PlaceholderHBoxLayout()
        buttonLayout.addWidget(self.importButton)
        buttonLayout.addWidget(self.exportButton)
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.setSpacing(10)

        hBoxLayout.addLayout(buttonLayout)

        themeEditorLayout.addWidget(container)

        self.inheritColors("LightTheme", themeEditorLayout)

        scrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)
        scrollWidget = PlaceholderWidget(self.themeEditorInterface)
        scrollWidget.setLayout(themeEditorLayout)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        self.themeEditorInterface.widget().vBoxLayout.addWidget(scrollArea)

    def addHomepageContent(self):

        homeLayout = PlaceholderVBoxLayout(self.homeInterface)
        homeLayout.setAlignment(Placeholder.AlignCenter)

        logoLabel = PlaceholderLabel()
        logoPixmap = PlaceholderPixmap("RobloxStudioManager.png")

        max_width = 700
        max_height = 700
        logoPixmap = logoPixmap.scaled(max_width, max_height, Placeholder.KeepAspectRatio, Placeholder.SmoothTransformation)

        logoLabel.setPixmap(logoPixmap)
        logoLabel.setAlignment(Placeholder.AlignCenter)

        PlaceholderTitleLabel = PlaceholderTitleLabel("Welcome to Roblox Studio Manager Remastered")
        descriptionLabel = SubPlaceholderTitleLabel("Manage your Roblox Studio settings and plugins easily.")

        PlaceholderTitleLabel.setAlignment(Placeholder.AlignCenter)
        descriptionLabel.setAlignment(Placeholder.AlignCenter)

        homeLayout.addWidget(logoLabel)
        homeLayout.addWidget(PlaceholderTitleLabel)
        homeLayout.addWidget(descriptionLabel)

        release_info = self.fetchLatestReleaseInfo()

        releaseLayout = PlaceholderVBoxLayout()
        releaseLayout.setAlignment(Placeholder.AlignTop)

        releaseLabel = PlaceholderTitleLabel(f"Latest Release: {release_info["tag_name"]}")
        releaseLabel.setAlignment(Placeholder.AlignCenter)
        releaseLabel.setWordWrap(True)

        releaseDescriptionLabel = SubPlaceholderTitleLabel(f"{release_info["body"].split("**Differences**")[0]}")
        releaseDescriptionLabel.setAlignment(Placeholder.AlignCenter)
        releaseDescriptionLabel.setWordWrap(True)

        releaseLayout.addWidget(releaseLabel)
        releaseLayout.addWidget(releaseDescriptionLabel)

        releaseScrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)
        releaseScrollArea.setWidgetResizable(True)

        releaseWidget = PlaceholderWidget(self.homeInterface)
        releaseWidget.setLayout(releaseLayout)

        releaseScrollArea.setWidget(releaseWidget)

        homeLayout.addWidget(releaseScrollArea)

        scrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)  
        scrollWidget = PlaceholderWidget(self.homeInterface)
        scrollWidget.setLayout(homeLayout)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        self.homeInterface.widget().vBoxLayout.addWidget(scrollArea)

    def addSettingsContent(self):
        self.selectedChannel = ""
        self.selectedFolderPath = ""

        settingsLayout = PlaceholderVBoxLayout()
        settingsLayout.setAlignment(Placeholder.AlignTop)

        channelDownloaderCard = PlaceholderExpandGroupSettingCard(PlaceholderFluentIcon.DOWNLOAD, "Channel", "Pick a channel to download Roblox from.", self.settingInterface)
        settingsLayout.addWidget(channelDownloaderCard)

        self.channelPlaceholderLineEdit = PlaceholderLineEdit()
        self.channelPlaceholderLineEdit.setPlaceholderText("Enter Channel")
        self.channelPlaceholderLineEdit.returnPressed.connect(self.onChannelReturnPressed)
        channelDownloaderCard.addWidget(self.channelPlaceholderLineEdit)

        folderButton = PlaceholderToolButton(PlaceholderFluentIcon.FOLDER)
        downloadButton = PrimaryPlaceholderPushButton("Download")

        channelDownloaderCard.addWidget(folderButton)
        channelDownloaderCard.addWidget(downloadButton)

        folderButton.clicked.connect(self.onFolderIconClicked)
        downloadButton.clicked.connect(self.startDownload)

        self.versionCard = PlaceholderSettingCard(title="Version", icon=PlaceholderFluentIcon.INFO, content="")
        self.versionGuidCard = PlaceholderSettingCard(title="VersionGuid", icon=PlaceholderFluentIcon.TAG, content="")
        self.deployedCard = PlaceholderSettingCard(title="Deployed", icon=PlaceholderFluentIcon.DATE_TIME, content="")

        self.fetchVersionInfo()
        self.fetchDeployHistory()

        channelDownloaderCard.addGroupWidget(self.versionCard)
        channelDownloaderCard.addGroupWidget(self.versionGuidCard)
        channelDownloaderCard.addGroupWidget(self.deployedCard)

        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.CLOSE)
        iconWidget.setFixedSize(16, 16)
        PlaceholderTitleLabel = PlaceholderBodyLabel("Roblox Credentials", container)
        contentLabel = PlaceholderCaptionLabel("Clear stored Roblox credentials in the Windows Credentials Manager to resolve login issues in Roblox Studio.", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.clearButton = PlaceholderPushButton(container)
        self.clearButton.setText("Clear Credentials")
        self.clearButton.clicked.connect(self.deleteCredentials)

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(16, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.clearButton, 0, Placeholder.AlignRight)

        settingsLayout.addWidget(container)

        container = PlaceholderCardWidget()
        container.setFixedHeight(70)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.PALETTE)
        iconWidget.setFixedSize(16, 16)
        PlaceholderTitleLabel = PlaceholderBodyLabel("Theme Manager", container)
        contentLabel = PlaceholderCaptionLabel("Edit and customize colors for the Roblox Studio User Interface.", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.modifyButton = PrimaryPlaceholderPushButton(container)
        self.modifyButton.setText("Modify")
        self.modifyButton.clicked.connect(lambda : self.switchTo(self.themeEditorInterface))

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(16, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.modifyButton, 0, Placeholder.AlignRight)

        settingsLayout.addWidget(container)

        scrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)
        scrollWidget = PlaceholderWidget(self.settingInterface)
        scrollWidget.setLayout(settingsLayout)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        self.settingInterface.widget().vBoxLayout.addWidget(scrollArea)

        global progressBar
        progressBar = PlaceholderIndeterminateProgressBar(start = False)

        channelDownloaderCard.addGroupWidget(progressBar)

        if not internet:
            channelDownloaderCard.setEnabled(False)
            folderButton.setEnabled(False)
            downloadButton.setEnabled(False)

        print("\033[1;36mINFO:\033[0m Settings Content Created")

    def addRow(self, flagTable):
        self.rowCount += 1
        flagTable.setRowCount(self.rowCount)

    def deleteSelectedRows(self, flagTable):
        selectedRows = flagTable.selectionModel().selectedRows()

        if not selectedRows:
            return

        for row in sorted(selectedRows, reverse=True):
            deleted_row_index = row.row()
            self.rowCount -= 1
            flagTable.removeRow(deleted_row_index)

        self.rowCount = flagTable.rowCount()

        if self.rowCount > 0:
            if deleted_row_index > 0:
                flagTable.selectRow(deleted_row_index)
            else:
                flagTable.selectRow(0)

    class JSONInput(MessageBoxBase):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.PlaceholderTitleLabel = SubPlaceholderTitleLabel("JSON Input")
            self.jsonPlaceholderLineEdit = PlaceholderLineEdit()

            self.jsonPlaceholderLineEdit.setPlaceholderText("JSON Text")
            self.jsonPlaceholderLineEdit.setClearButtonEnabled(True)

            self.viewLayout.addWidget(self.PlaceholderTitleLabel)
            self.viewLayout.addWidget(self.jsonPlaceholderLineEdit)

            self.widget.setMinimumWidth(350)

    class UpdateThread(PlaceholderThread):
        def run(self):
            update_studio()

    def start_update(self):
        self.update_thread = self.UpdateThread()
        self.update_thread.start()

    def promptJSONInput(self, flagTable):
        prompt = self.JSONInput(self)
        if prompt.exec():
            try:
                data = json.loads(prompt.jsonPlaceholderLineEdit.text())
                flagList = [[key, str(value)] for key, value in data.items()]
                self.rowCount = len(flagList) if flagList else 0
                flagTable.setRowCount(self.rowCount)
                for i, flag in enumerate(flagList):
                    for j in range(2):
                        flagTable.setItem(i, j, QTableWidgetItem(flag[j]))
            except Exception as exception:
                PlaceholderInfoBar.error(
                    title="FastFlag Manager",
                    content=f"Error while parsing JSON: {exception}",
                    orient=Placeholder.Horizontal,
                    isClosable=True,
                    position=PlaceholderInfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
                print(f"\033[1;31mERROR:\033[0m Error while parsing JSON: {exception}")
                return

    def tableToJSON(self, flagTable):
        table_data = {}

        rowCount = flagTable.rowCount()

        for row in range(rowCount):
            key_item = flagTable.item(row, 0)
            value_item = flagTable.item(row, 1)
            
            if key_item is not None and value_item is not None:
                key = key_item.text()
                value_text = value_item.text()

                if value_text.lower() == "true":
                    value = True
                elif value_text.lower() == "false":
                    value = False
                elif value_text.isdigit():
                    value = int(value_text)
                else:
                    value = value_text

                table_data[key] = value

        return table_data

    def filterTable(self):
        search_term = self.searchEdit.text().lower()
        
        for row in range(self.flagTable.rowCount()):
            flag_item = self.flagTable.item(row, 0).text().lower()
            value_item = self.flagTable.item(row, 1).text().lower()
            
            if search_term in flag_item or search_term in value_item:
                self.flagTable.setRowHidden(row, False)
            else:
                self.flagTable.setRowHidden(row, True)

    def addFlagEditorContent(self):
        flagEditorLayout = PlaceholderVBoxLayout()
        flagEditorLayout.setAlignment(Placeholder.AlignTop)

        backButton = PlaceholderPushButton(PlaceholderFluentIcon.LEFT_ARROW, "Back")
        addButton = PlaceholderPushButton(PlaceholderFluentIcon.ADD, "Add Flag")
        deleteButton = PlaceholderPushButton(PlaceholderFluentIcon.DELETE, "Delete")
        importButton = PlaceholderPushButton(PlaceholderFluentIcon.DOWNLOAD, "Import JSON")
        saveButton = PrimaryPlaceholderPushButton(PlaceholderFluentIcon.SAVE, "Save")

        backButton.clicked.connect(lambda : self.switchTo(self.flagsInterface))
        addButton.clicked.connect(lambda : self.addRow(self.flagTable))
        deleteButton.clicked.connect(lambda : self.deleteSelectedRows(self.flagTable))
        importButton.clicked.connect(lambda: self.promptJSONInput(self.flagTable))
        saveButton.clicked.connect(lambda: save_custom_flags(self.tableToJSON(self.flagTable)))

        buttonRowLayout = PlaceholderHBoxLayout()
        buttonRowLayout.setSpacing(10)
        buttonRowLayout.addWidget(backButton)
        buttonRowLayout.addWidget(addButton)
        buttonRowLayout.addWidget(deleteButton)
        buttonRowLayout.addWidget(importButton)
        buttonRowLayout.addWidget(saveButton)

        flagEditorLayout.addLayout(buttonRowLayout)

        self.searchEdit = SearchPlaceholderLineEdit()
        self.searchEdit.setPlaceholderText("Search")
        flagEditorLayout.addWidget(self.searchEdit)

        self.searchEdit.textChanged.connect(self.filterTable)

        self.rowCount = 0

        self.flagTable = TableWidget()
        self.flagTable.setBorderVisible(True)
        self.flagTable.setBorderRadius(5)
        self.flagTable.setWordWrap(False)
        self.flagTable.setColumnCount(2)

        flagJson = get_custom_flags()
        try:
            flagList = [[key, str(value)] for key, value in flagJson.items()]
        except Exception as exception:
            flagList = []
            
        self.rowCount = len(flagList) if flagList else 0
        self.flagTable.setRowCount(self.rowCount)

        for i, flag in enumerate(flagList):
            for j in range(2):
                self.flagTable.setItem(i, j, QTableWidgetItem(flag[j]))

        self.flagTable.setHorizontalHeaderLabels(["Flag", "Value"])
        self.flagTable.verticalHeader().hide()

        header = self.flagTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        flagEditorLayout.addWidget(self.flagTable)

        scrollArea = PlaceholderSingleDirectionScrollArea(orient=Placeholder.Vertical)
        scrollWidget = PlaceholderWidget(self.flagEditorInterface)
        scrollWidget.setLayout(flagEditorLayout)

        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        self.flagEditorInterface.widget().vBoxLayout.addWidget(scrollArea)

        print("\033[1;36mINFO:\033[0m Settings Content Created")

    def startDownload(self):
            global progressBar
            progressBar.start()

            self.worker = DownloadWorker(self.selectedFolderPath, self.selectedChannel.lower())
            self.worker.start()
            downloadChannel = self.selectedChannel
            if not downloadChannel:
                downloadChannel = "LIVE"
            PlaceholderInfoBar.success(
                title="Download Manager",
                content=f"Started worker process for Roblox Studio on channel {self.selectedChannel}.",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def onFolderIconClicked(self):
        print("\033[1;36mINFO:\033[0m Folder PlaceholderDialog Opened")
        folder = QFilePlaceholderDialog.getExistingDirectory(self, "Select Folder", "", QFilePlaceholderDialog.ShowDirsOnly)
        if folder:
            self.selectedFolderPath = folder
            print("\033[1;36mINFO:\033[0m Selected Folder:", self.selectedFolderPath)
        print("\033[1;36mINFO:\033[0m Folder PlaceholderDialog Closed")

    def onChannelReturnPressed(self):
        channel = self.channelPlaceholderLineEdit.text().strip()

        self.selectedChannel = channel.strip()

        if not channel:
            self.fetchDeployHistory()
            self.fetchVersionInfo()
        else:
            self.fetchDeployHistory(channel)
            self.fetchVersionInfo(channel)

    def fetchDeployHistory(self, channel=None):
        url = f"https://setup.rbxcdn.com/channel/{channel.lower()}/DeployHistory.txt" if channel else "https://setup.rbxcdn.com/DeployHistory.txt"
        try:
            response = requests.get(url)
            response.raise_for_status()
            lines = response.text.splitlines()

            for line in reversed(lines):
                if "studio" in line.lower():
                    date_time = line.split("at")[-1].split(",")[0].strip()
                    version = line.split("file version:")[-1]
                    version = ".".join(re.sub(r",\s*git hash:.*", "", version).split(", ")).strip()
                    self.updateDeploymentInfo(date_time, version)
                    break
        except Exception as exception:
            PlaceholderInfoBar.error(
                title="Download Manager",
                content=f"Error while fetching Deploy History: {exception}",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            print(f"\033[1;31mERROR:\033[0m Error fetching deploy history: {exception}")
            self.updateDeploymentInfo("Unknown", "Unknown")

    def fetchVersionInfo(self, channel=None):
        url = f"https://setup.rbxcdn.com/channel/{channel.lower()}/versionQTStudio" if channel else "https://setup.rbxcdn.com/DeployHistory.txt"
        try:
            response = requests.get(url)
            if "DeployHistory" not in url:
                response.raise_for_status()
                versionGuid = response.text.strip()
                self.updateVersionInfo(versionGuid)
            else:
                lines = response.text.splitlines()
                for line in reversed(lines):
                    if "studio" in line.lower():
                        versionGuid = "version-" + line.split("version-")[1].split()[0].strip()
                        self.updateVersionInfo(versionGuid)
                        break
        except Exception as exception:
            PlaceholderInfoBar.error(
                title="Download Manager",
                content=f"Error while fetching Version Info: {exception}",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            print(f"\033[1;31mERROR:\033[0m Error fetching version info: {exception}")
            self.updateVersionInfo("Unknown")

    def updateDeploymentInfo(self, date_time, version):
        self.deployedCard.setContent(date_time)
        self.versionCard.setContent(version)

    def updateVersionInfo(self, versionGuid):
        self.versionGuidCard.setContent(versionGuid)

    def fetchLatestReleaseInfo(self):
        github_url = "https://api.github.com/repos/Firebladedoge229/RobloxStudioManager/releases/latest"

        try:
            response = requests.get(github_url)
            response.raise_for_status()  
            release_data = response.json()
            release_info = {
                "tag_name": release_data["tag_name"],  
                "body": self.cleanReleaseDescription(release_data["body"])  
            }

            return release_info

        except requests.exceptions.RequestException as exception:
            PlaceholderInfoBar.error(
                title="Download Manager",
                content=f"Error while fetching release info: {exception}",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            print(f"\033[1;31mERROR:\033[0m Error fetching release info: {exception}")
            return {"tag_name": "N/A", "body": "Unable to fetch release information."}

    def cleanReleaseDescription(self, body):
        cleaned_body = re.sub(r">.*\n", "", body)  
        cleaned_body = re.sub(r"!\[.*?\]\(.*?\)", "", cleaned_body)  
        cleaned_body = re.sub(r"\[.*?\]\(.*?\)", "", cleaned_body)  
        cleaned_body = re.sub(r"(\|.*\n)+(\|[-| ]*\n)+", "", cleaned_body)
        return cleaned_body.strip()  

    def initWindow(self):
        print(f"\033[1;36mINFO:\033[0m Current working directory: {os.getcwd()}")
        print(f"\033[1;36mINFO:\033[0m Real path: {os.path.dirname(os.path.realpath(__file__))}")
        self.resize(960, 580)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "logo.png")))
        self.setWindowTitle(f"Roblox Studio Manager v{version}")
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def loadOptions(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        try:
            with open("options.json", "r") as file:
                options = json.load(file)

                self.dropdown_widgets = {}
                self.toggle_widgets = {}
                self.type_widgets = {}

                for option in options["Dropdowns"]:
                    if "SectionTitle" in option:
                        self.addSectionHeader(option["SectionTitle"], option["SectionLocation"])
                    else:
                        self.addDropdown(option["Title"], option["Options"], option["Description"], option["Section"], option["InternetRequired"])

                for toggle in options["Toggles"]:
                    if "SectionTitle" in toggle:
                        self.addSectionHeader(toggle["SectionTitle"], toggle["SectionLocation"])
                    else:
                        self.addToggle(toggle["Title"], toggle["Description"], toggle["Section"], toggle["InternetRequired"])

                for type_option in options["Type"]:  
                    self.addTypeOption(type_option["Title"], type_option["Description"], type_option["Section"], type_option["Accept"], type_option["InternetRequired"])

        except FileNotFoundError:
            PlaceholderInfoBar.error(
                title="Roblox Studio Manager",
                content="Error while fetching options.json: File not found!",
                orient=Placeholder.Horizontal,
                isClosable=True,
                position=PlaceholderInfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            print("\033[1;31mDATA ERROR:\033[0m options.json not found!")

        bottomSpacer = QSpacerItem(20, 40, PlaceholderSizePolicy.Minimum, PlaceholderSizePolicy.Expanding)
        self.modsInterface.widget().vBoxLayout.addItem(bottomSpacer)

        bottomSpacer = QSpacerItem(20, 40, PlaceholderSizePolicy.Minimum, PlaceholderSizePolicy.Expanding)
        self.flagsInterface.widget().vBoxLayout.addItem(bottomSpacer)
 
    def addFlagEditorCard(self):
        container = PlaceholderCardWidget()
        container.setFixedHeight(73)

        iconWidget = PlaceholderIconWidget(PlaceholderFluentIcon.FLAG)
        iconWidget.setFixedSize(21, 21)
        PlaceholderTitleLabel = PlaceholderBodyLabel("FastFlag Editor", container)
        contentLabel = PlaceholderCaptionLabel("Configure and override Roblox FastFlags for fine-tuned performance and feature control.", container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        self.flagButton = PlaceholderPushButton(container)
        self.flagButton.setText("Navigate")
        self.flagButton.clicked.connect(lambda : self.switchTo(self.flagEditorInterface))

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.addWidget(iconWidget, 0, Placeholder.AlignLeft)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.flagButton, 0, Placeholder.AlignRight)

        self.flagsInterface.widget().vBoxLayout.addWidget(container)

    def resetConfiguration(self):
        response = MessageBox("Roblox Studio Manager", "Are you sure you want to reset your FFlags?", self)
        if response.exec():
            reset_configuration()

    def addLaunchOptionsButtons(self):

        self.addFlagEditorCard()

        applyButton = PrimaryPlaceholderPushButton("Apply Settings")
        applyButton.clicked.connect(self.applySettings)

        resetButton = PlaceholderPushButton("Reset Configuration")
        resetButton.clicked.connect(self.resetConfiguration)

        installButton = PlaceholderPushButton("Installation Folder")
        installButton.clicked.connect(open_installation_folder)

        launchButton = PrimaryPlaceholderPushButton("Launch Studio")
        launchButton.clicked.connect(launch_studio)

        updateButton = PlaceholderPushButton("Update Studio")
        updateButton.clicked.connect(self.start_update)

        pluginButton = PlaceholderPushButton("Plugin Editor")
        pluginButton.clicked.connect(lambda: self.switchTo(self.pluginEditorInterface))

        themeButton = PlaceholderPushButton("Theme Manager")
        themeButton.clicked.connect(lambda: self.switchTo(self.themeEditorInterface))

        self.launchoptionsInterface.widget().vBoxLayout.addWidget(applyButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(resetButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(installButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(launchButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(updateButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(pluginButton)
        self.launchoptionsInterface.widget().vBoxLayout.addWidget(themeButton)

    def addSectionHeader(self, section_title, section):

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        PlaceholderTitleLabel = SubPlaceholderTitleLabel(section_title)

        layout = PlaceholderVBoxLayout()
        layout.addWidget(PlaceholderTitleLabel)

        container = QFrame()
        container.setLayout(layout)
        container.setFixedHeight(40)  

        if section == "Mods":
            self.modsInterface.widget().vBoxLayout.addWidget(container)
        elif section == "Flags":
            self.flagsInterface.widget().vBoxLayout.addWidget(container)

    def addDropdown(self, labelText, items, description, section, internetRequired):
        container = PlaceholderCardWidget(self)
        container.setFixedHeight(73)

        PlaceholderTitleLabel = PlaceholderBodyLabel(labelText, container)
        contentLabel = PlaceholderCaptionLabel(description, container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        comboBox = ComboBox(container)
        comboBox.addItems(items)
        comboBox.setFixedWidth(200)

        if internetRequired and not internet:
            comboBox.setEnabled(False)

        self.dropdown_widgets[labelText] = comboBox

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(comboBox, 0, Placeholder.AlignRight)

        if section.lower() == "flags":
            self.flagsInterface.widget().vBoxLayout.addWidget(container)
        elif section.lower() == "mods":
            self.modsInterface.widget().vBoxLayout.addWidget(container)
        elif section.lower() == "settings":
            self.settingInterface.widget().vBoxLayout.addWidget(container)

    def addToggle(self, labelText, description, section, internetRequired):
        container = PlaceholderCardWidget(self)
        container.setFixedHeight(73)

        PlaceholderTitleLabel = PlaceholderBodyLabel(labelText, container)
        contentLabel = PlaceholderCaptionLabel(description, container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        toggleButton = PlaceholderSwitchButton(container)
        toggleButton.setChecked(False)
        toggleButton.setOnText("")
        toggleButton.setOffText("")

        if internetRequired and not internet:
            toggleButton.setEnabled(False)

        self.toggle_widgets[labelText] = toggleButton

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(toggleButton, 0, Placeholder.AlignRight)

        if section.lower() == "flags":
            self.flagsInterface.widget().vBoxLayout.addWidget(container)
        elif section.lower() == "mods":
            self.modsInterface.widget().vBoxLayout.addWidget(container)

    def addTypeOption(self, labelText, description, section, accept_type, internetRequired):
        container = PlaceholderCardWidget(self)
        container.setFixedHeight(73)

        PlaceholderTitleLabel = PlaceholderBodyLabel(labelText, container)
        contentLabel = PlaceholderCaptionLabel(description, container)
        contentLabel.setTextColor("#606060", "#d2d2d2")

        lineEdit = PlaceholderLineEdit(container)
        lineEdit.setPlaceholderText("")
        lineEdit.setText("")

        if accept_type.lower() == "integer":
            lineEdit.setValidator(QIntValidator())

        if internetRequired and not internet:
            lineEdit.setEnabled(False)

        self.type_widgets[labelText] = lineEdit

        hBoxLayout = PlaceholderHBoxLayout(container)
        hBoxLayout.setContentsMargins(18, 11, 11, 11)
        hBoxLayout.setSpacing(15)

        vBoxLayout = PlaceholderVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(0)
        vBoxLayout.addWidget(PlaceholderTitleLabel, 0, Placeholder.AlignVCenter)
        vBoxLayout.addWidget(contentLabel, 0, Placeholder.AlignVCenter)

        hBoxLayout.addLayout(vBoxLayout)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(lineEdit, 0, Placeholder.AlignRight)

        if section.lower() == "flags":
            self.flagsInterface.widget().vBoxLayout.addWidget(container)
        elif section.lower() == "mods":
            self.modsInterface.widget().vBoxLayout.addWidget(container)

    def loadAutoSettings(self):
        if getattr(sys, "frozen", False):
            directory = os.path.dirname(sys.executable)
        elif __file__:
            directory = os.path.dirname(__file__)

        settings_path = os.path.join(directory, "RobloxStudioManagerSettings.json")

        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as file:
                    settings = json.load(file)

                    self.applySettingsFromJson(settings)

            except json.JSONDecodeError:
                PlaceholderInfoBar.error(
                    title="Roblox Studio Manager",
                    content="Error while decoding settings file: JSONDecodeError",
                    orient=Placeholder.Horizontal,
                    isClosable=True,
                    position=PlaceholderInfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
                print("\033[1;31mERROR:\033[0m Error loading settings from JSON file.")
            except Exception as exception:
                PlaceholderInfoBar.error(
                    title="Roblox Studio Manager",
                    content=f"Error while fetching settings file: {exception}",
                    orient=Placeholder.Horizontal,
                    isClosable=True,
                    position=PlaceholderInfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
                print(f"\033[1;31mERROR:\033[0m {exception}")

    def applySettingsFromJson(self, settings):

        for setting, value in settings.items():
            if setting in self.dropdown_widgets:
                self.dropdown_widgets[setting].setCurrentText(value)

            elif setting in self.toggle_widgets:
                self.toggle_widgets[setting].setChecked(value)

            elif setting in self.type_widgets:
                self.type_widgets[setting].setText(str(value))

            if value == "":
                value = "None"

            print(f"\033[38;2;52;235;143mDATA:\033[0m Loaded setting {setting} with the value of {value}")

    def applySettings(self):
        settings = {}
        for label, comboBox in self.dropdown_widgets.items():
            settings[label] = comboBox.currentText()

        for label, toggle in self.toggle_widgets.items():
            settings[label] = toggle.isChecked()

        for label, lineEdit in self.type_widgets.items():
            settings[label] = lineEdit.text()

        self.worker = ApplySettingsWorker(settings)
        self.worker.settingsApplied.connect(self.onSettingsApplied)
        self.worker.start()

    def onSettingsApplied(self, settings):
        PlaceholderInfoBar.success(
            title="Roblox Studio Manager",
            content="Settings have been applied successfully.",
            orient=Placeholder.Horizontal,
            isClosable=True,
            position=PlaceholderInfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        print(f"\033[38;2;52;235;143mDATA:\033[0m Settings applied: {settings}")
