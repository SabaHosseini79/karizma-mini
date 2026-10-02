# دستیار کارگزاری کاریزما

چت‌بات پرسش و پاسخ فارسی برای کارگزاری کاریزما که با روش **RAG (Retrieval-Augmented Generation)** به سؤالات کاربران از روی اسناد و منابع داخلی پاسخ می‌دهد.

![نمایی از برنامه](screenshot.png)

## ویژگی‌ها

- رابط چت فارسی (راست‌به‌چپ) با Streamlit
- جستجوی معنایی در منابع و پاسخ‌دهی بر اساس آنها
- نمایش منابع استفاده‌شده برای هر پاسخ
- حفظ تاریخچه‌ی گفتگو

## تکنولوژی‌ها

- Python
- Streamlit
- Supabase

## نصب و اجرا

۱. نصب وابستگی‌ها:

    pip install -r requirements.txt

۲. ساخت فایل `.env` کنار `app.py` و قرار دادن کلیدها در آن (کلیدها را در مخزن قرار ندهید):

    SUPABASE_URL=your-supabase-url
    SUPABASE_KEY=your-supabase-key
    # سایر کلیدهای موردنیاز rag.py

۳. اجرا:

    streamlit run app.py

## ساختار پروژه

    app.py            رابط کاربری چت
    rag.py            منطق RAG (بازیابی و تولید پاسخ)
    requirements.txt  وابستگی‌ها
