import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import sys
import threading

def create_training_tab(tab, ai_toolkit_folder):
    frame = ttk.Frame(tab)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Information label
    info_label = ttk.Label(frame, text="Please set the AI Toolkit folder path in the Settings tab to view config files.", 
                           wraplength=400, justify="center", style="Info.TLabel")
    info_label.grid(row=0, column=0, columnspan=5, pady=10)

    # Available configs
    available_label = ttk.Label(frame, text="Available Configs:")
    available_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
    available_listbox = tk.Listbox(frame, width=40, height=10)
    available_listbox.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    available_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=available_listbox.yview)
    available_scrollbar.grid(row=2, column=1, sticky="ns")
    available_listbox.configure(yscrollcommand=available_scrollbar.set)

    # Selected configs
    selected_label = ttk.Label(frame, text="Selected Configs (In Order):")
    selected_label.grid(row=1, column=3, sticky="w", padx=5, pady=5)
    selected_listbox = tk.Listbox(frame, width=40, height=10)
    selected_listbox.grid(row=2, column=3, padx=5, pady=5, sticky="nsew")
    selected_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=selected_listbox.yview)
    selected_scrollbar.grid(row=2, column=4, sticky="ns")
    selected_listbox.configure(yscrollcommand=selected_scrollbar.set)

    # Buttons for moving configs
    add_button = ttk.Button(frame, text="Add >", command=lambda: move_item(available_listbox, selected_listbox))
    add_button.grid(row=2, column=2, pady=5)
    remove_button = ttk.Button(frame, text="< Remove", command=lambda: move_item(selected_listbox, available_listbox))
    remove_button.grid(row=3, column=2, pady=5)
    move_up_button = ttk.Button(frame, text="Move Up", command=lambda: move_item_in_list(selected_listbox, -1))
    move_up_button.grid(row=4, column=3, pady=5)
    move_down_button = ttk.Button(frame, text="Move Down", command=lambda: move_item_in_list(selected_listbox, 1))
    move_down_button.grid(row=5, column=3, pady=5)

    # Add a progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
    progress_bar.grid(row=7, column=0, columnspan=5, sticky="ew", padx=5, pady=5)

    # Add a status label
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(frame, textvariable=status_var, wraplength=400, justify="center")
    status_label.grid(row=8, column=0, columnspan=5, pady=5)

    # Start training button
    start_button = ttk.Button(frame, text="Start Training", command=lambda: start_training_thread(selected_listbox, ai_toolkit_folder, progress_var, status_var))
    start_button.grid(row=6, column=0, columnspan=5, pady=10)

    # Refresh button
    refresh_button = ttk.Button(frame, text="Refresh Configs", command=lambda: refresh_configs(ai_toolkit_folder, available_listbox, info_label))
    refresh_button.grid(row=1, column=1, padx=5, pady=5)

    # Configure grid weights
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(3, weight=1)
    frame.rowconfigure(2, weight=1)

    # Initial population of configs
    refresh_configs(ai_toolkit_folder, available_listbox, info_label)

def refresh_configs(ai_toolkit_folder, available_listbox, info_label):
    available_listbox.delete(0, tk.END)
    ai_toolkit_path = ai_toolkit_folder.get()
    
    if not ai_toolkit_path:
        info_label.config(text="Please set the AI Toolkit folder path in the Settings tab to view config files.")
        return

    config_folder = os.path.join(ai_toolkit_path, 'config')
    if not os.path.exists(config_folder):
        info_label.config(text=f"The selected AI Toolkit folder '{ai_toolkit_path}' does not contain a 'config' folder.")
        return

    info_label.config(text="")
    config_files = [f for f in os.listdir(config_folder) if f.endswith('.yaml')]
    for config in sorted(config_files):
        available_listbox.insert(tk.END, config)

def move_item(from_listbox, to_listbox):
    selection = from_listbox.curselection()
    if selection:
        item = from_listbox.get(selection[0])
        from_listbox.delete(selection[0])
        to_listbox.insert(tk.END, item)

def move_item_in_list(listbox, direction):
    selection = listbox.curselection()
    if selection:
        index = selection[0]
        if 0 <= index + direction < listbox.size():
            item = listbox.get(index)
            listbox.delete(index)
            listbox.insert(index + direction, item)
            listbox.selection_set(index + direction)

def start_training_thread(selected_listbox, ai_toolkit_folder, progress_var, status_var):
    configs = list(selected_listbox.get(0, tk.END))
    if not configs:
        messagebox.showerror("Error", "No config files selected.")
        return

    # Start the training in a separate thread to keep the UI responsive
    threading.Thread(target=run_training, args=(configs, ai_toolkit_folder, progress_var, status_var), daemon=True).start()

def update_status(status_var, message):
    status_var.set(message)
    print(message)  # Also print to console for logging

def update_progress(progress_var, value):
    progress_var.set(value)

def run_training(configs, ai_toolkit_folder, progress_var, status_var):
    ai_toolkit_path = ai_toolkit_folder.get()
    venv_path = os.path.join(ai_toolkit_path, 'venv')
    run_script_path = os.path.join(ai_toolkit_path, 'run.py')

    if not os.path.exists(venv_path):
        update_status(status_var, "Error: Virtual environment not found.")
        return

    if not os.path.exists(run_script_path):
        update_status(status_var, "Error: run.py script not found.")
        return

    total_configs = len(configs)
    
    # Prepare the command to open a new CMD window and run all configs sequentially
    if sys.platform == "win32":
        activate_cmd = os.path.join(venv_path, 'Scripts', 'activate.bat')
        commands = [f'call "{activate_cmd}"']
        for i, config in enumerate(configs, 1):
            config_path = os.path.join(ai_toolkit_path, 'config', config)
            commands.append(f'echo Starting training for config: {config} ({i}/{total_configs})')
            commands.append(f'python "{run_script_path}" "{config_path}"')
        commands.append('echo All trainings completed.')
        commands.append('pause')
        
        cmd = ' && '.join(commands)
        full_cmd = f'start cmd /K "{cmd}"'
    else:
        # For non-Windows systems, we'll use a similar approach with bash
        activate_cmd = f'. "{os.path.join(venv_path, "bin", "activate")}"'
        commands = [activate_cmd]
        for i, config in enumerate(configs, 1):
            config_path = os.path.join(ai_toolkit_path, 'config', config)
            commands.append(f'echo "Starting training for config: {config} ({i}/{total_configs})"')
            commands.append(f'python "{run_script_path}" "{config_path}"')
        commands.append('echo "All trainings completed."')
        commands.append('read -p "Press Enter to close this window..."')
        
        cmd = '; '.join(commands)
        full_cmd = f'gnome-terminal -- bash -c \'{cmd}\''

    try:
        # Run the command to open a new window and start all trainings
        subprocess.Popen(full_cmd, shell=True, cwd=ai_toolkit_path)
        
        update_status(status_var, f"Batch training for {total_configs} configs started in a new window.")
        update_progress(progress_var, 100)
        
        messagebox.showinfo("Training Started", f"Batch training for {total_configs} configs has been started in a new window. The trainings will run automatically in sequence. Please monitor the new window for progress.")

    except Exception as e:
        update_status(status_var, f"An unexpected error occurred: {str(e)}")
        messagebox.showerror("Error", f"An error occurred while starting the training: {str(e)}")

    update_status(status_var, "Batch training process initiated. Please check the new window for progress.")