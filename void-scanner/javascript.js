const inputImg = document.querySelector('#image');
const image = document.querySelector("img");
const reset = document.querySelector("button[type=reset]");
const form = document.querySelector("form");
const slider = document.querySelector('#slider');
const valid = document.querySelector(".valid");

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
})

slider.addEventListener("change", () => {
    let value = slider.value;
    try {
        image.src = `http://127.0.0.1:8000/get-image/${value-1}`;
    }
    catch {
        console.log('prob index error');
    }
})
