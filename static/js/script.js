const page = document.body.dataset.page;
const sidebarToggle = document.getElementById('sidebarToggle');

const fadeElements = document.querySelectorAll('.fade-up');
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.2 });
fadeElements.forEach((element) => observer.observe(element));

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        document.querySelector('.app-sidebar').classList.toggle('sidebar-open');
    });
}

function showLoading(container, message) {
    container.innerHTML = `
        <div class="result-empty">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>`;
}

function updateResultSummary(data) {
    const resultSection = document.getElementById('resultSection');
    const confidenceValue = document.getElementById('confidenceValue');
    const confidenceBarFill = document.getElementById('confidenceBarFill');
    const breedCategory = document.getElementById('breedCategory');
    const breedOrigin = document.getElementById('breedOrigin');

    if (!resultSection) return;

    resultSection.innerHTML = `
        <div class="result-empty">
            <i class="fa-solid fa-check-circle"></i>
            <h3>${data.breed}</h3>
            <p>${data.characteristics}</p>
        </div>`;

    if (confidenceValue) confidenceValue.textContent = `${data.confidence}%`;
    if (confidenceBarFill) confidenceBarFill.style.width = `${data.confidence}%`;
    if (breedCategory) breedCategory.textContent = data.category || '-';
    if (breedOrigin) breedOrigin.textContent = data.origin || '-';
}

function handleImagePreview(file, previewImage, previewText) {
    if (!file) {
        previewImage.style.display = 'none';
        previewText.style.display = 'block';
        previewText.textContent = 'No image selected yet.';
        return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
        previewImage.src = event.target.result;
        previewImage.style.display = 'block';
        previewText.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

function uploadPageLogic() {
    const imageInput = document.getElementById('imageInput');
    const dropZone = document.getElementById('dropZone');
    const predictButton = document.getElementById('predictButton');
    const resetButton = document.getElementById('resetButton');
    const previewImage = document.getElementById('previewImage');
    const previewText = document.querySelector('.preview-text');
    const resultSection = document.getElementById('resultSection');
    const confidenceBarFill = document.getElementById('confidenceBarFill');
    const confidenceValue = document.getElementById('confidenceValue');
    const breedCategory = document.getElementById('breedCategory');
    const breedOrigin = document.getElementById('breedOrigin');
    let selectedFile = null;

    const resetForm = () => {
        selectedFile = null;
        predictButton.disabled = true;
        previewImage.style.display = 'none';
        previewText.style.display = 'block';
        previewText.textContent = 'No image selected yet.';
        if (confidenceValue) confidenceValue.textContent = '0%';
        if (confidenceBarFill) confidenceBarFill.style.width = '0%';
        if (breedCategory) breedCategory.textContent = '-';
        if (breedOrigin) breedOrigin.textContent = '-';
        resultSection.innerHTML = `
            <div class="result-empty">
                <i class="fa-solid fa-chart-simple"></i>
                <p>Start a prediction to see the AI result summary here.</p>
            </div>`;
    };

    const handleFiles = (file) => {
        if (!file) return;
        selectedFile = file;
        handleImagePreview(file, previewImage, previewText);
        predictButton.disabled = false;
    };

    imageInput.addEventListener('change', (event) => handleFiles(event.target.files[0]));

    ['dragenter', 'dragover'].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (event) => {
        const file = event.dataTransfer.files[0];
        handleFiles(file);
    });

    dropZone.addEventListener('click', () => imageInput.click());
    resetButton.addEventListener('click', resetForm);

    predictButton.addEventListener('click', async () => {
        if (!selectedFile) return;
        showLoading(resultSection, 'Analyzing image...');

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('source', 'Upload');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                resultSection.innerHTML = `<div class="result-empty"><p>${data.error || 'Prediction failed.'}</p></div>`;
                return;
            }
            updateResultSummary(data);
            setTimeout(() => window.location.href = '/result', 700);
        } catch (error) {
            resultSection.innerHTML = `<div class="result-empty"><p>${error.message}</p></div>`;
        }
    });
}

