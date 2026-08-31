import cv2
import numpy as np
import pandas as pd
from itertools import combinations

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

images = []

app = FastAPI()

@app.get("/get-image/{image_number}")
async def home(image_number: int):
    if images:
        return Response(content=images[image_number], media_type="image/png")
    else:
        return {"Message": "Congrats! This is your first API!"}

@app.post("/upload-image")
async def create_upload_file(image: UploadFile = File(...)):
    content = await image.read()

    content = decode(content)

    images.append(encode(content))

    content = thresh(content, 199, 50)
    images.append(encode(content))

    content = blur(content, 5)
    images.append(encode(content))

    content = convexity_analysis(content, .1)
    images.append(encode(content))

    return {
        "filename": image.filename,
        "content_type": image.content_type,
    }

class Filter:
    def __init__(self, filter, params: list):
        self.filter = filter
        self.params = params

class Parameter:
    def __init__(self, name: str, range: tuple, even: bool):
        self.name = name
        self.range = range
        self.even = even

def decode(img):
    return cv2.imdecode(
        np.frombuffer(img, np.uint8),
        cv2.IMREAD_GRAYSCALE
    )

def encode(img):
    success, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()

def otsu(img):
    _, thresh = cv2.threshold(
        img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return thresh

def thresh(img, block_size, sensitivity):
    return cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        block_size, # was 199
        sensitivity,
    )

def blur(img, kernel_size):
    return cv2.medianBlur(img, kernel_size)

def convexity_analysis(img, error: float):
    def similar(vec1, vec2):
        vec1_unit = vec1 / np.linalg.norm(vec1)
        vec2_unit = vec2 / np.linalg.norm(vec2)
        dot_similarity = vec1_unit @ vec2_unit
        return np.isclose(dot_similarity, -1, atol=error)

    contours, _ = cv2.findContours(
        img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
    )

    for cntr in contours:
        hull = cv2.convexHull(cntr, returnPoints = False)
        defects = cv2.convexityDefects(cntr, hull)

        pts = []
        if defects is not None:
            for defect in defects:
                start_idx = defect[0]
                end_idx = defect[1]
                far_idx = defect[2]
                depth = defect[3]

                if depth/256.0 < 5:
                    continue

                start_pt = cntr[start_idx][0]
                end_pt = cntr[end_idx][0]
                far_pt = cntr[far_idx][0] # cv2 has extra wrapper, dont ask me man

                SF = far_pt - start_pt
                SE = end_pt - start_pt

                proj = (SF @ SE) / (SE @ SE) * SE

                foot = start_pt + proj
                pts.append((foot, far_pt))

        for (foot1, far1), (foot2, far2) in combinations(pts, 2):
            v1 = far1 - foot1
            v2 = far2 - foot2
            if similar(v1, v2):
                cv2.line(img, far1, far2, 0, thickness=2)

    return img

otsu_obj = Filter(otsu, [])

thresh_obj = Filter(
    thresh,
    [
        Parameter("block_size", (100, 300), True),
        Parameter("sensitivity", (0, 100), False),
    ],
)

blur_obj = Filter(
    blur,
    [
        Parameter("kernel_size", (0, 50), True),
    ],
)

convexity_analysis_obj = Filter(
    convexity_analysis,
    [
        #Parameter("contour_sens", (0, 100), False),
        Parameter("error", (0, 1), False),
    ]
)
