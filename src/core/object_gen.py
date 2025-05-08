"""
Object Generation Module

This module provides functions to determine if an object can be placed at given coordinates
based on a seed. It uses a custom simplex noise implementation to create natural-looking 
distributions of objects while maintaining deterministic results.
"""

# Use the correct module structure.
try:
    from render.object_manager import Object3D
except ImportError:
    # Fallback for when run directly.
    try:
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from render.object_manager import Object3D
    except ImportError:
        # Mock Object3D class for when running as a standalone script
        class Object3D:
            def __init__(self, model_path):
                self.model_path = model_path
                
            def translate(self, x, y, z):
                self.position = (x, y, z)

try:
    from core.enums import Region
except ImportError:
    # Fallback for when run directly.
    try:
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from core.enums import Region
    except ImportError:
        # Final fallback - create a simple enum.
        from enum import Enum
        class Region(Enum):
            STEPPE = 0
            FOREST = 1
            HILLS = 2
            MOUNTAINS = 3
            SNOW_PLAINS = 4

import math
import random
import os

class SimplexNoise:
    """
    Custom implementation of simplex noise algorithm for educational purposes.
    This provides smooth, continuous noise values that can be used for natural
    object distribution in the terrain.
    """
    def __init__(self, seed):
        # Store the seed as an attribute so it can be checked later.
        self.seed = seed

        # Initialize with seed for deterministic results.
        random.seed(seed)

        # Generate permutation table.
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm += self.perm  # Double for easier index wrapping.

        # Gradient vectors for 3D simplex noise.
        self.grad3 = [
            (1,1,0), (-1,1,0), (1,-1,0), (-1,-1,0),
            (1,0,1), (-1,0,1), (1,0,-1), (-1,0,-1),
            (0,1,1), (0,-1,1), (0,1,-1), (0,-1,-1)
        ]

    def dot(self, g, x, y, z):
        """Calculate dot product between gradient and position vector."""
        return g[0]*x + g[1]*y + g[2]*z

    def fade(self, t):
        """Smoothing function for interpolation."""
        # 6t^5 - 15t^4 + 10t^3
        return t * t * t * (t * (t * 6 - 15) + 10)

    def noise3d(self, x, y, z):
        """Generate 3D simplex noise at coordinates (x,y,z)."""
        # Find unit cube that contains point.
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255

        # Find relative position in cube.
        x -= math.floor(x)
        y -= math.floor(y)
        z -= math.floor(z)

        # Compute fade curves.
        u = self.fade(x)
        v = self.fade(y)
        w = self.fade(z)

        # Hash coordinates of cube corners.
        A = self.perm[X] + Y
        AA = self.perm[A] + Z
        AB = self.perm[A + 1] + Z
        B = self.perm[X + 1] + Y
        BA = self.perm[B] + Z
        BB = self.perm[B + 1] + Z

        # Select gradient vectors.
        g1 = self.grad3[self.perm[AA] % 12]
        g2 = self.grad3[self.perm[BA] % 12]
        g3 = self.grad3[self.perm[AB] % 12]
        g4 = self.grad3[self.perm[BB] % 12]
        g5 = self.grad3[self.perm[AA + 1] % 12]
        g6 = self.grad3[self.perm[BA + 1] % 12]
        g7 = self.grad3[self.perm[AB + 1] % 12]
        g8 = self.grad3[self.perm[BB + 1] % 12]

        # Calculate noise contributions from each corner.
        n1 = self.dot(g1, x, y, z)
        n2 = self.dot(g2, x-1, y, z)
        n3 = self.dot(g3, x, y-1, z)
        n4 = self.dot(g4, x-1, y-1, z)
        n5 = self.dot(g5, x, y, z-1)
        n6 = self.dot(g6, x-1, y, z-1)
        n7 = self.dot(g7, x, y-1, z-1)
        n8 = self.dot(g8, x-1, y-1, z-1)

        # Interpolate noise contributions.
        x1 = u * (n2 - n1) + n1
        x2 = u * (n4 - n3) + n3
        y1 = v * (x2 - x1) + x1

        x1 = u * (n6 - n5) + n5
        x2 = u * (n8 - n7) + n7
        y2 = v * (x2 - x1) + x1

        # Return result in range [-1, 1].
        return w * (y2 - y1) + y1


