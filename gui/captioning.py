import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
import shutil
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from functools import partial
import threading
import queue

class ImageCaptioningTab:
    def __init__(self, tab):
        self.tab = tab
        self.images = []
        self.captions = {}
        self.image_queue = queue.Queue()
        self.setup_ui()
        self.setup_florence()

    def setup_florence(self):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model_name = "microsoft/Florence-2-base"
        self.florence_processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.florence_model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch_dtype, trust_remote_code=True).to(device)

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.tab)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_image_loading_section()
        self.create_auto_captioning_section()
        self.create_caption_modification_section()
        self.create_gallery_section()

        self.feedback_label = ttk.Label(self.main_frame, text="", anchor="w", justify="left")
        self.feedback_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def create_image_loading_section(self):
        load_frame = ttk.LabelFrame(self.main_frame, text="Image Loading")
        load_frame.pack(fill=tk.X, pady=(0, 10))

        folder_symbol = "\U0001F4C1"  # Unicode for folder emoji
        load_button = ttk.Button(load_frame, text=f"{folder_symbol} Load Images", command=self.load_images_thread)
        load_button.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(load_frame, text="Add Missing Caption Files", command=self.add_missing_captions).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(load_frame, text="Convert to PNG & Backup", command=self.convert_to_png_and_backup).pack(side=tk.LEFT, padx=5, pady=5)

    def create_auto_captioning_section(self):
        auto_caption_frame = ttk.LabelFrame(self.main_frame, text="Auto Captioning")
        auto_caption_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(auto_caption_frame, text="Florence Model:").pack(side=tk.LEFT, padx=5, pady=5)
        self.model_selector = ttk.Combobox(auto_caption_frame, values=["base", "large"], state="readonly", width=10)
        self.model_selector.set("base")
        self.model_selector.pack(side=tk.LEFT, padx=5, pady=5)

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

    def load_images_thread(self):
        threading.Thread(target=self.load_images, daemon=True).start()

    def load_images(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            for img in images:
                self.image_queue.put(img)
            self.tab.after(0, self.process_image_queue)

    def process_image_queue(self):
        try:
            while not self.image_queue.empty():
                img_path = self.image_queue.get_nowait()
                self.images.append(img_path)
                self.captions[img_path] = self.load_caption(img_path)
            self.display_gallery()
        except queue.Empty:
            pass

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

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        prompt = "<DETAILED_CAPTION>"
        
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

        # Update the displayed caption in the UI
        self.update_caption_in_ui(img_path, caption)

    def update_caption_in_ui(self, img_path, new_caption):
        for widget in self.gallery_frame.winfo_children():
            if hasattr(widget, 'img_path') and widget.img_path == img_path:
                caption_text = widget.caption_text
                caption_text.delete("1.0", tk.END)
                caption_text.insert(tk.END, new_caption)
                break

    def inject_trigger(self):
        trigger_word = self.trigger_entry.get()
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

    def save_caption(self, img_path, caption):
        caption_path = img_path.rsplit('.', 1)[0] + '.txt'
        with open(caption_path, 'w') as f:
            f.write(caption)

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

        scrollbar = ttk.Scrollbar(caption_frame, orient="vertical", command=caption_text.yview)
        scrollbar.pack(side="right", fill="y")
        caption_text.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(caption_frame)
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

    def convert_to_png_and_backup(self):
        backup_folder = "img_backup"
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        for img_path in self.images:
            # Backup original file
            shutil.copy(img_path, backup_folder)

            # Convert to PNG if not already PNG
            if not img_path.lower().endswith(".png"):
                img = Image.open(img_path)
                new_path = img_path.rsplit('.', 1)[0] + '.png'
                img.save(new_path, "PNG")
                self.images.append(new_path)
                self.captions[new_path] = self.captions[img_path]

        messagebox.showinfo("Conversion Complete", "All images have been backed up and converted to PNG where applicable.")
        self.display_gallery()

def create_captioning_tab(tab):
    ImageCaptioningTab(tab)