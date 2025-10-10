from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from ultralytics import YOLO
import cv2, os, numpy as np, base64, subprocess
from PIL import Image



app = Flask(__name__, static_folder="static", template_folder="templates")
os.makedirs("outputs", exist_ok=True)
model = YOLO("model/best.pt")

MAX_VIDEO_MB = 20
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

@app.route("/")
def index():
    return render_template("index.html")

# ---------- Image Upload ----------
@app.route("/upload_image", methods=["POST"])
def upload_image():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "No image uploaded"}), 400
    path = os.path.join("outputs", "processed_image.jpg")
    file.save(path)
    results = model(path)
    cv2.imwrite(path, results[0].plot())
    return jsonify({"url": f"/outputs/processed_image.jpg"})

# ---------- Video Upload ----------
@app.route("/upload_video", methods=["POST"])
def upload_video():
    try:
        file = request.files.get("video")
        if not file:
            return jsonify({"error": "No video uploaded"}), 400

        # محدودیت حجم
        size_mb = len(file.read()) / (1024*1024)
        file.seek(0)
        if size_mb > MAX_VIDEO_MB:
            return jsonify({"error": f"Video too large ({size_mb:.2f} MB). Max is {MAX_VIDEO_MB} MB."}), 400

        filename = file.filename
        input_path = os.path.join("outputs", filename)
        output_path = os.path.join("outputs", f"processed_{filename}")
        file.save(input_path)

        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # از codec مناسب مرورگر استفاده می‌کنیم
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            frame_out = results[0].plot()  # RGB
            frame_bgr = cv2.cvtColor(frame_out, cv2.COLOR_RGB2BGR)  # تبدیل به BGR
            out.write(frame_bgr)

        cap.release()
        out.release()


        return jsonify({"url": f"/outputs/processed_{filename}"})
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # نمایش کامل stacktrace در کنسول
        return jsonify({"error": str(e)}), 500

# -----------directory_upload--------------
@app.route("/upload_directory", methods=["POST"])
def upload_directory():
    files = request.files.getlist("images")
    if not files:
        return "No images uploaded", 400

    output_dir = "dir_results"
    folder_path = os.path.join("outputs", output_dir)
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        # read image bytes from upload
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # run YOLO
        results = model(img)
        frame_out = results[0].plot()  # RGB or BGR depending on version

        # convert to RGB if needed and save
        frame_out = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_out)
        out_path = os.path.join(folder_path, f"processed_{file.filename}")
        pil_img.save(out_path)
    return redirect(url_for("gallery", output_dir=output_dir))


#----------gallery_route-------------
@app.route("/gallery")
def gallery():
    output_dir = request.args.get("output_dir", "dir_results")
    folder_path = os.path.join("outputs", output_dir)
    if not os.path.exists(folder_path):
        return "Folder not found", 404

    # فقط تصاویر خروجی مدل
    images = sorted(os.listdir(folder_path))
    images = [img for img in images
              if img.lower().endswith((".jpg", ".jpeg", ".png"))
              and img.startswith("processed_")]

    return render_template("gallery.html", images=images, folder=output_dir)


# ---------- Serve Outputs ----------
@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory("outputs", filename)



# ---------- Webcam Frame ----------
@app.route("/webcam_frame", methods=["POST"])
def webcam_frame():
    data = request.json.get("frame")
    if not data:
        return jsonify({"error": "No frame received"}), 400
    img_data = base64.b64decode(data.split(",")[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    results = model(frame)
    frame_out = results[0].plot()
    _, buffer = cv2.imencode(".jpg", frame_out)
    jpg_as_text = base64.b64encode(buffer).decode("utf-8")
    return jsonify({"frame": f"data:image/jpeg;base64,{jpg_as_text}"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=7860)
