# Sử dụng một image Python chính thức làm base image
FROM python:3.9-slim-buster

# Đặt biến môi trường để Python không tạo file .pyc và output buffer không bị chặn
ENV PYTHONUNBUFFERED 1

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các dependencies đã liệt kê trong requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Tesseract OCR Engine và Poppler
# Tách việc cập nhật kho lưu trữ và cài đặt gói thành các bước riêng biệt
# để dễ dàng hơn trong việc tìm lỗi.
RUN apt-get update -y && apt-get install -y apt-transport-https ca-certificates curl gnupg
RUN apt-get update -y

# Cài đặt các gói cần thiết với --no-install-recommends để tránh các gói không cần thiết.
RUN apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libpoppler-dev \
    && rm -rf /var/lib/apt/lists/*

# Đặt biến môi trường cho Poppler để pdf2image có thể tìm thấy nó
ENV POPPLER_PATH /usr/bin

# Sao chép toàn bộ mã nguồn của ứng dụng vào thư mục làm việc
COPY . .

# Mở cổng mà ứng dụng sẽ lắng nghe (cổng mặc định của Flask/Gunicorn)
EXPOSE 5000

# Lệnh để chạy ứng dụng khi container khởi động
# Sử dụng Gunicorn để phục vụ ứng dụng Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
