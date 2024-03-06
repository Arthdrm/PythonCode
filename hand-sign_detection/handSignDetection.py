import cv2 as cv
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import math

# 0 merupakan id utk webcam pertama pada device.
# cap = capture (Tangkapan Video)
cap = cv.VideoCapture(0)

# Membuat objek classifier utk mengklasifikasi citra
# classifier = Classifier("Model\keras_model.h5", "Model\labels.txt")
classifier = Classifier("HandSign/Model/keras_model.h5", "HandSign/Model/labels.txt")

# Membuat list label
labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"]

# Membuat objek HandDetector utk mendeteksi tangan.
# Parameter maxHands diatur menjadi 1 utk hanya mendeteksi 1 tangan
detector = HandDetector(maxHands=1)

# Membuat infinite loop utk menampilkan potongan gambar dari webcam secara terus-menerus.
while True:
    # Tuple unpacking, fungsi objekVideoCapture.read() mengembalikan 2 nilai kembalian
    # 1 : Status berhasil tidaknya frame diambil dari sumber video (bool).
    # 2 : Matriks citra (Array Numpy 3D).
    success, img = cap.read()
    # Membuat salian citra tangan (Citra tanpa drawing).
    imgOutput = img.copy()    
    # Hands -> Metadata citra tangan(List), Img -> Citra frame yg telah diberi drawing/kerangka.
    hands, img = detector.findHands(img)

    if hands:
        # Jika tangan dideteksi pada frame, pilih tangan pertama
        hand = hands[0]
        # Bounding box -> Koordinat kotak yang membungkus suatu citra (Total 4 titik koordinat).
        # hand -> Merupakan suatu dictionary yg menyimpan metadata citra tangan yg dideteksi.
        # bbox -> Key dictionary yang menyimpan tuple utk koordinat bounding box citra.
        # x -> Titik awal bbox citra tangan pd sb-x (Titik sb-x awal)
        # y -> Titik awal bbox citra tangan pd sb-y (Titik sb-y awal)
        # w -> Lebar bbox citra tangan (Titik sb-x akhir)
        # h -> Tinggi bbox citra tangan (Titik sb-y akhir)
        x,y,w,h = hand['bbox']

        # Membuat potongan frame yang hanya menampilkan frame tangan.
        offset = 20 # Variabel offset utk memperbesar jangkauan frame.
        imgCrop = img[y-offset:y+h+offset, x-offset:x+w+offset]

        # Membuat canvas putih utk bounding box yang ukurannya konsisten
        canvasSize = 300      
        imgWhite = np.ones((canvasSize,canvasSize,3), np.uint8)*255
        #################################
        # Keterangan properti shape :   #
        # shape[0] -> Tinggi Gambar     #
        # shape[1] -> Lebar Gambar      #
        # shape[2] -> Jumlah channel    #
        #################################
        # Klausa if-else dibawah digunakan utk memposisikan gambar di tengah canvas.
        # Merentangkan tinggi/lebar gambar agar tinggi/lebar gambar dpt memenuhi canvas.
        # Perentangan dilakukan berdasarkan aspek rasio gambar (Perbandingan tinggi : lebar)
        aspectRatio = h/w
        if aspectRatio > 1:
            # Kasus jika tinggi gambar lebih besar dari lebarnya.
            # Kita akan merentangkan tinggi gambar hingga mencapai tepi canvas, 
            # dan mengkalkulasi perubahan lebarnya agar gambar tetap proporsional.
            # Variabel k merupakan pengali utk merentangkan lebar gambar.
            k = canvasSize / h
            # Menyesuaikan lebar gambar.
            wCal = math.ceil(k * w)
            # Mengubah lebar gambar : w (Lebar gambar crop) -> wCal
            # Mengubah tinggi gambar : h (Tinggi gambar crop) -> canvasSize
            imgResized = cv.resize(imgCrop, (wCal, canvasSize)) # Sintaks : resize(sumberGambar, (lebar, tinggi))
            # Memposisikan gambar tangan di tengah canvas.
            # Mengatur gap gambar.
            # Gap gambar = (Ukuran canvas - ukuran lebar gambar / 2)
            wGap = math.ceil((canvasSize-wCal)/2)
            # Meng-overlay gambar pada canvas putih, 
            # Slicing index mengatur pada koordinat mana overlay akan dilakukan.
            imgWhite[:, wGap:imgResized.shape[1]+wGap] = imgResized
        else:
            # Kasus jika lebar gambar lebih besar dari tingginya.
            # Kita akan merentangkan lebar gambar hingga mencapai tepi canvas, 
            # dan mengkalkulasi perubahan tingginya agar gambar tetap proporsional.
            k = canvasSize / w
            hCal = math.ceil(k * h)
            imgResized = cv.resize(imgCrop, (canvasSize, hCal))
            hGap = math.ceil((canvasSize-hCal)/2)
            imgWhite[hGap:imgResized.shape[0]+hGap,:] = imgResized

        # Mengklasifikasi frame tangan (Klasifikasi diberi pada pojok kiri atas frame)
        # prediction -> Bil. desimal yg merepresentasikan kemiripan objek
        # index -> No index kelas yg mirip dgn objek (Sesuai file labels.txt)
        prediction, index = classifier.getPrediction(imgWhite)

 
        print(*prediction, sep="\n")

        # Menambahkan label pada citra imgOutput
        if float(prediction[index]) > 0.85:
            cv.putText(imgOutput, labels[index], (x,y-10), cv.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
            print("Hasil deteksi : {}, Pada Indeks ke-{}".format(labels[index], index))
        else:
            cv.putText(imgOutput, "Tidak Dikenali", (x,y-10), cv.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)            
            print("Tidak dikenali")

    # Menampilkan video original
    cv.imshow("Original", imgOutput)
    # cv.waitKey() menentukan jeda antara satu frame ke frame yang lain.
    key = cv.waitKey(1)
    if key == ord('x'):
        break

cap.release()
cv.destroyAllWindows()


    