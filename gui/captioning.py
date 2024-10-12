import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
import shutil
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from functools import partial
import threading

class ImageCaptioningTab:
    def __init__(self, tab):
        self.tab = tab
        self.images = []
        self.captions = {}
        self.setup_ui()
        self.setup_florence()

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.tab)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_image_loading_section()
        self.create_auto_captioning_section()
        self.create_caption_modification_section()
        self.create_gallery_section()

        self.feedback_label = ttk.Label(self.main_frame, text="", anchor="w", justify="left")
        self.feedback_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        # Add a progress bar for image conversion
        self.conversion_progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=200, mode="determinate")
        self.conversion_progress.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Add a status label for conversion
        self.conversion_status = ttk.Label(self.main_frame, text="", anchor="w")
        self.conversion_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Add a button for image conversion
        self.convert_button = ttk.Button(self.main_frame, text="Convert Images to PNG", command=self.convert_images)
        self.convert_button.pack(side=tk.BOTTOM, pady=(5, 0))
        self.convert_button.config(state=tk.DISABLED)  # Initially disabled

    def create_image_loading_section(self):
        load_frame = ttk.LabelFrame(self.main_frame, text="Image Loading")
        load_frame.pack(fill=tk.X, pady=(0, 10))

        folder_symbol = "\U0001F4C1"  # Unicode for folder emoji
        load_button = ttk.Button(load_frame, text=f"{folder_symbol} Load Images", command=self.load_images)
        load_button.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(load_frame, text="Add Missing Caption Files", command=self.add_missing_captions).pack(side=tk.LEFT, padx=5, pady=5)

    def create_auto_captioning_section(self):
        auto_caption_frame = ttk.LabelFrame(self.main_frame, text="Auto Captioning")
        auto_caption_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(auto_caption_frame, text="Florence Model:").pack(side=tk.LEFT, padx=5, pady=5)
        self.model_selector = ttk.Combobox(auto_caption_frame, values=["Base", "Large"], state="readonly", width=10)
        self.model_selector.set("Large")
        self.model_selector.pack(side=tk.LEFT, padx=5, pady=5)
        self.model_selector.bind("<<ComboboxSelected>>", self.on_model_selection_changed)

        ttk.Label(auto_caption_frame, text="Detail Level:").pack(side=tk.LEFT, padx=5, pady=5)
        self.detail_selector = ttk.Combobox(auto_caption_frame, values=["Short", "Detailed", "More Detailed"], state="readonly", width=15)
        self.detail_selector.set("Short")
        self.detail_selector.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(auto_caption_frame, text="Generate All Captions", command=self.auto_caption_images).pack(side=tk.LEFT, padx=5, pady=5)

    def create_caption_modification_section(self):
        modify_frame = ttk.LabelFrame(self.main_frame, text="Caption Modification")
        modify_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(modify_frame, text="Trigger Word:").pack(side=tk.LEFT, padx=5, pady=5)
        self.trigger_entry = ttk.Entry(modify_frame, width=20)
        self.trigger_entry.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(modify_frame, text="Inject Trigger Word", command=self.inject_trigger).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(modify_frame, text="Clear All Captions", command=self.clear_all_captions).pack(side=tk.LEFT, padx=5, pady=5)

    def create_gallery_section(self):
        ttk.Label(self.main_frame, text="Image Gallery", font=("TkDefaultFont", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))

        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.gallery_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.gallery_frame, anchor="nw")

        self.bind_mouse_scroll()

    def bind_mouse_scroll(self):
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

    def load_images(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path = folder_path  # Store the folder path
            all_images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'))]
            
            self.images = all_images
            self.captions = {img: self.load_caption(img) for img in self.images}
            self.display_gallery()

            # Enable or disable convert button based on presence of non-PNG images
            non_png_images = [img for img in all_images if not img.lower().endswith('.png')]
            self.convert_button.config(state=tk.NORMAL if non_png_images else tk.DISABLED)

    def convert_images(self):
        if not hasattr(self, 'folder_path'):
            messagebox.showerror("Error", "Please load images first.")
            return

        non_png_images = [img for img in self.images if not img.lower().endswith('.png')]
        if not non_png_images:
            messagebox.showinfo("Info", "All images are already in PNG format.")
            return

        result = messagebox.askyesno("Convert Images", "Convert non-PNG images to PNG? Original files will be backed up.")
        if result:
            self.convert_to_png(non_png_images)

    def convert_to_png(self, image_paths):
        total = len(image_paths)
        
        self.conversion_progress["maximum"] = total
        self.conversion_progress["value"] = 0
        
        # Create backup folder
        backup_folder = os.path.join(self.folder_path, "backup-img")
        os.makedirs(backup_folder, exist_ok=True)
        
        for i, img_path in enumerate(image_paths, 1):
            try:
                with Image.open(img_path) as img:
                    # Backup original file
                    backup_path = os.path.join(backup_folder, os.path.basename(img_path))
                    shutil.copy2(img_path, backup_path)
                    
                    # Save as PNG
                    png_path = os.path.splitext(img_path)[0] + '.png'
                    img.save(png_path, 'PNG')
                
                # Remove original file after successful conversion and backup
                os.remove(img_path)
                
                # Update the image path in self.images and self.captions
                self.images[self.images.index(img_path)] = png_path
                self.captions[png_path] = self.captions.pop(img_path)
                
                self.conversion_status.config(text=f"Converted: {os.path.basename(img_path)} to PNG")
            except Exception as e:
                self.conversion_status.config(text=f"Error converting {os.path.basename(img_path)}: {str(e)}")
            
            self.conversion_progress["value"] = i
            self.tab.update_idletasks()
        
        self.conversion_status.config(text="Image conversion completed. Originals backed up in 'backup-img' folder.")
        self.display_gallery()  # Refresh the gallery to show converted images
        self.convert_button.config(state=tk.DISABLED)  # Disable button after conversion

    def load_caption(self, img_path):
        caption_path = img_path.rsplit('.', 1)[0] + '.txt'
        if os.path.exists(caption_path):
            with open(caption_path, 'r') as f:
                return f.read()
        return ""

    def add_missing_captions(self):
        missing_count = 0
        for img_path in self.images:
            caption_path = img_path.rsplit('.', 1)[0] + '.txt'
            if not os.path.exists(caption_path):
                with open(caption_path, 'w') as f:
                    f.write("")
                self.captions[img_path] = ""
                missing_count += 1

        if missing_count > 0:
            messagebox.showinfo("Captions Added", f"{missing_count} missing caption file{'s' if missing_count > 1 else ''} {'have' if missing_count > 1 else 'has'} been added.")
        else:
            messagebox.showinfo("No Missing Captions", "All images already have corresponding caption files.")

        self.display_gallery()

    def display_gallery(self):
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        for img_path in self.images:
            self.display_image_with_caption(img_path)

        self.gallery_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def display_image_with_caption(self, img_path):
        frame = ttk.Frame(self.gallery_frame)
        frame.pack(side="top", fill="x", padx=5, pady=5)
        frame.img_path = img_path  # Store img_path as an attribute of the frame

        try:
            img = Image.open(img_path)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.pack(side="left", padx=5, pady=5)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            ttk.Label(frame, text="Image not available").pack(side="left", padx=5, pady=5)

        caption_frame = ttk.Frame(frame)
        caption_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        caption_text = tk.Text(caption_frame, height=5, wrap="word")
        caption_text.insert("1.0", self.captions[img_path])
        caption_text.pack(side="top", fill="both", expand=True)
        frame.caption_text = caption_text  # Store caption_text as an attribute of the frame

        button_frame = ttk.Frame(frame)
        button_frame.pack(side="top", fill="x")

        ttk.Button(button_frame, text="Save", command=partial(self.save_caption_and_update, img_path, caption_text)).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Clear", command=partial(self.clear_caption, img_path, caption_text)).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Auto Caption", command=partial(self.auto_caption_single_image, img_path)).pack(side="left", padx=2)

    def save_caption_and_update(self, img_path, caption_text):
        new_caption = caption_text.get("1.0", "end-1c")
        self.save_caption(img_path, new_caption)
        self.captions[img_path] = new_caption
        messagebox.showinfo("Caption Saved", f"Caption for {os.path.basename(img_path)} has been saved.")

    def clear_caption(self, img_path, caption_text):
        caption_text.delete("1.0", tk.END)
        self.save_caption(img_path, "")
        self.captions[img_path] = ""
        messagebox.showinfo("Caption Cleared", f"Caption for {os.path.basename(img_path)} has been cleared.")

    def save_caption(self, img_path, caption):
        caption_path = img_path.rsplit('.', 1)[0] + '.txt'
        with open(caption_path, 'w') as f:
            f.write(caption)

    def setup_florence(self):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model_name = f"microsoft/Florence-2-{self.model_selector.get()}"
        self.florence_processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.florence_model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch_dtype, trust_remote_code=True).to(device)

    def on_model_selection_changed(self, event=None):
        # Reload the model when the selection changes
        self.setup_florence()

    def auto_caption_images(self):
        threading.Thread(target=self._auto_caption_images_thread, daemon=True).start()

    def _auto_caption_images_thread(self):
        for img_path in self.images:
            self.auto_caption_single_image(img_path)
        self.tab.after(0, lambda: messagebox.showinfo("Auto Captioning", "All images have been captioned."))
        self.tab.after(0, self.display_gallery)

    def auto_caption_single_image(self, img_path):
        self.feedback_label.config(text=f"Generating caption for {os.path.basename(img_path)}...")
        self.tab.update_idletasks()

        detail_level = self.detail_selector.get()
        if detail_level == "Short":
            prompt = "<CAPTION>"
        elif detail_level == "Detailed":
            prompt = "<DETAILED_CAPTION>"
        else:  # detail_level == "More Detailed"
            prompt = "<MORE_DETAILED_CAPTION>"

        device = 'cuda' if torch.cuda.is_available() else 'cpu'

        image = Image.open(img_path).convert("RGB")
        inputs = self.florence_processor(text=prompt, images=image, return_tensors="pt", do_rescale=False).to(self.florence_model.device)
        inputs["pixel_values"] = inputs["pixel_values"].to(device, torch.float32)

        with torch.no_grad():
            generated_ids = self.florence_model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                num_beams=3,
                do_sample=False
            )
            generated_text = self.florence_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        caption = generated_text.replace('</s>', '').replace('<s>', '').replace('<pad>', '').strip()
        self.captions[img_path] = caption
        self.save_caption(img_path, caption)

        self.feedback_label.config(text=f"Caption generated for {os.path.basename(img_path)}")
        self.tab.update_idletasks()

        self.update_caption_in_ui(img_path, caption)

    def update_caption_in_ui(self, img_path, new_caption):
        for widget in self.gallery_frame.winfo_children():
            if hasattr(widget, 'img_path') and widget.img_path == img_path:
                caption_text = widget.caption_text
                caption_text.delete("1.0", tk.END)
                caption_text.insert(tk.END, new_caption)
                break

    def inject_trigger(self):
        trigger_word = self.trigger_entry.get().strip()
        if not trigger_word:
            messagebox.showwarning("Trigger Word Missing", "Please enter a trigger word.")
            return

        for img_path, caption in self.captions.items():
            if not caption.startswith(trigger_word):
                self.captions[img_path] = f"{trigger_word} {caption}"
                self.save_caption(img_path, self.captions[img_path])

        messagebox.showinfo("Trigger Injection", "Trigger word has been injected into all captions.")
        self.display_gallery()

    def clear_all_captions(self):
        for img_path in self.captions:
            self.captions[img_path] = ""
            self.save_caption(img_path, "")
        messagebox.showinfo("Clear Captions", "All captions have been cleared.")
        self.display_gallery()

def create_captioning_tab(tab):
    return ImageCaptioningTab(tab)