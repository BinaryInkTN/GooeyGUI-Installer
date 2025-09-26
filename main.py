from gooey_button import *
from libgooey import *
from gooey_container import *
from gooey_window import *
from gooey_label import *
from gooey_canvas import *
from gooey_textbox import *
from gooey_progressbar import *
from gooey_checkbox import *
from gooey_dropdown import *
from gooey_image import *
from gooey_widget import *

import threading
import time
import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import subprocess

install_in_progress = False
current_page = 0
total_pages = 6
install_path = "/usr/local"
selected_components = []
install_options = {"launch_docs": False, "install_picoflasher": False, "link_bashrc": True}
source_path = os.path.dirname(os.path.abspath(__file__))
accepted_terms = False

main_container = None
progress_bar = None
status_label = None
next_button = None
back_button = None
path_textbox = None
terms_checkbox = None
page_counter = None
launch_check = None
progress_step_labels = []
win = None

@GooeyImageCallback
def image_placeholder_callback():
    pass

@GooeyCanvasCallback
def canvas_callback(x, y):
    pass

@GooeyTextboxCallback
def textbox_callback(text):
    global install_path
    install_path = text

def update_status(message):
    if status_label:
        GooeyLabel_SetText(status_label, message)

def update_progress(value):
    if progress_bar:
        GooeyProgressBar_Update(progress_bar, value)

@GooeyButtonCallback
def next_callback() -> None:
    global current_page, next_button, back_button, accepted_terms

    if current_page == total_pages - 1:
        if install_options.get("launch_docs", True):
            launch_documentation()
        GooeyWindow_Cleanup(1, win)
        sys.exit(0)
        return

    if current_page == 1:
        GooeyWidget_MakeVisible(launch_check, install_options["launch_docs"])
        if not validate_options():
            return

    if current_page == 2:
        if not accepted_terms:
            update_status("You must accept the terms and conditions to continue")
            return

    current_page += 1
    GooeyContainer_SetActiveContainer(main_container, current_page)

    if current_page == 4:
        install_callback()


    GooeyButton_SetText(next_button, "Finish" if current_page == total_pages - 1 else "Next")
    GooeyButton_SetEnabled(back_button, current_page > 0)

    if page_counter:
        GooeyLabel_SetText(page_counter, f"Page {current_page + 1} of {total_pages}")

@GooeyButtonCallback
def back_callback() -> None:
    global current_page, next_button, back_button
    if current_page > 0:
        current_page -= 1
        GooeyContainer_SetActiveContainer(main_container, current_page)
        GooeyButton_SetText(next_button, "Next")
        GooeyButton_SetEnabled(back_button, current_page > 0)

@GooeyButtonCallback
def install_callback() -> None:
    global install_in_progress
    if install_in_progress:
        return

    install_in_progress = True
    update_status("Starting installation...")
    GooeyButton_SetEnabled(next_button, False)
    GooeyButton_SetEnabled(back_button, False)

    thread = threading.Thread(target=install_thread)
    thread.daemon = True
    thread.start()

@GooeyButtonCallback
def cancel_callback() -> None:
    global win
    GooeyWindow_Cleanup(1, win)
    sys.exit(0)

@GooeyButtonCallback
def browse_callback() -> None:
    global install_path, path_textbox

    current_path = GooeyTextbox_GetText(path_textbox)
    default_paths = ["/usr/local", "/usr"]
    is_changing_from_default = any(current_path.startswith(path) for path in default_paths)

    if is_changing_from_default:
        root = tk.Tk()
        root.withdraw()
        response = messagebox.askyesno(
            "Warning: Changing Installation Path",
            "You are changing from the default system installation path.\n\n"
            "System paths (/usr/local/lib, /usr/local/include) are recommended for proper library detection.\n"
            "Custom paths may require additional configuration.\n\n"
            "Do you want to continue with a custom path?",
            icon=messagebox.WARNING
        )
        root.destroy()

        if not response:
            return

    root = tk.Tk()
    root.withdraw()
    selected_path = filedialog.askdirectory(
        title="Select Installation Directory",
        initialdir=os.path.expanduser("~")
    )
    root.destroy()

    if selected_path:
        install_path = selected_path
        GooeyTextbox_SetText(path_textbox, install_path)

