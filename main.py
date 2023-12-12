import numpy as np
import cv2
import eel

import math
import base64

FRAME_WIDTH = 1080
FRAME_HEIGHT = 720
FRAME_FOV = 120

def denormalize_coords(image_coords, size):
    # [img_x, img_y, [sphere_u., sphere_v.]] -> [img_x, img_y, [sphere_x, sphere_y]]
    coords = np.zeros(image_coords.shape)
    coords[:, :, 0] = (image_coords[:, :, 0] + 1) / 2 * size[0]
    coords[:, :, 1] = (image_coords[:, :, 1] + 1) / 2 * size[1]

    coords = coords.astype(np.int32)
    coords[:, :, 0] = np.clip(coords[:, :, 0], 0, size[1] - 1)
    coords[:, :, 1] = np.clip(coords[:, :, 1], 0, size[0] - 1)
    return coords

def image_coords_from_world_vec(world_vecs):
    # [img_x, img_y, [world_x, world_y, world_z]] -> [img_x, img_y, [sphere_u., sphere_v.]]
    frac = 1 / np.sqrt(2 * (world_vecs[:, :, 2] + 1))
    sphere_u = frac * world_vecs[:, :, 0]
    sphere_v = frac * world_vecs[:, :, 1]

    img_coords = np.stack([sphere_u, sphere_v], axis=2)
    return img_coords

def rotate_x(vecs, theta):
    # Rotate the vectors around the x axis
    rot_mat = np.array([
        [1, 0, 0],
        [0, math.cos(theta), -math.sin(theta)],
        [0, math.sin(theta), math.cos(theta)]
    ])
    return np.matmul(vecs, rot_mat)

def rotate_y(vecs, theta):
    # Rotate the vectors around the x axis
    rot_mat = np.array([
        [math.cos(theta), 0, math.sin(theta)],
        [0, 1, 0],
        [-math.sin(theta), 0, math.cos(theta)]
    ])
    return np.matmul(vecs, rot_mat)

def camera_rays_from_view(azimuth, elevation):
    # azimuth, elevation -> [img_x, img_y, [world_x, world_y, world_z]]
    # Create a grid of image coordinates
    img_x = np.linspace(-1, 1, FRAME_WIDTH)
    img_y = np.linspace(-1, 1, FRAME_HEIGHT)
    img_x, img_y = np.meshgrid(img_x, img_y)

    # Create a grid of world coordinates
    world_x = np.tan(np.deg2rad(FRAME_FOV) / 2) * img_x
    world_y = np.tan(np.deg2rad(FRAME_FOV * FRAME_HEIGHT / FRAME_WIDTH) / 2) * img_y
    world_z = np.ones(world_x.shape)

    # Rotate the world coordinates
    world_vecs = np.stack([world_x, world_y, world_z], axis=2)
    world_vecs = rotate_x(world_vecs, elevation)
    world_vecs = rotate_y(world_vecs, azimuth)

    # Normalize the world coordinates
    world_vecs = world_vecs / np.linalg.norm(world_vecs, axis=2, keepdims=True)

    return world_vecs

def crop_image(image, crop):
    # crop = [x0, y0, w, h] in [0-1] range
    crop = np.array(crop)
    crop = crop * np.array([image.shape[1], image.shape[0], image.shape[1], image.shape[0]])
    crop = crop.astype(np.int32)
    return image[crop[1]:crop[1]+crop[3], crop[0]:crop[0]+crop[2]]

def draw_debug(azimuth, elevation):
    sphere_image = cv2.imread("images/mirror_ball_4.png")
    vecs = camera_rays_from_view(elevation, azimuth)

    normalized_coords = image_coords_from_world_vec(vecs)
    sphere_coords = denormalize_coords(normalized_coords, sphere_image.shape)
    sphere_image[sphere_coords[:, :, 1], sphere_coords[:, :, 0]] = [0, 0, 255]

    return sphere_image

def draw_image(sphere_image, azimuth, elevation):
    vecs = camera_rays_from_view(elevation, azimuth)
    normalized_coords = image_coords_from_world_vec(vecs)
    sphere_coords = denormalize_coords(normalized_coords, sphere_image.shape)
    image_out = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    image_out[:, :, :] = sphere_image[sphere_coords[:, :, 1], sphere_coords[:, :, 0], :]

    return image_out

class MirrorBallRenderer:
    def __init__(self):
        self.image = None
        self.azimuth = 0
        self.elevation = 0

    def set_image(self, image):
        self.image = image

    def render(self):
        return draw_image(self.image, self.elevation, self.azimuth)
    
    def move_camera(self, key):
        if key == 'a':
            self.azimuth += np.deg2rad(20)
        elif key == 'd':
            self.azimuth -= np.deg2rad(20)
        elif key == 'w':
            self.elevation -= np.deg2rad(20)
        elif key == 's':
            self.elevation += np.deg2rad(20)

        self.elevation = np.clip(self.elevation, -np.pi / 2, np.pi / 2)

if __name__ == "__main__":
    renderer = MirrorBallRenderer()

    def data_uri_to_cv2_img(uri):
        encoded_data = uri.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    
    def cv2_img_to_data_uri(img):
        _, buffer = cv2.imencode('.png', img)
        png_as_text = base64.b64encode(buffer)
        return f"data:image/png;base64,{png_as_text.decode('utf-8')}"

    @eel.expose
    def set_image(base_64_img, crop=None):
        try:
            image = data_uri_to_cv2_img(base_64_img)
            if crop is not None:
                image = crop_image(image, crop)
            renderer.set_image(image)
        except Exception as e:
            print(f"Error reading image: {e}")
            return f"Error reading image: {e}"
        return "OK"

    @eel.expose
    def render():
        image = renderer.render()
        return cv2_img_to_data_uri(image)
    
    @eel.expose
    def move_camera(key):
        renderer.move_camera(key)

    eel.init('web')
    eel.start('index.html', size=(FRAME_WIDTH, FRAME_HEIGHT))