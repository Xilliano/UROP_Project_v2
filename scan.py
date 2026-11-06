import cv2
import numpy as np
import itertools

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

from fastapi.middleware.cors import CORSMiddleware

import compare

images = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get-image/{image_number}")
async def home(image_number: int):
    if images:
        return Response(content=images[image_number], media_type="image/png")

@app.get("/get-parameters")
async def return_parameters():
    return getAllParameters(filters)

@app.get("/get-comparison")
async def return_comparison():
    return

@app.post("/set-parameters")
async def update_images(parameters: dict):
    filterNum = parameters['filterNumber']
    paramName = parameters['parameterName']
    paramValue = parameters['parameterValue']
    filters[filterNum-1].setParamValue(paramName, paramValue)

    applyFilters(images[0], filters, to=filterNum)

@app.post("/upload-image")
async def create_upload_file(image: UploadFile = File(...)):
    content = await image.read()
    applyFilters(content, filters)

    return {
        "filename": image.filename,
        "content_type": image.content_type,
    }

def getAllParameters(filters: list):
    return [
        {filter.name: filter.getParameters()}
        for filter in filters
    ]

def applyFilters(img, filters: list, to=None):
    # Assumes data still in png bytes
    images[0] = img
    img_dcd = decode(img)
    for i, filter in enumerate(filters, start=1):
        img_dcd = filter(img_dcd)
        images[i] = encode(img_dcd)

def optimizeParameters(step, filters):
    # vary 1 parameter by step
    # save points, append to list
    # after all possible combos, send to compare
    # return the best combination (minimum error)
    pointsList = []
    paramRanges = {}

    for filter in filters:
        for param in filter.params:
            param.value = param.min
            paramRanges[param.name] = np.arange(param.min, param.max, param.step*step)

    # get default values, then start trying different combos
    #pointsList.append(getFinalPoints())

    keys = paramRanges.keys()
    all_combinations = list(itertools.product(*paramRanges.values()))

    print(all_combinations)

def getFinalPoints():
    points = []
    final_image = decode(images[-1])
    contours, _ = cv2.findContours(final_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        M = cv2.moments(c)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

        else:
            cX, cY = 0, 0

        points.append((cX, cY))

    return points

class Filter:
    def __init__(self, name, filter, params: list):
        self.name = name
        self.filter = filter
        self.params = params

    def getParamLength(self):
        return len(self.params)

    def getParameters(self):
        return [param.getAsDict() for param in self.params]

    def setParamValue(self, paramName, paramValue):
        for param in self.params:
            if param.name == paramName:
                param.value = paramValue

    def getParamValue(self, paramName):
        for param in self.params:
            if param.name == paramName:
                return param.value

    def __call__(self, img):
        values = [param.value for param in self.params]
        return self.filter(img, *values)

class Parameter:
    def __init__(self, name: str, minmax: tuple, step: float, defaultValue: float):
        self.name = name
        self.min, self.max = minmax
        self.step = step
        self.value = defaultValue

    def getAsDict(self):
        return {
            'name': self.name,
            'min': self.min,
            'max': self.max,
            'step': self.step,
            'value': self.value,
        }


def decode(img):
    return cv2.imdecode(
        np.frombuffer(img, np.uint8),
        cv2.IMREAD_GRAYSCALE
    )

def encode(img):
    _, encoded = cv2.imencode(".png", img)
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

        for (foot1, far1), (foot2, far2) in itertools.combinations(pts, 2):
            v1 = far1 - foot1
            v2 = far2 - foot2
            if similar(v1, v2):
                cv2.line(img, far1, far2, 0, thickness=2)

    return img

OtsuThresh = Filter('Otsu', otsu, [])

Threshold = Filter(
    'Adaptive Threshold',
    thresh,
    [
        Parameter("block_size", (99, 299), 2, 199),
        Parameter("sensitivity", (0, 100), 1, 50),
    ],
)

Blurring = Filter(
    'Blur',
    blur,
    [
        Parameter("kernel_size", (1, 49), 2, 5),
    ],
)

ConvexityAnalysis = Filter(
    'Convexity Analysis',
    convexity_analysis,
    [
        #Parameter("contour_sens", (0, 100), False),
        Parameter("error", (0, 1), .1, 0.1),
    ]
)

filters = [Threshold, Blurring, ConvexityAnalysis]

optimizeParameters(4, filters)
