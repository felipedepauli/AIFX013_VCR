import os
import json
import statistics
from pathlib import Path
from collections import defaultdict
from PIL import Image

class VehicleStatsCalculator:
    """Calculates statistics for vehicle bounding boxes across JSON files."""
    
    def __init__(self, target_classes=("car", "motorcycle", "truck", "bus")):
        self.target_classes = set(target_classes)
        self.reset_stats()
        
    def reset_stats(self):
        # We store lists of float values to accurately calculate mean and variance.
        # stats structure:
        # { "general": {"cx": [], "cy": [], "area": [], "prop": []},
        #   "car": {"cx": [], ...}, ...
        # }
        self.stats = defaultdict(lambda: {"cx": [], "cy": [], "area": [], "prop": []})
        self.subdirectory_counts = defaultdict(int)

    def _get_image_size(self, img_path):
        try:
            with Image.open(img_path) as img:
                return img.size
        except Exception:
            return None, None

    def process_directory(self, base_directory):
        self.reset_stats()
        base_path = Path(base_directory)
        
        # We will iterate visually through all json files unconditionally
        for json_path in base_path.rglob('*.json'):
            # Ignore hidden files or registries
            if json_path.name.startswith('.'):
                continue
                
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            # Not a list of annotations? Skip
            if not isinstance(data, list):
                continue
                
            subdir = str(json_path.parent)
            
            # Find the matching image file to accurately calculate sizes
            # Trying standard extensions
            img_path = None
            for ext in ['.jpg', '.jpeg', '.png']:
                potential_img = json_path.with_suffix(ext)
                if potential_img.exists():
                    img_path = potential_img
                    break
                    
            if not img_path:
                continue
                
            img_width, img_height = self._get_image_size(img_path)
            if not img_width or not img_height or img_width == 0 or img_height == 0:
                continue
                
            for obj in data:
                label = obj.get("label", "").lower()
                rect = obj.get("rect")
                
                # We only calculate valid format bounds
                if label not in self.target_classes or not rect or len(rect) != 4:
                    continue
                    
                x, y, w, h = rect
                
                # normalized centroids
                cx = (x + w / 2) / img_width
                cy = (y + h / 2) / img_height
                
                # areas
                area = w * h
                prop = area / (img_width * img_height)
                
                # append 'general'
                self.stats["general"]["cx"].append(cx)
                self.stats["general"]["cy"].append(cy)
                self.stats["general"]["area"].append(area)
                self.stats["general"]["prop"].append(prop)
                
                # append 'class'
                self.stats[label]["cx"].append(cx)
                self.stats[label]["cy"].append(cy)
                self.stats[label]["area"].append(area)
                self.stats[label]["prop"].append(prop)
                
                self.subdirectory_counts[subdir] += 1
                

    def _calc_metrics(self, data_list):
        n = len(data_list)
        if n == 0:
            return 0.0, 0.0
        elif n == 1:
            return data_list[0], 0.0
        else:
            return statistics.mean(data_list), statistics.variance(data_list)

    def print_pretty_report(self):
        print("\n" + "="*60)
        print("          VEHICLE STATISTICS SUMMARY")
        print("="*60)
        
        ordered_keys = ["general"] + sorted([k for k in self.stats.keys() if k != "general"])
        
        for k in ordered_keys:
            metrics = self.stats[k]
            count = len(metrics["cx"])
            if count == 0:
                continue
                
            cx_mean, cx_var = self._calc_metrics(metrics["cx"])
            cy_mean, cy_var = self._calc_metrics(metrics["cy"])
            area_mean, area_var = self._calc_metrics(metrics["area"])
            prop_mean, prop_var = self._calc_metrics(metrics["prop"])
            
            print(f"\n--- CLASS: {k.upper()} (N = {count}) ---")
            print(f"  Centroid X (Norm):  Mean = {cx_mean:.4f}, Var = {cx_var:.6f}")
            print(f"  Centroid Y (Norm):  Mean = {cy_mean:.4f}, Var = {cy_var:.6f}")
            print(f"  Absolute Area:      Mean = {area_mean:.1f}, Var = {area_var:.1f}")
            print(f"  Proportional Area:  Mean = {prop_mean:.4f}, Var = {prop_var:.6f}")
            
        print("\n" + "="*60)
        print("          SAMPLES PER SUBDIRECTORY")
        print("="*60)
        
        if not self.subdirectory_counts:
            print("No matching objects found in any directory.")
        else:
            for subdir, count in sorted(self.subdirectory_counts.items()):
                print(f"  {subdir}: {count} vehicles")
        
        print("="*60 + "\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate vehicle object statistics.")
    parser.add_argument("directory", help="The root directory to scan for json and image files.")
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.directory} ...")
    calculator = VehicleStatsCalculator()
    calculator.process_directory(args.directory)
    calculator.print_pretty_report()
