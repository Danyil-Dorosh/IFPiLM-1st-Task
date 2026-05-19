# pha_lib — biblioteka do analizy danych z systemu PHA na W7-X

Modularna biblioteka Python do automatyzacji pulse-height analysis (PHA) — wykrywa
discharges w shocie z stelaratora W7-X, dopasowuje wykładniczy zanik
y(t) = A · exp(-(t - t_0)/tau) + C do każdej injekcji i zapisuje wyniki jako
DataFrame'y (po jednym na kanał energetyczny).

## Struktura projektu

```
pha_lib_project/
├── pha_lib/             ← właściwa biblioteka (każdy plik = jeden krok pipeline'u)
│   ├── __init__.py
│   ├── model.py         # dataclasses: Shot, EnergyChannelData, TimeTrace, Discharge, FitResult
│   ├── io.py            # load_united_txt, load_test_folder, placeholder load_pha
│   ├── timetrace.py     # integrate_energy_window — sumowanie countów w oknie energii
│   ├── discharges.py    # detect_discharges + DischargeDetectionConfig
│   ├── fit.py           # fit_discharge (2-parametrowy: A, tau; t_0 i C zafiksowane)
│   ├── pipeline.py      # analyze_shot, analyze_channel — wysokopoziomowe API
│   ├── export.py        # save_results_parquet, load_results_parquet
│   └── plotting.py      # plot_timetrace_with_discharges, plot_discharge_fit
├── tests/test_basic.py  # smoke tests (powinny przechodzić na danych testowych)
├── scripts/
│   ├── peek_data.py     # eksploracja: ile discharges, gdzie peaki
│   └── run_demo.py      # end-to-end demo na unitedc_62_239.txt
├── output/              # wyniki: results_channel{1,2}.parquet + .csv + diagnostyczne PNG
└── README.md
```

## Filozofia modularności

Każdy moduł = **jedna odpowiedzialność**, aby łatwo testować i podmieniać.

| Krok | Wejście | Wyjście | Moduł |
|---|---|---|---|
| 1. Wczytaj plik | `.txt` (united lub folder) | `Shot` | `io` |
| 2. Zsumuj okno energii | `EnergyChannelData` | `TimeTrace` | `timetrace` |
| 3. Wykryj discharges | `TimeTrace` | `list[Discharge]` | `discharges` |
| 4. Dopasuj eksponensę | `TimeTrace + Discharge` | `FitResult` | `fit` |
| 5. Połącz w tabelę | wszystko powyżej | `pd.DataFrame` | `pipeline` |
| 6. Zapisz | `dict[ch, DataFrame]` | `.parquet` (+ `.csv`) | `export` |
| 7. Wykres | `TimeTrace` / `Discharge` | `matplotlib.Axes` | `plotting` |

W przyszłości łatwo dodać: `load_pha()` (binarny format), alternatywny detektor
discharges, inny model fitu, multi-line analysis, itp.

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
    n_points=3,              # ile ramek do dopasowania
    channels=(1, 2),
)

# 3. zapisz Parquet (+CSV opcjonalnie)
export.save_results_parquet(results, out_dir="output", also_csv=True)
```

Demo end-to-end: `python scripts/run_demo.py`

## Format wyników

Każdy DataFrame ma jeden wiersz na discharge i
Demo end-to-end: `python scripts/run_demo.py`
 kolumny:

| kolumna | znaczenie |
|---|---|
| `discharge_n
Demo end-to-end: `python scripts/run_demo.py`
olejny discharge w shocie |
| `discharge_E` | energia linii (eV), np. 6660.0 |
| `start_frame` | pierwsza ramka discharge (pierwszy punkt burstu) |
| `finish_frame` | ostatnia ramka discharge |
| `A_f, t_0_f, tau_f, C_f` | współczynniki w jednostkach **ramek** |
| `A, t_0, tau, C` | współczynniki w jednostkach **sekund** (`t_0` i `tau` przeliczone) |
| `fit_success` | czy dopasowanie się powiodło |
| `fit_message` | diagnostyczna wiadomość z funkcji fit |

Suffix `_f` = wartości w **ramek**; bez suffixu = wartości przeliczone na **sekundy**
(`t_0`, `tau` mnożone przez `frame_dt_s`).

## Strategia dopasowania (obecna implementacja)

W obecnej wersji jest jedna spójna strategia dopasowania:
- `t_0` jest zafiksowane na `start_frame + 1` (drugi punkt burstu, tzn. pierwszy punkt
  używany do fitu),
- `C` (poziom tła) jest zafiksowany na medianie całego `TimeTrace`,
- wolne parametry dopasowania: `A` i `tau`.

Powód: przy `n_points = 3` mamy 3 punktów danych i 2 wolne parametry — stabilne
2-parametrowe dopasowanie (curve_fit optymalizuje tylko `A` i `tau`).

W przyszłości można dodać opcję pełnego 4-parametrowego fitu dla dłuższych okien `n_points >= 4`.

## Detekcja discharges — jak działa

Algorytm w `discharges.py` (część publicznego API: `DischargeDetectionConfig`):

1. **Tło i skala**: `bg = median(values)`, `scale = max(1.4826*MAD, 1.0)` (robustna estymacja),
2. **Start**: ramka, gdzie `value >= bg + peak_threshold_factor * scale` oraz skok od
   poprzedniej ramki >= `min_jump`,
3. **Finish**: sygnał spada poniżej `bg + end_threshold_factor * scale` i utrzymuje się przez
   `min_quiet_frames`,
4. **Filtry**: minimalna separacja `min_separation_frames` oraz maksymalna długość
   `max_frames_per_discharge`.

Wszystkie wartości domyślne i progi są konfigurowalne przez `DischargeDetectionConfig`.

## Stabilność fitu — uwaga numeryczna

Przy krótkich oknach (np. `n_points=3`) nie można niezawodnie dopasować 4 wolnych
parametrów. Dlatego obecna implementacja:

- zafiksowuje `t_0 = start_frame + 1` i `C = median(trace)`,
- dopasowuje 2 parametry: `A` i `tau` (numerycznie stabilne dla 3 punktów),

W przyszłości można dodać opcję pełnego 4-parametrowego fitu dla dłuższych okien `n_points >= 4`.

## Wyniki na danych testowych (`unitedc_62_239.txt`)

Przykładowe wyniki (kanały i liczba wykrytych discharges zależą od ustawień progów):
- Channel 1: słabszy sygnał (mniej wyraźne injekcje),
- Channel 2: kilka wyraźnych injekcji — na nich opieramy diagnostykę i wykresy.

Zobacz przykładowe wykresy w `output/` generowane przez skrypty w `scripts/`.

## Co dalej (roadmap)

1. `io.load_pha()` — implementacja binarnego formatu .pha po otrzymaniu specyfikacji,
2. automatyczne wykrywanie linii w spektrum i dostosowanie centrum okna,
3. per-discharge background subtraction (lokalne tło),
4. opcjonalny pełny 4-parametrowy fit dla dłuższych okien (`n_points >= 4`),
5. bootstrap/propagacja niepewności dla `tau` i `A`.

## Wymagane biblioteki

```
numpy, scipy, pandas, matplotlib, pyarrow
```

## Testy

`python tests/test_basic.py` — testy smoke sprawdzające parser, integrację okna,
detekcję i podstawowy pipeline.
