# Sử dụng một image Python 3.9 dựa trên Debian Bullseye mới hơn
FROM python:3.9-slim-bullseye

# Cấu hình môi trường non-interactive để tránh các yêu cầu nhập liệu
ENV DEBIAN_FRONTEND=noninteractive

# Đặt biến môi trường để Python không tạo file .pyc và output buffer không bị chặn
ENV PYTHONUNBUFFERED 1

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các dependencies đã liệt kê trong requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Hợp nhất tất cả các lệnh cài đặt gói hệ thống vào một RUN duy nhất
# để tăng tính ổn định và tránh lỗi cache giữa các layer.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libpoppler-dev \
    && apt-get clean \
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
