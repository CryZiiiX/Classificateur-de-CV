#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, sys, re, html, json
from pathlib import Path
import pandas as pd

# -------- utils --------
def read_csv_auto(path: Path) -> pd.DataFrame:
    encs = ["utf-8", "utf-8-sig"]; seps = [",", ";", "\t"]; last = None
    for enc in encs:
        for sep in seps:
            try:
                df = pd.read_csv(path, dtype=str, sep=sep, encoding=enc, engine="python")
                if df.shape[1] == 1 and sep != "\t":  # mauvais séparateur
                    continue
                return df
            except Exception as e:
                last = e
    raise RuntimeError(f"Echec lecture {path} ({last})")

def std_rename(df: pd.DataFrame, mapping: dict):
    for target, choices in mapping.items():
        for c in choices:
            if c in df.columns:
                df.rename(columns={c: target}, inplace=True)
                break

def clean_label(s):
    if s is None: return s
    s = html.unescape(str(s))
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def guess_domain_from_text(text: str) -> str:
    s = (text or "").lower()
    if re.search(r"(ml|ia|deep|tensorflow|pytorch|bert|nlp|ner|apprentissage|modèle|llm)", s): return "AI/ML"
    if re.search(r"(data|sql|spark|hadoop|etl|airflow|bi|analyse|analyst|scientist|lake|warehouse)", s): return "Data"
    if re.search(r"(devops|cicd|ci/cd|docker|kubernetes|k8s|ansible|terraform|sre|observabilit)", s): return "DevOps"
    if re.search(r"(sécur|pentest|soc|siem|forensic|owasp|iso 27|rgpd|iam)", s): return "Security"
    if re.search(r"(réseau|network|tcp/ip|switch|routeur|firewall|cisco|sd-wan)", s): return "Network"
    if re.search(r"(cloud|aws|azure|gcp|eks|ecs|ec2|s3|aks|gke|kinesis|redshift|bigquery)", s): return "Cloud/Infra"
    if re.search(r"(test|qa|qualit|intégration continue|unitair|fonctionnel|selenium|cypress)", s): return "QA/Test"
    return "Software"

# -------- main --------
def main():
    ap = argparse.ArgumentParser(description="Construire ESCO_IT_Pair.csv et esco_jobs_to_skills.csv")
    ap.add_argument("--data-dir", type=str, required=True,
                    help="Dossier avec skills_fr.csv, occupations_fr.csv, occupationSkillRelations_fr.csv")
    args = ap.parse_args()

    BASE = Path(args.data_dir).expanduser().resolve()
    OUT = BASE / "esco_outputs"
    OUT.mkdir(exist_ok=True)

    # 1) lecture
    skills = read_csv_auto(BASE / "skills_fr.csv")
    occs   = read_csv_auto(BASE / "occupations_fr.csv")
    rels   = read_csv_auto(BASE / "occupationSkillRelations_fr.csv")

    std_rename(skills, {
        "skillUri": ["skillUri","conceptUri","uri"],
        "skillLabel": ["preferredLabel","prefLabel","label","title"],
    })
    std_rename(occs, {
        "occupationUri": ["occupationUri","conceptUri","uri"],
        "occupationLabel": ["preferredLabel","prefLabel","label","title"],
        "isco": ["iscoCode","iscoGroup","group","isco"],
    })
    std_rename(rels, {
        "occupationUri": ["occupationUri","occupation","occupationURI","occupationUri_x"],
        "skillUri": ["skillUri","skill","skillURI","skillUri_x"],
        "relationType": ["relationType","relation","type"],
    })

    # 2) nettoyage labels
    skills["skillLabel"] = skills["skillLabel"].apply(clean_label)
    occs["occupationLabel"] = occs["occupationLabel"].apply(clean_label)

    # 3) fusion relations -> skills -> occupations
    rels_clean = rels[["occupationUri","skillUri","relationType"]].copy()
    for c in rels_clean.columns:
        rels_clean[c] = rels_clean[c].astype(str).str.strip()

    pairs = (rels_clean
             .merge(skills[["skillUri","skillLabel"]].drop_duplicates(), on="skillUri", how="left")
             .merge(occs[["occupationUri","occupationLabel","isco"]].drop_duplicates(), on="occupationUri", how="left"))
    pairs = pairs.dropna(subset=["skillLabel","occupationLabel"]).drop_duplicates()

    # 4) filtre IT strict ISCO (25*, 35*)
    pairs_it = pairs[pairs["isco"].str.startswith(("25","35"), na=False)].copy()

    # 5) ajouter un label de domaine (pour les deux exports)
    pairs_it["label"] = [guess_domain_from_text(f"{s} {o}") for s, o in zip(pairs_it["skillLabel"], pairs_it["occupationLabel"])]

    # --------------------------
    # A) esco_jobs_to_skills.csv
    # --------------------------
    grouped = pairs_it.groupby(["occupationUri","occupationLabel","label"], dropna=False)
    recs = []
    for (occ_uri, occ_label, lab), g in grouped:
        essential = sorted(set(g.loc[g["relationType"].str.contains("essential", case=False, na=False), "skillLabel"]))
        optional  = sorted(set(g.loc[g["relationType"].str.contains("optional",  case=False, na=False), "skillLabel"]))
        unknown   = sorted(set(g.loc[~g["relationType"].str.contains("essential|optional", case=False, na=False), "skillLabel"]))
        recs.append({
            "occupationUri": occ_uri,
            "occupationLabel": occ_label,
            "label": lab,
            "skills_essential": json.dumps(essential, ensure_ascii=False),
            "skills_optional":  json.dumps(optional,  ensure_ascii=False),
            "skills_unknown":   json.dumps(unknown,  ensure_ascii=False),
            "n_total": len(set(essential) | set(optional) | set(unknown)),
        })
    jobs_multi = pd.DataFrame.from_records(recs).sort_values(["occupationLabel","label"])
    multi_out = OUT / "esco_jobs_to_skills.csv"
    jobs_multi.to_csv(multi_out, index=False, encoding="utf-8")
    print(f"MULTI -> {multi_out} ({len(jobs_multi)} métiers)")

    # --------------------------
    # B) ESCO_IT_Pair.csv
    # --------------------------
    weight_map = {"essential": 2.0, "optional": 1.0}
    tmp = pairs_it.copy()
    tmp["w"] = tmp["relationType"].str.lower().map(weight_map).fillna(1.0)
    scores = tmp.groupby(["skillLabel","label"], as_index=False)["w"].sum()
    top = (scores.sort_values(["skillLabel","w"], ascending=[True, False])
                 .groupby("skillLabel", as_index=False).first()[["skillLabel","label"]])
    skill2domain_out = OUT / "ESCO_IT_Pair.csv"
    top.to_csv(skill2domain_out, index=False, sep="|", header=False, encoding="utf-8")
    print(f"SKILL|DOMAIN -> {skill2domain_out} ({len(top)} lignes)")

    print("\n[i] Terminé.")

if __name__ == "__main__":
    main()