@GooeyCheckboxCallback
def gui_component_callback(checked):
    global selected_components
    if checked and "gui" not in selected_components:
        selected_components.append("gui")
    elif not checked and "gui" in selected_components:
        selected_components.remove("gui")

@GooeyCheckboxCallback
def docs_component_callback(checked):
    global selected_components
    if checked and "docs" not in selected_components:
        selected_components.append("docs")
    elif not checked and "docs" in selected_components:
        selected_components.remove("docs")

@GooeyCheckboxCallback
def examples_component_callback(checked):
    global selected_components
    if checked and "examples" not in selected_components:
        selected_components.append("examples")
    elif not checked and "examples" in selected_components:
        selected_components.remove("examples")

@GooeyCheckboxCallback
def launch_docs_callback(checked):
    global install_options
    install_options["launch_docs"] = checked

@GooeyCheckboxCallback
def picoflasher_callback(checked):
    global install_options
    install_options["install_picoflasher"] = checked

@GooeyCheckboxCallback
def bashrc_callback(checked):
    global install_options
    install_options["link_bashrc"] = checked

@GooeyCheckboxCallback
def terms_callback(checked):
    global accepted_terms
    accepted_terms = checked
    update_status("Terms accepted" if checked else "Please accept the terms and conditions")

@GooeyButtonCallback
def github_callback():
    try:
        user = os.environ.get("SUDO_USER")
        if user:
            subprocess.Popen(['sudo', '-u', user, 'xdg-open', "https://github.com/BinaryInkTN/GooeyGUI"])
        else:
            webbrowser.open("https://github.com/BinaryInkTN/GooeyGUI")
    except Exception:
        webbrowser.open("https://github.com/BinaryInkTN/GooeyGUI")

@GooeyButtonCallback
def contribute_callback():
    webbrowser.open("https://github.com/BinaryInkTN/GooeyGUI/blob/main/CONTRIBUTING.md")

@GooeyButtonCallback
def issues_callback():
    webbrowser.open("https://github.com/BinaryInkTN/GooeyGUI/issues")

@GooeyButtonCallback
def documentation_callback():
    webbrowser.open("https://github.com/BinaryInkTN/GooeyGUI/wiki")

