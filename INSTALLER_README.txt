Giờ test first-run setup hoàn chỉnh bằng Python trước.

Làm 3 bước:

Xóa setting cũ để giả lập người dùng mới:
Remove-Item -Recurse -Force "HKCU:\Software\LeoTran\DesktopCalendar" -ErrorAction SilentlyContinue
Chạy:
E:\Python\python.exe E:\Projects\Experiments\desktop_calendar\app.py
Đi hết flow:
Sign in with Google
Chọn Edge/Chrome/Brave
Open browser to sign in
Đăng nhập đến khi thấy Google Calendar
Bấm Check sign-in
Finish setup

Sau đó kiểm tra widget hiện đủ:

event
appointment
task thường
recurring task như Pay rent
restart app lần 2 không hỏi setup lại
browser không popup ở lần chạy bình thường

Nếu tất cả ổn thì bước kế tiếp là build lại .exe từ source mới này.

ok ổn hết rồi giờ làm gì nữa

Giờ source đã ổn thì chuyển sang build bản release thật.

1. Xóa các print() debug tạm

Ví dụ:

print("Scraped tasks:", ...)
print("SCRAPED:", ...)
print("PAGE:", ...)
print("BUTTON COUNT:", ...)

Các print lỗi cần thiết có thể giữ.

2. Build bản không có PowerShell/console

Trong project:

cd E:\Projects\Experiments\desktop_calendar

Xóa build cũ:

Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
Remove-Item DesktopCalendar.spec -ErrorAction SilentlyContinue

Build:

E:\Python\python.exe -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name DesktopCalendar `
    --collect-all playwright `
    --add-data "credentials.json:." `
    app.py

Sau đó chạy:

.\dist\DesktopCalendar\DesktopCalendar.exe
3. Test chính .exe như người dùng mới

Reset:

Remove-Item -Recurse -Force "$env:LOCALAPPDATA\DesktopCalendar" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "HKCU:\Software\LeoTran\DesktopCalendar" -ErrorAction SilentlyContinue

Rồi chạy .exe và đảm bảo flow này hoạt động:

DesktopCalendar.exe
→ Google OAuth
→ chọn Edge/Chrome/Brave
→ login Google Calendar
→ Check sign-in
→ Finish setup
→ widget xuất hiện
→ event + appointment + task + recurring task
→ restart không hỏi setup lại
4. Nếu .exe qua bài test này

Thì bước tiếp theo là tạo:

DesktopCalendarSetup.exe

để người khác chỉ việc Download → Install → Sign in → dùng.

Trước khi phát công khai còn một việc rất quan trọng: cấu hình Google OAuth Consent Screen của project sang trạng thái phù hợp cho người dùng bên ngoài; nếu OAuth app vẫn ở Testing thì chỉ các tài khoản test được thêm trước mới đăng nhập được.

Bạn build bản --windowed và test clean-install trước. Nếu nó chạy đủ mọi thứ thì tiếp theo mình hướng dẫn bạn làm installer chuẩn Windows.

rồi giờ tạo DesktopCalendarSetup.exe đi

Được. Mình đã tạo bộ file để build ra DesktopCalendarSetup.exe.

Tải cả bộ ở đây:

DesktopCalendar installer builder

Hoặc từng file:

DesktopCalendar.iss
build_installer.ps1
INSTALLER_README.txt

Bạn làm như này:

Giải nén 2 file DesktopCalendar.iss và build_installer.ps1 vào root project:
E:\Projects\Experiments\desktop_calendar\
Đảm bảo có:
dist\DesktopCalendar\DesktopCalendar.exe
Cài Inno Setup 6.
Chạy:
cd E:\Projects\Experiments\desktop_calendar


powershell -ExecutionPolicy Bypass -File .\build_installer.ps1

Xong sẽ có:

installer_output\
└── DesktopCalendarSetup.exe

Installer này sẽ cài toàn bộ thư mục PyInstaller, tạo Start Menu shortcut, có tùy chọn desktop shortcut, có Uninstall và sau khi cài sẽ mở Desktop Calendar luôn.

Bước sau khi bạn tạo được DesktopCalendarSetup.exe là test nó như một máy người dùng mới, rồi mới đem phát cho người khác. 

build_installer.ps1
File
INSTALLER_README.txt
Document

Library
/
Anh Quan 2
/
INSTALLER_README.txt
Desktop Calendar installer build

1. Put these two files in the project root:
   - DesktopCalendar.iss
   - build_installer.ps1

2. Make sure this exists:
   dist\DesktopCalendar\DesktopCalendar.exe

3. Install Inno Setup 6 on Windows.

4. From PowerShell in the project root:
   powershell -ExecutionPolicy Bypass -File .\build_installer.ps1

5. Result:
   installer_output\DesktopCalendarSetup.exe
