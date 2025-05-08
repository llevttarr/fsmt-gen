"""
Object Generation Module

This module provides functions to determine if an object can be placed at given coordinates
based on a seed. It uses a custom simplex noise implementation to create natural-looking 
distributions of objects while maintaining deterministic results.
"""

# Use the correct module structure.
from render.object_manager import Object3D
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

def init_objects(seed,n_rings,intensity,rg_data,y_data):
    '''
    initializes objects for each block in a 3^n_rings sized world
    returns them as a dictionary where for (x,z) => Object||None
    '''
    border = (1 + ((n_rings-1)*3))*2
    obj_data = {}
    for x in range(-border,border+1,1):
        for z in range(-border,border+1,1):
            rg = rg_data[(x,z)]
            y = y_data[(x,z)]
            if intensity == 0:
                obj_data[(x,z)]=None
                continue
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
                    os.path.dirname(__file__),
                    "..","..", 
                    "static","assets",path
                    ))
                )
                obj_data[(x,z)].translate(x,y,z)
            else:
                obj_data[(x,z)]=None
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


if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.colors import ListedColormap
    except ImportError:
        print("Error: This visualization requires matplotlib and numpy.")
        print("Please install them with: pip install matplotlib numpy")
        exit(1)

    print("Visualizing Simplex Noise and Object Generation")
    print("----------------------------------------------")

    # Test parameters.
    seed = 45
    grid_size = 100
    intensity = 0.16  # Increased from 0.1 for higher density

    # Create noise instance.
    noise = SimplexNoise(seed)

    # Generate different noise maps for display.
    noise_map = np.zeros((grid_size, grid_size))
    object_map_steppe = np.zeros((grid_size, grid_size))
    object_map_forest = np.zeros((grid_size, grid_size))
    object_map_snow = np.zeros((grid_size, grid_size))

    # Type maps.
    type_map_steppe = np.zeros((grid_size, grid_size), dtype=int)
    type_map_forest = np.zeros((grid_size, grid_size), dtype=int)
    type_map_snow = np.zeros((grid_size, grid_size), dtype=int)

    # Populate maps.
    print("Generating noise and object placement maps...")
    for x in range(grid_size):
        for y in range(grid_size):
            # Scale coordinates for more interesting patterns.
            scaled_x = x / 10
            scaled_y = y / 10

            # Base noise for visualization.
            noise_val = noise.noise3d(scaled_x, scaled_y, 0)
            noise_map[y, x] = noise_val

            # Check object placement for each region.
            steppe_coord = (scaled_x * 20, 0, scaled_y * 20)
            forest_coord = (scaled_x * 20, 0, scaled_y * 20)
            snow_coord = (scaled_x * 20, 0, scaled_y * 20)

            # Object placement maps.
            object_map_steppe[y, x] = 1 if can_place(steppe_coord, seed, Region.STEPPE, intensity) else 0
            object_map_forest[y, x] = 1 if can_place(forest_coord, seed, Region.FOREST, intensity) else 0
            object_map_snow[y, x] = 1 if can_place(snow_coord, seed, Region.SNOW_PLAINS, intensity) else 0

            # Type maps (using enumeration).
            if object_map_steppe[y, x]:
                obj_type = get_object_type(steppe_coord, seed, Region.STEPPE)
                # Add support for the new object types
                if obj_type == "grass_tall": type_map_steppe[y, x] = 1
                elif obj_type == "grass_short": type_map_steppe[y, x] = 1  # Still grass category
                elif obj_type == "bush_small": type_map_steppe[y, x] = 2
                elif obj_type == "bush_flowering": type_map_steppe[y, x] = 2  # Still bush category
                elif obj_type == "rock": type_map_steppe[y, x] = 3

            if object_map_forest[y, x]:
                obj_type = get_object_type(forest_coord, seed, Region.FOREST)
                if obj_type == "tree_tall": type_map_forest[y, x] = 1
                elif obj_type == "tree_pine": type_map_forest[y, x] = 2
                elif obj_type == "bush": type_map_forest[y, x] = 3

            if object_map_snow[y, x]:
                obj_type = get_object_type(snow_coord, seed, Region.SNOW_PLAINS)
                if obj_type == "snow_rock": type_map_snow[y, x] = 1
                elif obj_type == "pine_snow": type_map_snow[y, x] = 2
                elif obj_type == "ice_formation": type_map_snow[y, x] = 3

    # Create figure for visualization.
    fig = plt.figure(figsize=(15, 12))
    fig.suptitle(f"Simplex Noise and Object Generation Visualization (Seed: {seed})", fontsize=16)

    # Plot 1: Raw Noise.
    ax1 = fig.add_subplot(331)
    im1 = ax1.imshow(noise_map, cmap='terrain', interpolation='bilinear')
    ax1.set_title("Raw Simplex Noise")
    fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    # Plot 2-4: Object Placement Maps.
    ax2 = fig.add_subplot(332)
    im2 = ax2.imshow(object_map_steppe, cmap='binary', interpolation='nearest')
    ax2.set_title(f"Object Placement (Steppe)")

    ax3 = fig.add_subplot(333)
    im3 = ax3.imshow(object_map_forest, cmap='binary', interpolation='nearest')
    ax3.set_title(f"Object Placement (Forest)")

    ax4 = fig.add_subplot(334)
    im4 = ax4.imshow(object_map_snow, cmap='binary', interpolation='nearest')
    ax4.set_title(f"Object Placement (Snow Plains)")

    # Plot 5-7: Object Type Maps.
    # Custom colormaps for each region.
    steppe_cmap = ListedColormap(['white', 'yellowgreen', 'darkgreen', 'sienna'])
    forest_cmap = ListedColormap(['white', 'darkgreen', 'forestgreen', 'olive'])
    snow_cmap = ListedColormap(['white', 'lightgrey', 'skyblue', 'white'])

    ax5 = fig.add_subplot(335)
    im5 = ax5.imshow(type_map_steppe, cmap=steppe_cmap, interpolation='nearest', vmin=0, vmax=3)
    ax5.set_title("Object Types (Steppe)")
    steppe_legend = ["None", "Grass", "Bush", "Rock"]
    steppe_patches = [plt.Rectangle((0,0),1,1, color=steppe_cmap(i)) for i in range(4)]
    ax5.legend(steppe_patches, steppe_legend, loc='upper right', fontsize='small')

    ax6 = fig.add_subplot(336)
    im6 = ax6.imshow(type_map_forest, cmap=forest_cmap, interpolation='nearest', vmin=0, vmax=3)
    ax6.set_title("Object Types (Forest)")
    forest_legend = ["None", "Tall Tree", "Pine Tree", "Bush"]
    forest_patches = [plt.Rectangle((0,0),1,1, color=forest_cmap(i)) for i in range(4)]
    ax6.legend(forest_patches, forest_legend, loc='upper right', fontsize='small')

    ax7 = fig.add_subplot(337)
    snow_cmap = ListedColormap(['white', 'gray', 'deepskyblue', 'paleturquoise'])
    im7 = ax7.imshow(type_map_snow, cmap=snow_cmap, interpolation='nearest', vmin=0, vmax=3)
    ax7.set_title("Object Types (Snow Plains)")
    snow_legend = ["None", "Snow Rock", "Snow Pine", "Ice Formation"]
    snow_patches = [plt.Rectangle((0,0),1,1, color=snow_cmap(i)) for i in range(4)]
    ax7.legend(snow_patches, snow_legend, loc='upper right', fontsize='small')

    # Print statistics.
    print("\nObject Placement Statistics:")
    print(f"Steppe Region: {np.sum(object_map_steppe)} objects placed ({np.sum(object_map_steppe)/(grid_size*grid_size)*100:.2f}%)")
    print(f"Forest Region: {np.sum(object_map_forest)} objects placed ({np.sum(object_map_forest)/(grid_size*grid_size)*100:.2f}%)")
    print(f"Snow Region: {np.sum(object_map_snow)} objects placed ({np.sum(object_map_snow)/(grid_size*grid_size)*100:.2f}%)")

    # Calculate object type distribution in steppe.
    if np.sum(object_map_steppe) > 0:
        grass_count = np.sum(type_map_steppe == 1)
        bush_count = np.sum(type_map_steppe == 2)
        rock_count = np.sum(type_map_steppe == 3)
        print(f"\nSteppe Object Types:")
        print(f"  Grass: {grass_count} ({grass_count/np.sum(object_map_steppe)*100:.2f}%)")
        print(f"  Bush: {bush_count} ({bush_count/np.sum(object_map_steppe)*100:.2f}%)")
        print(f"  Rock: {rock_count} ({rock_count/np.sum(object_map_steppe)*100:.2f}%)")

    # Calculate object type distribution in forest.
    if np.sum(object_map_forest) > 0:
        tall_tree_count = np.sum(type_map_forest == 1)
        pine_count = np.sum(type_map_forest == 2)
        bush_count = np.sum(type_map_forest == 3)
        print(f"\nForest Object Types:")
        print(f"  Tall Trees: {tall_tree_count} "
              f"({tall_tree_count/np.sum(object_map_forest)*100:.2f}%)")
        print(f"  Pine Trees: {pine_count} ({pine_count/np.sum(object_map_forest)*100:.2f}%)")
        print(f"  Bushes: {bush_count} ({bush_count/np.sum(object_map_forest)*100:.2f}%)")
        
    # Add statistical output for snow plains object type.
    if np.sum(object_map_snow) > 0:
        rock_count = np.sum(type_map_snow == 1)
        pine_count = np.sum(type_map_snow == 2)
        ice_count = np.sum(type_map_snow == 3)
        print(f"\nSnow Plains Object Types:")
        print(f"  Snow Rocks: {rock_count} ({rock_count/np.sum(object_map_snow)*100:.2f}%)")
        print(f"  Snow Pines: {pine_count} ({pine_count/np.sum(object_map_snow)*100:.2f}%)")
        print(f"  Ice Formations: {ice_count} ({ice_count/np.sum(object_map_snow)*100:.2f}%)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    print("\nDisplaying visualization. Close the plot window to exit.")
    plt.show()
