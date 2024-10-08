# gui/config_generator.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import os
import json
import random
from pathlib import Path

CONFIG_FILE = "ai_toolkit_helper_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            return json.load(config_file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config, config_file)

def add_tooltip(widget, text):
    tooltip = None

    def on_enter(event):
        nonlocal tooltip
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        x = event.x_root + 20
        y = event.y_root + 10
        tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def on_leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def convert_windows_path(path):
    return str(Path(path).as_posix())

def create_config_generator_tab(tab, ai_toolkit_folder):
    frame = ttk.Frame(tab)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Training subject selection
    label_subject = ttk.Label(frame, text="Training Subject:")
    label_subject.grid(row=0, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_subject, "Select what you are training: person, style, or object.")
    subject_selector = ttk.Combobox(frame, values=["Person", "Style", "Object"], state="readonly")
    subject_selector.grid(row=0, column=1, padx=5, pady=5)
    subject_selector.set("Person")

    # Kind of person input
    label_kind_of_person = ttk.Label(frame, text="Kind of Person:")
    label_kind_of_person.grid(row=1, column=0, sticky="w", padx=5, pady=5)
    kind_of_person_entry = ttk.Entry(frame)
    kind_of_person_entry.grid(row=1, column=1, padx=5, pady=5)
    add_tooltip(kind_of_person_entry, "Specify the type of person (e.g., man, woman, boy, girl)")

    # Model Name input
    label_model_name = ttk.Label(frame, text="Model Name:")
    label_model_name.grid(row=2, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_model_name, "Enter the model name for the training configuration.")
    model_name_entry = ttk.Entry(frame)
    model_name_entry.grid(row=2, column=1, padx=5, pady=5)

    # Trigger word input
    label_trigger_word = ttk.Label(frame, text="Trigger Word:")
    label_trigger_word.grid(row=3, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_trigger_word, "Enter a trigger word for your model.")
    trigger_word_entry = ttk.Entry(frame)
    trigger_word_entry.grid(row=3, column=1, padx=5, pady=5)

    # Folder path input with Browse button
    label_folder_path = ttk.Label(frame, text="Dataset Folder Path:")
    label_folder_path.grid(row=4, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_folder_path, "Select the folder containing your dataset images.")
    folder_path_entry = ttk.Entry(frame)
    folder_path_entry.grid(row=4, column=1, padx=5, pady=5)
    folder_path_browse_button = ttk.Button(frame, text="Browse", command=lambda: browse_folder(folder_path_entry))
    folder_path_browse_button.grid(row=4, column=2, padx=5, pady=5)

    # Rank input
    label_rank = ttk.Label(frame, text="Rank:")
    label_rank.grid(row=5, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_rank, "Set the rank value for LoRA training. Higher values increase model capacity.")
    rank_entry = ttk.Entry(frame)
    rank_entry.grid(row=5, column=1, padx=5, pady=5)
    rank_entry.insert(0, "64")  # Default value

    # Learning rate input
    label_lr = ttk.Label(frame, text="Learning Rate:")
    label_lr.grid(row=6, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_lr, "Specify the learning rate for training. Typical values are between 1e-5 and 1e-3.")
    lr_entry = ttk.Entry(frame)
    lr_entry.grid(row=6, column=1, padx=5, pady=5)
    lr_entry.insert(0, "1e-4")  # Default value

    # Training steps input
    label_steps = ttk.Label(frame, text="Training Steps:")
    label_steps.grid(row=7, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_steps, "Enter the total number of training steps.")
    steps_entry = ttk.Entry(frame)
    steps_entry.grid(row=7, column=1, padx=5, pady=5)
    steps_entry.insert(0, "2000")  # Default value

    # Batch size input
    label_batch_size = ttk.Label(frame, text="Batch Size:")
    label_batch_size.grid(row=8, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_batch_size, "Set the batch size for training. Adjust based on your GPU memory.")
    batch_size_entry = ttk.Entry(frame)
    batch_size_entry.grid(row=8, column=1, padx=5, pady=5)
    batch_size_entry.insert(0, "1")  # Default value

    # Save every input
    label_save_every = ttk.Label(frame, text="Save Every:")
    label_save_every.grid(row=9, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_save_every, "Specify how often (in steps) to save checkpoints.")
    save_every_entry = ttk.Entry(frame)
    save_every_entry.grid(row=9, column=1, padx=5, pady=5)
    save_every_entry.insert(0, "250")  # Default value

    # Max step saves input
    label_max_saves = ttk.Label(frame, text="Max Step Saves:")
    label_max_saves.grid(row=10, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_max_saves, "Specify the maximum number of checkpoint saves to keep.")
    max_saves_entry = ttk.Entry(frame)
    max_saves_entry.grid(row=10, column=1, padx=5, pady=5)
    max_saves_entry.insert(0, "10")  # Default value

    # Sample every input
    label_sample_every = ttk.Label(frame, text="Sample Every:")
    label_sample_every.grid(row=11, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_sample_every, "Specify how often (in steps) to generate sample images.")
    sample_every_entry = ttk.Entry(frame)
    sample_every_entry.grid(row=11, column=1, padx=5, pady=5)
    sample_every_entry.insert(0, "250")  # Default value

    # Shuffle tokens input
    label_shuffle_tokens = ttk.Label(frame, text="Shuffle Tokens:")
    label_shuffle_tokens.grid(row=12, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_shuffle_tokens, "Choose whether to randomly shuffle the order of words in captions.")
    shuffle_tokens_var = tk.BooleanVar(value=False)
    shuffle_tokens_checkbox = ttk.Checkbutton(frame, variable=shuffle_tokens_var)
    shuffle_tokens_checkbox.grid(row=12, column=1, padx=5, pady=5)

    # Prompt entries
    prompt_entries = []
    for i in range(5):
        label = ttk.Label(frame, text=f"Prompt {i+1}:")
        label.grid(row=13+i, column=0, sticky="w", padx=5, pady=5)
        entry = ttk.Entry(frame, width=50)
        entry.grid(row=13+i, column=1, columnspan=2, padx=5, pady=5)
        prompt_entries.append(entry)

    # Seed input
    label_seed = ttk.Label(frame, text="Seed:")
    label_seed.grid(row=18, column=0, sticky="w", padx=5, pady=5)
    add_tooltip(label_seed, "Enter a seed number or 'random' for reproducibility.")
    seed_entry = ttk.Entry(frame)
    seed_entry.grid(row=18, column=1, padx=5, pady=5)
    seed_entry.insert(0, "random")  # Default value

    def update_prompt_templates(*args):
        subject = subject_selector.get().lower()
        templates = {
            "person": [
                "[trigger], [kind_of_person], candid closeup portrait photograph",
                "[trigger], [kind_of_person], in a professional studio setting",
                "[trigger], [kind_of_person], wearing traditional clothing",
                "[trigger], [kind_of_person], in an outdoor adventure scene",
                "[trigger], [kind_of_person], engaged in their profession"
            ],
            "object": [
                "[trigger] on a wooden table",
                "[trigger] surrounded by nature",
                "[trigger] in a modern setting",
                "[trigger] being used by a person",
                "[trigger] in an abstract composition"
            ],
            "style": [
                "A painting in the style of [trigger]",
                "An illustration inspired by [trigger]",
                "A sculpture resembling [trigger]",
                "A landscape in the manner of [trigger]",
                "A portrait using techniques of [trigger]"
            ]
        }
        for entry, template in zip(prompt_entries, templates.get(subject, [])):
            entry.delete(0, tk.END)
            entry.insert(0, template)
        
        # Show/hide "Kind of Person" input based on subject
        if subject == "person":
            label_kind_of_person.grid()
            kind_of_person_entry.grid()
        else:
            label_kind_of_person.grid_remove()
            kind_of_person_entry.grid_remove()

    # Bind the update function to the subject selector
    subject_selector.bind("<<ComboboxSelected>>", update_prompt_templates)

    # Initial update of prompt templates
    update_prompt_templates()

    def generate_yaml_config():
        # Get values from entries
        training_subject = subject_selector.get().lower()
        kind_of_person = kind_of_person_entry.get() if training_subject == "person" else ""
        model_name = model_name_entry.get() or "my_first_flux_lora"
        trigger_word = trigger_word_entry.get() or model_name
        folder_path = folder_path_entry.get() or "/path/to/images/folder"
        rank = int(rank_entry.get() or "64")
        lr = lr_entry.get() or "1e-4"
        steps = int(steps_entry.get() or "2000")
        batch_size = int(batch_size_entry.get() or "1")
        save_every = int(save_every_entry.get() or "250")
        max_step_saves = int(max_saves_entry.get() or "10")
        sample_every = int(sample_every_entry.get() or "250")
        shuffle_tokens = shuffle_tokens_var.get()
        prompts = [entry.get() for entry in prompt_entries if entry.get()]
        seed_input = seed_entry.get()

        # Process seed
        if seed_input.lower() == 'random':
            seed = random.randint(1, 1000000)
        else:
            seed = int(seed_input)

        # Rename the LoRA with settings appended
        lora_name = f"{model_name}_flux_r{rank}_{lr.replace('e-', '-e')}"

        # Replace placeholders in prompts
        replaced_prompts = []
        for prompt in prompts:
            replaced_prompt = prompt.replace("[trigger]", trigger_word)
            if training_subject == "person":
                replaced_prompt = replaced_prompt.replace("[kind_of_person]", kind_of_person)
            replaced_prompts.append(replaced_prompt)

        # Define the base YAML structure
        yaml_content = {
            "job": "extension",
            "config": {
                "name": lora_name,
                "process": [
                    {
                        "type": "sd_trainer",
                        "training_folder": f"output/{lora_name}",
                        "device": "cuda:0",
                        "trigger_word": trigger_word,
                        "network": {
                            "type": "lora",
                            "linear": rank,
                            "linear_alpha": rank,
                        },
                        "save": {
                            "dtype": "float16",
                            "save_every": save_every,
                            "max_step_saves_to_keep": max_step_saves,
                        },
                        "datasets": [
                            {
                                "folder_path": convert_windows_path(folder_path),
                                "caption_ext": "txt",
                                "caption_dropout_rate": 0.05,
                                "shuffle_tokens": shuffle_tokens,
                                "cache_latents_to_disk": True,
                                "resolution": [512, 768, 1024],
                            }
                        ],
                        "train": {
                            "batch_size": batch_size,
                            "steps": steps,
                            "gradient_accumulation_steps": 1,
                            "train_unet": True,
                            "train_text_encoder": False,
                            "gradient_checkpointing": True,
                            "noise_scheduler": "flowmatch",
                            "optimizer": "adamw8bit",
                            "lr": float(lr),
                            "ema_config": {
                                "use_ema": True,
                                "ema_decay": 0.99,
                            },
                            "dtype": "bf16",
                        },
                        "model": {
                            "name_or_path": "black-forest-labs/FLUX.1-dev",
                            "is_flux": True,
                            "quantize": True,
                        },
                        "sample": {
                            "sampler": "flowmatch",
                            "sample_every": sample_every,
                            "width": 1024,
                            "height": 1024,
                            "prompts": replaced_prompts,
                            "neg": "",
                            "seed": seed,
                            "walk_seed": True,
                            "guidance_scale": 4,
                            "sample_steps": 20,
                        }
                    }
                ],
            },
            "meta": {
                "name": lora_name,
                "version": "1.0",
            },
        }

        # Get AI Toolkit folder from global setting
        ai_toolkit_folder_value = ai_toolkit_folder.get()
        if not ai_toolkit_folder_value:
            messagebox.showerror("Error", "AI Toolkit installation folder is not set. Please set it in the Settings tab.")
            return

        # Create the config folder in the AI Toolkit installation path
        config_folder = os.path.join(ai_toolkit_folder_value, 'config')
        os.makedirs(config_folder, exist_ok=True)

        # Write the modified content to a new file in the config folder
        output_filename = f"{lora_name}.yaml"
        output_path = os.path.join(config_folder, output_filename)
        with open(output_path, 'w') as file:
            yaml.dump(yaml_content, file, default_flow_style=False, sort_keys=False)

        # Notify the user that the YAML file has been generated
        messagebox.showinfo("YAML Generation Complete",
                            f"New YAML file '{output_filename}' has been generated in the 'config' folder at '{ai_toolkit_folder_value}'.")

    # Generate YAML button
    generate_button = ttk.Button(frame, text="Generate YAML", command=generate_yaml_config)
    generate_button.grid(row=19, column=0, columnspan=3, pady=10)

def browse_folder(entry):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry.delete(0, tk.END)
        entry.insert(0, folder_selected)

def update_recommended_values(subject_selector, lr_entry, steps_entry):
    subject = subject_selector.get()
    if subject == "Person":
        lr_entry.delete(0, tk.END)
        lr_entry.insert(0, "5e-5")
        steps_entry.delete(0, tk.END)
        steps_entry.insert(0, "2000")
    elif subject == "Object":
        lr_entry.delete(0, tk.END)
        lr_entry.insert(0, "1e-4")
        steps_entry.delete(0, tk.END)
        steps_entry.insert(0, "1500")
    elif subject == "Style":
        lr_entry.delete(0, tk.END)
        lr_entry.insert(0, "1e-4")
        steps_entry.delete(0, tk.END)
        steps_entry.insert(0, "3000")