function historyPageLogic() {
    const searchInput = document.getElementById('searchInput');
    const filterSelect = document.getElementById('filterSelect');
    const tableBody = document.querySelector('#historyTable tbody');
    if (!tableBody) return;
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    const filterRows = () => {
        const query = searchInput.value.toLowerCase();
        const source = filterSelect.value;

        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            const matchesQuery = query ? text.includes(query) : true;
            const matchesSource = source === 'all' ? true : text.includes(source.toLowerCase());
            row.style.display = matchesQuery && matchesSource ? '' : 'none';
        });
    };

    if (searchInput) searchInput.addEventListener('input', filterRows);
    if (filterSelect) filterSelect.addEventListener('change', filterRows);
}

function dashboardPageLogic() {
    const buildChart = (canvasId, type, labels, values, color) => {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: type === 'doughnut' ? 'Source count' : 'Breed count',
                    data: values,
                    borderColor: color,
                    backgroundColor: color.map((item) => item),
                    fill: type === 'line',
                    tension: 0.35,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: type === 'doughnut' ? {} : {
                    x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.08)' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.08)' }, beginAtZero: true }
                }
            }
        });
    };

    const breedChart = document.getElementById('breedChart');
    const sourceChart = document.getElementById('sourceChart');

    if (breedChart) {
        buildChart('breedChart', 'bar', JSON.parse(breedChart.dataset.labels), JSON.parse(breedChart.dataset.values), ['rgba(124,58,237,0.95)']);
    }

    if (sourceChart) {
        buildChart('sourceChart', 'doughnut', JSON.parse(sourceChart.dataset.labels), JSON.parse(sourceChart.dataset.values), ['rgba(37,99,235,0.9)', 'rgba(124,58,237,0.85)']);
    }
}

function cameraPageLogic() {
    const video = document.getElementById('cameraStream');
    const captureButton = document.getElementById('captureButton');
    const clearButton = document.getElementById('clearCamera');
    const cameraPreview = document.getElementById('cameraPreview');
    const previewText = document.querySelector('.camera-preview .preview-text');
    const cameraResultSection = document.getElementById('cameraResultSection');
    let stream = null;

    const startCamera = async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
        } catch (error) {
            cameraResultSection.innerHTML = `<div class="result-empty"><p>${error.message}</p></div>`;
        }
    };

    const resetPreview = () => {
        cameraPreview.src = '';
        cameraPreview.style.display = 'none';
        previewText.style.display = 'block';
        previewText.textContent = 'Capture an image to preview the detection result.';
        cameraResultSection.innerHTML = `<div class="result-empty"><i class="fa-solid fa-wave-square"></i><p>Captured predictions appear here.</p></div>`;
    };

    const submitCapture = async (blob) => {
        showLoading(cameraResultSection, 'Analyzing camera frame...');
        const formData = new FormData();
        formData.append('image', blob, 'camera-capture.png');
        formData.append('source', 'Camera');

        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            const data = await response.json();
            if (!response.ok) {
                cameraResultSection.innerHTML = `<div class="result-empty"><p>${data.error || 'Prediction failed.'}</p></div>`;
                return;
            }
            cameraPreview.src = URL.createObjectURL(blob);
            cameraPreview.style.display = 'block';
            previewText.style.display = 'none';
            cameraResultSection.innerHTML = `
                <div class="result-empty">
                    <i class="fa-solid fa-check-circle"></i>
                    <h3>${data.breed}</h3>
                    <p>${data.category} • ${data.origin}</p>
                    <p>${data.confidence}% confidence</p>
                </div>`;
        } catch (error) {
            cameraResultSection.innerHTML = `<div class="result-empty"><p>${error.message}</p></div>`;
        }
    };

    captureButton.addEventListener('click', () => {
        if (!stream) return;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
            if (blob) submitCapture(blob);
        }, 'image/png');
    });

    clearButton.addEventListener('click', resetPreview);
    startCamera();
}

if (page === 'detect') {
    uploadPageLogic();
}

if (page === 'history') {
    historyPageLogic();
}

if (page === 'dashboard') {
    dashboardPageLogic();
}

if (page === 'camera') {
    cameraPageLogic();
}
