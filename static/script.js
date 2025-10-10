// -------- Image --------
async function uploadImage() {
  const input = document.getElementById("imageInput");
  if (!input.files[0]) return alert("Please upload an image.");

  const formData = new FormData();
  formData.append("image", input.files[0]);

  try {
    const res = await fetch("/upload_image", { method: "POST", body: formData });
    const data = await res.json();
    if (data.error) return alert(data.error);

    document.getElementById("imageResult").innerHTML =
      `<img src="${data.url}?t=${Date.now()}">`;
  } catch(e) {
    console.error(e);
    alert("Upload failed");
  }
}

// -------- Video --------
async function uploadVideo() {
  const input = document.getElementById("videoInput");
  if (!input.files[0]) return alert("Please upload a video.");

  const formData = new FormData();
  formData.append("video", input.files[0]);

  try {
    const res = await fetch("/upload_video", { method: "POST", body: formData });
    const data = await res.json();
    if (data.error) return alert(data.error);

    document.getElementById("videoResult").innerHTML =
      `<video controls src="${data.url}?t=${Date.now()}"></video>`;
  } catch(e) {
    console.error(e);
    alert("Upload failed");
  }
}

//directory

async function uploadDirectory() {
  const input = document.getElementById("dirInput");
  if (!input.files.length) return alert("Please select images.");

  const formData = new FormData();
  for (const file of input.files) {
    formData.append("images", file);
  }

  try {
    const res = await fetch("/upload_directory", { method: "POST", body: formData });
    const data = await res.json();

    if (data.error) return alert(data.error);

    const container = document.getElementById("dirResults");
    container.innerHTML = ""; // پاک کردن خروجی قبلی

    data.results.forEach(item => {
      const div = document.createElement("div");
      div.classList.add("image-card");
      div.innerHTML = `
        <img src="/outputs/${data.output_dir}/${item.filename}?t=${Date.now()}" width="200">
        <p>Labels: ${item.labels.join(", ")}</p>
      `;
      container.appendChild(div);
    });

  } catch(e) {
    console.error(e);
    alert("Upload failed");
  }
}



// -------- Webcam --------
let webcamInterval = null;

async function startWebcam() {
  const video = document.getElementById("webcam");
  const canvas = document.getElementById("canvas");
  const output = document.getElementById("outputFrame");

  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  video.srcObject = stream;

  webcamInterval = setInterval(async () => {
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const frame = canvas.toDataURL("image/jpeg");

    try {
      const res = await fetch("/webcam_frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame }),
      });
      const data = await res.json();
      if (data.error) return console.error(data.error);
      output.src = data.frame;
    } catch(e) {
      console.error(e);
    }
  }, 300);
}

function stopWebcam() {
  clearInterval(webcamInterval);
  const video = document.getElementById("webcam");
  if (video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
  }
}