def validate_options():
    global install_path
    if not install_path or not install_path.strip():
        update_status("Please select an installation path")
        return False
    if not selected_components or "gui" not in selected_components:
        update_status("Please select at least the GUI components to install")
        return False

    if sys.platform.startswith('linux') and not install_path.startswith(('/usr', '/usr/local')):
        root = tk.Tk()
        root.withdraw()
        response = messagebox.askyesno(
            "Custom Installation Path Warning",
            "You have selected a custom installation path instead of the recommended system paths.\n\n"
            "For proper library detection on Linux, it's recommended to use:\n"
            "- /usr/local/lib and /usr/local/include (default)\n"
            "- /usr/lib and /usr/include\n\n"
            "Custom paths may require setting LD_LIBRARY_PATH and C_INCLUDE_PATH environment variables.\n\n"
            "Do you want to continue with the custom path?",
            icon=messagebox.WARNING
        )
        root.destroy()

        if not response:
            return False

    try:
        test_file = os.path.join(install_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        update_status(f"Cannot write to directory: {str(e)}")
        return False

    return True

def launch_documentation():
    try:
        docs_path = os.path.join(install_path, "docs")
        if not os.path.exists(docs_path):
            update_status("Documentation not installed")
            return

        html_file = os.path.join(docs_path, "files.html")
        if os.path.exists(html_file):
            webbrowser.open(f"file://{html_file}")
            update_status("Documentation launched successfully!")
            return

        for file in os.listdir(docs_path):
            if file.endswith('.html'):
                webbrowser.open(f"file://{os.path.join(docs_path, file)}")
                update_status("Documentation launched successfully!")
                return

        update_status("No HTML documentation files found")
    except Exception as e:
        update_status(f"Error launching documentation: {str(e)}")

def update_progress_steps(step_index):
    for i, label in enumerate(progress_step_labels):
        if i < step_index:
            GooeyLabel_SetColor(label, 0x4CAF50)
        elif i == step_index:
            GooeyLabel_SetColor(label, 0x2196F3)
        else:
            GooeyLabel_SetColor(label, 0x757575)

def add_to_bashrc():
    if not install_options.get("link_bashrc", True):
        return True

    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        if not os.path.exists(bashrc_path):
            bashrc_path = os.path.expanduser("~/.bash_profile")
            if not os.path.exists(bashrc_path):
                bashrc_path = os.path.expanduser("~/.profile")
                if not os.path.exists(bashrc_path):
                    update_status("No bashrc file found - skipping bashrc linking")
                    return True

        with open(bashrc_path, 'r') as f:
            content = f.read()

        gooey_export = f'export GOOEY_PATH="{install_path}"'
        if gooey_export in content:
            update_status("Gooey path already in bashrc")
            return True

        with open(bashrc_path, 'a') as f:
            f.write(f"\n# Gooey Framework Installation Path\n")
            f.write(f'{gooey_export}\n')
            f.write(f'export PATH="$GOOEY_PATH/bin:$PATH"\n')
            f.write(f'export LD_LIBRARY_PATH="$GOOEY_PATH/lib:$LD_LIBRARY_PATH"\n')

        update_status("Successfully added Gooey Framework to bashrc")
        return True

    except Exception as e:
        update_status(f"Error adding to bashrc: {str(e)}")
        return False
    
def copy_files_with_progress():
    global source_path, install_path, selected_components
    files_to_copy = []

    if install_path.startswith(('/usr', '/usr/local')):
        dest_lib = "/usr/local/lib"
        dest_include = "/usr/local/include/Gooey"
        dest_docs = "/usr/local/GooeyDocs"
    else:
        dest_lib = os.path.join(install_path, "lib")
        dest_include = os.path.join(install_path, "include", "Gooey")
        dest_docs = os.path.join(install_path, "docs")

    if "gui" in selected_components:
        lib_dir = os.path.join(source_path, "lib")
        include_dir = os.path.join(source_path, "include")
        
        if os.path.exists(lib_dir):
            for file in os.listdir(lib_dir):
                if file.endswith(('.so', '.dll', '.dylib', '.a')):
                    files_to_copy.append((os.path.join(lib_dir, file), dest_lib))
        
        if os.path.exists(include_dir):
            for root, _, files in os.walk(include_dir):
                for file in files:
                    if file.endswith(('.h', '.hpp')):
                        rel_path = os.path.relpath(os.path.join(root, file), include_dir)
                        dest_file_path = os.path.join(dest_include, rel_path)
                        files_to_copy.append((os.path.join(root, file), os.path.dirname(dest_file_path)))

    if "docs" in selected_components:
        docs_dir = os.path.join(source_path, "docs")
        if os.path.exists(docs_dir):
            for root, _, files in os.walk(docs_dir):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), docs_dir)
                    dest_file_path = os.path.join(dest_docs, rel_path)
                    files_to_copy.append((os.path.join(root, file), os.path.dirname(dest_file_path)))

    if "examples" in selected_components:
        examples_dir = os.path.join(source_path, "examples")
        if os.path.exists(examples_dir):
            dest_examples = os.path.join(install_path, "examples")
            for root, _, files in os.walk(examples_dir):
                for file in files:
                    if file.endswith(('.c', '.cpp', '.h', '.hpp', '.py', 'Makefile', 'CMakeLists.txt')):
                        rel_path = os.path.relpath(os.path.join(root, file), examples_dir)
                        dest_file_path = os.path.join(dest_examples, rel_path)
                        files_to_copy.append((os.path.join(root, file), os.path.dirname(dest_file_path)))

    if not files_to_copy:
        update_status("No files found to copy")
        return True

    try:
        if not install_path.startswith(('/usr', '/usr/local')):
            os.makedirs(dest_lib, exist_ok=True)
            os.makedirs(dest_include, exist_ok=True)
            if "docs" in selected_components:
                os.makedirs(dest_docs, exist_ok=True)
            if "examples" in selected_components:
                os.makedirs(os.path.join(install_path, "examples"), exist_ok=True)
        else:
            if "gui" in selected_components:
                os.makedirs(dest_include, exist_ok=True)
            if "docs" in selected_components:
                os.makedirs(dest_docs, exist_ok=True)
            if "examples" in selected_components:
                os.makedirs(os.path.join(install_path, "examples"), exist_ok=True)
    except PermissionError:
        update_status("Permission denied: Need sudo for system directory installation")
        return False

    total_files = len(files_to_copy)
    copied_files = 0

    for src_file, dest_dir in files_to_copy:
        try:
            dest_file = os.path.join(dest_dir, os.path.basename(src_file))
            
            if "lib" in src_file and src_file.endswith(('.so', '.dll', '.dylib', '.a')):
                update_progress_steps(0)
            elif "include" in src_file:
                update_progress_steps(0)
            elif "docs" in src_file:
                update_progress_steps(1)
            elif "examples" in src_file:
                update_progress_steps(1)
            else:
                update_progress_steps(2)

            os.makedirs(dest_dir, exist_ok=True)
            
            print(f"Copying: {src_file} -> {dest_file}")
            shutil.copy2(src_file, dest_file)
            copied_files += 1
            progress = int((copied_files / total_files) * 100)
            update_progress(progress)
            update_status(f"Copying files... {copied_files}/{total_files}")
            time.sleep(0.05)

        except PermissionError as e:
            update_status(f"Permission denied copying {os.path.basename(src_file)} to {dest_dir}")
            update_status("Try running the installer with sudo for system directory installation")
            return False
        except Exception as e:
            update_status(f"Error copying {os.path.basename(src_file)}: {str(e)}")
            return False

    return True

