from PIL import Image
import os

# Replace with the path to your PNG images
input_directory = 'data/images/entities/cat/run_2'
output_directory = 'data/images/entities/cat/run'

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

for filename in os.listdir(input_directory):
    if filename.endswith('.png'):
        png_path = os.path.join(input_directory, filename)
        img = Image.open(png_path)
        jpeg_filename = os.path.splitext(filename)[0] + '.jpg'
        jpeg_path = os.path.join(output_directory, jpeg_filename)
        img = img.convert('RGB')
        img.save(jpeg_path, 'JPEG')

print('Conversion complete.')
