# Cu-AAS Digital Lab
Digitalisasi instrumentasi: penetapan kadar Cu dalam sampel air dengan Flame AAS (Streamlit).

## Menjalankan
    pip install -r requirements.txt
    streamlit run app.py

## Deploy
Push ke GitHub, lalu deploy di share.streamlit.io (main file: `app.py`).

## Model 3D sendiri
Taruh file `model.glb` di folder yang sama dengan `app.py`. Aplikasi otomatis memakainya
menggantikan model bawaan. Daftar komponen/bobot ada di `COMP` pada `app.py`.