def install_picoflasher():
    if not install_options.get("install_picoflasher", False):
        return True

    try:
        update_status("Downloading PicoFlasher installer...")
        update_progress_steps(2)
        time.sleep(1.0)
        update_status("PicoFlasher installer downloaded successfully")
        return True
    except Exception as e:
        update_status(f"Error downloading PicoFlasher: {str(e)}")
        return False

def install_thread():
    global install_in_progress, next_button, current_page
    try:
        update_status("Preparing installation...")
        update_progress(0)
        update_progress_steps(-1)
        time.sleep(1.0)

        if not copy_files_with_progress():
            update_status("Installation failed during file copy")
            return

        if not install_picoflasher():
            update_status("Installation failed during PicoFlasher setup")
            return

        update_status("Updating bashrc...")
        update_progress_steps(3)
        if not add_to_bashrc():
            update_status("Warning: Could not update bashrc, but installation continues")

        update_status("Finalizing installation...")
        update_progress_steps(4)
        for i in range(20):
            time.sleep(0.2)
            update_progress(80 + int(i * 20 / 20))

        update_status("Installation completed successfully!")
        current_page = total_pages - 1
        GooeyContainer_SetActiveContainer(main_container, current_page)

    except Exception as e:
        update_status(f"Installation error: {str(e)}")
    finally:
        install_in_progress = False
        GooeyButton_SetEnabled(next_button, True)
        GooeyButton_SetText(next_button, "Finish")
        GooeyButton_SetEnabled(back_button, False)

