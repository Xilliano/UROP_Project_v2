const inputImg = document.querySelector('#image');
const image = document.querySelector("img");
const reset = document.querySelector("button[type=reset]");
const form = document.querySelector("form");
const slider = document.querySelector('#slider');
const valid = document.querySelector(".valid");
const server = 'http://127.0.0.1:8000';
const parametersDiv = document.querySelector(".parameters");

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
    slider.value = 1;
    slider.style.display = 'none';
    valid.style.display = 'none';
})

form.addEventListener("submit", (event) => {
    slider.style.display = "block";
    valid.style.display = 'none';

    // displayParameters(data);
})

async function getData() {
    let parameters = await fetch(`${server}/get-parameters`);
    let data = await parameters.json();
}

slider.addEventListener("change", () => {
    let value = slider.value;
    try {
        image.src = `http://127.0.0.1:8000/get-image/${value-1}`;
    }
    catch {
        console.log('prob index error');
    }
})

function displayParameters(parameters) {
    let length = parameters.length;
    for(let i = 0; i < length; i++) {
        let container = document.createElement("div");
        container.classList.add("parameter");
        container.style.border = '1px red solid'
        container.style.height = '50px';
        container.style.width = 'auto';
        container.textContent = parameters[i];

        parametersDiv.appendChild(container);
    }
}