# Global simplex noise instance, initialized when needed.
_simplex_noise = None

def get_simplex_noise(seed):
    """Get or create simplex noise instance with given seed."""
    global _simplex_noise
    if _simplex_noise is None or getattr(_simplex_noise, 'seed', None) != seed:
        _simplex_noise = SimplexNoise(seed)
    return _simplex_noise


def can_place(coordinates, seed, region=Region.STEPPE, intensity=0.03):
    """
    Determines whether an object can be placed at given coordinates based on a seed.
    Uses simplex noise to create natural clusters of objects.
    
    Args:
        coordinates (tuple): (x, y, z) coordinates to check
        seed (int): Random seed to ensure consistent generation
        region (Region): Region type that affects object density and types
        intensity (float): Base probability multiplier (0.0-1.0)
    
    Returns:
        bool: True if an object can be placed at the coordinates
    """
    x, y, z = coordinates

    # Get simplex noise instance.
    noise = get_simplex_noise(seed)

    # Scale coordinates to get more interesting patterns.
    scale = 0.05

    if region == Region.STEPPE:
        scale = 0.08

    # Generate multi-octave noise for natural clustering.
    base_noise = noise.noise3d(x * scale, y * scale, z * scale)
    detail_noise = noise.noise3d(x * scale * 2, y * scale * 2, z * scale * 2) * 0.5

    if region == Region.STEPPE:
        micro_detail = noise.noise3d(x * scale * 4, y * scale * 4, z * scale * 4) * 0.25
        combined_noise = (base_noise + detail_noise + micro_detail) * 0.4
    else:
        combined_noise = (base_noise + detail_noise) * 0.5

    # Convert from [-1, 1] to [0, 1] range.
    normalized_noise = (combined_noise + 1) * 0.5

    region_multipliers = {
        Region.STEPPE: 0.4,
        Region.FOREST: 1.9,
        Region.SNOW_PLAINS: 1.6
    }

    if region == Region.STEPPE:
        base_threshold = 0.65
    else:
        base_threshold = 0.85
    
    threshold = base_threshold - (intensity * region_multipliers.get(region, 1.0))

    if region == Region.STEPPE:
        threshold = max(0.4, min(threshold, 0.9))
    else:
        threshold = max(0.5, min(threshold, 0.95))

    return normalized_noise > threshold

def model_exists(path):
    """
    Check if a model file exists at the specified path.
    
    Args:
        path (str): Path to the model file
        
    Returns:
        bool: True if file exists, False otherwise
    """
    return os.path.isfile(path)

def init_objects(seed, n_rings, intensity, rg_data, y_data):
    '''
    initializes objects for each block in a 3^n_rings sized world
    returns them as a dictionary where for (x,z) => Object||None
    '''
    border = (1 + ((n_rings-1)*3))*2
    obj_data = {}
    
    # Default fallback model
    fallback_model = "spruce.obj"
    
    for x in range(-border, border+1, 1):
        for z in range(-border, border+1, 1):
            rg = rg_data[(x,z)]
            y = y_data[(x,z)]
            
            if intensity == 0:
                obj_data[(x,z)] = None
                continue
