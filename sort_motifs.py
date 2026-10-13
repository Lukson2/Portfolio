#!/usr/bin/env python3
"""
sort_motifs.py - Razvršča slike motivov v strukturo:
  Sorted/
  └── [KODA]_[POLNO_IME]/
      ├── SI/  EN/  DE/  ES/  FR/  IT/  PT/
      └── (vsaka mapa vsebuje slike z ustrezno jezikovno kodo)

Uporaba:
  python sort_motifs.py <vhodna_mapa> [izhodna_mapa]

  <vhodna_mapa>  - mapa z nerazvrščenimi slikami
  [izhodna_mapa] - kjer nastane Sorted/ (privzeto: poleg vhodne mape)
"""

import os
import sys
import shutil
from pathlib import Path

JEZIKI = {"SI", "EN", "DE", "ES", "FR", "IT", "PT"}
PODPRTE_PRIPONE = {".webp", ".tif", ".jpg", ".jpeg", ".png", ".tif.webp"}


def razčleni_ime(ime_datoteke: str) -> tuple[str, str, str] | None:
    """
    Razčleni ime datoteke v (mapa_motiva, varianta, jezik).

    Pričakovan format: KODA_IME_..._VARIANTA_JEZIK.ext
    - Jezik je zadnji del pred pripono (SI, EN, DE ...)
    - Varianta vsebuje številke (npr. HC_710, W_913_NF)
    - Mapa motiva = vse do prve komponente s številko

    Vrne None, če datoteka ne ustreza pričakovanemu formatu.
    """
    pot = Path(ime_datoteke)

    # Odstrani pripone (.tif.webp, .webp, .tif ...)
    ime = pot.name
    for pripona in (".tif.webp", ".tif", ".webp", ".jpg", ".jpeg", ".png"):
        if ime.lower().endswith(pripona):
            ime = ime[: -len(pripona)]
            break
    else:
        return None

    deli = ime.split("_")
    if len(deli) < 3:
        return None

    # Zadnji del mora biti jezikovna koda
    jezik = deli[-1].upper()
    if jezik not in JEZIKI:
        return None

    # Ostalo: KODA_IME_VARIANTA
    ostalo = deli[:-1]

    # Varianta ima obliko: [KODA]_[ŠTEV]_[OPCIJSKI_SUFIKS]  npr. HC_710, W_913_NF
    # Prepoznamo jo tako, da poiščemo prvo komponento, ki je čisto iz cifer (npr. 710)
    # Varianta se začne EEN korak pred to komponento (npr. HC, W, C, M …)
    # Vse pred tem je KODA + POLNO_IME mape
    prvi_st_idx = None
    for i, del_ in enumerate(ostalo):
        if del_.isdigit():
            prvi_st_idx = i
            break

    if prvi_st_idx is None or prvi_st_idx < 2:
        # Ni najdene variante ali neveljavna struktura
        return None

    ime_deli = ostalo[:prvi_st_idx - 1]   # KODA + IME (brez zadnjega dela variante)
    varianta_deli = ostalo[prvi_st_idx - 1:]  # HC_710, W_913_NF …

    if not ime_deli:
        return None

    mapa_motiva = "_".join(ime_deli)
    varianta = "_".join(varianta_deli) if varianta_deli else ""

    return mapa_motiva, varianta, jezik


def razvrsti(vhodna_mapa: str, izhodna_mapa: str | None = None, kopija: bool = True):
    """
    Razvrsti vse podprte slike iz vhodne_mape v Sorted/ strukturo.

    kopija=True  → kopira datoteke (originali ostanejo)
    kopija=False → premakne datoteke
    """
    vhodna = Path(vhodna_mapa).resolve()
    if not vhodna.exists():
        print(f"NAPAKA: Mapa '{vhodna}' ne obstaja.")
        sys.exit(1)

    if izhodna_mapa:
        sorted_koren = Path(izhodna_mapa).resolve() / "Sorted"
    else:
        sorted_koren = vhodna.parent / "Sorted"

    sorted_koren.mkdir(parents=True, exist_ok=True)
    print(f"Izhodna mapa: {sorted_koren}\n")

    stevec_ok = 0
    stevec_preskoceno = 0
    neznane = []

    for datoteka in sorted(vhodna.rglob("*")):
        if not datoteka.is_file():
            continue

        # Preveri pripono
        ime = datoteka.name
        if not any(ime.lower().endswith(p) for p in PODPRTE_PRIPONE):
            continue

        razčlenitev = razčleni_ime(ime)
        if razčlenitev is None:
            neznane.append(str(datoteka.relative_to(vhodna)))
            stevec_preskoceno += 1
            continue

        mapa_motiva, varianta, jezik = razčlenitev

        # Ustvari pot: Sorted/KODA_IME/JEZIK/
        ciljna_mapa = sorted_koren / mapa_motiva / jezik
        ciljna_mapa.mkdir(parents=True, exist_ok=True)

        cilj = ciljna_mapa / ime
        if cilj.exists():
            print(f"  [OBSTAJA] {cilj.relative_to(sorted_koren)}")
            stevec_preskoceno += 1
            continue

        if kopija:
            shutil.copy2(datoteka, cilj)
            dejanje = "Kopirano"
        else:
            shutil.move(str(datoteka), str(cilj))
            dejanje = "Premaknjeno"

        print(f"  [{dejanje}] {ime}  →  {mapa_motiva}/{jezik}/")
        stevec_ok += 1

    print(f"\n{'='*60}")
    print(f"Razvrščenih:   {stevec_ok}")
    print(f"Preskočenih:   {stevec_preskoceno}")
    if neznane:
        print(f"\nDatoteke z neprepoznanim imenom ({len(neznane)}):")
        for n in neznane:
            print(f"  - {n}")
    print("Končano.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    vhodna = sys.argv[1]
    izhodna = sys.argv[2] if len(sys.argv) > 2 else None

    razvrsti(vhodna, izhodna, kopija=True)
