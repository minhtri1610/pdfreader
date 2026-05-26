# Kế hoạch phát triển phần mềm PDF Reader đa nền tảng (PyQt6 + PyMuPDF)

Tài liệu này ghi lại chi tiết các giai đoạn phát triển, thiết kế hệ thống và các quyết định kỹ thuật đã thống nhất cho ứng dụng PDF Reader.

---

## 1. Kế hoạch phát triển (Project Phases)

Dự án được chia thành 4 giai đoạn chính để phát triển cuốn chiếu:

### Phase 1: Khung xương (Foundation) - MVP 1
*   **Mục tiêu:** Thiết lập cấu trúc dự án và hiển thị được trang đầu tiên của file PDF.
*   **Các công việc:**
    *   Tạo file `requirements.txt` và cài đặt môi trường.
    *   Tạo cấu trúc thư mục (`core`, `ui`, `utils`).
    *   Xây dựng `PDFEngine` để load file và render trang đầu tiên thành `QPixmap`.
    *   Tạo `MainWindow` và nút "Open File" cơ bản.

### Phase 2: Tính năng cốt lõi (Core Features) - MVP 2
*   **Mục tiêu:** Xây dựng hoàn chỉnh các tính năng điều hướng, phóng to/thu nhỏ, và tối ưu hóa hiển thị.
*   **Các công việc:**
    *   Xây dựng `DocumentState` quản lý trạng thái đọc tập trung (`core/state.py`).
    *   Thiết kế thanh công cụ `PDFToolBar` hiện đại, hiển thị trực tiếp các nút chức năng hay dùng (Mở file, Next/Prev, Zoom In/Out, Fit trang, Đổi Theme) bằng các icon trực quan để người dùng thao tác nhanh mà không cần tìm trong menu.
    *   Cấu hình `QScrollArea` cuộn trang mượt mà trong `PDFViewer`.
    *   Hiện thực hóa tính năng **Tự động co giãn (Auto-Resize)** trang PDF theo kích thước cửa sổ khi chọn chế độ Fit.
    *   Xây dựng hệ thống giao diện hai chế độ **Sáng - Tối (Light - Dark Mode)** sử dụng stylesheet QSS tùy chỉnh chất lượng cao.

### Phase 3: Nâng cao UX và Mở rộng
*   **Mục tiêu:** Tăng trải nghiệm người dùng bằng cách bổ sung phím tắt, tìm kiếm và thanh Sidebar.
*   **Các công việc:**
    *   Xây dựng `PDFSidebar` hiển thị mục lục (Table of Contents) trích xuất từ file PDF.
    *   Thêm phím tắt điều hướng nhanh (Mũi tên Trái/Phải để đổi trang, `Ctrl + Cuộn chuột` để Zoom).
    *   Hiện thực hóa chức năng tìm kiếm từ khóa cơ bản và tô sáng (highlight) kết quả trên trang hiển thị.

### Phase 4: AI Integration & Đóng gói
*   **Mục tiêu:** Chuẩn bị dữ liệu phục vụ AI (RAG, LLM) và đóng gói phân phối.
*   **Các công việc:**
    *   Xây dựng module trích xuất văn bản thô (Text Extraction) từ PDF.
    *   Đóng gói ứng dụng thành file thực thi `.exe` (Windows) và `.app` (macOS) bằng PyInstaller.

---

## 2. Thiết kế Hệ thống & Luồng Dữ liệu (System Design)

Ứng dụng áp dụng kiến trúc Event-Driven tách biệt giữa UI và Business Logic:

### Luồng mở File (File Open Flow)
1.  Người dùng click nút "Open File" -> Mở hộp thoại `QFileDialog` -> Nhận đường dẫn file.
2.  Đường dẫn được truyền cho `PDFEngine` để mở file bằng PyMuPDF (`fitz.open`).
3.  Nếu thành công: Khởi tạo dữ liệu trong `DocumentState` (tổng số trang, trang hiện tại = 0) -> Cập nhật các widget UI (mở khóa nút, hiển thị tổng số trang).
4.  Kích hoạt luồng Render trang 1.

### Luồng Render trang (Render Flow)
1.  `UIController` yêu cầu `PDFEngine` render trang dựa trên `page_index` và `zoom_level`.
2.  `PDFEngine` trích xuất trang, áp dụng ma trận zoom, chuyển đổi cấu trúc ảnh raw từ PyMuPDF thành `QImage`/`QPixmap`.
3.  `PDFViewer` nhận `QPixmap` và cập nhật lên canvas hiển thị.

---

## 3. Bản đồ Component UI (Component Tree)

```text
MainWindow (QMainWindow)
│
├── MenuBar (QMenuBar)
│   ├── File (Open, Close, Exit)
│   ├── View (Zoom In, Zoom Out, Fit Width, Toggle Theme)
│   └── Help (About)
│
├── ToolBar (QToolBar) -> Đưa toàn bộ chức năng hay dùng ra ngoài dưới dạng nút bấm có Icon trực quan
│   ├── [Icon Open File]
│   ├── [Separator]
│   ├── [Icon < Prev] Page Input [ 1 ] / [ Total ] [Icon Next >]
│   ├── [Separator]
│   ├── [Icon Zoom Out] [ Zoom % ] [Icon Zoom In]
│   ├── [Icon Fit Width] [Icon Fit Height]
│   ├── [Spacer] (Đẩy nút chuyển theme về góc phải)
│   └── [Icon Toggle Theme] (Nút icon chuyển chế độ Sáng/Tối ở góc phải)
│
├── CentralWidget (QWidget)
│   └── Layout chính (QHBoxLayout)
│       ├── Sidebar (QDockWidget / QTreeWidget) -> Hiển thị mục lục (TOC)
│       └── PDFViewerContainer (QVBoxLayout)
│           └── ScrollArea (QScrollArea)
│               └── Canvas (QLabel) -> Hiển thị ảnh trang PDF
│
└── StatusBar (QStatusBar) -> Hiển thị trạng thái tải, kích thước file
```
