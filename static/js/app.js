/**
 * ASCII Art Generator - Frontend Application
 */

document.addEventListener('DOMContentLoaded', () => {
    // ============== IMAGE TAB ELEMENTS ==============
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

    // ============== VIDEO TAB ELEMENTS ==============
    const videoDropZone = document.getElementById('videoDropZone');
    const videoInput = document.getElementById('videoInput');
    const videoInfo = document.getElementById('videoInfo');
    const videoPreview = document.getElementById('videoPreview');
    const clearVideoBtn = document.getElementById('clearVideo');
    const previewBtn = document.getElementById('previewBtn');
    const extractBtn = document.getElementById('extractBtn');
    const previewComparison = document.getElementById('previewComparison');
    const previewPlaceholder = document.getElementById('previewPlaceholder');
    const originalFrame = document.getElementById('originalFrame');
    const processedFrame = document.getElementById('processedFrame');

    // ============== BULK TAB ELEMENTS ==============
    const bulkDropZone = document.getElementById('bulkDropZone');
    const bulkInput = document.getElementById('bulkInput');
    const bulkInfo = document.getElementById('bulkInfo');
    const bulkPreview = document.getElementById('bulkPreview');
    const clearBulkBtn = document.getElementById('clearBulk');
    const bulkPreviewBtn = document.getElementById('bulkPreviewBtn');
    const bulkConvertBtn = document.getElementById('bulkConvertBtn');
    const bulkPreviewComparison = document.getElementById('bulkPreviewComparison');
    const bulkPreviewPlaceholder = document.getElementById('bulkPreviewPlaceholder');
    const bulkOriginalFrame = document.getElementById('bulkOriginalFrame');
    const bulkAsciiOutput = document.getElementById('bulkAsciiOutput');
    const bulkOutputActions = document.getElementById('bulkOutputActions');
    const bulkConverterList = document.getElementById('bulkConverterList');
    const bulkOptionsContainer = document.getElementById('bulkOptionsContainer');

    // State
    let selectedFile = null;
    let currentConverter = 'brightness';
    let currentAsciiArt = '';

    // Video state
    let videoPath = null;
    let videoMetadata = null;

    // Bulk state
    let bulkBatchId = null;
    let bulkFrameCount = 0;
    let bulkConverter = 'brightness';

    // Animation state
    let animationId = null;
    let animFrames = [];
    let animCurrentFrame = 0;
    let animInterval = null;
    let isPlaying = false;
    let animFps = 12;
    let exportedCode = {};

    // Initialize
    init();

    function init() {
        setupTabs();
        setupDropZone();
        setupConverterSelection();
        setupButtons();
        setupFontSize();
        loadConverterOptions(currentConverter);
        setupVideoTab();
        setupBulkTab();
        setupAnimationTab();
    }

    // ============== TAB NAVIGATION ==============
    function setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;

                // Update buttons
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Update content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${tabId}Tab`) {
                        content.classList.add('active');
                    }
                });
            });
        });
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

    // ============== VIDEO TAB ==============
    function setupVideoTab() {
        // Drop zone
        videoDropZone.addEventListener('click', () => videoInput.click());

        videoDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            videoDropZone.classList.add('drag-over');
        });

        videoDropZone.addEventListener('dragleave', () => {
            videoDropZone.classList.remove('drag-over');
        });

        videoDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            videoDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleVideoSelect(e.dataTransfer.files[0]);
            }
        });

        videoInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleVideoSelect(e.target.files[0]);
            }
        });

        clearVideoBtn.addEventListener('click', clearVideo);
        previewBtn.addEventListener('click', previewGreenScreen);
        extractBtn.addEventListener('click', extractFrames);

        // Range sliders live update
        setupRangeSlider('hueCenter');
        setupRangeSlider('hueTolerance');
        setupRangeSlider('saturationMin');
    }

    function setupRangeSlider(id) {
        const slider = document.getElementById(id);
        const display = document.getElementById(`${id}Value`);
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = slider.value;
            });
        }
    }

    async function handleVideoSelect(file) {
        if (!file.type.startsWith('video/')) {
            showToast('Please select a video file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('video', file);

        try {
            showToast('Uploading video...', 'success');

            const response = await fetch('/api/video/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Store video info
            videoPath = result.video_path;
            videoMetadata = result.info;

            // Update UI
            videoPreview.src = result.preview;
            document.getElementById('videoResolution').textContent =
                `${result.info.width}x${result.info.height}`;
            document.getElementById('videoDuration').textContent = result.info.duration;
            document.getElementById('videoFps').textContent = result.info.fps.toFixed(1);
            document.getElementById('videoFrames').textContent = result.info.frame_count;

            videoDropZone.hidden = true;
            videoInfo.hidden = false;
            previewBtn.disabled = false;
            extractBtn.disabled = false;

            showToast('Video uploaded successfully!', 'success');

        } catch (error) {
            console.error('Video upload error:', error);
            showToast(error.message || 'Failed to upload video', 'error');
        }
    }

    async function clearVideo() {
        if (videoPath) {
            try {
                await fetch('/api/video/cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ video_path: videoPath })
                });
            } catch (e) {
                console.error('Cleanup error:', e);
            }
        }

        videoPath = null;
        videoMetadata = null;
        videoInput.value = '';
        videoPreview.src = '';
        videoDropZone.hidden = false;
        videoInfo.hidden = true;
        previewBtn.disabled = true;
        extractBtn.disabled = true;
        previewComparison.hidden = true;
        previewPlaceholder.hidden = false;
    }

    function getGreenScreenSettings() {
        return {
            hue_center: parseInt(document.getElementById('hueCenter').value),
            hue_tolerance: parseInt(document.getElementById('hueTolerance').value),
            saturation_min: parseInt(document.getElementById('saturationMin').value),
            value_min: 40,
            background: document.getElementById('bgReplacement').value
        };
    }

    async function previewGreenScreen() {
        if (!videoPath) return;

        previewBtn.disabled = true;
        previewBtn.textContent = 'Processing...';

        try {
            const settings = getGreenScreenSettings();
            const middleFrame = Math.floor(videoMetadata.frame_count / 2);

            const response = await fetch('/api/video/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_path: videoPath,
                    frame_number: middleFrame,
                    ...settings
                })
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Show comparison
            originalFrame.src = result.original;
            processedFrame.src = result.processed;
            previewPlaceholder.hidden = true;
            previewComparison.hidden = false;

            if (result.has_green_screen) {
                showToast('Green screen detected!', 'success');
            } else {
                showToast('No green screen detected in this frame', 'error');
            }

        } catch (error) {
            console.error('Preview error:', error);
            showToast(error.message || 'Preview failed', 'error');
        } finally {
            previewBtn.disabled = false;
            previewBtn.textContent = 'Preview Frame';
        }
    }

    async function extractFrames() {
        if (!videoPath) return;

        const btnText = extractBtn.querySelector('.btn-text');
        const btnLoading = extractBtn.querySelector('.btn-loading');
        btnText.hidden = true;
        btnLoading.hidden = false;
        extractBtn.disabled = true;

        try {
            const settings = getGreenScreenSettings();
            const targetFps = parseInt(document.getElementById('targetFps').value) || 12;
            const maxFrames = document.getElementById('maxFrames').value;

            const requestBody = {
                video_path: videoPath,
                fps: targetFps,
                ...settings
            };

            if (maxFrames) {
                requestBody.max_frames = parseInt(maxFrames);
            }

            const response = await fetch('/api/video/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Extraction failed');
            }

            // Download the ZIP file
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'frames.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('Frames extracted and downloaded!', 'success');

        } catch (error) {
            console.error('Extraction error:', error);
            showToast(error.message || 'Extraction failed', 'error');
        } finally {
            btnText.hidden = false;
            btnLoading.hidden = true;
            extractBtn.disabled = false;
        }
    }

    // ============== BULK CONVERT TAB ==============
    function setupBulkTab() {
        // Drop zone
        bulkDropZone.addEventListener('click', () => bulkInput.click());

        bulkDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            bulkDropZone.classList.add('drag-over');
        });

        bulkDropZone.addEventListener('dragleave', () => {
            bulkDropZone.classList.remove('drag-over');
        });

        bulkDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            bulkDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleBulkUpload(e.dataTransfer.files[0]);
            }
        });

        bulkInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleBulkUpload(e.target.files[0]);
            }
        });

        clearBulkBtn.addEventListener('click', clearBulk);
        bulkPreviewBtn.addEventListener('click', previewBulkFrame);
        bulkConvertBtn.addEventListener('click', convertBulkFrames);

        // Converter selection for bulk
        const radios = bulkConverterList.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                bulkConverter = e.target.value;
                loadBulkConverterOptions(bulkConverter);
            });
        });

        // Load initial options
        loadBulkConverterOptions(bulkConverter);

        // Font size slider
        const bulkFontSizeSlider = document.getElementById('bulkFontSizeSlider');
        const bulkFontSizeValue = document.getElementById('bulkFontSizeValue');
        bulkFontSizeSlider.addEventListener('input', () => {
            const size = bulkFontSizeSlider.value;
            bulkFontSizeValue.textContent = `${size}px`;
            bulkAsciiOutput.style.fontSize = `${size}px`;
        });
    }

    async function loadBulkConverterOptions(converterId) {
        try {
            const response = await fetch(`/api/convert/${converterId}/options`);
            const options = await response.json();
            renderBulkOptions(options);
        } catch (error) {
            console.error('Error loading options:', error);
            bulkOptionsContainer.innerHTML = '<p style="color: var(--text-secondary)">Error loading options</p>';
        }
    }

    function renderBulkOptions(options) {
        bulkOptionsContainer.innerHTML = '';

        for (const [key, config] of Object.entries(options)) {
            const group = document.createElement('div');
            group.className = 'option-group';

            if (config.type === 'number') {
                group.innerHTML = `
                    <label for="bulk_${key}">${config.label}</label>
                    <input type="number" id="bulk_${key}" name="${key}"
                           value="${config.default}"
                           min="${config.min}" max="${config.max}">
                `;
            } else if (config.type === 'range') {
                group.innerHTML = `
                    <label for="bulk_${key}">${config.label}</label>
                    <input type="range" id="bulk_${key}" name="${key}"
                           value="${config.default}"
                           min="${config.min}" max="${config.max}" step="${config.step}">
                    <span class="range-value" id="bulk_${key}Value">${config.default}</span>
                `;
                setTimeout(() => {
                    const range = document.getElementById(`bulk_${key}`);
                    const display = document.getElementById(`bulk_${key}Value`);
                    range?.addEventListener('input', () => {
                        display.textContent = range.value;
                    });
                }, 0);
            } else if (config.type === 'checkbox') {
                group.innerHTML = `
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="bulk_${key}" name="${key}"
                               ${config.default ? 'checked' : ''}>
                        <label for="bulk_${key}">${config.label}</label>
                    </div>
                `;
            } else if (config.type === 'select') {
                const optionsHtml = config.options
                    .map(opt => `<option value="${opt.value}" ${opt.value === config.default ? 'selected' : ''}>${opt.label}</option>`)
                    .join('');
                group.innerHTML = `
                    <label for="bulk_${key}">${config.label}</label>
                    <select id="bulk_${key}" name="${key}">${optionsHtml}</select>
                `;
            }

            bulkOptionsContainer.appendChild(group);
        }
    }

    async function handleBulkUpload(file) {
        if (!file.name.toLowerCase().endsWith('.zip')) {
            showToast('Please upload a ZIP file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('frames_zip', file);

        try {
            showToast('Uploading frames...', 'success');

            const response = await fetch('/api/bulk/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Store batch info
            bulkBatchId = result.batch_id;
            bulkFrameCount = result.frame_count;

            // Update UI
            bulkPreview.src = result.preview;
            document.getElementById('bulkFrameCount').textContent = result.frame_count;

            // Show first few filenames
            const fileList = result.frames.slice(0, 3).join(', ');
            const suffix = result.frames.length > 3 ? `, ... (+${result.frames.length - 3} more)` : '';
            document.getElementById('bulkFileList').textContent = fileList + suffix;

            bulkDropZone.hidden = true;
            bulkInfo.hidden = false;
            bulkPreviewBtn.disabled = false;
            bulkConvertBtn.disabled = false;

            showToast(`Uploaded ${result.frame_count} frames!`, 'success');

        } catch (error) {
            console.error('Bulk upload error:', error);
            showToast(error.message || 'Failed to upload frames', 'error');
        }
    }

    async function clearBulk() {
        if (bulkBatchId) {
            try {
                await fetch('/api/bulk/cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ batch_id: bulkBatchId })
                });
            } catch (e) {
                console.error('Cleanup error:', e);
            }
        }

        bulkBatchId = null;
        bulkFrameCount = 0;
        bulkInput.value = '';
        bulkPreview.src = '';
        bulkDropZone.hidden = false;
        bulkInfo.hidden = true;
        bulkPreviewBtn.disabled = true;
        bulkConvertBtn.disabled = true;
        bulkPreviewComparison.hidden = true;
        bulkPreviewPlaceholder.hidden = false;
        bulkOutputActions.hidden = true;
    }

    function getBulkOptions() {
        const options = {
            converter: bulkConverter,
            batch_id: bulkBatchId
        };

        const inputs = bulkOptionsContainer.querySelectorAll('input, select');
        inputs.forEach(input => {
            const name = input.name;
            if (input.type === 'checkbox') {
                options[name] = input.checked;
            } else if (input.type === 'number' || input.type === 'range') {
                options[name] = parseFloat(input.value);
            } else {
                options[name] = input.value;
            }
        });

        return options;
    }

    async function previewBulkFrame() {
        if (!bulkBatchId) return;

        bulkPreviewBtn.disabled = true;
        bulkPreviewBtn.textContent = 'Processing...';

        try {
            const options = getBulkOptions();
            options.frame_index = 0;

            const response = await fetch('/api/bulk/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(options)
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Show comparison
            bulkOriginalFrame.src = result.original;
            bulkAsciiOutput.textContent = result.ascii_art;
            bulkPreviewPlaceholder.hidden = true;
            bulkPreviewComparison.hidden = false;
            bulkOutputActions.hidden = false;

            showToast(`Preview of ${result.filename}`, 'success');

        } catch (error) {
            console.error('Preview error:', error);
            showToast(error.message || 'Preview failed', 'error');
        } finally {
            bulkPreviewBtn.disabled = false;
            bulkPreviewBtn.textContent = 'Preview First Frame';
        }
    }

    async function convertBulkFrames() {
        if (!bulkBatchId) return;

        const btnText = bulkConvertBtn.querySelector('.btn-text');
        const btnLoading = bulkConvertBtn.querySelector('.btn-loading');
        btnText.hidden = true;
        btnLoading.hidden = false;
        bulkConvertBtn.disabled = true;

        try {
            const options = getBulkOptions();

            const response = await fetch('/api/bulk/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(options)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Conversion failed');
            }

            // Download the ZIP file
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ascii_frames.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast(`Converted ${bulkFrameCount} frames!`, 'success');

        } catch (error) {
            console.error('Conversion error:', error);
            showToast(error.message || 'Conversion failed', 'error');
        } finally {
            btnText.hidden = false;
            btnLoading.hidden = true;
            bulkConvertBtn.disabled = false;
        }
    }

    // ============== ANIMATION PLAYER TAB ==============
    function setupAnimationTab() {
        const animDropZone = document.getElementById('animDropZone');
        const animInput = document.getElementById('animInput');
        const animInfo = document.getElementById('animInfo');
        const clearAnimBtn = document.getElementById('clearAnim');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        const animAsciiOutput = document.getElementById('animAsciiOutput');
        const animationDisplay = document.getElementById('animationDisplay');
        const animPlaceholder = document.getElementById('animPlaceholder');
        const frameInfo = document.getElementById('frameInfo');
        const animFpsSlider = document.getElementById('animFps');
        const animFpsValue = document.getElementById('animFpsValue');
        const animFontSizeSlider = document.getElementById('animFontSize');
        const animFontSizeValue = document.getElementById('animFontSizeValue');

        // Export buttons
        const exportHtmlBtn = document.getElementById('exportHtmlBtn');
        const exportReactBtn = document.getElementById('exportReactBtn');
        const exportPythonBtn = document.getElementById('exportPythonBtn');
        const exportPygameBtn = document.getElementById('exportPygameBtn');

        // Modal elements
        const codeModal = document.getElementById('codeModal');
        const modalTitle = document.getElementById('modalTitle');
        const codeOutput = document.getElementById('codeOutput');
        const closeModalBtn = document.getElementById('closeModal');
        const copyCodeBtn = document.getElementById('copyCodeBtn');
        const downloadCodeBtn = document.getElementById('downloadCodeBtn');

        let currentCodeType = '';

        // Drop zone setup
        animDropZone.addEventListener('click', () => animInput.click());

        animDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            animDropZone.classList.add('drag-over');
        });

        animDropZone.addEventListener('dragleave', () => {
            animDropZone.classList.remove('drag-over');
        });

        animDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            animDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleAnimUpload(e.dataTransfer.files[0]);
            }
        });

        animInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleAnimUpload(e.target.files[0]);
            }
        });

        // Controls
        clearAnimBtn.addEventListener('click', clearAnimation);
        playPauseBtn.addEventListener('click', togglePlayPause);
        stopBtn.addEventListener('click', stopAnimation);

        // FPS slider
        animFpsSlider.addEventListener('input', () => {
            animFps = parseInt(animFpsSlider.value);
            animFpsValue.textContent = animFps;
            if (isPlaying) {
                // Restart with new FPS
                clearInterval(animInterval);
                animInterval = setInterval(advanceFrame, 1000 / animFps);
            }
        });

        // Font size slider
        animFontSizeSlider.addEventListener('input', () => {
            const size = animFontSizeSlider.value;
            animFontSizeValue.textContent = `${size}px`;
            animAsciiOutput.style.fontSize = `${size}px`;
        });

        // Export buttons
        exportHtmlBtn.addEventListener('click', () => showExportModal('html', 'HTML/JavaScript'));
        exportReactBtn.addEventListener('click', () => showExportModal('react', 'React Component'));
        exportPythonBtn.addEventListener('click', () => showExportModal('python', 'Python (Terminal)'));
        exportPygameBtn.addEventListener('click', () => showExportModal('pygame', 'Pygame'));

        // Modal controls
        closeModalBtn.addEventListener('click', () => codeModal.hidden = true);
        codeModal.addEventListener('click', (e) => {
            if (e.target === codeModal) codeModal.hidden = true;
        });
        copyCodeBtn.addEventListener('click', copyExportedCode);
        downloadCodeBtn.addEventListener('click', downloadExportedCode);

        async function handleAnimUpload(file) {
            if (!file.name.toLowerCase().endsWith('.zip')) {
                showToast('Please upload a ZIP file', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('ascii_zip', file);

            try {
                showToast('Uploading ASCII frames...', 'success');

                const response = await fetch('/api/animation/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.error) {
                    throw new Error(result.error);
                }

                // Store animation info
                animationId = result.animation_id;
                animFrames = result.frames;
                animCurrentFrame = 0;

                // Update UI
                document.getElementById('animFrameCount').textContent = result.frame_count;
                document.getElementById('animDimensions').textContent =
                    `${result.dimensions.width} × ${result.dimensions.height} chars`;
                document.getElementById('totalFrameNum').textContent = result.frame_count;
                document.getElementById('currentFrameNum').textContent = '1';

                animDropZone.hidden = true;
                animInfo.hidden = false;
                animPlaceholder.hidden = true;
                animationDisplay.classList.add('active');
                frameInfo.hidden = false;

                // Show first frame
                animAsciiOutput.textContent = animFrames[0].content;

                // Enable controls
                playPauseBtn.disabled = false;
                stopBtn.disabled = false;
                exportHtmlBtn.disabled = false;
                exportReactBtn.disabled = false;
                exportPythonBtn.disabled = false;
                exportPygameBtn.disabled = false;

                // Generate export code
                await generateExportCode();

                showToast(`Loaded ${result.frame_count} frames!`, 'success');

            } catch (error) {
                console.error('Animation upload error:', error);
                showToast(error.message || 'Failed to upload animation', 'error');
            }
        }

        async function generateExportCode() {
            try {
                const response = await fetch('/api/animation/export-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        frames: animFrames,
                        fps: animFps
                    })
                });

                const result = await response.json();
                if (result.success) {
                    exportedCode = result.code;
                }
            } catch (error) {
                console.error('Error generating export code:', error);
            }
        }

        function togglePlayPause() {
            if (isPlaying) {
                pauseAnimation();
            } else {
                playAnimation();
            }
        }

        function playAnimation() {
            if (animFrames.length === 0) return;

            isPlaying = true;
            document.getElementById('playIcon').textContent = '⏸ Pause';
            animInterval = setInterval(advanceFrame, 1000 / animFps);
        }

        function pauseAnimation() {
            isPlaying = false;
            document.getElementById('playIcon').textContent = '▶ Play';
            if (animInterval) {
                clearInterval(animInterval);
                animInterval = null;
            }
        }

        function stopAnimation() {
            pauseAnimation();
            animCurrentFrame = 0;
            if (animFrames.length > 0) {
                animAsciiOutput.textContent = animFrames[0].content;
                document.getElementById('currentFrameNum').textContent = '1';
            }
        }

        function advanceFrame() {
            animCurrentFrame = (animCurrentFrame + 1) % animFrames.length;
            animAsciiOutput.textContent = animFrames[animCurrentFrame].content;
            document.getElementById('currentFrameNum').textContent = animCurrentFrame + 1;
        }

        async function clearAnimation() {
            pauseAnimation();

            if (animationId) {
                try {
                    await fetch('/api/animation/cleanup', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ animation_id: animationId })
                    });
                } catch (e) {
                    console.error('Cleanup error:', e);
                }
            }

            animationId = null;
            animFrames = [];
            animCurrentFrame = 0;
            exportedCode = {};

            animInput.value = '';
            animDropZone.hidden = false;
            animInfo.hidden = true;
            animPlaceholder.hidden = false;
            animationDisplay.classList.remove('active');
            frameInfo.hidden = true;
            animAsciiOutput.textContent = '';

            playPauseBtn.disabled = true;
            stopBtn.disabled = true;
            exportHtmlBtn.disabled = true;
            exportReactBtn.disabled = true;
            exportPythonBtn.disabled = true;
            exportPygameBtn.disabled = true;
        }

        function showExportModal(codeType, title) {
            currentCodeType = codeType;
            modalTitle.textContent = `Export: ${title}`;
            codeOutput.textContent = exportedCode[codeType] || 'Loading...';
            codeModal.hidden = false;
        }

        function copyExportedCode() {
            const code = exportedCode[currentCodeType];
            if (!code) return;

            navigator.clipboard.writeText(code)
                .then(() => showToast('Code copied to clipboard!', 'success'))
                .catch(() => showToast('Failed to copy', 'error'));
        }

        function downloadExportedCode() {
            const code = exportedCode[currentCodeType];
            if (!code) return;

            const extensions = {
                'html': 'html',
                'react': 'jsx',
                'python': 'py',
                'pygame': 'py'
            };

            const ext = extensions[currentCodeType] || 'txt';
            const filename = `ascii_animation.${ext}`;

            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast(`Downloaded ${filename}!`, 'success');
        }
    }
});
