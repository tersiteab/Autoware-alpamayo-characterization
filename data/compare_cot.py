import pandas as pd

a = pd.read_csv("frames_gen32.csv")
b = pd.read_csv("frames_gen64.csv")

merged = a.merge(b, on="cam_stamp", suffixes=("_32", "_64"))
print(f"gen32: {len(a)} frames, gen64: {len(b)} frames, matched: {len(merged)}")


for _, row in merged.iterrows():
    print(f"\n--- cam_stamp={row['cam_stamp']:.3f} scene={row['scene_32']} ---")
    print(f"[32 tok] {row['cot_32']}")
    print(f"[64 tok] {row['cot_64']}")


merged["len_32"] = merged["cot_32"].str.len()
merged["len_64"] = merged["cot_64"].str.len()
print(merged[["cam_stamp", "len_32", "len_64", "scene_32"]].describe())


scene_diff = merged[merged["scene_32"] != merged["scene_64"]]
print(f"Scene disagreements: {len(scene_diff)}/{len(merged)}")
print(scene_diff[["cam_stamp", "scene_32", "scene_64", "cot_32", "cot_64"]])
