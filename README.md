# Hệ Thống Quản Lý Trung Tâm Sửa Chữa Xe

Nền tảng quản trị toàn diện dành cho **trung tâm sửa chữa xe**, tích hợp **E-commerce** và hệ thống theo dõi trạng thái dịch vụ

---

## Giới thiệu

Hệ thống giúp:
- Quản lý toàn bộ quy trình sửa chữa xe  
- Bán phụ tùng trực tuyến  
- Theo dõi trạng thái sửa chữa
- Thanh toán online (Momo, VNPAY)
- Quản lý nhân sự, kho và doanh thu

---

## Các tính năng chính

### Phân hệ Khách hàng

- **Thương mại điện tử**
  - Xem danh mục sản phẩm & dịch vụ
  - Giỏ hàng, mua phụ tùng và thanh toán trực tuyến
  - Bình luận, đánh giá sản phẩm  

- **Đặt lịch trực tuyến**
  - Chủ động đặt lịch sửa chữa  
  - Theo dõi trạng thái:
    ```
    Đặt lịch -> Tiếp nhận -> Đang sửa -> Hoàn thành
    ```

- **Thanh toán đa phương thức**
  - Thanh toán qua:
    - Momo  
    - VNPAY  
    - Tiền mặt  

- **Quản lý tài khoản**
  - Đăng ký / đăng nhập  
  - Reset mật khẩu qua Email

- **Số hóa hóa đơn**
  - Xem lịch sử thanh toán  
  - In hóa đơn trực tiếp từ web  

---

### Phân hệ Quản trị

- **Quản trị nhân sự**
  - Quản lý tài khoản nhân viên  
  - Phân quyền truy cập  
  - Quản lý thông tin khách hàng  

- **Vận hành sửa chữa**
  - Xác nhận lịch đặt  
  - Lập **Phiếu tiếp nhận** từ lịch hẹn  
  - Lập **Phiếu sửa chữa** và báo giá  
  - Cập nhật trạng thái sửa chữa  

- **Tài chính & Kho**
  - Tự động xuất hóa đơn  
  - Trừ tồn kho phụ tùng  
  - Thống kê doanh thu  

---

## Quy trình nghiệp vụ

1. **Đặt lịch**  
   Khách hàng đặt lịch trên website  

2. **Tiếp nhận**  
   Admin xác nhận -> tạo Phiếu tiếp nhận  

3. **Báo giá**  
   Kỹ thuật kiểm tra -> lập Phiếu sửa chữa -> gửi báo giá  

4. **Thực hiện**  
   Khách đồng ý -> chuyển trạng thái "Đang sửa"  

5. **Thanh toán**  
   Chọn phương thức:
   - Tiền mặt  
   - Momo  
   - VNPAY  

6. **Hoàn tất**  
   - Cập nhật doanh thu  
   - Trừ kho  
   - Xuất hóa đơn  

---

## Công nghệ sử dụng

- **Backend:** Flask 
- **Frontend:** Jinja2, HTML5, CSS3, JavaScript  
- **Database:** MySQL
- **Integration:**
  - Momo API  
  - VNPAY Sandbox  
  - Flask-Mail 


---
## Ảnh Lược đồ cơ sở dữ liệu

## Hướng dẫn cài đặt

### 1. Clone dự án

```bash
git clone https://github.com/pgiahuy/cnpm-trung-tam-sua-xe.git
cd cnpm-trung-tam-sua-xe
```
### 2. Tạo môi trường ảo
```
python -m venv venv
```
Windows:
```
venv\Scripts\activate
```
Linux / MacOS:
```
source venv/bin/activate
```
### 3. Cài đặt thư viện
```
pip install -r requirements.txt
```
### 4. Cấu hình hệ thống

- Tạo database 'garage' trong MySQL

5. Khởi chạy ứng dụng
```
python index.py
```
Truy cập:
```
http://127.0.0.1:5000
```

## Web đã được triển khai tại:
```
https://giahuy123.pythonanywhere.com/
```

## Danh sách tài khoản demo
> Vui lòng không thay đổi các dữ liệu mẫu

| Vai trò        | Username | Password |
|---------------|----------|----------|
| Admin     | `admin`  | `123`  |
| Khách hàng | `Có thể đăng ký mới`  |  |


một số ảnh minh hoạ