<<<<<<< Updated upstream
            if can_place((x,y,z),seed,rg,intensity):
                #TODO: implement all objects
                path="spruce.obj"
                match rg:
                    case Region.HILLS:
                        path="tree.obj"
                    case Region.STEPPE:
                        path="bush.obj"
                    case Region.FOREST:
                        path="spruce.obj"
                    case Region.MOUNTAINS:
                        path="rock.obj"
                    case Region.SNOW_PLAINS:
                        path="spruce.obj"
                obj_data[(x,z)]=Object3D(os.path.abspath(os.path.join(
=======
                
            if can_place((x,y,z), seed, rg, intensity):
                # Map regions to specific object models
                match rg:
                    case Region.STEPPE:
                        path = "bush.obj"
                    case Region.FOREST:
                        path = "spruce.obj"
                    case Region.HILLS:
                        path = "tree.obj"
                    case Region.MOUNTAINS:
                        path = "rock.obj"
                    case Region.SNOW_PLAINS:
                        path = "spruce.obj"
                    case _:
                        path = fallback_model
                
                # Full path to the model file
                full_path = os.path.abspath(os.path.join(
>>>>>>> Stashed changes
                    os.path.dirname(__file__),
                    "..","..", 
                    "static","assets", path
                ))
                
                # Check if the model exists, use fallback if not
                if not model_exists(full_path):
                    print(f"Warning: Model {path} not found, using fallback model")
                    path = fallback_model
                    full_path = os.path.abspath(os.path.join(
                        os.path.dirname(__file__),
                        "..","..", 
                        "static","assets", path
                    ))
                
                # Create the 3D object
                try:
                    obj_data[(x,z)] = Object3D(full_path)
                    obj_data[(x,z)].translate(x, y, z)
                except Exception as e:
                    print(f"Error loading model {path}: {e}")
                    obj_data[(x,z)] = None
            else:
                obj_data[(x,z)] = None
                
    return obj_data


def get_object_type(coordinates, seed, region=Region.STEPPE):
    """
    Determines what type of object to place at the given coordinates.
    Uses simplex noise for natural variations in object distribution.
    
    Args:
        coordinates (tuple): (x, y, z) coordinates
        seed (int): Random seed to ensure consistent generation
        region (Region): Region type that affects object types
        
    Returns:
        str: Object type identifier
    """
    x, y, z = coordinates

    noise = get_simplex_noise(seed)

    if region == Region.STEPPE:
        scale = 0.15
    else:
        scale = 0.1
        
    type_noise = noise.noise3d(x * scale, y * scale, z * scale)

    if region == Region.STEPPE:
        detail_noise = noise.noise3d(x * scale * 2.5, y * scale * 2.5, z * scale * 2.5) * 0.4
        pattern_noise = noise.noise3d(x * scale * 5, y * scale * 5, z * scale * 5) * 0.2
        combined_noise = type_noise + detail_noise + pattern_noise

        type_selector = (combined_noise + 1.5) * 0.4
    else:
        detail_noise = noise.noise3d(x * scale * 3, y * scale * 3, z * scale * 3) * 0.3
        combined_noise = type_noise + detail_noise
        type_selector = (combined_noise + 1.3) * 0.5

    type_selector = max(0, min(type_selector, 1.0))

    if region == Region.FOREST:
        if type_selector < 0.6:      
            return "tree_tall"
        elif type_selector < 0.8:   
            return "tree_pine"
        else:                        
            return "bush"

    elif region == Region.STEPPE:
        if type_selector < 0.7:
            variety = noise.noise3d(x * 0.3, y * 0.3, z * 0.3)
            if variety > 0.3:
                return "grass_tall"
            else:
                return "grass_short"
        elif type_selector < 0.9:
            variety = noise.noise3d(x * 0.25, y * 0.25, z * 0.25)
            if variety > 0:
                return "bush_small" 
            else:
                return "bush_flowering"
        else:                      
            return "rock"

    elif region == Region.SNOW_PLAINS:
        if type_selector < 0.5:     
            return "snow_rock"
        elif type_selector < 0.8:   
            return "pine_snow"
        else:                       
            return "ice_formation"

    return "rock"


def get_object_scale(coordinates, seed):
    """
    Determines the scale of an object based on coordinates and seed.
    Creates natural variations in object sizes.
    
    Args:
        coordinates (tuple): (x, y, z) coordinates
        seed (int): Random seed
        
    Returns:
        tuple: (x_scale, y_scale, z_scale) for the object
    """
    x, y, z = coordinates

    noise = get_simplex_noise(seed)

    scale_noise_x = noise.noise3d(x * 0.2, y * 0.2, z * 0.2)
    scale_noise_y = noise.noise3d(x * 0.2, y * 0.2, z * 0.2 + 100)
    scale_noise_z = noise.noise3d(x * 0.2, y * 0.2, z * 0.2 + 200)

    base_scale = 1.0
    variation = 0.3

    x_scale = base_scale + (scale_noise_x * variation)
    y_scale = base_scale + (scale_noise_y * variation)
    z_scale = base_scale + (scale_noise_z * variation)

    return (x_scale, y_scale, z_scale)


def get_object_rotation(coordinates, seed):
    """
    Determines the rotation of an object based on coordinates and seed.
    Creates natural variations in object orientations.
    
    Args:
        coordinates (tuple): (x, y, z) coordinates
        seed (int): Random seed
        
    Returns:
        float: Rotation angle in radians around the Y axis
    """
    x, y, z = coordinates

    noise = get_simplex_noise(seed)

    rotation_noise = noise.noise3d(x * 0.1, y * 0.1, z * 0.1)

    rotation = (rotation_noise + 1) * math.pi

    return rotation


def apply_cellular_automata(object_map, iterations=3, birth_threshold=3, survival_threshold=2):
    """
    Apply cellular automata rules to refine object placement.
    
    Args:
        object_map (numpy.ndarray): Binary object placement map
        iterations (int): Number of iterations to run
        birth_threshold (int): Minimum neighbors needed for a new object to appear
        survival_threshold (int): Minimum neighbors needed for an object to survive
        
    Returns:
        numpy.ndarray: Refined object placement map
    """
    import numpy as np
    
    height, width = object_map.shape
    result = object_map.copy()
    
    for _ in range(iterations):
        next_gen = result.copy()
        for i in range(1, height-1):
            for j in range(1, width-1):
                # Count live neighbors in 3x3 neighborhood
                neighbors = np.sum(result[i-1:i+2, j-1:j+2]) - result[i, j]
                
                # Apply rules
                if result[i, j] == 0 and neighbors >= birth_threshold:
                    # Birth: Empty cell with enough neighbors becomes alive
                    next_gen[i, j] = 1
                elif result[i, j] == 1 and neighbors < survival_threshold:
                    # Death: Living cell with too few neighbors dies
                    next_gen[i, j] = 0
                # Otherwise cell remains unchanged
        
        result = next_gen
    
    return result

if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.colors import ListedColormap
        import matplotlib.gridspec as gridspec
    except ImportError:
        print("Error: This visualization requires matplotlib and numpy.")
        print("Please install them with: pip install matplotlib numpy")
        exit(1)

    print("Visualizing Simplex Noise and Object Generation")
    print("----------------------------------------------")

    # Test parameters
    seed = 45
    grid_size = 100
    intensity = 0.16  # Increased from 0.1 for higher density
    ca_iterations = 2  # Cellular automata iterations

    # Create noise instance
    noise = SimplexNoise(seed)

    # Generate different noise maps for display
    noise_map = np.zeros((grid_size, grid_size))
    
    # Original object placement maps
    object_map_steppe = np.zeros((grid_size, grid_size))
    object_map_forest = np.zeros((grid_size, grid_size))
    object_map_snow = np.zeros((grid_size, grid_size))
    
    # Type maps
    type_map_steppe = np.zeros((grid_size, grid_size), dtype=int)
    type_map_forest = np.zeros((grid_size, grid_size), dtype=int)
    type_map_snow = np.zeros((grid_size, grid_size), dtype=int)

    # Populate maps
    print("Generating noise and object placement maps...")
    for x in range(grid_size):
        for y in range(grid_size):
            # Scale coordinates for more interesting patterns
            scaled_x = x / 10
            scaled_y = y / 10

            # Base noise for visualization
            noise_val = noise.noise3d(scaled_x, scaled_y, 0)
            noise_map[y, x] = noise_val

            # Check object placement for each region
            steppe_coord = (scaled_x * 20, 0, scaled_y * 20)
            forest_coord = (scaled_x * 20, 0, scaled_y * 20)
            snow_coord = (scaled_x * 20, 0, scaled_y * 20)

            # Object placement maps
            object_map_steppe[y, x] = 1 if can_place(steppe_coord, seed, Region.STEPPE, intensity) else 0
            object_map_forest[y, x] = 1 if can_place(forest_coord, seed, Region.FOREST, intensity) else 0
            object_map_snow[y, x] = 1 if can_place(snow_coord, seed, Region.SNOW_PLAINS, intensity) else 0

    # Apply cellular automata to refine object placement
    print("Applying cellular automata to refine object placement...")
    object_map_steppe_refined = apply_cellular_automata(object_map_steppe, iterations=ca_iterations)
    object_map_forest_refined = apply_cellular_automata(object_map_forest, iterations=ca_iterations)
    object_map_snow_refined = apply_cellular_automata(object_map_snow, iterations=ca_iterations)

    # Generate object type maps based on refined object maps
    for x in range(grid_size):
        for y in range(grid_size):
            scaled_x = x / 10
            scaled_y = y / 10
            
            steppe_coord = (scaled_x * 20, 0, scaled_y * 20)
            forest_coord = (scaled_x * 20, 0, scaled_y * 20)
            snow_coord = (scaled_x * 20, 0, scaled_y * 20)
            
            # Type maps (using enumeration)
            if object_map_steppe_refined[y, x]:
                obj_type = get_object_type(steppe_coord, seed, Region.STEPPE)
                if obj_type in ["grass_tall", "grass_short"]:
                    type_map_steppe[y, x] = 1  # Grass category
                elif obj_type in ["bush_small", "bush_flowering"]:
                    type_map_steppe[y, x] = 2  # Bush category
                elif obj_type == "rock":
                    type_map_steppe[y, x] = 3

            if object_map_forest_refined[y, x]:
                obj_type = get_object_type(forest_coord, seed, Region.FOREST)
                if obj_type == "tree_tall":
                    type_map_forest[y, x] = 1
                elif obj_type == "tree_pine":
                    type_map_forest[y, x] = 2
                elif obj_type == "bush":
                    type_map_forest[y, x] = 3

            if object_map_snow_refined[y, x]:
                obj_type = get_object_type(snow_coord, seed, Region.SNOW_PLAINS)
                if obj_type == "snow_rock":
                    type_map_snow[y, x] = 1
                elif obj_type == "pine_snow":
                    type_map_snow[y, x] = 2
                elif obj_type == "ice_formation":
                    type_map_snow[y, x] = 3
                    
    # Function to create visualizations with different styles
    def create_visualization(style_name, transparent=False, text_color='#333333'):
        if style_name == 'light':
            plt.style.use('default')
            chart_colors = ['#4CAF50', '#2196F3']
            pie_colors = ['#8BC34A', '#2E7D32', '#795548', '#64B5F6']
            info_box_params = dict(boxstyle="round,pad=0.5", facecolor='#E3F2FD', edgecolor='#1976D2', alpha=0.8)
            
            # Light theme colormaps
            steppe_cmap = ListedColormap(['white', '#8BC34A', '#388E3C', '#795548'])
            forest_cmap = ListedColormap(['white', '#2E7D32', '#66BB6A', '#AED581'])
            snow_cmap = ListedColormap(['white', '#90A4AE', '#64B5F6', '#E1F5FE'])
        else:  # For dark mode
            plt.style.use('dark_background')
            chart_colors = ['#81C784', '#64B5F6']  # Brighter colors for dark background
            pie_colors = ['#AED581', '#43A047', '#A1887F', '#90CAF9']  # Brighter for dark background
            info_box_params = dict(boxstyle="round,pad=0.5", facecolor='#263238', edgecolor='#64B5F6', alpha=0.9)
            
            # Dark theme colormaps - fixed to use proper RGBA tuples
            if transparent:
                # Use transparent black for background (index 0)
                steppe_cmap = ListedColormap(['#00000000', '#8BC34A', '#388E3C', '#795548'])
                forest_cmap = ListedColormap(['#00000000', '#2E7D32', '#66BB6A', '#AED581']) 
                snow_cmap = ListedColormap(['#00000000', '#90A4AE', '#64B5F6', '#E1F5FE'])
            else:
                # Use solid black for background (index 0)
                steppe_cmap = ListedColormap(['#121212', '#8BC34A', '#388E3C', '#795548'])
                forest_cmap = ListedColormap(['#121212', '#2E7D32', '#66BB6A', '#AED581'])
                snow_cmap = ListedColormap(['#121212', '#90A4AE', '#64B5F6', '#E1F5FE'])
                
        # Create figure with appropriate background
        fig = plt.figure(figsize=(16, 14))
        if transparent:
            fig.patch.set_alpha(0.0)  # Make figure background transparent
        
        fig.suptitle(f"Terrain Object Generation with Cellular Automata (Seed: {seed})", 
                    fontsize=20, fontweight='bold', y=0.98, color=text_color)
        
        # Use GridSpec for more control over layout
        gs = gridspec.GridSpec(4, 3, figure=fig, height_ratios=[1, 1, 1, 0.8], 
                              hspace=0.3, wspace=0.3)

        # Plot 1: Raw Noise
        ax1 = fig.add_subplot(gs[0, 0])
        if transparent:
            ax1.patch.set_alpha(0.0)
        im1 = ax1.imshow(noise_map, cmap='terrain', interpolation='bilinear')
        ax1.set_title("Simplex Noise Base", fontsize=12, fontweight='bold', color=text_color)
        ax1.set_xticks([])
        ax1.set_yticks([])
        fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
        
        # Row 1: Original object placement maps
        ax2 = fig.add_subplot(gs[0, 1])
        if transparent:
            ax2.patch.set_alpha(0.0)
        im2 = ax2.imshow(object_map_steppe, cmap='Greens', interpolation='nearest')
        ax2.set_title("Raw Object Placement (Steppe)", fontsize=12, fontweight='bold', color=text_color)
        ax2.set_xticks([])
        ax2.set_yticks([])
        
        ax3 = fig.add_subplot(gs[0, 2])
        if transparent:
            ax3.patch.set_alpha(0.0)
        im3 = ax3.imshow(object_map_forest, cmap='Greens', interpolation='nearest')
        ax3.set_title("Raw Object Placement (Forest)", fontsize=12, fontweight='bold', color=text_color)
        ax3.set_xticks([])
        ax3.set_yticks([])
        
        # Row 2: Refined object placement maps (after cellular automata)
        ax4 = fig.add_subplot(gs[1, 0])
        if transparent:
            ax4.patch.set_alpha(0.0)
        im4 = ax4.imshow(object_map_snow, cmap='Blues', interpolation='nearest')
        ax4.set_title("Raw Object Placement (Snow Plains)", fontsize=12, fontweight='bold', color=text_color)
        ax4.set_xticks([])
        ax4.set_yticks([])
        
        ax5 = fig.add_subplot(gs[1, 1])
        if transparent:
            ax5.patch.set_alpha(0.0)
        im5 = ax5.imshow(object_map_steppe_refined, cmap='Greens', interpolation='nearest')
        ax5.set_title(f"After Cellular Automata (Steppe, {ca_iterations} iterations)", fontsize=12, fontweight='bold', color=text_color)
        ax5.set_xticks([])
        ax5.set_yticks([])
        
        ax6 = fig.add_subplot(gs[1, 2])
        if transparent:
            ax6.patch.set_alpha(0.0)
        im6 = ax6.imshow(object_map_forest_refined, cmap='Greens', interpolation='nearest')
        ax6.set_title(f"After Cellular Automata (Forest, {ca_iterations} iterations)", fontsize=12, fontweight='bold', color=text_color)
        ax6.set_xticks([])
        ax6.set_yticks([])
        
        # Row 3: Object type maps
        ax7 = fig.add_subplot(gs[2, 0])
        if transparent:
            ax7.patch.set_alpha(0.0)
        im7 = ax7.imshow(object_map_snow_refined, cmap='Blues', interpolation='nearest')
        ax7.set_title(f"After Cellular Automata (Snow Plains, {ca_iterations} iterations)", fontsize=12, fontweight='bold', color=text_color)
        ax7.set_xticks([])
        ax7.set_yticks([])
        
        ax8 = fig.add_subplot(gs[2, 1])
        if transparent:
            ax8.patch.set_alpha(0.0)
        im8 = ax8.imshow(type_map_steppe, cmap=steppe_cmap, interpolation='nearest', vmin=0, vmax=3)
        ax8.set_title("Object Types (Steppe)", fontsize=12, fontweight='bold', color=text_color)
        ax8.set_xticks([])
        ax8.set_yticks([])
        
        ax9 = fig.add_subplot(gs[2, 2])
        if transparent:
            ax9.patch.set_alpha(0.0)
        im9 = ax9.imshow(type_map_forest, cmap=forest_cmap, interpolation='nearest', vmin=0, vmax=3)
        ax9.set_title("Object Types (Forest)", fontsize=12, fontweight='bold', color=text_color)
        ax9.set_xticks([])
        ax9.set_yticks([])

        # Row 4: Statistics visualization
        ax10 = fig.add_subplot(gs[3, 0])
        if transparent:
            ax10.patch.set_alpha(0.0)
        im10 = ax10.imshow(type_map_snow, cmap=snow_cmap, interpolation='nearest', vmin=0, vmax=3)
        ax10.set_title("Object Types (Snow Plains)", fontsize=12, fontweight='bold', color=text_color)
        ax10.set_xticks([])
        ax10.set_yticks([])
        
        # Create legends for the object types - fixed to use the color correctly for transparent theme
        steppe_legend = ["None", "Grass", "Bush", "Rock"]
        if transparent and style_name == 'dark':
            # For transparent themes, use manual colors instead of the cmap for the legend
            legend_colors = ['#00000000', '#8BC34A', '#388E3C', '#795548']
            steppe_patches = [plt.Rectangle((0,0),1,1, color=legend_colors[i]) for i in range(4)]
            
            forest_legend = ["None", "Tall Tree", "Pine Tree", "Bush"]
            forest_colors = ['#00000000', '#2E7D32', '#66BB6A', '#AED581']
            forest_patches = [plt.Rectangle((0,0),1,1, color=forest_colors[i]) for i in range(4)]
            
            snow_legend = ["None", "Snow Rock", "Snow Pine", "Ice Formation"]
            snow_colors = ['#00000000', '#90A4AE', '#64B5F6', '#E1F5FE']
            snow_patches = [plt.Rectangle((0,0),1,1, color=snow_colors[i]) for i in range(4)]
        else:
            # For non-transparent themes, use the cmap directly
            steppe_patches = [plt.Rectangle((0,0),1,1, color=steppe_cmap(i)) for i in range(4)]
            forest_legend = ["None", "Tall Tree", "Pine Tree", "Bush"]
            forest_patches = [plt.Rectangle((0,0),1,1, color=forest_cmap(i)) for i in range(4)]
            snow_legend = ["None", "Snow Rock", "Snow Pine", "Ice Formation"]
            snow_patches = [plt.Rectangle((0,0),1,1, color=snow_cmap(i)) for i in range(4)]
        
        # Apply legend with proper alpha setting
        ax8.legend(steppe_patches, steppe_legend, loc='lower right', fontsize='small', 
                   framealpha=0.7 if transparent else 1.0)
        ax9.legend(forest_patches, forest_legend, loc='lower right', fontsize='small', 
                   framealpha=0.7 if transparent else 1.0)
        ax10.legend(snow_patches, snow_legend, loc='lower right', fontsize='small', 
                    framealpha=0.7 if transparent else 1.0)
        
        # Statistics plots
        # Calculate statistics for raw and refined object maps
        steppe_before = np.sum(object_map_steppe)
        steppe_after = np.sum(object_map_steppe_refined)
        forest_before = np.sum(object_map_forest)
        forest_after = np.sum(object_map_forest_refined)
        snow_before = np.sum(object_map_snow)
        snow_after = np.sum(object_map_snow_refined)
        
        # Bar chart showing object counts before and after cellular automata
        ax11 = fig.add_subplot(gs[3, 1])
        if transparent:
            ax11.patch.set_alpha(0.0)
        regions = ['Steppe', 'Forest', 'Snow Plains']
        before_counts = [steppe_before, forest_before, snow_before]
        after_counts = [steppe_after, forest_after, snow_after]
        
        x = np.arange(len(regions))
        width = 0.35
        
        ax11.bar(x - width/2, before_counts, width, label='Before CA', color=chart_colors[0], alpha=0.7)
        ax11.bar(x + width/2, after_counts, width, label='After CA', color=chart_colors[1], alpha=0.7)
        
        ax11.set_title('Object Count Before/After CA', fontsize=12, fontweight='bold', color=text_color)
        ax11.set_xticks(x)
        ax11.set_xticklabels(regions, color=text_color)
        ax11.set_ylabel('Number of Objects', color=text_color)
        ax11.tick_params(colors=text_color)
        ax11.legend(framealpha=0.7 if transparent else 1.0)
        
        # Draw grid lines for better readability in presentations
        ax11.grid(axis='y', linestyle='--', alpha=0.4)
        
        # Pie chart showing object type distribution
        ax12 = fig.add_subplot(gs[3, 2])
        if transparent:
            ax12.patch.set_alpha(0.0)
        
        # Get the combined object type counts
        grass_count = np.sum(type_map_steppe == 1)
        bush_count = np.sum(type_map_steppe == 2)
        rock_count = np.sum(type_map_steppe == 3)
        tall_tree_count = np.sum(type_map_forest == 1)
        pine_count = np.sum(type_map_forest == 2)
        forest_bush_count = np.sum(type_map_forest == 3)
        snow_rock_count = np.sum(type_map_snow == 1)
        snow_pine_count = np.sum(type_map_snow == 2)
        ice_count = np.sum(type_map_snow == 3)
        
        # Combine similar types across regions for the pie chart
        labels = ['Bush (All)', 'Tree (All)', 'Rock (All)', 'Snow/Ice']
        sizes = [bush_count + forest_bush_count, 
                tall_tree_count + pine_count + snow_pine_count,
                rock_count + snow_rock_count,
                ice_count]
        explode = (0, 0.1, 0, 0)  # Explode the tree slice
        
        wedges, texts, autotexts = ax12.pie(sizes, explode=explode, labels=labels, colors=pie_colors, 
                                          autopct='%1.1f%%', shadow=True, startangle=140)
        
        # Set text properties for better visibility
        for text in texts:
            text.set_color(text_color)
        for autotext in autotexts:
            autotext.set_color('white' if style_name == 'dark' else 'black')
            
        ax12.set_title('Object Type Distribution', fontsize=12, fontweight='bold', color=text_color)
        ax12.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Add text info about cellular automata
        fig.text(0.5, 0.01, 
                f"Cellular Automata: {ca_iterations} iterations with birth threshold=3, survival threshold=2",
                ha='center', fontsize=12, fontweight='bold', color=text_color,
                bbox=info_box_params)

        # Adjust layout and save
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Determine filename suffix
        suffix = "_dark" if style_name == 'dark' else "_light"
        if transparent:
            suffix += "_transparent"
            
        # Save with appropriate settings
        plt.savefig(f'terrain_generation_seed_{seed}{suffix}.png', 
                    dpi=300, bbox_inches='tight', 
                    transparent=transparent)
        
        print(f"Saved visualization as 'terrain_generation_seed_{seed}{suffix}.png'")
        return fig

    # Create light version (default style)
    print("\nCreating light theme visualization...")
    light_fig = create_visualization('light', transparent=False)
    
    # Create dark version with transparent background
    print("\nCreating dark theme visualization with transparent background...")
    dark_fig = create_visualization('dark', transparent=True, text_color='white')
    
    # Create dark version with dark background (for preview)
    print("\nCreating dark theme visualization with dark background...")
    dark_bg_fig = create_visualization('dark', transparent=False, text_color='white')
    
    # Print statistics
    print("\nObject Placement Statistics:")
    print(f"Steppe Region: Before CA: {np.sum(object_map_steppe)} objects, After CA: {np.sum(object_map_steppe_refined)} objects")
    print(f"Forest Region: Before CA: {np.sum(object_map_forest)} objects, After CA: {np.sum(object_map_forest_refined)} objects")
    print(f"Snow Region: Before CA: {np.sum(object_map_snow)} objects, After CA: {np.sum(object_map_snow_refined)} objects")

    # Calculate totals for object type statistics
    grass_count = np.sum(type_map_steppe == 1)
    bush_count = np.sum(type_map_steppe == 2)
    rock_count = np.sum(type_map_steppe == 3)
    tall_tree_count = np.sum(type_map_forest == 1)
    pine_count = np.sum(type_map_forest == 2)
    forest_bush_count = np.sum(type_map_forest == 3)
    snow_rock_count = np.sum(type_map_snow == 1)
    snow_pine_count = np.sum(type_map_snow == 2)
    ice_count = np.sum(type_map_snow == 3)
    
    total_objects = np.sum([grass_count, bush_count, rock_count, tall_tree_count, pine_count, 
                          forest_bush_count, snow_rock_count, snow_pine_count, ice_count])
    
    print("\nObject Type Distribution:")
    print(f"  Bush (All Regions): {bush_count + forest_bush_count} ({(bush_count + forest_bush_count)/total_objects*100:.1f}%)")
    print(f"  Tree (All Types): {tall_tree_count + pine_count + snow_pine_count} ({(tall_tree_count + pine_count + snow_pine_count)/total_objects*100:.1f}%)")
    print(f"  Rock (All Types): {rock_count + snow_rock_count} ({(rock_count + snow_rock_count)/total_objects*100:.1f}%)")
    print(f"  Snow/Ice: {ice_count} ({ice_count/total_objects*100:.1f}%)")

    print("\nDisplaying visualizations. Close the plot windows to exit.")
    plt.show()