def create_welcome_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 0, bg)

    gooey_logo = GooeyImage_Create("gooey_logo.png", 50, 20, 84, 84, image_placeholder_callback)
    GooeyContainer_AddWidget(win, container, 0, gooey_logo)

    title = GooeyLabel_Create("Gooey Framework v1.0.3 Installer", 0.5, 50, 150)
    GooeyLabel_SetColor(title, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 0, title)

    msg = GooeyLabel_Create("Welcome to the Gooey Framework installation wizard", 0.26, 50, 190)
    GooeyLabel_SetColor(msg, 0x424242)
    GooeyContainer_AddWidget(win, container, 0, msg)

    desc = GooeyLabel_Create(
        "This wizard will guide you through the installation of Gooey Framework, "
        "a modern GUI framework for C applications.", 0.26, 50, 220
    )
    GooeyLabel_SetColor(desc, 0x616161)
    GooeyContainer_AddWidget(win, container, 0, desc)

    req = GooeyLabel_Create("System Requirements: C compiler, 50MB disk space", 0.26, 50, 360)
    GooeyLabel_SetColor(req, 0x757575)
    GooeyContainer_AddWidget(win, container, 0, req)

def create_options_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 1, bg)

    title = GooeyLabel_Create("Installation Options", 0.5, 30, 40)
    GooeyLabel_SetColor(title, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 1, title)

    path_label = GooeyLabel_Create("Installation Directory:", 0.26, 30, 80)
    GooeyLabel_SetColor(path_label, 0x424242)
    GooeyContainer_AddWidget(win, container, 1, path_label)

    global path_textbox
    if sys.platform.startswith('linux'):
        default_path = "/usr/local"
    else:
        default_path = os.path.join(os.path.expanduser("~"), "GooeyFramework")

    path_textbox = GooeyTextBox_Create(30, 85, 450, 30, default_path, False, textbox_callback)
    GooeyContainer_AddWidget(win, container, 1, path_textbox)

    browse_btn = GooeyButton_Create("Browse", 490, 85, 80, 30, browse_callback)
    GooeyContainer_AddWidget(win, container, 1, browse_btn)

    path_note = GooeyLabel_Create(
        "Recommended (Requires root privileges): /usr/local (system-wide) or /usr (distribution-wide)",
        0.26, 30, 130
    )
    GooeyLabel_SetColor(path_note, 0x757575)
    GooeyContainer_AddWidget(win, container, 1, path_note)

    comp_label = GooeyLabel_Create("Select Components:", 0.26, 30, 150)
    GooeyLabel_SetColor(comp_label, 0x424242)
    GooeyContainer_AddWidget(win, container, 1, comp_label)

    gui_checkbox = GooeyCheckbox_Create(30, 160, "GUI Components (required)", gui_component_callback)
    GooeyContainer_AddWidget(win, container, 1, gui_checkbox)

    docs_checkbox = GooeyCheckbox_Create(30, 190, "Documentation", docs_component_callback)
    GooeyContainer_AddWidget(win, container, 1, docs_checkbox)

    examples_checkbox = GooeyCheckbox_Create(30, 220, "Example Projects", examples_component_callback)
    GooeyContainer_AddWidget(win, container, 1, examples_checkbox)

    bashrc_checkbox = GooeyCheckbox_Create(30, 250, "Add Gooey Framework to bashrc (recommended)", bashrc_callback)
    GooeyContainer_AddWidget(win, container, 1, bashrc_checkbox)

    bashrc_note = GooeyLabel_Create("Adds environment variables to your bashrc for easy access", 0.26, 50, 280)
    GooeyLabel_SetColor(bashrc_note, 0x757575)
    GooeyContainer_AddWidget(win, container, 1, bashrc_note)

