# X1 rep1 x gemini-3.5-flash
Q: Using the Janaagraha iChangeMyCity complaints CSV on OpenCity (it has latitude and longitude columns) and the OpenStreetMap polygon for Bellandur lake, how many complaints fall within 1 km of the lake? Use haversine distance to the lake shoreline, not just the centroid. Show your working and citations.
elapsed:431s

---

### Final Results

There are exactly **283 complaints** in the Janaagraha iChangeMyCity dataset that fall within **1 km** of the OpenStreetMap shoreline polygon for Bellandur Lake.

---

### Data Sources & Citations

1. **Janaagraha iChangeMyCity Complaints Dataset**
   - **Source**: OpenCity Data Portal
   - **Dataset Name**: *I Change My City Complaints Log - 2019 - 2022* (curated by Vivek Mathew and Haji Shariefullah)
   - **Download Link**: [newdata.opencity.in/dataset/9183b0b2.../download/5f99b09a-64b5-45f0-ab18-4cf0a0cabf6d.csv](https://newdata.opencity.in/dataset/9183b0b2-b49a-40a9-b36d-275e1eaedb3f/resource/a60abf5c-3a15-4967-af32-c3074248580f/download/5f99b09a-64b5-45f0-ab18-4cf0a0cabf6d.csv)
   - **Volume**: 16,071 geotagged, non-null coordinate complaints.

2. **Bellandur Lake Boundary (OSM)**
   - **Source**: OpenStreetMap Official DB
   - **Feature Relation ID**: [Relation 19751547](https://www.openstreetmap.org/relation/19751547) (*natural=water*, *water=lake*, *type=multipolygon*)
   - **API Endpoint**: `https://www.openstreetmap.org/api/0.6/relation/19751547/full.json`
   - **Shoreline Nodes**: 410 coordinates forming 4 boundary ways representing the shoreline.

---

### Methodology & Mathematical Working

To calculate the exact great-circle (Haversine) distance from a complaint point $P$ to a shoreline segment $AB$ on the Earth's surface without projection distortions, we used 3D spherical vector algebra:

1. **Vector Representation**:
   Convert coordinates $(\phi, \lambda)$ of $P$, $A$, and $B$ to unit 3D Cartesian vectors on a sphere:
   \[
   \vec{v} = [\cos(\phi)\cos(\lambda), \; \cos(\phi)\sin(\lambda), \; \sin(\phi)]
   \]

2. **Great Circle Projection**:
   Find the unit normal vector $\vec{\hat{n}}$ to the plane containing the segment $AB$:
   \[
   \vec{\hat{n}} = \frac{\vec{a} \times \vec{b}}{\|\vec{a} \times \vec{b}\|}
   \]
   Project $\vec{p}$ onto this plane and normalize it to get the closest point $\vec{\hat{c}}_{\text{gc}}$ on the infinite great circle:
   \[
   \vec{p}_{\text{proj}} = \vec{p} - (\vec{p} \cdot \vec{\hat{n}})\vec{\hat{n}} \qquad \text{and} \qquad \vec{\hat{c}}_{\text{gc}} = \frac{\vec{p}_{\text{proj}}}{\|\vec{p}_{\text{proj}}\|}
   \]

3. **Segment Boundary Constraints**:
   $\vec{\hat{c}}_{\text{gc}}$ lies on the great-circle segment between $A$ and $B$ if and only if its angular distance to both $A$ and $B$ is less than the segment angle $\theta_{AB}$:
   \[
   \vec{\hat{c}}_{\text{gc}} \cdot \vec{a} \ge \vec{a} \cdot \vec{b} \quad \text{and} \quad \vec{\hat{c}}_{\text{gc}} \cdot \vec{b} \ge \vec{a} \cdot \vec{b}
   \]

4. **Minimum Distance Determination**:
   - If $\vec{\hat{c}}_{\text{gc}}$ is within the segment, the distance is: $d = R \cdot \arccos(\vec{p} \cdot \vec{\hat{c}}_{\text{gc}})$.
   - Otherwise, the closest point is one of the endpoints: $d = \min\big(R \cdot \arccos(\vec{p} \cdot \vec{a}), \; R \cdot \arccos(\vec{p} \cdot \vec{b})\big)$.
   *(where $R = 6,371,000$ meters is the Earth's mean radius)*

Here is the exact NumPy vector-accelerated python implementation of this spherical point-to-segment algorithm used to process all 16,071 records:

```60:143:/work/find_complaints.py
def point_to_segment_distance_numpy(p_lats, p_lons, seg_a_lats, seg_a_lons, seg_b_lats, seg_b_lons):
    """
    Computes exact spherical point-to-segment distance in meters for arrays of points and segments.
    p_lats, p_lons: shape (N,)
    seg_a_lats, seg_a_lons, seg_b_lats, seg_b_lons: shape (M,)
    Returns: distance matrix of shape (N, M)
    """
    R = 6371000.0  # Earth's radius in meters
    
    N = len(p_lats)
    M = len(seg_a_lats)
    
    # Convert lat/lon to 3D unit vectors
    # Shape: (N, 3)
    p_vecs = latlon_to_vector(p_lats, p_lons)
    # Shape: (M, 3)
    a_vecs = latlon_to_vector(seg_a_lats, seg_a_lons)
    b_vecs = latlon_to_vector(seg_b_lats, seg_b_lons)
    
    # Reshape for broadcasting
    # p_vecs: (N, 1, 3)
    p_vecs = p_vecs[:, np.newaxis, :]
    # a_vecs, b_vecs: (1, M, 3)
    a_vecs = a_vecs[np.newaxis, :, :]
    b_vecs = b_vecs[np.newaxis, :, :]
    
    # Cross product a x b to get normal vectors to the great circle planes
    # Shape: (1, M, 3)
    n_vecs = np.cross(a_vecs, b_vecs, axis=-1)
    n_norms = np.linalg.norm(n_vecs, axis=-1, keepdims=True)
    
    # Handle collinear segments (where a and b are identical)
    collinear_mask = (n_norms[..., 0] < 1e-12)
    
    # Standardize normal vectors
    # Shape: (1, M, 3)
    # Use np.where to avoid division by zero
    n_norms_safe = np.where(n_norms < 1e-12, 1.0, n_norms)
    u_n = n_vecs / n_norms_safe
    
    # Project p onto the great circle plane: p_proj = p - (p . u_n) * u_n
    # Dot product shape: (N, M, 1)
    dot_pu = np.sum(p_vecs * u_n, axis=-1, keepdims=True)
    p_proj = p_vecs - dot_pu * u_n
    p_proj_norms = np.linalg.norm(p_proj, axis=-1, keepdims=True)
    
    # Handle projections that are 0 (p is collinear with normal u_n)
    p_proj_norms_safe = np.where(p_proj_norms < 1e-12, 1.0, p_proj_norms)
    c_gc = p_proj / p_proj_norms_safe
    
    # Calculate dot products for boundary check
    dot_ab = np.sum(a_vecs * b_vecs, axis=-1)  # (1, M)
    dot_ca = np.sum(c_gc * a_vecs, axis=-1)    # (N, M)
    dot_cb = np.sum(c_gc * b_vecs, axis=-1)    # (N, M)
    
    # Broadcast dot_ab to (N, M)
    dot_ab_br = np.broadcast_to(dot_ab, (N, M))
    
    # Mask where projection falls inside the segment
    in_segment = (dot_ca >= dot_ab_br - 1e-12) & (dot_cb >= dot_ab_br - 1e-12)
    
    # Spherical distance to infinite great circle: acos(p . c_gc)
    dot_pc = np.sum(p_vecs * c_gc, axis=-1) # (N, M)
    dist_c = R * np.arccos(clip(dot_pc))
    
    # Spherical distance to endpoints: A and B
    dot_pa = np.sum(p_vecs * a_vecs, axis=-1) # (N, M)
    dot_pb = np.sum(p_vecs * b_vecs, axis=-1) # (N, M)
    dist_a = R * np.arccos(clip(dot_pa))
    dist_b = R * np.arccos(clip(dot_pb))
    dist_endpoints = np.minimum(dist_a, dist_b)
    
    # If point is normal to plane, default distance is pi/2 * R
    dist_c = np.where(p_proj_norms[..., 0] < 1e-12, R * (math.pi / 2.0), dist_c)
    
    # Choose between great circle projection or endpoints
    # Shape: (N, M)
    final_dist = np.where(in_segment, dist_c, dist_endpoints)
    
    # If segment is collinear/zero-length, use distance to A
    final_dist = np.where(collinear_mask, dist_a, final_dist)
    
    return final_dist
```

---

### Geographic Statistics (283 Complaints)

- **Minimum Shoreline Distance**: $4.36$ meters
- **Maximum Shoreline Distance**: $995.27$ meters
- **Mean Shoreline Distance**: $665.56$ meters

#### Top 5 Wards Reporting Near the Shoreline
1. **Bellanduru** (Ward ID 150): **134 complaints** (47.3%)
2. **Koramangala** (Ward ID 151): **40 complaints** (14.1%)
3. **HSR Layout** (Ward ID 174): **37 complaints** (13.1%)
4. **Agaram** (Ward ID 114): **36 complaints** (12.7%)
5. **Marathahalli** (Ward ID 86): **17 complaints** (6.0%)

#### Top Categories of Shoreline Complaints
- **Mobility (Roads, Footpaths & Infrastructure)**: **83 complaints** (29.3%) — *most commonly "Fixing/Repairing Potholes" (47 complaints)*
- **Garbage & Unsanitary Practices**: **57 complaints** (20.1%) — *most commonly "Clearance of Garbage Dump" (41 complaints)*
- **Traffic and Road Safety**: **33 complaints** (11.7%)
- **Yellow Spot**: **26 complaints** (9.2%)
- **Street lighting**: **21 complaints** (7.4%)The background Overpass API query tasks (both the global search and the bounded search) timed out or failed due to public Overpass servers experiencing high loads (HTTP 504 Gateway Timeout).

As a successful workaround, we used the fast **Photon API** to discover the active, precise OpenStreetMap Relation ID for Bellandur Lake (**19751547**). We then fetched its exact geometry directly from the official **OpenStreetMap API**, which successfully returned the 410 shoreline nodes. 

With this complete boundary, we calculated the exact spherical point-to-segment distances for all 16,071 geotagged complaints in the Janaagraha iChangeMyCity CSV, yielding **283 complaints** within 1 km of the shoreline. No further follow-up actions are needed!
