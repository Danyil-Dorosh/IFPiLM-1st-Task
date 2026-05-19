# pha_lib — biblioteka do analizy danych z systemu PHA na W7-X

Modularna biblioteka Python do automatyzacji pulse-height analysis (PHA) — wykrywa discharges
w shocie z stelaratora W7-X, dopasowuje wykładniczy zanik
\( y(t) = A \cdot \exp\!\left(-\dfrac{t-t_0}{\tau}\right) + C \) do każdej injekcji
i zapisuje wyniki w postaci dwóch DataFrame'ów (po jednym na kanał energetyczny).

## Struktura projektu

```
pha_lib_project/
├── pha_lib/             ← właściwa biblioteka (każdy plik = jeden krok pipeline'u)
│   ├── __init__.py
│   ├── model.py         # dataclasses: Shot, EnergyChannelData, TimeTrace, Discharge, ExpDecayFit
│   ├── io.py            # load_united_txt, load_test_folder, (placeholder load_pha)
│   ├── timetrace.py     # integrate_energy_window — sumowanie countów w oknie energii
│   ├── discharges.py    # detect_discharges — znalezienie start/finish frame
│   ├── fit.py           # fit_exp_decay + fit_discharge_two_strategies
│   ├── pipeline.py      # analyze_shot, analyze_channel — wysokopoziomowe API
│   ├── export.py        # save_results_parquet
│   └── plotting.py      # plot_timetrace_with_discharges, plot_discharge_fit
├── tests/test_basic.py  # smoke tests (6/6 PASS na danych testowych)
├── scripts/
│   ├── peek_data.py     # eksploracja: ile discharges, gdzie peaki
│   └── run_demo.py      # end-to-end demo na unitedc_62_239.txt
├── output/              # wyniki: results_channel{1,2}.parquet + .csv + diagnostyczne PNG
└── README.md
```

## Filozofia modularności

Każdy moduł = **jedna odpowiedzialność**, żeby łatwo testować osobno i podmieniać:

| Krok | Wejście | Wyjście | Moduł |
|---|---|---|---|
| 1. Wczytaj plik | `.txt` (united lub folder) | `Shot` | `io` |
| 2. Zsumuj okno energii | `EnergyChannelData` | `TimeTrace` | `timetrace` |
| 3. Wykryj discharges | `TimeTrace` | `list[Discharge]` | `discharges` |
| 4. Dopasuj eksponensę | `TimeTrace + Discharge` | `ExpDecayFit ×2` | `fit` |
| 5. Połącz w tabelę | wszystko powyżej | `pd.DataFrame` | `pipeline` |
| 6. Zapisz | `dict[ch, DataFrame]` | `.parquet` (+ `.csv`) | `export` |
| 7. Wykres | `TimeTrace` / `Discharge` | `matplotlib.Axes` | `plotting` |

W przyszłości łatwo dorobić: `load_pha()` (binarny format), inny detektor discharges,
inne modele fitu, inną linię (np. 6660 → C V, O VIII...), więcej kanałów.

## Quick start

```python
from pha_lib import io, pipeline, export

# 1. wczytaj shot
shot = io.load_united_txt("unitedc_62_239.txt", shot_id="united_62_239")

# 2. analiza całego shotu — zwraca {1: df, 2: df}
results = pipeline.analyze_shot(
    shot,
    line_energy_eV=6660.0,   # centrum linii (Fe XXV)
    half_width_eV=50.0,      # +- 50 eV okno
    n_points=3,              # ile ramek do dopasowania (specyfikacja: 3)
    channels=(1, 2),
)

# 3. zapisz Parquet
export.save_results_parquet(results, out_dir="output", also_csv=True)
```

Demo end-to-end: `python scripts/run_demo.py`

## Format wyników

Każdy DataFrame ma jeden wiersz na discharge i kolumny:

| kolumna | znaczenie |
|---|---|
| `discharge_no` | numer kolejny discharge w shocie |
| `discharge_E` | energia linii (eV), np. 6660.0 |
| `start_frame` | pierwsza ramka discharge |
| `finish_frame` | ostatnia ramka (powrót do tła) |
| `A_f, t_0_f, tau_f, C_f` | fit od **pierwszej** ramki (`first` strategy) |
| `A, t_0, tau, C` | fit od **drugiej** ramki (`second` strategy — zwykle lepsza) |
| `fit_first_success, fit_second_success` | czy `curve_fit` się udał |
| `fit_first_message, fit_second_message` | diagnostyczna wiadomość |
| `A_f_err, tau_f_err, A_err, tau_err` | niepewności (sqrt diag covariance) |

> **Uwaga o nazwach:** w specyfikacji zadania były dwie kolumny `C` (jedna od fitu "first",
> druga od "second"). Pandas wymaga unikalnych nazw, więc rozróżniam je jako `C_f` i `C`.

## Strategie dopasowania (dlaczego dwie?)

**„first"** — fit zaczyna się od ramki, w której algorytm wykrył start discharge.
Gdy injekcja jest niemal natychmiastowa (lub gdy patrzymy na ramp-down typu plasma startup),
ta strategia dobrze opisuje zanik.

**„second"** — fit zaczyna się od **drugiej** ramki discharge. Często jest lepsza, bo
pierwsza ramka łapie injekcję jeszcze w trakcie wzrostu (ramp-up) — wtedy prawdziwy peak
jest właśnie *w drugiej ramce*. Patrząc na nasze dane (channel 2, ramki 100–102: 1270 → **1995** → 1642)
widać dokładnie ten efekt — peak jest w ramce 101, nie 100.

