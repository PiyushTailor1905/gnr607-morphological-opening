"""Download sample Sentinel-2 L2A crops (public AWS COGs via Element84 Earth Search STAC).

Writes, for each site, a 1024x1024 true-colour PNG (B04,B03,B02 at 10 m) and a metadata JSON
into 04_Sample_Data/<site>/.  No account needed.  Usage: python fetch_data.py
"""
import json, sys, urllib.request
from pathlib import Path
import numpy as np, rasterio, cv2
from rasterio.windows import Window
from rasterio.warp import transform

STAC = "https://earth-search.aws.element84.com/v1/search"
SIZE = 1024  # pixels (= 10.24 km at 10 m)
SITES = {
    "urban_image": dict(lon=77.2090, lat=28.6139, label="New Delhi, India (urban core)"),
    "smooth_landscape_image": dict(lon=78.7600, lat=29.5300, label="Ramganga reservoir / Corbett forest, Uttarakhand, India"),
}

def search(lon, lat):
    d = 0.02
    body = {"collections": ["sentinel-2-l2a"], "bbox": [lon-d, lat-d, lon+d, lat+d], "limit": 20,
            "datetime": "2024-01-01T00:00:00Z/2026-06-30T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": 2}}}
    req = urllib.request.Request(STAC, json.dumps(body).encode(), {"Content-Type": "application/json"})
    feats = json.load(urllib.request.urlopen(req, timeout=60))["features"]
    feats.sort(key=lambda f: f["properties"]["eo:cloud_cover"])
    return feats

def read_band(href, lon, lat):
    with rasterio.open(href) as ds:
        x, y = transform("EPSG:4326", ds.crs, [lon], [lat]); r, c = ds.index(x[0], y[0])
        w = Window(c - SIZE//2, r - SIZE//2, SIZE, SIZE)
        return ds.read(1, window=w), ds.crs.to_string()

def main(out_root):
    for name, s in SITES.items():
        for f in search(s["lon"], s["lat"]):
            a = f["assets"]
            bands = [read_band(a[k]["href"], s["lon"], s["lat"]) for k in ("red", "green", "blue")]
            rgb = np.stack([b[0] for b in bands], -1).astype(np.float32)
            nodata = float((rgb.sum(-1) == 0).mean()); bright = float((rgb.min(-1) > 2400).mean())
            print("  candidate", f["id"], "nodata=%.3f cloudy=%.4f" % (nodata, bright))
            if nodata == 0 and bright < 0.002:   # whole window valid and essentially cloud-free
                break
        else:
            raise SystemExit("no clean scene found for " + name)
        # fixed reflectance stretch (same for both sites): L2A DN 0..3000 -> 0..255
        rgb8 = np.clip(rgb / 3000.0 * 255.0, 0, 255).astype(np.uint8)
        d = Path(out_root) / name; d.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(d / f"{name}.png"), rgb8[..., ::-1])
        meta = dict(site=s["label"], centre_lon=s["lon"], centre_lat=s["lat"], stac_item=f["id"],
                    acquisition=f["properties"]["datetime"], cloud_cover=f["properties"]["eo:cloud_cover"],
                    platform=f["properties"].get("platform"), crs=bands[0][1], size_px=SIZE, gsd_m=10,
                    bands="B04 (red), B03 (green), B02 (blue), stretch DN/3000*255",
                    source="https://earth-search.aws.element84.com/v1 (Sentinel-2 L2A COGs, ESA/Copernicus)",
                    item_url=f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{f['id']}")
        (d / f"{name}_metadata.json").write_text(json.dumps(meta, indent=2))
        print(name, f["id"], meta["acquisition"], meta["cloud_cover"])

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../04_Sample_Data")