def create_terms_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 2, bg)

    title = GooeyLabel_Create("Terms and Conditions", 0.5, 30, 40)
    GooeyLabel_SetColor(title, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 2, title)

    terms_text = [
        "END-USER LICENSE AGREEMENT FOR GOOEY FRAMEWORK",
        "",
        "1. GRANT OF LICENSE. binaryink.dev grants you the right to use one copy of the",
        "   software on a single computer.",
        "",
        "2. COPYRIGHT. The software is owned by binaryink.dev and is protected by copyright laws.",
        "",
        "3. NO WARRANTY. The software is provided 'as is' without warranty of any kind.",
        "",
        "4. LIMITATION OF LIABILITY. In no event shall binaryink.dev be liable for any damages",
        "   arising from the use of this software.",
        "",
        "5. DISTRIBUTION. You may not distribute, rent, lease, or sell this software.",
        "",
        "By accepting this agreement, you agree to be bound by these terms and conditions."
    ]

    y_pos = 70
    for line in terms_text:
        term_label = GooeyLabel_Create(line, 0.26, 30, y_pos)
        GooeyLabel_SetColor(term_label, 0x616161)
        GooeyContainer_AddWidget(win, container, 2, term_label)
        y_pos += 18

    global terms_checkbox
    terms_checkbox = GooeyCheckbox_Create(30, 350, "I accept the terms and conditions", terms_callback)
    GooeyContainer_AddWidget(win, container, 2, terms_checkbox)

