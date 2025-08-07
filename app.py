import os
import logging
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image # Thư viện xử lý ảnh
import pytesseract # Thư viện OCR
from pdf2image import convert_from_path # Thư viện chuyển PDF sang ảnh
from docx import Document # Thư viện tạo file Word
import re
import shutil # Để xóa thư mục tạm thời

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Cấu hình thư mục lưu trữ file tạm thời
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
TEMP_IMAGES_FOLDER = 'temp_images' # Thư mục tạm để lưu ảnh từ PDF
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.config['TEMP_IMAGES_FOLDER'] = TEMP_IMAGES_FOLDER

# Tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
os.makedirs(TEMP_IMAGES_FOLDER, exist_ok=True)

# Hàm để chuyển đổi PDF dạng ảnh sang Word sử dụng OCR
# LƯU Ý QUAN TRỌNG:
# 1. Cần cài đặt Tesseract OCR Engine và Poppler trên hệ thống/máy chủ.
# 2. Độ chính xác của OCR phụ thuộc vào chất lượng ảnh PDF và độ phức tạp của font/bố cục.
# 3. Định dạng (căn lề, font, bảng biểu, hình ảnh) sẽ KHÔNG được giữ nguyên hoàn hảo.
#    Chỉ văn bản được nhận dạng sẽ được đưa vào file Word.
def pdf_image_to_word_ocr(pdf_path, docx_path):
    """
    Chuyển đổi file PDF dạng ảnh sang Word bằng cách sử dụng OCR.
    Trích xuất văn bản từ từng trang ảnh của PDF và đưa vào tài liệu Word.
    """
    try:
        logging.info(f"Bắt đầu chuyển đổi PDF dạng ảnh sang Word bằng OCR: {pdf_path}")
        
        # Sử dụng tạm thời một thư mục con trong TEMP_IMAGES_FOLDER cho mỗi lần chuyển đổi
        session_temp_dir = os.path.join(app.config['TEMP_IMAGES_FOLDER'], os.urandom(16).hex())
        os.makedirs(session_temp_dir, exist_ok=True)
        
        images = convert_from_path(pdf_path, output_folder=session_temp_dir, fmt='jpeg')
        logging.info(f"Đã chuyển đổi {len(images)} trang PDF thành hình ảnh.")

        document = Document()
        full_text = []

        # 2. Thực hiện OCR trên từng hình ảnh và thêm vào tài liệu Word
        for i, image in enumerate(images):
            logging.info(f"Đang xử lý OCR cho trang {i+1}...")
            # Sử dụng ngôn ngữ tiếng Việt cho Tesseract
            text = pytesseract.image_to_string(image, lang='vie')
            full_text.append(text)
            document.add_paragraph(text)
            logging.info(f"OCR trang {i+1} hoàn tất.")
        
        # 3. Lưu tài liệu Word
        document.save(docx_path)
        logging.info(f"Lưu tài liệu Word vào: {docx_path}")
        return True
    except pytesseract.TesseractNotFoundError:
        logging.error("Tesseract OCR engine không được tìm thấy. Vui lòng cài đặt Tesseract.")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi chuyển đổi PDF dạng ảnh sang Word cho {pdf_path}: {e}", exc_info=True)
        return False
    finally:
        # Dọn dẹp các file ảnh tạm thời
        if os.path.exists(session_temp_dir):
            try:
                shutil.rmtree(session_temp_dir)
                logging.info(f"Đã xóa thư mục ảnh tạm thời: {session_temp_dir}")
            except Exception as e:
                logging.error(f"Lỗi khi xóa thư mục ảnh tạm thời {session_temp_dir}: {e}", exc_info=True)

@app.route('/')
def index():
    logging.info("Truy cập trang chủ.")
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_pdf():
    logging.info("Nhận yêu cầu chuyển đổi PDF.")
    if 'pdf_file' not in request.files:
        logging.warning("Không có tệp nào được chọn trong yêu cầu.")
        return jsonify({'error': 'Không có tệp nào được chọn'}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        logging.warning("Tên tệp trống.")
        return jsonify({'error': 'Không có tệp nào được chọn'}), 400

    # Server-side file type validation
    if not file.filename.lower().endswith('.pdf'):
        logging.warning(f"Tệp không phải PDF: {file.filename}")
        return jsonify({'error': 'Tệp đã chọn không phải là PDF. Vui lòng chọn tệp PDF.'}), 400

    if file:
        original_filename = secure_filename(file.filename)
        base_filename = os.path.splitext(original_filename)[0]
        
        safe_base_filename = re.sub(r'[^\w\s-]', '', base_filename).strip()
        safe_base_filename = re.sub(r'[-\s]+', '-', safe_base_filename)
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        docx_filename = f"{safe_base_filename}_OCR.docx" # Thêm _OCR để phân biệt
        docx_path = os.path.join(app.config['CONVERTED_FOLDER'], docx_filename)

        try:
            logging.info(f"Lưu file PDF tải lên: {pdf_path}")
            file.save(pdf_path)
            
            # Gọi hàm chuyển đổi mới sử dụng OCR
            if pdf_image_to_word_ocr(pdf_path, docx_path):
                logging.info(f"Chuyển đổi thành công, file Word: {docx_filename}")
                return jsonify({
                    'message': 'Chuyển đổi thành công! (Lưu ý: Định dạng có thể thay đổi do OCR)',
                    'download_filename': docx_filename
                }), 200
            else:
                return jsonify({'error': 'Không thể chuyển đổi tệp PDF. Vui lòng kiểm tra file hoặc thử lại.'}), 500
        except pytesseract.TesseractNotFoundError:
            logging.error("Lỗi: Tesseract OCR Engine không được tìm thấy trên máy chủ. Vui lòng cài đặt Tesseract.")
            return jsonify({'error': 'Lỗi máy chủ: Tesseract OCR Engine chưa được cài đặt.'}), 500
        except Exception as e:
            logging.error(f"Lỗi xử lý file {original_filename}: {e}", exc_info=True)
            return jsonify({'error': f'Lỗi máy chủ nội bộ: {e}'}), 500
        finally:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    logging.info(f"Đã xóa file PDF tạm thời: {pdf_path}")
                except Exception as e:
                    logging.error(f"Lỗi khi xóa file PDF tạm thời {pdf_path}: {e}", exc_info=True)

@app.route('/download/<filename>')
def download_file(filename):
    logging.info(f"Yêu cầu tải file: {filename}")
    try:
        response = send_from_directory(app.config['CONVERTED_FOLDER'], filename, as_attachment=True)
        return response
    except FileNotFoundError:
        logging.warning(f"Không tìm thấy tệp để tải xuống: {filename}")
        return jsonify({'error': 'Không tìm thấy tệp hoặc tệp đã bị xóa.'}), 404
    except Exception as e:
        logging.error(f"Lỗi khi tải file {filename}: {e}", exc_info=True)
        return jsonify({'error': 'Lỗi máy chủ khi tải xuống tệp.'}), 500

if __name__ == '__main__':
    logging.info("Ứng dụng Flask đang chạy ở chế độ phát triển.")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
