const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const overlay = document.getElementById('overlay');
const progress = document.getElementById('progress');
const resultDiv = document.getElementById('result');

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Load the image preview
    const imageURL = URL.createObjectURL(file);
    preview.src = imageURL;

    // Wait for image to load fully before proceeding
    preview.onload = async () => {
        // Set canvas size to match the displayed image size
        overlay.width = preview.naturalWidth;
        overlay.height = preview.naturalHeight;

        const formData = new FormData();
        formData.append('file', file);

        progress.style.display = 'block';
        resultDiv.innerHTML = '';
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);

        try {
            const response = await fetch('/scan', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.success) {
                let resultHTML = `<h3>Found ${data.count} barcode(s)</h3><div class="results-container">`;

                data.items.forEach((item, index) => {
                    const loc = item.location;

                    // Scale coordinates from original image to displayed image
                    const x1 = loc.x1;
                    const y1 = loc.y1;
                    const x2 = loc.x2;
                    const y2 = loc.y2;
                    const x3 = loc.x3;
                    const y3 = loc.y3;
                    const x4 = loc.x4;
                    const y4 = loc.y4;

                    // Draw the polygon
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.lineTo(x3, y3);
                    ctx.lineTo(x4, y4);
                    ctx.closePath();
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = 'red';
                    ctx.stroke();

                    // Draw the text near first point
                    ctx.font = '16px Arial';
                    ctx.fillStyle = 'blue';
                    ctx.fillText(item.text, x1 + 5, y1 - 5);

                    resultHTML += `
                        <div class="barcode-result">
                            <h4>Barcode #${index + 1}</h4>
                            <p><strong>Type:</strong> ${item.format}</p>
                            <p><strong>Content:</strong> ${item.text}</p>
                        </div>
                    `;
                });

                resultHTML += `</div>`;
                resultDiv.innerHTML = resultHTML;
            } else {
                resultDiv.innerHTML = `Error: ${data.error}`;
            }
        } catch (err) {
            resultDiv.innerHTML = 'Request failed';
        } finally {
            progress.style.display = 'none';
        }
    };
});