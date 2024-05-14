from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io
from skimage.transform import resize
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

# Load your generator model for binarization
binarization_model_path = 'model/last_model_with_architecture.h5'
binarization_generator = load_model(binarization_model_path)

def split2(dataset, size, h, w):
    newdataset = []
    nsize1 = 256
    nsize2 = 256
    for i in range(size):
        im = dataset[i]
        for ii in range(0, h, nsize1):
            for iii in range(0, w, nsize2):
                newdataset.append(im[ii:ii+nsize1, iii:iii+nsize2, :])
    return np.array(newdataset)

def merge_image2(splitted_images, h, w):
    image = np.zeros(((h, w, 1)))
    nsize1 = 256
    nsize2 = 256
    ind = 0
    for ii in range(0, h, nsize1):
        for iii in range(0, w, nsize2):
            image[ii:ii+nsize1, iii:iii+nsize2, :] = splitted_images[ind]
            ind += 1
    return np.array(image)

def apply_binarization(generator, img_array):
    deg_image = Image.fromarray((img_array * 255).astype(np.uint8))
    h = ((img_array.shape[0] // 256) + 1) * 256
    w = ((img_array.shape[1] // 256) + 1) * 256
    test_padding = np.ones((h, w))
    test_padding[:img_array.shape[0], :img_array.shape[1]] = img_array
    test_image_p = split2(test_padding.reshape(1, h, w, 1), 1, h, w)
    predicted_list = []
    for l in range(test_image_p.shape[0]):
        predicted_list.append(generator.predict(test_image_p[l].reshape(1, 256, 256, 1)))
    predicted_image = np.array(predicted_list)
    predicted_image = merge_image2(predicted_image, h, w)
    predicted_image = predicted_image[:img_array.shape[0], :img_array.shape[1]]
    predicted_image = predicted_image.reshape(predicted_image.shape[0], predicted_image.shape[1])
    bin_thresh = 0.6
    binarized_image = (predicted_image[:, :] <= bin_thresh) * 1
    inverted_binarized_image = 1 - binarized_image
    return inverted_binarized_image

@app.post('/enhance_image')
async def enhance_image(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('L')
        img_array = np.array(img) / 255.0
        enhanced_image = apply_binarization(binarization_generator, img_array)
        enhanced_image_bytes = io.BytesIO()
        Image.fromarray((enhanced_image * 255).astype(np.uint8)).save(enhanced_image_bytes, format='PNG')
        enhanced_image_bytes.seek(0)
        return StreamingResponse(io.BytesIO(enhanced_image_bytes.read()), media_type="application/octet-stream")
    except Exception as e:
        return str(e)

@app.get('/')
async def home():
    return {"message": "Upload an image for enhancement"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