def create_collaborate_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 3, bg)

    title = GooeyLabel_Create("Get Involved in the Development", 0.5, 30, 40)
    GooeyLabel_SetColor(title, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 3, title)

    subtitle = GooeyLabel_Create("Join the Gooey Framework community", 0.26, 30, 80)
    GooeyLabel_SetColor(subtitle, 0x424242)
    GooeyContainer_AddWidget(win, container, 3, subtitle)

    desc = GooeyLabel_Create(
        "Gooey Framework is an open-source project. We welcome contributions "
        "from developers of all skill levels.", 0.26, 30, 110
    )
    GooeyLabel_SetColor(desc, 0x616161)
    GooeyContainer_AddWidget(win, container, 3, desc)

    view_on_github_image = GooeyImage_Create("visit_github.png", 20, 180, int(625//2), int(151//2), github_callback)
    GooeyContainer_AddWidget(win, container, 3, view_on_github_image)
   
    note = GooeyLabel_Create(
        "This option will open an external web browser.",
        0.26, 30, 300
    )
    GooeyLabel_SetColor(note, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 3, note)

def create_install_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 4, bg)

    title = GooeyLabel_Create("Installing Gooey Framework", 0.5, 30, 50)
    GooeyLabel_SetColor(title, 0x2196F3)
    GooeyContainer_AddWidget(win, container, 4, title)

    subtitle = GooeyLabel_Create(
        "Please wait while the installer sets up Gooey Framework on your system.", 0.26, 30, 90
    )
    GooeyLabel_SetColor(subtitle, 0x424242)
    GooeyContainer_AddWidget(win, container, 4, subtitle)

    step_label = GooeyLabel_Create("Installation Steps:", 0.26, 30, 130)
    GooeyLabel_SetColor(step_label, 0x616161)
    GooeyContainer_AddWidget(win, container, 4, step_label)

    global progress_step_labels
    progress_step_labels = [
        GooeyLabel_Create("• Copying library files...", 0.26, 50, 160),
        GooeyLabel_Create("• Installing selected components...", 0.26, 50, 190),
        GooeyLabel_Create("• Updating bashrc...", 0.26, 50, 220),
        GooeyLabel_Create("• Finalizing installation...", 0.26, 50, 250)
    ]
    for label in progress_step_labels:
        GooeyLabel_SetColor(label, 0x757575)
        GooeyContainer_AddWidget(win, container, 4, label)

    global progress_bar
    progress_bar = GooeyProgressBar_Create(30, 280, 520, 30, 0)
    GooeyContainer_AddWidget(win, container, 4, progress_bar)

    global status_label
    status_label = GooeyLabel_Create("Preparing to install...", 0.26, 30, 330)
    GooeyLabel_SetColor(status_label, 0x616161)
    GooeyContainer_AddWidget(win, container, 4, status_label)

def create_complete_page(container):
    bg = GooeyCanvas_Create(0, 0, 600, 400, canvas_callback)
    GooeyCanvas_DrawRectangle(bg, 0, 0, 600, 400, 0xF5F5F5, True, 1.0, False, 0.0)
    GooeyContainer_AddWidget(win, container, 5, bg)

    complete_icon = GooeyImage_Create("progress-complete.png", 60, 75, 96, 96, image_placeholder_callback)
    GooeyContainer_AddWidget(win, container, 5, complete_icon)

    title = GooeyLabel_Create("Installation Complete", 0.5, 50, 220)
    GooeyLabel_SetColor(title, 0x4CAF50)
    GooeyContainer_AddWidget(win, container, 5, title)

    msg = GooeyLabel_Create("Gooey Framework has been successfully installed on your system.", 0.26, 50, 260)
    GooeyLabel_SetColor(msg, 0x424242)
    GooeyContainer_AddWidget(win, container, 5, msg)

    steps = GooeyLabel_Create("You can now start using Gooey Framework in your C projects.", 0.26, 50, 290)
    GooeyLabel_SetColor(steps, 0x616161)
    GooeyContainer_AddWidget(win, container, 5, steps)

    if install_options.get("link_bashrc", True):
        bashrc_note = GooeyLabel_Create("Note: Gooey Framework has been added to your bashrc. Restart your terminal or run 'source ~/.bashrc' to apply changes.", 0.26, 20, 350)
        GooeyLabel_SetColor(bashrc_note, 0x2196F3)
        GooeyContainer_AddWidget(win, container, 5, bashrc_note)

    #launch_check = GooeyCheckbox_Create(50, 310, "Launch documentation after installation", launch_docs_callback)
    #GooeyContainer_AddWidget(win, container, 5, launch_check)

def main():
    global main_container, next_button, back_button, win
    Gooey_Init()
    win = GooeyWindow_Create("Gooey Framework Installer", 600, 500, True)
    GooeyWindow_MakeResizable(win, False)

    main_container = GooeyContainer_Create(0, 0, 600, 400)
    for _ in range(total_pages):
        GooeyContainer_InsertContainer(main_container)

    create_welcome_page(main_container)
    create_options_page(main_container)
    create_terms_page(main_container)
    create_collaborate_page(main_container)
    create_install_page(main_container)
    create_complete_page(main_container)

    GooeyContainer_SetActiveContainer(main_container, 0)
    GooeyWindow_RegisterWidget(win, main_container)

    back_button = GooeyButton_Create("Back", 400, 420, 80, 30, back_callback)
    GooeyButton_SetEnabled(back_button, False)
    GooeyWindow_RegisterWidget(win, back_button)

    next_button = GooeyButton_Create("Next", 490, 420, 80, 30, next_callback)
    GooeyWindow_RegisterWidget(win, next_button)
    GooeyButton_SetHighlight(next_button, True)

    cancel_btn = GooeyButton_Create("Cancel", 310, 420, 80, 30, cancel_callback)
    GooeyWindow_RegisterWidget(win, cancel_btn)

    global page_counter
    page_counter = GooeyLabel_Create(f"Page {current_page + 1} of {total_pages}", 0.26, 30, 425)
    GooeyLabel_SetColor(page_counter, 0x757575)
    GooeyWindow_RegisterWidget(win, page_counter)

    footer = GooeyCanvas_Create(0, 460, 600, 40, canvas_callback)
    GooeyCanvas_DrawRectangle(footer, 0, 0, 600, 40, 0xEEEEEE, True, 1.0, False, 0.0)
    GooeyWindow_RegisterWidget(win, footer)

    copyright = GooeyLabel_Create("Installer made with Gooey by binaryink.dev | Version 1.0.3", 0.26, 30, 485)
    GooeyLabel_SetColor(copyright, 0x616161)
    GooeyWindow_RegisterWidget(win, copyright)

    GooeyWindow_Run(1, win)
    GooeyWindow_Cleanup(1, win)

if __name__ == "__main__":
    main()