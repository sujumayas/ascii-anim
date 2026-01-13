/**
 * ASCII Art Generator - Frontend Application
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('dropZone');
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewContainer = document.getElementById('previewContainer');
    const clearImageBtn = document.getElementById('clearImage');
    const converterList = document.getElementById('converterList');
    const optionsContainer = document.getElementById('optionsContainer');
    const convertBtn = document.getElementById('convertBtn');
    const asciiOutput = document.getElementById('asciiOutput');
    const outputActions = document.getElementById('outputActions');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const fontSizeSlider = document.getElementById('fontSizeSlider');
    const fontSizeValue = document.getElementById('fontSizeValue');

    // State
    let selectedFile = null;
    let currentConverter = 'brightness';
    let currentAsciiArt = '';

    // Initialize
    init();

    function init() {
        setupDropZone();
        setupConverterSelection();
        setupButtons();
        setupFontSize();
        loadConverterOptions(currentConverter);
    }

    // Drop Zone Setup
    function setupDropZone() {
        dropZone.addEventListener('click', () => imageInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        clearImageBtn.addEventListener('click', clearImage);
    }

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Please select an image file', 'error');
            return;
        }

        selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            dropZone.hidden = true;
            previewContainer.hidden = false;
            convertBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function clearImage() {
        selectedFile = null;
        imageInput.value = '';
        imagePreview.src = '';
        dropZone.hidden = false;
        previewContainer.hidden = true;
        convertBtn.disabled = true;
    }

    // Converter Selection
    function setupConverterSelection() {
        const radios = converterList.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                currentConverter = e.target.value;
                loadConverterOptions(currentConverter);
            });
        });
    }

    async function loadConverterOptions(converterId) {
        try {
            const response = await fetch(`/api/convert/${converterId}/options`);
            const options = await response.json();
            renderOptions(options);
        } catch (error) {
            console.error('Error loading options:', error);
            optionsContainer.innerHTML = '<p style="color: var(--text-secondary)">Error loading options</p>';
        }
    }

    function renderOptions(options) {
        optionsContainer.innerHTML = '';

        for (const [key, config] of Object.entries(options)) {
            const group = document.createElement('div');
            group.className = 'option-group';

            if (config.type === 'number') {
                group.innerHTML = `
                    <label for="${key}">${config.label}</label>
                    <input type="number" id="${key}" name="${key}"
                           value="${config.default}"
                           min="${config.min}" max="${config.max}">
                `;
            } else if (config.type === 'range') {
                group.innerHTML = `
                    <label for="${key}">${config.label}</label>
                    <input type="range" id="${key}" name="${key}"
                           value="${config.default}"
                           min="${config.min}" max="${config.max}" step="${config.step}">
                    <span class="range-value" id="${key}Value">${config.default}</span>
                `;
                // Add live update
                setTimeout(() => {
                    const range = document.getElementById(key);
                    const display = document.getElementById(`${key}Value`);
                    range?.addEventListener('input', () => {
                        display.textContent = range.value;
                    });
                }, 0);
            } else if (config.type === 'checkbox') {
                group.innerHTML = `
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="${key}" name="${key}"
                               ${config.default ? 'checked' : ''}>
                        <label for="${key}">${config.label}</label>
                    </div>
                `;
            } else if (config.type === 'select') {
                const optionsHtml = config.options
                    .map(opt => `<option value="${opt.value}" ${opt.value === config.default ? 'selected' : ''}>${opt.label}</option>`)
                    .join('');
                group.innerHTML = `
                    <label for="${key}">${config.label}</label>
                    <select id="${key}" name="${key}">${optionsHtml}</select>
                `;
            }

            optionsContainer.appendChild(group);
        }
    }

    // Buttons
    function setupButtons() {
        convertBtn.addEventListener('click', convertImage);
        copyBtn.addEventListener('click', copyToClipboard);
        downloadBtn.addEventListener('click', downloadAscii);
    }

    async function convertImage() {
        if (!selectedFile) {
            showToast('Please select an image first', 'error');
            return;
        }

        // Show loading state
        const btnText = convertBtn.querySelector('.btn-text');
        const btnLoading = convertBtn.querySelector('.btn-loading');
        btnText.hidden = true;
        btnLoading.hidden = false;
        convertBtn.disabled = true;

        try {
            // Build form data
            const formData = new FormData();
            formData.append('image', selectedFile);
            formData.append('converter', currentConverter);

            // Add all options
            const inputs = optionsContainer.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    formData.append(input.name, input.checked);
                } else {
                    formData.append(input.name, input.value);
                }
            });

            // Make request
            const response = await fetch('/api/convert', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Display result
            currentAsciiArt = result.ascii_art;
            asciiOutput.textContent = currentAsciiArt;
            outputActions.hidden = false;

            showToast('Conversion complete!', 'success');

        } catch (error) {
            console.error('Conversion error:', error);
            showToast(error.message || 'Conversion failed', 'error');
        } finally {
            btnText.hidden = false;
            btnLoading.hidden = true;
            convertBtn.disabled = false;
        }
    }

    function copyToClipboard() {
        if (!currentAsciiArt) return;

        navigator.clipboard.writeText(currentAsciiArt)
            .then(() => showToast('Copied to clipboard!', 'success'))
            .catch(() => showToast('Failed to copy', 'error'));
    }

    function downloadAscii() {
        if (!currentAsciiArt) return;

        const blob = new Blob([currentAsciiArt], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ascii-art.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast('Downloaded!', 'success');
    }

    // Font Size
    function setupFontSize() {
        fontSizeSlider.addEventListener('input', () => {
            const size = fontSizeSlider.value;
            fontSizeValue.textContent = `${size}px`;
            asciiOutput.style.fontSize = `${size}px`;
        });
    }

    // Toast Notifications
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