Diagnostyczny wykres `output/fits_channel2.png` pokazuje obie krzywe (czerwoną i zieloną),
żebyś mógł sam ocenić, która lepiej pasuje do każdego discharge.

## Detekcja discharges — jak działa

Algorytm w `discharges.py`:

1. **Tło i szum**: mediana (`background`) + 1.4826·MAD (`scale`) — robust wobec peaków,
   bo `median` nie ucieknie z powodu kilku wystrzałów.
2. **Start**: pierwsza ramka, w której sygnał > `bg + 3·scale` ORAZ skok od poprzedniej
   ramki > `min_jump=20` events.
3. **Finish**: gdy sygnał wraca poniżej `bg + 1.5·scale` przez `min_quiet_frames=2` ramki.
4. **Filtry**: minimalna separacja 3 ramki między dwoma discharges, max długość 25 ramek
   (chroni przed „discharge'em który nigdy się nie kończy").

Wszystkie progi konfigurowalne przez `DischargeDetectionConfig`.

## Stabilność fitu — uwaga numeryczna

Z 3 punktami i 4 parametrami `scipy.optimize.curve_fit` zawiedzie ("more parameters than
data points"). Dlatego dla `n_points=3` biblioteka:

- **fixuje t_0** na pierwszej ramce okna fitu (fizycznie: to jest nasz wybrany moment startu),
- **fixuje C** na medianie całego trace (fizycznie: tło to cecha shotu, nie 3 punktów),
- robi **2-parametrowy least-squares** dla (A, tau) — numerycznie stabilne.

Dla `n_points ≥ 4` używamy pełnego 4-parametrowego fitu z bounds:
\(A \geq 0, \tau > 0, C \geq 0, t_0 \in [t_{\min}-\Delta, t_{\max}]\).

## Wyniki na danych testowych (`unitedc_62_239.txt`)

| Channel | # discharges | Komentarz |
|---|---|---|
| 1 | 2 | sygnał słaby (max ~3.8σ ponad tło) — typowe dla ch1 nieoptymalizowanego dla 6660 eV |
| 2 | 4 | 3 wyraźne injekcje (ramki ~100, ~147, ~194) + 1 ramp-down ~64 |

Zobacz `output/overview_timetrace.png` i `output/fits_channel2.png`.

Najlepsze τ (channel 2, strategia "second"):
- **Discharge ramka 100**: τ ≈ 13.8 ramek ≈ 0.69 s (przy frame_dt=50 ms)
- **Discharge ramka 146**: τ ≈ 5.6 ramek ≈ 0.28 s
- **Discharge ramka 194**: τ wpada w upper bound — ten discharge jest słaby, fit niepewny

## Konteks fizyczny — krótkie notki dydaktyczne

- **Linia 6660 eV** to prawdopodobnie linia rezonansowa **Fe XXV** (helium-like żelazo,
  przejście 1s² → 1s2p, energia ~6700 eV). W artykule [3] (Soft X-ray PHA na W7-X) ta
  linia jest wymieniana jako jedna z głównych obserwowanych przy injekcji żelaza — patrz
  rys. 2 i 3 w tym artykule.
- **τ (confinement time)** to czas, po którym koncentracja zanieczyszczenia spada e-krotnie.
  W artykule [2] τ jest interpretowane jako kombinacja particle confinement + recycling.
- **Channel 1 vs 2**: różne membrany/filtry → różna efektywność na 6660 eV. Z artykułu [2]:
  "The 1st PHA channel was optimized... the 2nd and 3rd still need more time" — w naszym
  shocie ch2 lepiej widzi 6660 eV, co jest spójne z tym, że ch1 ma cieńszą membranę
  (blokuje high-E fotony słabiej).
- **Doppler broadening** — linia ma naturalną szerokość zależną od temperatury jonów.
  W naszych danych okno ±50 eV (10 binów) jest komfortowo szersze niż typowa szerokość
  Dopplera dla Fe XXV przy T_i ~ keV.

## Co dalej (roadmap)

1. **`io.load_pha()`** — gdy będzie dostępna specyfikacja binarnego formatu .pha.
2. **Lepsza identyfikacja linii** — `find_peaks` w widmie, automatyczne dopasowanie
   centrum okna do prawdziwego maksimum (Doppler-shift compensation).
3. **Per-discharge background subtraction** — odjęcie tła osobno przed każdym discharge,
   nie tylko mediana globalna.
4. **Multi-line analysis** — równolegle 2–3 linie (np. Fe XXV 6660 + Ar XVII 3140), żeby
   porównać τ dla różnych zanieczyszczeń.
5. **Niepewności na τ** — propagacja error bars z curve_fit (jest już w kolumnie `tau_err`,
   ale można też bootstrap).
6. **Konfiguracja YAML** — żeby zapisać próg detekcji, zakres okien itp. obok wyników.

## Wymagane biblioteki

```
numpy, scipy, pandas, matplotlib, pyarrow
```

Zgodne z naszą wcześniejszą rozmową: NumPy = "magazyn liczb", SciPy = "laboratoria
obliczeniowe" (`curve_fit`), Pandas = "urząd miasta" (tabela wyników), Matplotlib = "okno"
(diagnostyka), Parquet = format kolumnowy idealny pod tabele wynikowe.

## Testy

`python tests/test_basic.py` — 6 testów (parser, oś energii, integracja okna, detekcja,
roundtrip fitu, pełny pipeline). Wszystkie powinny przejść.
