#!/usr/bin/env python3
"""Re-annotation tool for fixing vehicle color labels.

Interactive GUI to review and correct color labels in the manifest.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import shutil
from datetime import datetime


# Define valid colors and vehicle types (contamination)
VALID_COLORS = [
    "black", "blue", "brown", "gray", "green", 
    "red", "silver", "white", "yellow", "unknown"
]

VEHICLE_TYPES = [
    "bus", "car", "motorcycle", "pickup", "suv", "tow", "truck"
]


class ColorReAnnotator:
    """GUI tool for re-annotating vehicle colors."""
    
    def __init__(self, manifest_path: str):
        """Initialize the re-annotation tool.
        
        Args:
            manifest_path: Path to manifest.jsonl file
        """
        self.manifest_path = Path(manifest_path)
        self.backup_path = None
        
        # Load manifest
        self.records = []
        with open(self.manifest_path, 'r') as f:
            for line in f:
                self.records.append(json.loads(line))
        
        # Track problematic samples (labels that are vehicle types)
        self.problematic_indices = [
            i for i, r in enumerate(self.records) 
            if r['label'] in VEHICLE_TYPES
        ]
        
        # Current state
        self.current_index = 0
        self.show_only_problematic = False
        self.modified_records = set()
        self.history = []  # Undo history
        
        # Statistics
        self.total_records = len(self.records)
        self.total_problematic = len(self.problematic_indices)
        self.fixed_count = 0
        
        # Setup GUI
        self.root = tk.Tk()
        self.root.title("Vehicle Color Re-Annotation Tool")
        self.root.geometry("1400x900")
        
        self.setup_ui()
        self.load_current_image()
        
    def get_current_indices(self):
        """Get list of indices to iterate based on filter."""
        if self.show_only_problematic:
            return self.problematic_indices
        return list(range(self.total_records))
    
    def get_display_index(self):
        """Get display index (1-based) and total."""
        indices = self.get_current_indices()
        if not indices:
            return 0, 0
        # Find position of current_index in filtered list
        try:
            pos = indices.index(self.current_index)
            return pos + 1, len(indices)
        except ValueError:
            return 0, len(indices)
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left panel (image)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Image display
        self.image_label = ttk.Label(left_frame, text="Loading image...")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Right panel (controls)
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Statistics section
        stats_frame = ttk.LabelFrame(right_frame, text="Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="", justify=tk.LEFT)
        self.stats_label.pack(anchor=tk.W)
        self.update_stats()
        
        # Current image info
        info_frame = ttk.LabelFrame(right_frame, text="Current Image", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="", justify=tk.LEFT, wraplength=300)
        self.info_label.pack(anchor=tk.W)
        
        # Current label (highlighted if problematic)
        label_frame = ttk.LabelFrame(right_frame, text="Current Label", padding="10")
        label_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_label = ttk.Label(label_frame, text="", font=('Arial', 16, 'bold'))
        self.current_label.pack(anchor=tk.W)
        
        self.label_status = ttk.Label(label_frame, text="", foreground="red")
        self.label_status.pack(anchor=tk.W)
        
        # New label selector
        selector_frame = ttk.LabelFrame(right_frame, text="Change Color To:", padding="10")
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(selector_frame, text="Select new color:").pack(anchor=tk.W)
        
        self.color_var = tk.StringVar()
        self.color_dropdown = ttk.Combobox(
            selector_frame, 
            textvariable=self.color_var,
            values=VALID_COLORS,
            state="readonly",
            width=20
        )
        self.color_dropdown.pack(fill=tk.X, pady=(5, 10))
        
        # Buttons
        btn_frame = ttk.Frame(selector_frame)
        btn_frame.pack(fill=tk.X)
        
        self.save_btn = ttk.Button(btn_frame, text="💾 Save Change", command=self.save_change)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.undo_btn = ttk.Button(btn_frame, text="↶ Undo", command=self.undo_last, state=tk.DISABLED)
        self.undo_btn.pack(side=tk.LEFT)
        
        # Filter controls
        filter_frame = ttk.LabelFrame(right_frame, text="Filter", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.filter_var = tk.BooleanVar(value=False)
        filter_check = ttk.Checkbutton(
            filter_frame,
            text="Show only problematic images (vehicle types)",
            variable=self.filter_var,
            command=self.toggle_filter
        )
        filter_check.pack(anchor=tk.W)
        
        # Navigation
        nav_frame = ttk.LabelFrame(right_frame, text="Navigation", padding="10")
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.nav_label = ttk.Label(nav_frame, text="")
        self.nav_label.pack()
        
        btn_nav_frame = ttk.Frame(nav_frame)
        btn_nav_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_nav_frame, text="⏮ First", command=self.first_image, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_nav_frame, text="◀ Prev", command=self.prev_image, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_nav_frame, text="Next ▶", command=self.next_image, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_nav_frame, text="Last ⏭", command=self.last_image, width=10).pack(side=tk.LEFT, padx=2)
        
        # Actions
        action_frame = ttk.LabelFrame(right_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="💾 Save All Changes to Manifest", 
                  command=self.save_manifest, style="Accent.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🔄 Reload Manifest", 
                  command=self.reload_manifest).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="❌ Exit", 
                  command=self.exit_app).pack(fill=tk.X, pady=2)
        
        # Keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Home>', lambda e: self.first_image())
        self.root.bind('<End>', lambda e: self.last_image())
        self.root.bind('<Control-s>', lambda e: self.save_change())
        self.root.bind('<Control-z>', lambda e: self.undo_last())
        
    def update_stats(self):
        """Update statistics display."""
        total_to_show = self.total_problematic if self.show_only_problematic else self.total_records
        
        stats_text = (
            f"Total images: {self.total_records:,}\n"
            f"Problematic: {self.total_problematic:,} ({100*self.total_problematic/self.total_records:.1f}%)\n"
            f"Fixed: {self.fixed_count}\n"
            f"Modified (unsaved): {len(self.modified_records)}"
        )
        self.stats_label.config(text=stats_text)
        
        # Update navigation label
        pos, total = self.get_display_index()
        self.nav_label.config(text=f"Image {pos} of {total}")
    
    def load_current_image(self):
        """Load and display current image."""
        if not self.records:
            return
        
        record = self.records[self.current_index]
        
        # Load image
        crop_path = Path(record.get('crop_path', ''))
        if not crop_path.exists():
            # Try image_path with bbox
            img_path = Path(record.get('image_path', ''))
            if img_path.exists():
                img = Image.open(img_path).convert('RGB')
                bbox = record.get('bbox_xyxy', [0, 0, img.width, img.height])
                img = img.crop(bbox)
            else:
                img = Image.new('RGB', (400, 400), color='gray')
        else:
            img = Image.open(crop_path).convert('RGB')
        
        # Resize for display (max 800x800)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)
        
        # Update info
        info_text = (
            f"ID: {record['id']}\n"
            f"Path: {crop_path.name if crop_path.exists() else img_path.name}\n"
            f"Split: {record.get('split', 'N/A')}\n"
            f"Original Index: {self.current_index + 1}/{self.total_records}"
        )
        self.info_label.config(text=info_text)
        
        # Update current label
        current_label = record['label']
        self.current_label.config(text=current_label)
        
        # Highlight if problematic
        if current_label in VEHICLE_TYPES:
            self.label_status.config(
                text="⚠️ VEHICLE TYPE (should be COLOR!)",
                foreground="red"
            )
            self.current_label.config(foreground="red")
        else:
            self.label_status.config(text="✓ Valid color", foreground="green")
            self.current_label.config(foreground="green")
        
        # Set dropdown to current value
        self.color_var.set(current_label if current_label in VALID_COLORS else VALID_COLORS[0])
        
        self.update_stats()
    
    def save_change(self):
        """Save the color change for current image."""
        new_color = self.color_var.get()
        if not new_color:
            messagebox.showwarning("No Color", "Please select a color!")
            return
        
        record = self.records[self.current_index]
        old_label = record['label']
        
        if new_color == old_label:
            messagebox.showinfo("No Change", "Selected color is the same as current!")
            return
        
        # Save to history for undo
        self.history.append({
            'index': self.current_index,
            'old_label': old_label,
            'old_label_idx': record['label_idx'],
            'new_label': new_color
        })
        
        # Update record
        record['label'] = new_color
        record['label_idx'] = VALID_COLORS.index(new_color) if new_color in VALID_COLORS else 0
        
        # Track modification
        self.modified_records.add(self.current_index)
        
        # Update fixed count if it was problematic
        if old_label in VEHICLE_TYPES and new_color in VALID_COLORS:
            self.fixed_count += 1
            # Remove from problematic list
            if self.current_index in self.problematic_indices:
                self.problematic_indices.remove(self.current_index)
        
        # Enable undo
        self.undo_btn.config(state=tk.NORMAL)
        
        messagebox.showinfo("Saved", f"Changed: {old_label} → {new_color}")
        
        # Move to next image
        self.next_image()
    
    def undo_last(self):
        """Undo the last change."""
        if not self.history:
            return
        
        last_change = self.history.pop()
        idx = last_change['index']
        
        # Restore old values
        self.records[idx]['label'] = last_change['old_label']
        self.records[idx]['label_idx'] = last_change['old_label_idx']
        
        # Update fixed count
        if last_change['old_label'] in VEHICLE_TYPES:
            self.fixed_count -= 1
            if idx not in self.problematic_indices:
                self.problematic_indices.append(idx)
                self.problematic_indices.sort()
        
        # Disable undo if no more history
        if not self.history:
            self.undo_btn.config(state=tk.DISABLED)
        
        # Navigate to that image
        self.current_index = idx
        self.load_current_image()
        
        messagebox.showinfo("Undone", f"Reverted change at index {idx + 1}")
    
    def toggle_filter(self):
        """Toggle between showing all images or only problematic ones."""
        self.show_only_problematic = self.filter_var.get()
        
        # Reset to first in filtered list
        if self.show_only_problematic:
            if self.problematic_indices:
                self.current_index = self.problematic_indices[0]
            else:
                messagebox.showinfo("No Problems", "No problematic images found!")
                self.filter_var.set(False)
                self.show_only_problematic = False
        else:
            self.current_index = 0
        
        self.load_current_image()
    
    def first_image(self):
        """Go to first image in current filter."""
        indices = self.get_current_indices()
        if indices:
            self.current_index = indices[0]
            self.load_current_image()
    
    def last_image(self):
        """Go to last image in current filter."""
        indices = self.get_current_indices()
        if indices:
            self.current_index = indices[-1]
            self.load_current_image()
    
    def prev_image(self):
        """Go to previous image."""
        indices = self.get_current_indices()
        if not indices:
            return
        
        try:
            pos = indices.index(self.current_index)
            if pos > 0:
                self.current_index = indices[pos - 1]
                self.load_current_image()
        except ValueError:
            self.current_index = indices[0]
            self.load_current_image()
    
    def next_image(self):
        """Go to next image."""
        indices = self.get_current_indices()
        if not indices:
            return
        
        try:
            pos = indices.index(self.current_index)
            if pos < len(indices) - 1:
                self.current_index = indices[pos + 1]
                self.load_current_image()
        except ValueError:
            self.current_index = indices[0]
            self.load_current_image()
    
    def save_manifest(self):
        """Save all changes back to manifest file."""
        if not self.modified_records:
            messagebox.showinfo("No Changes", "No changes to save!")
            return
        
        # Confirm
        response = messagebox.askyesno(
            "Save Changes",
            f"Save {len(self.modified_records)} changes to manifest?\n\n"
            f"A backup will be created."
        )
        
        if not response:
            return
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.manifest_path.parent / f"{self.manifest_path.stem}_backup_{timestamp}.jsonl"
        shutil.copy(self.manifest_path, self.backup_path)
        
        # Write updated manifest
        with open(self.manifest_path, 'w') as f:
            for record in self.records:
                f.write(json.dumps(record) + '\n')
        
        # Update class_to_idx.json
        self.update_class_mapping()
        
        messagebox.showinfo(
            "Saved!",
            f"Changes saved to {self.manifest_path}\n\n"
            f"Backup: {self.backup_path}\n"
            f"Modified: {len(self.modified_records)} records\n"
            f"Fixed problematic: {self.fixed_count}"
        )
        
        # Clear modification tracking
        self.modified_records.clear()
        self.history.clear()
        self.undo_btn.config(state=tk.DISABLED)
        self.update_stats()
    
    def update_class_mapping(self):
        """Update class_to_idx.json with only valid colors."""
        class_mapping_path = Path("data/processed/class_to_idx.json")
        
        if class_mapping_path.exists():
            # Create new mapping with only valid colors
            new_mapping = {color: idx for idx, color in enumerate(sorted(VALID_COLORS))}
            
            with open(class_mapping_path, 'w') as f:
                json.dump(new_mapping, f, indent=2)
            
            print(f"Updated {class_mapping_path} with {len(new_mapping)} color classes")
    
    def reload_manifest(self):
        """Reload manifest from disk (discard unsaved changes)."""
        if self.modified_records:
            response = messagebox.askyesno(
                "Discard Changes?",
                f"You have {len(self.modified_records)} unsaved changes.\n\n"
                "Reload will discard them. Continue?"
            )
            if not response:
                return
        
        # Reload
        self.records = []
        with open(self.manifest_path, 'r') as f:
            for line in f:
                self.records.append(json.loads(line))
        
        # Reset state
        self.problematic_indices = [
            i for i, r in enumerate(self.records) 
            if r['label'] in VEHICLE_TYPES
        ]
        self.modified_records.clear()
        self.history.clear()
        self.fixed_count = 0
        self.current_index = 0
        self.undo_btn.config(state=tk.DISABLED)
        
        self.load_current_image()
        messagebox.showinfo("Reloaded", "Manifest reloaded from disk.")
    
    def exit_app(self):
        """Exit the application."""
        if self.modified_records:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"You have {len(self.modified_records)} unsaved changes.\n\n"
                "Save before exiting?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes, save
                self.save_manifest()
        
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    manifest_path = "data/manifests/manifest_ready.jsonl"
    
    if not Path(manifest_path).exists():
        print(f"Error: Manifest not found at {manifest_path}")
        return 1
    
    print(f"Loading manifest: {manifest_path}")
    print("\n🎨 Vehicle Color Re-Annotation Tool")
    print("=" * 50)
    print("\nKeyboard Shortcuts:")
    print("  ← / → : Previous / Next image")
    print("  Home / End : First / Last image")
    print("  Ctrl+S : Save current change")
    print("  Ctrl+Z : Undo last change")
    print("\nStarting GUI...")
    
    app = ColorReAnnotator(manifest_path)
    app.run()
    
    return 0


if __name__ == "__main__":
    exit(main())
