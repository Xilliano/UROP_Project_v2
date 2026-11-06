const inputImg = document.querySelector('#image');
const image = document.querySelector("img");
const reset = document.querySelector("button[type=reset]");
const form = document.querySelector("form");
const slider = document.querySelector('#slider');
const compare = document.querySelector('#compare');
const valid = document.querySelector(".valid");
const server = 'http://127.0.0.1:8000';
const parametersDiv = document.querySelector(".parameters");

let currentImg = 0;

inputImg.addEventListener("change", () => {
    const [file] = inputImg.files;

    if (file && file.type.match('image.*')) {
        image.src = URL.createObjectURL(file);
        valid.style.display = 'block';
    }
})

image.addEventListener("dblclick", (event) => {
    const rect = image.getBoundingClientRect();

    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    image.style.transformOrigin = `${x}% ${y}%`;
    image.classList.toggle("zoomed");
});

reset.addEventListener("click", () => {
    image.src = '';
    slider.value = 0;
    slider.style.display = 'none';
    valid.style.display = 'none';
    compare.style.display = 'none';
    removeChildren(parametersDiv);
})

form.addEventListener("submit", submit);

slider.addEventListener("input", () => {
    let value = slider.value;
    try {
        image.src = `${server}/get-image/${value}?t=${Date.now()}`;
        currentImg = Number(value);
    }
    catch (error){
        console.log(error);
    }
})

compare.addEventListener("click", () => {
    
})

function removeChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.lastChild);
    }
}

async function submit() {
    slider.style.display = "block";
    compare.style.display = 'inline';
    valid.style.display = 'none';
    let data = await getData();

    displayParameters(data);
}


async function getData() {
    let request = new Request(`${server}/get-parameters`);
    let response = await fetch(request)
    let parameters = await response.json();

    return parameters;
}

async function parameterSliderEvent(slider, label, filterInfo) {
    label.textContent = `${slider.value}`;
    let filterNum = filterInfo[0];
    let filterName = filterInfo[1];

    const response = await fetch(`${server}/set-parameters`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filterNumber: filterNum,
            parameterName: filterName,
            parameterValue: Number(slider.value)
        })
    });

    if (filterNum <= currentImg) {
        image.src = `${server}/get-image/${currentImg}?t=${Date.now()}`;;
    }
}

function displayParameters(parameters) {
    let filters = parameters.map(filter => Object.keys(filter)[0]);
    for(let i = 0; i < filters.length; i++) {
        let container = document.createElement("div");
        container.classList.add("parameter");
        container.style.fontFamily = 'Roboto';
        container.textContent = filters[i] + ':';

        let propertiesContainer = document.createElement("ul");
        let properties = Object.values(parameters[i])[0];
        for(let j = 0; j < properties.length; j++) {
            let propContainer = document.createElement('div');

            let prop = document.createElement("li");
            let parameter = properties[j];
            prop.textContent = parameter.name + ':';
            prop.style.listStyle = 'none';

            let label = document.createElement('label');
            label.textContent = `${parameter.value}`;

            let input = document.createElement('input');
            input.type = 'range';
            input.min = parameter.min;
            input.max = parameter.max;

            input.step = parameter.step;

            input.value = parameter.value;
            input.style.display = 'block';

            let filterInfo = [i+1, parameter.name]

            input.addEventListener("input", () => parameterSliderEvent(input, label, filterInfo));

            propContainer.append(prop);
            propContainer.append(label);
            propContainer.append(input);
            propertiesContainer.appendChild(propContainer);
        }

        parametersDiv.appendChild(container);
        container.appendChild(propertiesContainer);
    }
}
