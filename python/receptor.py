"""
Receptor Morse por video (Tarea 1, Sistemas de Comunicaciones 2026).
Uso:
    python receptor.py calibrar  video_paris.mp4
    python receptor.py decodificar video.mp4 --ref "SIS COM"
    python receptor.py espectro  video.mp4
"""
import json, argparse
import numpy as np
import cv2

# ======================================================================
# TRAMO 1. Del video a la señal I[n]
# ======================================================================
def leer_video(ruta, escala=8):
    """Lee el video cuadro por cuadro. Devuelve los cuadros reducidos en gris
    y la hora t[n] de cada cuadro, en segundos."""
    cap = cv2.VideoCapture(ruta)
    cuadros, tiempos = [], []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gris.shape
        chico = cv2.resize(gris, (w // escala, h // escala), interpolation=cv2.INTER_AREA)
        cuadros.append(chico.astype(np.float32))
        tiempos.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
    return np.array(cuadros), np.array(tiempos)


def ubicar_roi(cuadros, ancho, alto, centro=None):
    """Centra la ROI donde el brillo más varía a lo largo del video,
    que es la fuente que se enciende y se apaga. Si se entrega 'centro'
    (x, y en píxeles reducidos), se usa ese punto (selección manual)."""
    if centro is None:
        variacion = cuadros.std(axis=0)
        variacion = cv2.GaussianBlur(variacion, (5, 5), 0)
        y, x = np.unravel_index(np.argmax(variacion), variacion.shape)
    else:
        x, y = centro
    x0 = int(np.clip(x - ancho // 2, 0, cuadros.shape[2] - ancho))
    y0 = int(np.clip(y - alto // 2, 0, cuadros.shape[1] - alto))
    return x0, y0, ancho, alto


def intensidad(cuadros, roi):
    """I[n] = promedio de los niveles de gris de la ROI en el cuadro n."""
    x0, y0, w, h = roi
    return cuadros[:, y0:y0 + h, x0:x0 + w].mean(axis=(1, 2))


# ======================================================================
# TRAMO 2. Calibración: umbral de Otsu y T
# ======================================================================
def umbral_otsu(I):
    """Prueba todos los umbrales de 0 a 255 y elige el que más separa
    los promedios de los dos grupos (encendido y apagado), ponderando
    por el tamaño de cada grupo. Si varios empatan, toma el centro."""
    hist, _ = np.histogram(I, bins=256, range=(0, 256))
    p = hist / hist.sum()
    k = np.arange(256)
    w0 = np.cumsum(p)                 # fracción de datos bajo el umbral
    mu = np.cumsum(p * k)             # suma acumulada de niveles
    mu_t = mu[-1]                     # promedio total
    sep = (mu_t * w0 - mu) ** 2 / (w0 * (1 - w0) + 1e-12)
    mejores = np.flatnonzero(sep >= sep.max() * (1 - 1e-6))
    return (mejores.min() + mejores.max()) / 2 + 0.5


# ======================================================================
# TRAMO 3. Decisión binaria y rachas
# ======================================================================
def rachas(I, t, Iu, margen=2.5):
    """b[n] = 1 si I[n] > Iu. Agrupa cuadros seguidos con el mismo valor.
    La duración de cada racha se mide con la hora de los cuadros (no
    contando cuadros), porque la frecuencia de cuadros puede variar.
    El mensaje es el grupo de pulsos entre los márgenes apagados: las pausas
    de más de 'margen' segundos lo separan de lo que aparece antes o después
    (por ejemplo, la página antes de pasar a negro). Se usa el grupo con más pulsos."""
    b = (I > Iu).astype(int)
    cambios = np.flatnonzero(np.diff(b)) + 1
    bordes = np.r_[0, cambios, len(b)]
    grupos, actual = [], []
    for ini, fin in zip(bordes[:-1], bordes[1:]):
        dur = float((t[fin] if fin < len(t) else t[-1]) - t[ini])
        if b[ini] == 0 and dur >= margen:
            grupos.append(actual); actual = []
        else:
            actual.append((int(b[ini]), dur))
    grupos.append(actual)
    mejor = []
    for g in grupos:
        while g and g[0][0] == 0: g.pop(0)
        while g and g[-1][0] == 0: g.pop()
        if sum(n for n, _ in g) > sum(n for n, _ in mejor): mejor = g
    return mejor


def calibrar(ruta, roi_tam=(24, 12), escala=8, n_intervalos=93):
    """PARIS PARIS dura 93 T. T = duración del mensaje / 93."""
    cuadros, t = leer_video(ruta, escala)
    roi = ubicar_roi(cuadros, *roi_tam)
    I = intensidad(cuadros, roi)
    Iu = umbral_otsu(I)
    R = rachas(I, t, Iu)
    T = sum(d for _, d in R) / n_intervalos
    return {"umbral": float(Iu), "T": float(T), "roi_tamano": list(roi_tam), "escala": escala}


# ======================================================================
# TRAMO 4. Clasificación y traducción a texto
# ======================================================================
MORSE = {".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
         "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
         "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
         "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
         "-.--": "Y", "--..": "Z"}

def a_texto(R, T):
    """Encendido: < 2T punto, 2T a 6T raya, >= 6T inválido.
    Apagado: < 2T entre símbolos, 2T a 5T entre letras, >= 5T entre palabras."""
    texto, letra = "", ""
    for nivel, dur in R:
        x = dur / T
        if nivel == 1:
            letra += "." if x < 2 else ("-" if x < 6 else "#")
        else:
            if x >= 2:                                # termina la letra
                texto += MORSE.get(letra, "?")
                letra = ""
            if x >= 5:                                # termina la palabra
                texto += " "
    texto += MORSE.get(letra, "?")
    return texto


# ======================================================================
# TRAMO 5. Error: distancia de Levenshtein y CER
# ======================================================================
def levenshtein(ref, rec):
    """Tabla de Wagner-Fischer: dp[i][j] = costo mínimo para pasar de
    ref[:i] a rec[:j]. Al final se recorre hacia atrás para contar S, D, I."""
    n, m = len(ref), len(rec)
    dp = np.zeros((n + 1, m + 1), dtype=int)
    dp[:, 0] = np.arange(n + 1)
    dp[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            costo = 0 if ref[i - 1] == rec[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j - 1] + costo,   # sustituir (o igual)
                           dp[i - 1, j] + 1,           # eliminar
                           dp[i, j - 1] + 1)           # insertar
    S = D = Ins = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (ref[i - 1] != rec[j - 1]):
            S += ref[i - 1] != rec[j - 1]; i -= 1; j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + 1:
            D += 1; i -= 1
        else:
            Ins += 1; j -= 1
    return int(S), D, Ins


def cer(ref, rec):
    S, D, Ins = levenshtein(ref.upper(), rec.upper())
    return {"S": S, "D": D, "I": Ins, "CER": (S + D + Ins) / len(ref)}


# ======================================================================
# TRAMO 6. Espectro, PSD y B95
# ======================================================================
def espectro(I, fs):
    """Resta el promedio, calcula la FFT y devuelve el espectro de amplitud,
    la PSD (periodograma) y B95."""
    x = I - I.mean()
    N = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(N, d=1 / fs)
    amplitud = 2 * np.abs(X) / N
    psd = 2 * np.abs(X) ** 2 / (fs * N)
    psd[0] = 0
    area = np.r_[0, np.cumsum((psd[1:] + psd[:-1]) / 2 * np.diff(f))]   # trapecios
    k = np.searchsorted(area, 0.95 * area[-1])
    B95 = f[k - 1] + (0.95 * area[-1] - area[k - 1]) / (area[k] - area[k - 1]) * (f[k] - f[k - 1])
    return f, amplitud, psd, float(B95)


def graficar(t, I, Iu, texto, nombre):
    """Muestra I[n] contra el tiempo, con el umbral y el texto reconstruido,
    y la guarda como imagen PNG junto al video."""
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 3.5))
    plt.plot(t - t[0], I, ".-", ms=3, lw=0.8, label="I[n]")
    plt.axhline(Iu, color="orange", ls="--", label=f"umbral = {Iu:.1f}")
    plt.xlabel("Tiempo [s]"); plt.ylabel("Intensidad media de la ROI")
    plt.title(f"Texto reconstruido: {texto}")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(nombre.rsplit(".", 1)[0] + "_senal.png", dpi=150)
    plt.show()


# ======================================================================
# TRAMO 7. Programa principal
# ======================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["calibrar", "decodificar", "espectro"])
    ap.add_argument("video")
    ap.add_argument("--ref", default="SIS COM")
    ap.add_argument("--calib", default="calib.json")
    ap.add_argument("--roi", type=int, nargs=2, default=[24, 12], help="ancho y alto de la ROI en píxeles reducidos")
    ap.add_argument("--centro", type=int, nargs=2, default=None, help="centro manual de la ROI (x y, píxeles reducidos)")
    ap.add_argument("--escala", type=int, default=8, help="factor de reducción del cuadro")
    a = ap.parse_args()

    if a.accion == "calibrar":
        cal = calibrar(a.video, a.roi, a.escala)
        json.dump(cal, open(a.calib, "w"), indent=1)
        print("Calibración:", cal)
        return

    cal = json.load(open(a.calib))
    cuadros, t = leer_video(a.video, cal["escala"])
    roi = ubicar_roi(cuadros, *cal["roi_tamano"], centro=a.centro)
    I = intensidad(cuadros, roi)
    fs = (len(t) - 1) / (t[-1] - t[0])

    if a.accion == "decodificar":
        R = rachas(I, t, cal["umbral"])
        texto = a_texto(R, cal["T"])
        print(f"fs = {fs:.2f} Hz, rachas = {len(R)}")
        print("Texto reconstruido:", repr(texto))
        print("Error:", cer(a.ref, texto))
        graficar(t, I, cal["umbral"], texto, a.video)
    else:
        f, A, P, B95 = espectro(I, fs)
        sobre1 = f > 1.0                       # se ignoran las variaciones lentas
        pico = f[sobre1][np.argmax(A[sobre1])]
        print(f"N = {len(I)}, fs = {fs:.2f} Hz, pico principal = {pico:.2f} Hz, B95 = {B95:.2f} Hz")


if __name__ == "__main__":
    main()
