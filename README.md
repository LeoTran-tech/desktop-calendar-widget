# Desktop Calendar

## Cài đặt

```powershell
pip install -r requirements.txt
```

## Cấu hình

Copy:

```text
config.example.json
```

thành:

```text
config.json
```

Sau đó dán `Secret address in iCal format` của Google Calendar vào `calendar_url`.

## Chạy

```powershell
python app.py
```

## Hiện có

- Calendar desktop
- Google Calendar qua iCal
- Upcoming events
- Dấu `•` cho ngày có event
- Auto refresh mỗi 5 phút
- Drag widget
- Resize 4 cạnh + 4 góc
